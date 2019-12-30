#!/usr/bin/env python
# -*- coding: utf-8 -*-


import logging
from influxdatabase import database
import requests
import datetime
import time

logger = logging.getLogger()


def measurement(cfg):
    db = get_db(cfg)
    logger.info('InfluxDB measurement name: '
                '\'{}\''.format(cfg['database']['measurement']))
    prev_data = get_previous_measurement(db, cfg)
    cur_data = get_bike_points(cfg)
    time_stamp = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')
    data_sets = []
    for entry in cur_data:
        fields = build_fields(entry)
        fields = calculate_fields(fields, prev_data)
        tags = build_tags(fields, ['id'])
        data_sets.append((fields, tags))
    save_data_set(db, cfg, data_sets, 'bike point', time_stamp)
    total_fields = calculate_totals(data_sets)
    tags = {}
    data_sets = [(total_fields, tags)]
    save_data_set(db, cfg, data_sets, 'bike points total', time_stamp)


def get_db(cfg):
    db = database.Database(host=cfg['database']['host'],
                           port=cfg['database']['port'],
                           dbuser=cfg['database']['user'],
                           dbuser_password=cfg['database']['password'],
                           dbname=cfg['database']['name'])
    return db


def get_previous_measurement(db, cfg):
    query = 'SELECT "NbDocks", "NbBikes", "NbEmptyDocks", "NbBrokenDocks" ' \
            'FROM "{}" GROUP BY id ' \
            'ORDER BY DESC LIMIT 1;'.format(cfg['database']['measurement'])
    logger.info('reading data set from previous measurement')
    result = db.client.query(query)
    result_series = result.raw.get('series', None)
    prev_data = {}
    if result_series:
        for bike_point in result_series:
            bike_point_id = bike_point['tags']['id']
            cols = bike_point['columns']
            for values in bike_point['values']:
                vals = values
            fields = dict(zip(cols, vals))
            prev_data[bike_point_id] = fields
    else:
        prev_data = None
    return prev_data


def get_bike_points(cfg):
    url = 'https://api.tfl.gov.uk/BikePoint?' \
          'app_key={}&app_id={}'.format(cfg['TfL_API']['app_key'],
                                        cfg['TfL_API']['app_id'])
    logger.info('requesting data from TfL API')
    response = requests.get(url)
    data = response.json()
    logger.info('received {} data sets'.format(len(data)))
    return data


def build_fields(entry):
    fields = dict(
        id=entry['id'],
        commonName=entry['commonName'],
        lon=entry['lon'], lat=entry['lat'],
    )
    for prop in entry['additionalProperties']:
        fields[prop['key']] = prop['value']
        fields[prop['key'] + '_modified'] = prop['modified']
    # convert type for some attributes
    fields['NbBikes'] = int(fields['NbBikes'])
    fields['NbDocks'] = int(fields['NbDocks'])
    fields['NbEmptyDocks'] = int(fields['NbEmptyDocks'])
    fields['Locked'] = fields['Locked'] in ['True', 'true']
    fields['Installed'] = fields['Installed'] in ['True', 'true']
    fields['Temporary'] = fields['Temporary'] in ['True', 'true']
    return fields


def calculate_fields(fields, prev_data):
    # add calculated data
    fields['NbBrokenDocks'] = fields['NbDocks'] - \
                              fields['NbBikes'] - fields['NbEmptyDocks']
    if fields['NbDocks'] == 0:
        logger.error('value of \'NbDocks\' attribute is zero. '
                     'received fields data = {}'.format(fields))
    else:
        fields['percentage_NbBikes'] = \
            fields['NbBikes'] / fields['NbDocks']
        fields['percentage_NbEmptyDocks'] = \
            fields['NbEmptyDocks'] / fields['NbDocks']
        fields['percentage_NbBrokenDocks'] = \
            fields['NbBrokenDocks'] / fields['NbDocks']
    if prev_data and prev_data.get(fields['id'], False):
        fields['delta_NbDocks'] = prev_data[fields['id']]['NbDocks'] - \
                                  fields['NbDocks']
        fields['delta_NbBikes'] = prev_data[fields['id']]['NbBikes'] - \
                                  fields['NbBikes']
        fields['delta_NbEmptyDocks'] = prev_data[fields['id']]['NbEmptyDocks'] - \
                                       fields['NbEmptyDocks']
        fields['delta_NbBrokenDocks'] = prev_data[fields['id']]['NbBrokenDocks'] - \
                                        fields['NbBrokenDocks']
    else:
        fields['delta_NbDocks'] = 0
        fields['delta_NbBikes'] = 0
        fields['delta_NbEmptyDocks'] = 0
        fields['delta_NbBrokenDocks'] = 0
    fields['abs_NbDocks'] = abs(fields['delta_NbDocks'])
    fields['abs_NbBikes'] = abs(fields['delta_NbBikes'])
    fields['abs_NbEmptyDocks'] = abs(fields['delta_NbEmptyDocks'])
    fields['abs_NbBrokenDocks'] = abs(fields['delta_NbBrokenDocks'])
    return fields


def build_tags(fields, fields_to_tags):
    # some fields are tags
    tags = {}
    for key in fields_to_tags:
        tags[key] = fields[key]
    return tags


def save_data_set(db, cfg, data_set, set_name, time_stamp):
    max_sets = len(data_set)
    nth_entry = max(max_sets // 20, 1)
    for idx, (fields, tags) in enumerate(data_set):
        if (idx + 1) % nth_entry == 0 or (idx + 1) == max_sets:
            logger.info('{} of {} {} data sets written '
                        'to database'.format(idx + 1, max_sets, set_name))
        save_to_database(db, cfg['database']['measurement'],
                         time_stamp, tags, fields)


def save_to_database(db, measurement, time_stamp, tags, fields):
    # write to database
    data_json = [{
        'measurement': measurement,
        'time': time_stamp,
        "tags": tags,
        'fields': fields,
    }]
    db.write(data_json)


def calculate_totals(data_sets):
    field_keys = ['NbBrokenDocks', 'NbBikes', 'NbDocks', 'NbEmptyDocks',
                  'abs_NbBrokenDocks', 'abs_NbBikes', 'abs_NbDocks', 'abs_NbEmptyDocks',
                  'delta_NbBrokenDocks', 'delta_NbBikes', 'delta_NbDocks', 'delta_NbEmptyDocks']
    total_fields = {}
    total_fields['total_BikeStations'] = len(data_sets)
    for key in field_keys:
        values = [fields[key] for fields, _ in data_sets]
        total_fields['total_' + key] = sum(values)
    total_fields['total_percentage_NbEmptyDocks'] = \
        total_fields['total_NbEmptyDocks'] / total_fields['total_NbDocks']
    total_fields['total_percentage_NbBikes'] = \
        total_fields['total_NbBikes'] / total_fields['total_NbDocks']
    total_fields['total_percentage_NbBrokenDocks'] = \
        total_fields['total_NbBrokenDocks'] / total_fields['total_NbDocks']
    return total_fields
