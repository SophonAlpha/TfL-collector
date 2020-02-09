"""

Test suite for collector script.

coverage test ('pip install pytest-cov'):
    pytest --cov=collector tests/ --cov-report html --config <path to collector_config.yml>

"""
#!/usr/bin/env python
# -*- coding: utf-8 -*-


import pytest
import sys
import re

from collector import collector
from collector.tflbikepoints import tflbikepoints
from collector.influxdatabase import database

TARGET_CFG = [
    {
        'TfL_API': {
            'app_key': '<app key>',
            'app_id': '<app id>'
        },
        'database': {
            'host': '<host address>',
            'port': 8086,
            'user': '<user id>',
            'password': '<password>',
            'name': '<database name>',
            'measurement': '<measurement>'
        }
    },
]


@pytest.mark.parametrize('target_cfg', TARGET_CFG)
def test_get_script_config(target_cfg, pytestconfig):
    """ tests """
    sys.argv = ['', '-config', pytestconfig.getoption('config')]
    cfg = collector.get_script_config()
    assert cmp_dict_keys(cfg, target_cfg)


def test_measurement(pytestconfig):
    """
    Test the sequence of actions. Each step is dependent on the previous step.
    Therefore all actions in one test.
    """

    #  test get_db()

    sys.argv = ['', '-config', pytestconfig.getoption('config')]
    cfg = collector.get_script_config()
    db = tflbikepoints.get_db(cfg)

    assert isinstance(db, database.Database)

    #  test get_previous_measurement()

    prev_data = tflbikepoints.get_previous_measurement(db, cfg)
    regexec = re.compile(r'BikePoints_.*')
    assert all([isinstance(regexec.match(key), re.Match) for key in prev_data.keys()])
    expected = {'time', 'NbDocks', 'NbBikes', 'NbEmptyDocks', 'NbBrokenDocks'}
    first_key = list(prev_data.keys())[0]
    assert set(prev_data[first_key].keys()) == expected or prev_data is None

    #  test get_bike_points()

    cur_data = tflbikepoints.get_bike_points(cfg)
    assert isinstance(cur_data, list)
    expected = {'$type', 'id', 'url', 'commonName', 'placeType',
                'additionalProperties', 'children', 'childrenUrls',
                'lat', 'lon'}
    assert set(cur_data[0].keys()) == expected

    #  test build_fields()

    fields = tflbikepoints.build_fields(cur_data[0])
    expected = {'id', 'commonName', 'lon', 'lat', 'TerminalName',
                'TerminalName_modified', 'Installed',
                'Installed_modified', 'Locked', 'Locked_modified',
                'InstallDate', 'InstallDate_modified', 'RemovalDate',
                'RemovalDate_modified', 'Temporary',
                'Temporary_modified', 'NbBikes', 'NbBikes_modified',
                'NbEmptyDocks', 'NbEmptyDocks_modified', 'NbDocks',
                'NbDocks_modified'}
    assert set(fields.keys()) == expected

    #  test calculate_fields()

    fields = tflbikepoints.calculate_fields(fields, prev_data)
    expected = {'id', 'commonName', 'lon', 'lat', 'TerminalName',
                'TerminalName_modified', 'Installed',
                'Installed_modified', 'Locked', 'Locked_modified',
                'InstallDate', 'InstallDate_modified', 'RemovalDate',
                'RemovalDate_modified', 'Temporary',
                'Temporary_modified', 'NbBikes', 'NbBikes_modified',
                'NbEmptyDocks', 'NbEmptyDocks_modified', 'NbDocks',
                'NbDocks_modified', 'NbBrokenDocks',
                'percentage_NbBikes', 'percentage_NbEmptyDocks',
                'percentage_NbBrokenDocks', 'delta_NbDocks',
                'delta_NbBikes', 'delta_NbEmptyDocks',
                'delta_NbBrokenDocks', 'abs_NbDocks', 'abs_NbBikes',
                'abs_NbEmptyDocks', 'abs_NbBrokenDocks'}
    assert set(fields.keys()) == expected

    #  test build_tags()

    tags = tflbikepoints.build_tags(fields, ['id'])
    expected = {'id'}
    assert set(tags.keys()) == expected


def cmp_dict_keys(d1, d2):
    """
    Check if the keys and the type of the values in two dictionaries are the
    same. The check is done recursively.

    :param d1: first dictionary
    :param d2: second dictionary
    :return: True if keys() of d1 and d2 and any sub-keys are equal.
    Otherwise False.
    """

    equal = True
    if isinstance(d1, dict) and isinstance(d2, dict):
        for key in d1.keys():
            if key not in d2.keys():
                return False
            equal = cmp_dict_keys(d1[key], d2[key])
    elif type(d1) == type(d2):
        equal = True
    else:
        return False
    return equal



