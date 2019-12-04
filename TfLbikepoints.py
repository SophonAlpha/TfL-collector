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
    data = get_bike_points(cfg)
    time_stamp = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')
    max_sets = len(data)
    nth_entry = max_sets // 20
    for idx, entry in enumerate(data):
        fields, tags = get_fields_tags(entry)
        save_to_database(db, 'BikePoints', time_stamp, tags, fields)
        if (idx + 1) % nth_entry == 0 or (idx + 1) == max_sets:
            logger.info('{} of {} data sets written '
                        'to database'.format(idx + 1, max_sets))
    save_to_database(db, data)


def get_previous_measurement(db):
    query = 'SELECT "NbDocks", "NbBikes", "NbEmptyDocks" FROM "BikePoints" ' \
            'GROUP BY id ORDER BY DESC LIMIT 1;'
    result = db.client.query(query)
    prev_data = []
    for bike_point in result.raw['series']:
        bike_point_id = bike_point['tags']['id']
        cols = bike_point['columns']
        for values in bike_point['values']:
            vals = values
        fields = dict(zip(cols, vals))
        prev_data.append({bike_point_id: fields})
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


def get_fields_tags(entry):
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
    # add calculated data
    fields['BrokenDocks'] = fields['NbDocks'] - \
                            fields['NbBikes'] - fields['NbEmptyDocks']
    fields['percentageBikes'] = fields['NbBikes'] / fields['NbDocks']
    fields['percentageBrokenDocks'] = fields['BrokenDocks'] / \
                                      fields['NbDocks']
    # some fields are tags
    tags = {}
    for key in ['TerminalName', 'commonName', 'id']:
        tags[key] = fields[key]
        fields.pop(key, None)  # remove fields that are now tags
    return fields, tags


def save_to_database(db, measurement, time_stamp, tags, fields):
    # write to database
    data_json = [{
        'measurement': measurement,
        'time': time_stamp,
        "tags": tags,
        'fields': fields
    }]
    db.write(data_json)
