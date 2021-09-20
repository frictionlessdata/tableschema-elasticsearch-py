# tableschema-elasticsearch-py

[![Travis](https://img.shields.io/travis/frictionlessdata/tableschema-elasticsearch-py/master.svg)](https://travis-ci.org/frictionlessdata/tableschema-elasticsearch-py)
[![Coveralls](http://img.shields.io/coveralls/frictionlessdata/tableschema-elasticsearch-py/master.svg)](https://coveralls.io/r/frictionlessdata/tableschema-elasticsearch-py?branch=master)
[![PyPi](https://img.shields.io/pypi/v/tableschema-elasticsearch.svg)](https://pypi.python.org/pypi/tableschema-elasticsearch)
[![Github](https://img.shields.io/badge/github-master-brightgreen)](https://github.com/frictionlessdata/tableschema-elasticsearch-py)
[![Gitter](https://img.shields.io/gitter/room/frictionlessdata/chat.svg)](https://gitter.im/frictionlessdata/chat)

Generate and load ElasticSearch indexes based on [Table Schema](http://specs.frictionlessdata.io/table-schema/) descriptors.

## Features

- implements `tableschema.Storage` interface

## Contents

<!--TOC-->

  - [Getting Started](#getting-started)
    - [Installation](#installation)
  - [Documentation](#documentation)
    - [Usage overview](#usage-overview)
    - [Mappings](#mappings)
    - [Custom mappings](#custom-mappings)
  - [API Reference](#api-reference)
    - [`Storage`](#storage)
  - [Contributing](#contributing)
  - [Changelog](#changelog)

<!--TOC-->

## Getting Started

### Installation

The package use semantic versioning. It means that major versions  could include breaking changes. It's highly recommended to specify `package` version range in your `setup/requirements` file e.g. `package>=1.0,<2.0`.

```bash
pip install tableschema-elasticsearch
```

## Documentation

### Usage overview

```python
import elasticsearch
import jsontableschema_es

INDEX_NAME = 'testing_index'

# Connect to Elasticsearch instance running on localhost
es=elasticsearch.Elasticsearch()
storage=jsontableschema_es.Storage(es)

# List all indexes
print(list(storage.buckets))

# Create a new index
storage.create('test', {
         'fields': [
             {
                 'name': 'num',
                 'type': 'number'
             }
         ]
     }
)

# Write data to index
l=list(storage.write(INDEX_NAME, ({'num':i} for i in range(1000)), ['num']))
print(len(l))
print(l[:10], '...')

l=list(storage.write(INDEX_NAME, ({'num':i} for i in range(500,1500)), ['num']))
print(len(l))
print(l[:10], '...')

# Read all data from index
storage=jsontableschema_es.Storage(es)
print(list(storage.buckets))
l=list(storage.read(INDEX_NAME))
print(len(l))
print(l[:10])

```

In this driver `elasticsearch` is used as the db wrapper. We can get storage this way:

```python
from elasticsearch import Elasticsearch
from jsontableschema_elasticsearch import Storage

engine = Elasticsearch()
storage = Storage(engine)
```

Then we could interact with storage ('buckets' are ElasticSearch indexes in this context):

```python
storage.buckets # iterator over bucket names
storage.create('bucket', descriptor,
               reindex=False,
               always_recreate=False,
               mapping_generator_cls=None)
        # reindex will copy existing documents from an existing index with the same name (in case of a mapping conflict)
        # always_recreate will always recreate an index, even if it already exists. default is to update mappings only.
        # mapping_generator_cls allows customization of the generated mapping
storage.delete('bucket')
storage.describe('bucket') # return descriptor, not implemented yet
storage.iter('bucket') # yield rows
storage.read('bucket') # return rows
storage.write('bucket', rows, primary_key,
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

### Custom mappings

By providing a custom mapping generator class (via `mapping_generator_cls`), inheriting from the MappingGenerator class you should be able

## API Reference

### `Storage`
```python
Storage(self, es=None)
```
Elasticsearch Tabular Storage.

Package implements
[Tabular Storage](https://github.com/frictionlessdata/tableschema-py#storage)
interface (see full documentation on the link):

![Storage](https://i.imgur.com/RQgrxqp.png)

> Only additional API is documented

__Arguments__
- __es (object)__: ElasticSearch instance


#### `storage.create`
```python
storage.create(self, bucket, descriptor, reindex=False, always_recreate=False, mapping_generator_cls=None, index_settings=None)
```
Create index with mapping by schema.

__Arguments__
- __bucket(str)__:
        Name of index to be created
- __descriptor__:
        dDscriptor of index to be created
- __always_recreate__:
        Delete index if already exists (otherwise just update mapping)
- __reindex__:
        On mapping mismath, automatically create
        new index and migrate existing indexes to it
- __mapping_generator_cls__:
        subclass of MappingGenerator
- __index_settings__:
        settings which will be used in index creation


#### `storage.delete`
```python
storage.delete(self, bucket=None)
```
Delete index with mapping by schema.

__Arguments__
- __bucket(str)__: Name of index to delete


## Contributing

> The project follows the [Open Knowledge International coding standards](https://github.com/okfn/coding-standards).

Recommended way to get started is to create and activate a project virtual environment.
To install package and development dependencies into active environment:

```bash
$ make install
```

To run tests with linting and coverage:

```bash
$ make test
```

## Changelog

Here described only breaking and the most important changes. The full changelog and documentation for all released versions could be found in nicely formatted [commit history](https://github.com/frictionlessdata/tableschema-elasticsearch-py/commits/master).

#### v1.0

- Initial driver implementation
