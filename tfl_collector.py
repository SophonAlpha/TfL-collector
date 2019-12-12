#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import boto3
import logging.handlers
import urllib3
import argparse
import yaml
import TfLbikepoints
from base64 import b64decode


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
    if REGION == 'local':
        # read from local config file
        args = parse_args()
        cfg = load_config(args.config)
    else:
        # read from environment variables
        cfg = load_env_config()
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


def load_file_config(config):
    logger.info('reading configuration file')
    with open(config, 'r') as ymlfile:
        cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)
    return cfg


def load_env_config():
    cfg['TfL_API']['app_key'] = env_decrypt(os.environ['TfLAPI_appkey'])
    cfg['TfL_API']['app_id'] = env_decrypt(os.environ['TfLAPI_appid'])
    cfg['database']['host'] = env_decrypt(os.environ['database_host'])
    cfg['database']['port'] = env_decrypt(os.environ['database_port'])
    cfg['database']['user'] = env_decrypt(os.environ['database_user'])
    cfg['database']['password'] = env_decrypt(os.environ['database_password'])
    cfg['database']['name'] = env_decrypt(os.environ['database_name'])
    return cfg


def env_decrypt(var_encrypted):
    cipher_text_blob = b64decode(var_encrypted)
    var_decrypted = boto3.client('kms').decrypt(CiphertextBlob=cipher_text_blob)['Plaintext']
    return var_decrypted


if __name__ == '__main__':
    main()
