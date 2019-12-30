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
from tflbikepoints import tflbikepoints
import influxdatabase

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


def test_get_db(pytestconfig):
    """ tests """
    sys.argv = ['', '-config', pytestconfig.getoption('config')]
    cfg = collector.get_script_config()
    db = tflbikepoints.get_db(cfg)
    assert isinstance(db, influxdatabase.database.Database)


def test_get_previous_measurement(pytestconfig):
    """ tests """
    sys.argv = ['', '-config', pytestconfig.getoption('config')]
    cfg = collector.get_script_config()
    db = tflbikepoints.get_db(cfg)
    prev_data = tflbikepoints.get_previous_measurement(db, cfg)
    regexec = re.compile(r'BikePoints_.*')
    assert all([isinstance(regexec.match(key), re.Match) for key in prev_data.keys()])
    expected_attributes = set(['time', 'NbDocks', 'NbBikes', 'NbEmptyDocks',
                              'NbBrokenDocks'])
    first_key = list(prev_data.keys())[0]
    assert set(prev_data[first_key].keys()) == expected_attributes


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



