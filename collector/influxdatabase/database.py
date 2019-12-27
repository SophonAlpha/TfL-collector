#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from influxdb import InfluxDBClient
import requests


logger = logging.getLogger()


class Database:

    def __init__(self, host, port, dbuser, dbuser_password, dbname):
        self.client = InfluxDBClient(host=host, port=port, ssl=True,
                                     username=dbuser, password=dbuser_password,
                                     database=dbname)
        logger.info('database configuration: host: {}:{}, '
                    'user: {}, database: {}'.format(host, port,
                                                    dbuser, dbname))

    def write(self, data):
        try:
            self.client.write_points(data)
        except requests.exceptions.ConnectionError as err:
            logger.error('writing to database failed with '
                         'error: \'{}\'.'.format(err))
