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
    - [Examples](#examples)
  - [Documentation](#documentation)
    - [Storage](#storage)
    - [Mappings](#mappings)
  - [Contributing](#contributing)
  - [Changelog](#changelog)

<!--TOC-->

## Getting Started

### Installation

The package use semantic versioning. It means that major versions  could include breaking changes. It's highly recommended to specify `package` version range in your `setup/requirements` file e.g. `package>=1.0,<2.0`.

```bash
pip install tableschema-elasticsearch
```

### Examples

Code examples in this readme requires Python 3.3+ interpreter. You could see even more example in [examples](https://github.com/frictionlessdata/tableschema-spss-py/tree/master/examples) directory.

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

```

## Documentation

The whole public API of this package is described here and follows semantic versioning rules. Everyting outside of this readme are private API and could be changed without any notification on any new version.

### Storage

Package implements [Tabular Storage](https://github.com/frictionlessdata/tableschema-py#storage) interface (see full documentation on the link):

![Storage](https://i.imgur.com/RQgrxqp.png)

This driver provides an additional API:

#### `Storage(es=None)`

- `es (object)` - `elasticsearch.Elastisearc` instance. If not provided new one will be created.

In this driver `elasticsearch` is used as the db wrapper. We can get storage this way:

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
        # reindex will copy existing documents from an existing index with the same name (in case of a mapping conflict)
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

## Contributing

The project follows the [Open Knowledge International coding standards](https://github.com/okfn/coding-standards).

Recommended way to get started is to create and activate a project virtual environment.
To install package and development dependencies into active environment:

```
$ make install
```

To run tests with linting and coverage:

```bash
$ make test
```

For linting `pylama` configured in `pylama.ini` is used. On this stage it's already
installed into your environment and could be used separately with more fine-grained control
as described in documentation - https://pylama.readthedocs.io/en/latest/.

For example to sort results by error type:

```bash
$ pylama --sort <path>
```

For testing `tox` configured in `tox.ini` is used.
It's already installed into your environment and could be used separately with more fine-grained control as described in documentation - https://testrun.org/tox/latest/.

For example to check subset of tests against Python 2 environment with increased verbosity.
All positional arguments and options after `--` will be passed to `py.test`:

```bash
tox -e py27 -- -v tests/<path>
```

Under the hood `tox` uses `pytest` configured in `pytest.ini`, `coverage`
and `mock` packages. This packages are available only in tox envionments.

## Changelog

Here described only breaking and the most important changes. The full changelog and documentation for all released versions could be found in nicely formatted [commit history](https://github.com/frictionlessdata/tableschema-elasticsearch-py/commits/master).

#### v1.0

- Initial driver implementation
