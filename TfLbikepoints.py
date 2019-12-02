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
    data = get_bike_points(cfg)
    save_to_database(db, data)


def get_bike_points(cfg):
    url = 'https://api.tfl.gov.uk/BikePoint?' \
          'app_key={}&app_id={}'.format(cfg['TfL_API']['app_key'],
                                        cfg['TfL_API']['app_id'])
    logger.info('requesting data from TfL API')
    response = requests.get(url)
    data = response.json()
    logger.info('received {} data sets'.format(len(data)))
    return data


def save_to_database(db, data):
    nth_entry = 30
    logger.info('saving data sets to database')
    time_stamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    for idx, entry in enumerate(data):
        db_data = dict(id=entry['id'],
                       commonName=entry['commonName'],
                       lon=entry['lon'], lat=entry['lat'],)
        for prop in entry['additionalProperties']:
            db_data[prop['key']] = prop['value']
            db_data[prop['key'] + '_modified'] = prop['modified']
        data_json = [{
            'measurement': db_data['id'],
            'time': time_stamp,
            'fields': db_data
        }]
        db.write(data_json)
        if (idx + 1) % nth_entry == 0 or (idx + 1) == len(data):
            logger.info('{} data sets written to database'.format(idx + 1))
