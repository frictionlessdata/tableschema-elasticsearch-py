# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import pytest
from mock import Mock
from tableschema_elasticsearch import mappers


# Tests

def test_descriptor_to_mapping():
    assert mappers.descriptor_to_mapping({
        'fields': [
            {'name': 'a-string', 'type': 'string'},
            {'name': 'an-int', 'type': 'integer'},
            {'name': 'a-number', 'type': 'number'},
            {'name': 'a-bool', 'type': 'boolean'},
            {'name': 'a-date', 'type': 'date', 'format': '%Y::%m::%d'},
            {'name': 'another-date', 'type': 'date'},
            {'name': 'a-datetime', 'type': 'datetime', 'format': '%Y::%m::%d T %H__%M__%S'},
            {'name': 'another-datetime', 'type': 'datetime'},
            {'name': 'a-time', 'type': 'time', 'format': '%H__%M__%S'},
            {'name': 'another-time', 'type': 'time'},
            {'name': 'an-array', 'type': 'array', 'es:itemType': 'string'},
            {'name': 'another-array', 'type': 'array', 'es:itemType': 'integer'},
            {'name': 'a-geopoint', 'type': 'geopoint'},
            {'name': 'an-object', 'type': 'object', 'es:schema': {'fields': [{'name': 'inner', 'type': 'integer'}]}},
            {'name': 'another-object', 'type': 'object', 'es:index': False},
        ]
    }) == {
     'properties': {'a-string': {'type': 'text'},
                    'an-int': {'type': 'long', 'ignore_malformed': True, 'index': False},
                    'a-number': {'type': 'scaled_float', 'scaling_factor': 100, 'ignore_malformed': True,
                                 'index': False},
                    'a-bool': {'type': 'boolean'},
                    'a-date': {'type': 'date', 'ignore_malformed': True, 'format': 'yyyy::MM::dd'},
                    'another-date': {'type': 'date', 'ignore_malformed': True, 'format': 'strict_date_optional_time'},
                    'a-datetime': {'type': 'date', 'ignore_malformed': True, 'format': 'yyyy::MM::dd \'T\' HH__mm__ss'},
                    'another-datetime': {'type': 'date', 'ignore_malformed': True,
                                         'format': 'strict_date_optional_time'},
                    'a-time': {'type': 'date', 'ignore_malformed': True, 'format': 'HH__mm__ss'},
                    'another-time': {'type': 'date', 'ignore_malformed': True, 'format': 'strict_date_optional_time'},
                    'an-array': {'type': 'text'},
                    'another-array': {'type': 'long', 'ignore_malformed': True, 'index': False},
                    'a-geopoint': {'type': 'geo_point', 'ignore_malformed': True,'index': False},
                    'an-object': {'properties': {'inner': {'type': 'long', 'ignore_malformed': True, 'index': False}},
                                  'enabled': True, 'dynamic': False},
                    'another-object': {'properties': {}, 'enabled': False, 'dynamic': False}}}


def test_descriptor_to_mapping_missing_itemtype():
    descriptor = {
        'fields': [{'name': 'name', 'type': 'array'}],
    }
    with pytest.raises(ValueError):
        mappers.descriptor_to_mapping(descriptor)


def test_descriptor_to_mapping_missing_schema():
    descriptor = {
        'fields': [{'name': 'name', 'type': 'object'}],
    }
    with pytest.raises(ValueError):
        mappers.descriptor_to_mapping(descriptor)
