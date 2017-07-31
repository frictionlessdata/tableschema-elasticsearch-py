# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import datetime
import itertools
import collections
import uuid

from elasticsearch import Elasticsearch
from elasticsearch.helpers import streaming_bulk

from . import mappers


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
        today = datetime.datetime.now().strftime('%Y%m%d')
        return '{}_{}_{}'.format(bucket, today, uid)

    def generate_doc_id(self, row, primary_key):
        return '/'.join([str(row.get(k)) for k in primary_key])

    def create(self, bucket, doc_types,
               reindex=False, mapping_generator_cls=None):
        """Create index with mapping by schema.

        Parameters
        ----------
        bucket: str
            Name of index to be created
        doc_types: list<(doc_type, descriptor)>
            List of tuples of doc_types and matching descriptors

        """
        existing_index_names = []
        if self.__es.indices.exists_alias(name=bucket):
            existing_index_names = self.__es.indices.get_alias(bucket)
            existing_index_names = list(existing_index_names.keys())
        index_name = self.get_index_name(bucket)
        self.__es.indices.create(index_name)
        self.__es.indices.put_alias(index_name, bucket)

        for doc_type, descriptor in doc_types:
            mapping = mappers.descriptor_to_mapping(
                descriptor, mapping_generator_cls=mapping_generator_cls
            )
            self.__es.indices.put_mapping(doc_type, mapping, index=index_name)

        if reindex:
            raise NotImplementedError
        else:
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
            results = self.__es.search(index=bucket,
                                       doc_type=doc_type,
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

    def write(self, bucket, doc_type, rows, primary_key, as_generator=False):

        if primary_key is None or len(primary_key) == 0:
            raise ValueError('primary_key cannot be an empty list')

        def actions(rows_, doc_type_, primary_key_):
            for row in rows_:
                yield {
                    '_op_type': 'index',
                    '_index': bucket,
                    '_type': doc_type_,
                    '_id': self.generate_doc_id(row, primary_key_),
                    '_source': row
                }

        iterables = itertools.tee(rows)
        actions_iterable = actions(iterables[0], doc_type, primary_key)

        iter = zip(streaming_bulk(self.__es, actions=actions_iterable), iterables[1])

        if as_generator:
            for result, row in iter:
                yield row
        else:
            collections.deque(iter, maxlen=0)

        self.__es.indices.flush(bucket)
