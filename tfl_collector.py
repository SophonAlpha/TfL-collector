#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import logging.handlers
import urllib3
import argparse
import yaml
import TfLbikepoints


# Disable warnings for "Unverified HTTPS request is being made. Adding
# certificate verification is strongly advised". We do this because we use a
# self-signed certificate for HTTPS.
urllib3.disable_warnings()

# initialise global variable for logging object
logger = None

# set global variable to identify whether code runs locally or s AWS lambda
# function
REGION = os.environ.get('AWS_REGION', 'local')


def main(event=None, context=None):
    global logger
    logger = set_up_logging()
    try:
        take_measurement()
    except Exception:
        # log any exception, required for troubleshooting
        logger.exception('an unhandled exception occurred:')


def set_up_logging():
    my_logger = logging.getLogger()
    my_logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(filename)s - '
        '%(funcName)s - %(message)s')
    if REGION == 'local':
        # if the code runs locally log to rotating log file
        handler = logging.handlers.RotatingFileHandler('tfl_collector.log',
                                                        maxBytes=104857600,
                                                        backupCount=1)
        my_logger.addHandler(handler)
    for handler in my_logger.handlers:
        handler.setFormatter(formatter)
    return my_logger


def take_measurement():
    logger.info('---------- script started ------------')
    args = parse_args()
    cfg = load_config(args.config)
    TfLbikepoints.measurement(cfg)
    logger.info('---------- script completed ----------')


def parse_args():
    """ parse the args from the command line call """
    parser = argparse.ArgumentParser(description='Collect data from Transport '
                                                 'for London (TfL) data portal.')
    parser.add_argument('-config', type=str, required=True,
                        default='tfl-collector_config.yml',
                        help='configuration file')
    return parser.parse_args()


def load_config(config):
    logger.info('reading configuration file')
    with open(config, 'r') as ymlfile:
        cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)
    return cfg


if __name__ == '__main__':
    main()
