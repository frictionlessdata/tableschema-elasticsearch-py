# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import six
import json
import io
from tabulator import Stream
from elasticsearch import Elasticsearch
from tableschema_elasticsearch import Storage


# Tests

def test_storage():

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
    storage.create(
            'unit-tests',
            [('articles', articles_descriptor),
             ('comments', comments_descriptor)])

    # Write data to buckets
    list(storage.write('unit-tests', 'articles', articles_rows, articles_descriptor['primaryKey']))
    gen = storage.write('unit-tests', 'comments', comments_rows,
                        comments_descriptor['primaryKey'], as_generator=True)
    lst = list(gen)
    assert len(lst) == 1

    # Create new storage to use reflection only
    storage = Storage(engine)

    # Assert representation
    assert repr(storage).startswith('Storage')

    # Assert buckets
    assert sorted(list(storage.buckets)) == ['unit-tests']

    # Assert descriptors
    # assert storage.describe('articles') == sync_descriptor(articles_descriptor)
    # assert storage.describe('comments') == sync_descriptor(comments_descriptor)

    # Assert rows
    print(storage.read('unit-tests'))
    assert sorted(list(storage.read('unit-tests', doc_type='articles')),
                  key=lambda x:x['id']) == articles_rows
    assert list(storage.read('unit-tests', doc_type='comments')) == comments_rows

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
