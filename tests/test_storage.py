# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import six
import json
import io
import time
import pytest
import logging
from tabulator import Stream
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import RequestError
from tableschema_elasticsearch import Storage


# Tests
def test_reindex():
    # Prepare data
    articles_rows = Stream('data/articles.csv').open().iter()
    headers = next(articles_rows)
    schema = dict(
        fields=[
            dict(
                name=name,
                type='string'
            )
            for name in headers
        ],
        primaryKey=['id']
    )
    datas = [
        dict(zip(headers, row)) for row in articles_rows
    ]

    # Prepare engine
    engine = Elasticsearch()
    storage = Storage(engine)
    storage.delete()
    storage.create('reindexing', schema)
    
    # Write data
    list(storage.write('reindexing', datas, schema['primaryKey']))

    engine.indices.flush('_all')
    time.sleep(3)

    assert sorted(list(storage.read('reindexing')), key=lambda x:x['id']) == datas

    # Prepare engine
    engine = Elasticsearch()
    storage = Storage(engine)
    assert sorted(list(storage.read('reindexing')), key=lambda x:x['id']) == datas

    # Modify schema
    for f in schema['fields']:
        if f['name'] == 'created_year':
            f['type'] = 'integer'
        if f['name'] == 'created_date':
            f['type'] = 'date'

    try:
        storage.create('reindexing', schema)
        assert False
    except:
        pass

    # Prepare engine
    engine = Elasticsearch()
    storage = Storage(engine)
    assert sorted(list(storage.read('reindexing')), key=lambda x:x['id']) == datas

    assert(len(engine.indices.get_alias('reindexing'))==1)

    # Reindex with new schema    
    storage.create('reindexing', schema, reindex=True)

    engine.indices.flush('_all')
    time.sleep(3)

    # Prepare engine
    engine = Elasticsearch()
    storage = Storage(engine)
    assert(len(engine.indices.get_alias('reindexing'))==1)
    assert sorted(list(storage.read('reindexing')), key=lambda x:x['id']) == datas
    assert(len(engine.indices.get_alias('reindexing'))==1)


def test_basic_flow():

    # Get resources
    articles_descriptor = json.load(io.open('data/articles.json', encoding='utf-8'))
    comments_descriptor = json.load(io.open('data/comments.json', encoding='utf-8'))
    articles_rows = Stream('data/articles.csv', headers=1).open().read(keyed=True)
    comments_rows = Stream('data/comments.csv', headers=1).open().read(keyed=True)

    # Engine
    engine = Elasticsearch()

    # Storage
    storage = Storage(engine)

    # Delete buckets
    storage.delete()

    # Create buckets
    storage.create('unit-tests-articles', articles_descriptor)
    storage.create('unit-tests-comments', comments_descriptor)

    # Write data to buckets
    list(storage.write('unit-tests-articles', articles_rows, articles_descriptor['primaryKey']))
    gen = storage.write('unit-tests-comments', comments_rows,
                        comments_descriptor['primaryKey'], as_generator=True)
    lst = list(gen)
    assert len(lst) == 1

    engine.indices.flush('_all')
    time.sleep(3)

    # Create new storage to use reflection only
    storage = Storage(engine)

    # Assert representation
    assert repr(storage).startswith('Storage')

    # Assert buckets
    assert sorted(list(storage.buckets)) == ['unit-tests-articles', 'unit-tests-comments']

    # Assert descriptors
    # assert storage.describe('articles') == sync_descriptor(articles_descriptor)
    # assert storage.describe('comments') == sync_descriptor(comments_descriptor)

    # Assert rows
    print(storage.read('unit-tests-articles'))
    print(storage.read('unit-tests-comments'))
    assert sorted(list(storage.read('unit-tests-articles')),
                  key=lambda x:x['id']) == articles_rows
    assert list(storage.read('unit-tests-comments')) == comments_rows

    # Test update mode
    articles_rows.append({
        'id': 'last-one',
        'name': 'My last article',
    })
    updates = [
        dict(
            id=article['id'],
            index='%08d' % i
        )
        for i, article in enumerate(articles_rows)
    ]
    list(storage.write('unit-tests-articles', updates,
                       articles_descriptor['primaryKey'],
                       update=True))
    list(storage.write('unit-tests-articles', [articles_rows[-1]],
                       articles_descriptor['primaryKey'],
                       update=True))
    for a, u in zip(articles_rows, updates):
        a.update(u)

    engine.indices.flush('_all')
    time.sleep(3)

    assert sorted(list(storage.read('unit-tests-articles')),
                  key=lambda x:x['id']) == articles_rows

    # Delete buckets
    storage.delete()


def test_es_instance():
    '''An Elasticsearch instance can be passed to Storage or will be created'''
    storage = Storage()
    assert repr(storage) == "Storage <Elasticsearch([{}])>"

    es = Elasticsearch(['localhost'])
    storage = Storage(es)

    if six.PY2:
        assert repr(storage) == "Storage <Elasticsearch([{u'host': u'localhost'}])>"
    else:
        assert repr(storage) == "Storage <Elasticsearch([{'host': 'localhost'}])>"
