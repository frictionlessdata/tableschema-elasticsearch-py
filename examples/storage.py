# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import elasticsearch
import jsontableschema_es

INDEX_NAME = 'testing_index'

# Connect to Elasticsearch instance running on localhost
es=elasticsearch.Elasticsearch()
storage=jsontableschema_es.Storage(es)

# List all indexes
print(list(storage.buckets))

# Create a new index
storage.create('test', [
    ('numbers',
     {
         'fields': [
             {
                 'name': 'num',
                 'type': 'number'
             }
         ]
     })
])

# Write data to index
l=list(storage.write(INDEX_NAME, 'numbers', ({'num':i} for i in range(1000)), ['num']))
print(len(l))
print(l[:10], '...')

l=list(storage.write(INDEX_NAME, 'numbers', ({'num':i} for i in range(500,1500)), ['num']))
print(len(l))
print(l[:10], '...')

# Read all data from index
storage=jsontableschema_es.Storage(es)
print(list(storage.buckets))
l=list(storage.read(INDEX_NAME))
print(len(l))
print(l[:10])
