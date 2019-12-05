#!/usr/bin/env python
# -*- coding: utf-8 -*-


import logging.handlers
import database
import requests
import datetime


logger = logging.getLogger('MyLogger')


def measurement(cfg):
    db = database.Database(host=cfg['database']['host'],
                           port=cfg['database']['port'],
                           dbuser=cfg['database']['user'],
                           dbuser_password=cfg['database']['password'],
                           dbname=cfg['database']['name'])
    prev_data = get_previous_measurement(db)
    cur_data = get_bike_points(cfg)
    time_stamp = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')
    for entry in process_list(cur_data):
        fields = build_fields(entry)
        fields = calculate_fields(fields, prev_data)
        tags = build_tags(fields, ['TerminalName', 'commonName', 'id'])
        save_to_database(db, 'BikePoints', time_stamp, tags, fields)


def get_previous_measurement(db):
    query = 'SELECT "NbDocks", "NbBikes", "NbEmptyDocks", "BrokenDocks" ' \
            'FROM "BikePoints" GROUP BY id ORDER BY DESC LIMIT 1;'
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


def process_list(data):
    max_sets = len(data)
    nth_entry = max_sets // 20
    for idx, entry in enumerate(data):
        if (idx + 1) % nth_entry == 0 or (idx + 1) == max_sets:
            logger.info('{} of {} data sets written '
                        'to database'.format(idx + 1, max_sets))
        yield entry


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
    fields['BrokenDocks'] = fields['NbDocks'] - \
                            fields['NbBikes'] - fields['NbEmptyDocks']
    fields['percentageBikes'] = fields['NbBikes'] / fields['NbDocks']
    fields['percentageBrokenDocks'] = fields['BrokenDocks'] / fields['NbDocks']
    if prev_data:
        fields['delta_NbDocks'] = prev_data[fields['id']]['NbDocks'] - \
                                  fields['NbDocks']
        fields['delta_NbBikes'] = prev_data[fields['id']]['NbBikes'] - \
                                  fields['NbBikes']
        fields['delta_NbEmptyDocks'] = prev_data[fields['id']]['NbEmptyDocks'] - \
                                       fields['NbEmptyDocks']
        fields['delta_BrokenDocks'] = prev_data[fields['id']]['BrokenDocks'] - \
                                      fields['BrokenDocks']
    else:
        fields['delta_NbDocks'] = 0
        fields['delta_NbBikes'] = 0
        fields['delta_NbEmptyDocks'] = 0
        fields['delta_BrokenDocks'] = 0
    fields['abs_NbDocks'] = abs(fields['delta_NbDocks'])
    fields['abs_NbBikes'] = abs(fields['delta_NbBikes'])
    fields['abs_NbEmptyDocks'] = abs(fields['delta_NbEmptyDocks'])
    fields['abs_BrokenDocks'] = abs(fields['delta_BrokenDocks'])
    return fields


def build_tags(fields, fields_to_tags):
    # some fields are tags
    tags = {}
    for key in fields_to_tags:
        tags[key] = fields[key]
    return tags


def save_to_database(db, measurement, time_stamp, tags, fields):
    # write to database
    data_json = [{
        'measurement': measurement,
        'time': time_stamp,
        "tags": tags,
        'fields': fields
    }]
    db.write(data_json)
