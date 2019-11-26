# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import sys
import datetime
import itertools
import collections
import uuid

import logging
from elasticsearch import Elasticsearch
from elasticsearch.helpers import streaming_bulk
from elasticsearch.exceptions import RequestError

from . import mappers


tracer = logging.getLogger('elasticsearch')
tracer.setLevel(logging.CRITICAL)
tracer.addHandler(logging.StreamHandler(sys.stderr))

# Module API


class Storage(object):
    """Elasticsearch Tabular Storage.

    It's an implementation of `tableschema.Storage`.

    Args:
        es (object): ElasticSearch instance
    """

    # Public

    def __init__(self, es=None):
        # Use the passed `es` or create a new Elasticsearch instance
        self.__es = es if es is not None else Elasticsearch()
        self.__no_mapping_types = self.__es.info()['version']['number'] >= '7'

    def __repr__(self):
        # Template and format
        template = 'Storage {engine}'
        text = template.format(engine=self.__es)
        return text

    @property
    def buckets(self):
        indexes = self.__es.indices.get_alias('*')
        for index_name, index in indexes.items():
            for alias_name in index.get('aliases', {}).keys():
                yield alias_name

    def get_index_name(self, bucket):
        uid = str(uuid.uuid4())[:8]
        today = datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')
        return '{}_{}_{}'.format(bucket, today, uid)

    def create_index(self, bucket, index_settings=None):
        index_name = self.get_index_name(bucket)
        body = None
        if index_settings is not None:
            body = dict(
                settings=index_settings
            )
        self.__es.indices.create(index_name, body=body)
        self.__es.indices.put_alias(index_name, bucket)
        return index_name

    def put_mapping(self, bucket, doc_types, index_name, mapping_generator_cls):
        for doc_type, descriptor in doc_types:
            mapping = mappers.descriptor_to_mapping(
                descriptor, mapping_generator_cls=mapping_generator_cls
            )
            params = dict()
            if doc_type is not None and self.__no_mapping_types:
                params = dict(include_type_name='true')
            self.__es.indices.put_mapping(mapping, doc_type=doc_type,
                                          index=index_name, params=params)

    def generate_doc_id(self, row, primary_key):
        return '/'.join([str(row.get(k)) for k in primary_key])

    def create(self, bucket, doc_types,
               reindex=False, always_recreate=False,
               mapping_generator_cls=None, index_settings=None):
        """Create index with mapping by schema.

        Parameters
        ----------
        bucket: str
            Name of index to be created
        doc_types: list<(doc_type, descriptor)>
            List of tuples of doc_types and matching descriptors
        always_recreate: Delete index if already exists (otherwise just update mapping)
        reindex: On mapping mismath, automatically create new index and migrate existing
                 indexes to it
        mapping_generator_cls: subclass of MappingGenerator
        index_settings: settings which will be used in index creation
        """
        existing_index_names = []
        if self.__es.indices.exists_alias(name=bucket):
            existing_index_names = self.__es.indices.get_alias(bucket)
            existing_index_names = sorted(existing_index_names.keys())

        if len(existing_index_names) == 0 or always_recreate:
            index_name = self.create_index(bucket, index_settings=index_settings)
            self.put_mapping(bucket, doc_types, index_name, mapping_generator_cls)

        else:
            index_name = existing_index_names[-1]
            try:
                self.put_mapping(bucket, doc_types, index_name, mapping_generator_cls)
                existing_index_names.pop(-1)

            except RequestError:
                if reindex:
                    index_name = self.create_index(bucket, index_settings=index_settings)
                    self.put_mapping(bucket, doc_types, index_name, mapping_generator_cls)
                else:
                    raise

        if reindex and len(existing_index_names) > 0:
            reindex_body = dict(
                source=dict(
                    index=existing_index_names
                ),
                dest=dict(
                    index=index_name,
                    version_type='external'
                )
            )
            self.__es.reindex(reindex_body)
            self.__es.indices.flush()

            for existing_index_name in existing_index_names:
                self.__es.indices.delete(existing_index_name)

    def delete(self, bucket=None):
        """Delete index with mapping by schema.

        Parameters
        ----------
        bucket: str
             Name of index to delete

        """
        def internal_delete(bucket):
            if self.__es.indices.exists_alias(name=bucket):
                existing_index_names = self.__es.indices.get_alias(bucket)
                existing_index_names = list(existing_index_names.keys())
                for existing_index_name in existing_index_names:
                    self.__es.indices.delete(existing_index_name)

        if bucket is None:
            for bucket in self.buckets:
                internal_delete(bucket)
        else:
            internal_delete(bucket)

    def describe(self, bucket, descriptor=None):
        raise NotImplementedError()

    def iter(self, bucket, doc_type=None):
        from_ = 0
        size = 100
        done = False
        while not done:
            body = None
            if doc_type is not None:
                body = dict(
                    query=dict(
                        bool=dict(
                            filter=dict(
                                match=dict(
                                    _type=doc_type
                                )
                            )
                        )
                    )
                )
            results = self.__es.search(index=bucket,
                                       body=body,
                                       from_=from_,
                                       size=size)
            hits = results.get('hits', {}).get('hits', [])
            for source in hits:
                yield source.get('_source')
            done = len(hits) == 0
            from_ += size

    def read(self, bucket, doc_type=None):
        # Get rows
        rows = list(self.iter(bucket, doc_type=doc_type))

        return rows

    def write(self, bucket, doc_type, rows, primary_key, update=False, as_generator=False):

        if primary_key is None or len(primary_key) == 0:
            raise ValueError('primary_key cannot be an empty list')

        def actions(rows_, doc_type_, primary_key_, update_):
            if update_:
                for row_ in rows_:
                    yield {
                        '_op_type': 'update',
                        '_index': bucket,
                        '_type': doc_type_,
                        '_id': self.generate_doc_id(row_, primary_key_),
                        '_source': {
                            'doc': row_,
                            'doc_as_upsert': True
                        }
                    }
            else:
                for row_ in rows_:
                    yield {
                        '_op_type': 'index',
                        '_index': bucket,
                        '_type': doc_type_,
                        '_id': self.generate_doc_id(row_, primary_key_),
                        '_source': row_
                    }

        iterables = itertools.tee(rows)
        actions_iterable = actions(iterables[0], doc_type, primary_key, update)

        iter = zip(streaming_bulk(self.__es, actions=actions_iterable), iterables[1])

        if as_generator:
            for result, row in iter:
                yield row
        else:
            collections.deque(iter, maxlen=0)

        self.__es.indices.flush(bucket)
