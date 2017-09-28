import elasticsearch
import jsontableschema_es

INDEX_NAME = 'testing_index'

es=elasticsearch.Elasticsearch()
storage=jsontableschema_es.Storage(es)
print(list(storage.buckets))


s.create('test', [
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

l=list(s.write(INDEX_NAME, 'numbers', ({'num':i} for i in range(1000)), ['num']))
print(len(l))
print(l[:10])

l=list(storage.write(INDEX_NAME, 'numbers', ({'num':i} for i in range(1000)), ['num']))
print(len(l))
print(l[:10])

storage=jsontableschema_es.Storage(es)
print(list(storage.buckets))
l=list(storage.read(INDEX_NAME))
print(len(l))
print(l[:10])
