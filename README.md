# tableschema-elasticsearch-py

[![Travis](https://img.shields.io/travis/frictionlessdata/tableschema-elasticsearch-py/master.svg)](https://travis-ci.org/frictionlessdata/tableschema-elasticsearch-py)
[![Coveralls](http://img.shields.io/coveralls/frictionlessdata/tableschema-elasticsearch-py/master.svg)](https://coveralls.io/r/frictionlessdata/tableschema-elasticsearch-py?branch=master)
[![PyPi](https://img.shields.io/pypi/v/tableschema-elasticsearch-py.svg)](https://pypi.python.org/pypi/tableschema-elasticsearch-py)
[![SemVer](https://img.shields.io/badge/versions-SemVer-brightgreen.svg)](http://semver.org/)
[![Gitter](https://img.shields.io/gitter/room/frictionlessdata/chat.svg)](https://gitter.im/frictionlessdata/chat)

Generate and load ElasticSearch indexes based on JSON Table Schema descriptors.

## Getting Started

### Installation

```bash
pip install tableschema-elasticsearch
```

### Storage

Package implements [Tabular Storage](https://github.com/frictionlessdata/jsontableschema-py#storage) interface.

`elasticsearch` is used as the db wrapper. We can get storage this way:

```python
from elasticsearch import Elasticsearch
from jsontableschema_sql import Storage

engine = Elasticsearch()
storage = Storage(engine)
```

Then we could interact with storage ('buckets' are ElasticSearch indexes in this context):

```python
storage.buckets # iterator over bucket names
storage.create('bucket', [(doc_type, descriptor)], 
               reindex=False,
               always_recreate=False,
               mapping_generator_cls=None)
        # reindex will copy existing documents from an existing index with the same name (not implemented yet)
        # always_recreate will always recreate an index, even if it already exists. default is to update mappings only.
        # mapping_generator_cls allows customization of the generated mapping  
storage.delete('bucket')
storage.describe('bucket') # return descriptor, not implemented yet
storage.iter('bucket', doc_type=optional) # yield rows
storage.read('bucket', doc_type=optional) # return rows
storage.write('bucket', doc_type, rows, primary_key,
              as_generator=False)
        # primary_key is a list of field names which will be used to generate document ids 
```

When creating indexes, we always create an index with a semi-random name and a matching alias that points to it. This allows us to decide whether to re-index documents whenever we're re-creating an index, or to discard the existing records.


### Mappings

When creating indexes, the tableschema types are converted to ES types and a mapping is generated for the index.

Some special properties in the schema provide extra information for generating the mapping:
 - `array` types need also to have the `es:itemType` property which specifies the inner data type of array items.
 - `object` types need also to have the `es:schema` property which provides a tableschema for the inner document contained in that object (or have `es:enabled=false` to disable indexing of that field).

Example:
```json
{
  "fields": [
    {
      "name": "my-number", 
      "type": "number"
    },
    {
      "name": "my-array-of-dates", 
      "type": "array",
      "es:itemType": "date"
    },
    {
      "name": "my-person-object", 
      "type": "object",
      "es:schema": {
        "fields": [
          {"name": "name", "type": "string"},
          {"name": "surname", "type": "string"},
          {"name": "age", "type": "integer"},
          {"name": "date-of-birth", "type": "date", "format": "%Y-%m-%d"}
        ]
      }
    },
    {
      "name": "my-library", 
      "type": "array",
      "es:itemType": "object",
      "es:schema": {
        "fields": [
          {"name": "title", "type": "string"},
          {"name": "isbn", "type": "string"},
          {"name": "num-of-pages", "type": "integer"}
        ]
      }
    },
    {
      "name": "my-user-provded-object", 
      "type": "object",
      "es:enabled": false
    }    
  ]
}
```

#### Custom mappings
By providing a custom mapping generator class (via `mapping_generator_cls`), inheriting from the MappingGenerator class you should be able


### Drivers

`elasticsearch-py` is used to access the ElasticSearch interface - [docs](https://elasticsearch-py.readthedocs.io/en/master/).

## API Reference

### Snapshot

https://github.com/frictionlessdata/tableschema-elasticsearch-py#snapshot

### Detailed

- [Changelog](https://github.com/frictionlessdata/tableschema-elasticsearch-py/commits/master)

## Contributing

Please read the contribution guideline:

[How to Contribute](CONTRIBUTING.md)

Thanks!
