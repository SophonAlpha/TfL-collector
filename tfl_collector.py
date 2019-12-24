"""

Script to collect data from the Transport for London open data portal
(https://api-portal.tfl.gov.uk).

Can be called from a command line:

    python3 tfl_collector.py -config <configuration file>

... or triggered as an AWS Lambda function. Function to be called is main().
When called as a AWS Lambda function run parameters need to be configured as
environment variables. See function load_env_config() for variable names.

"""
#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import logging.handlers
from base64 import b64decode
import argparse
import boto3
import yaml
import TfLbikepoints


# initialise global variable for logging object
LOGGER = None
# set global variable to identify whether code runs locally or as AWS lambda
# function
if os.environ.get('AWS_REGION', False):
    RUN_ENV = 'AWS Lambda'
else:
    RUN_ENV = 'local'


def main(event=None, context=None):
    """
    Main function.

    @param event: required by AWS Lambda but not used.
    @param context: required by AWS Lambda but not used.
    """

    global LOGGER
    LOGGER = set_up_logging()
    try:
        take_measurement()
    except Exception:
        # log any exception, required for troubleshooting
        LOGGER.exception('an unhandled exception occurred:')


def set_up_logging():
    """
    Set up the logging object.

    @return: logger object to be used throughout the script and it's sub-modules
    """

    my_logger = logging.getLogger()
    my_logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(filename)s - '
        '%(funcName)s - %(message)s')
    if RUN_ENV == 'local':
        # if the code runs locally log to rotating log file
        handler = logging.handlers.RotatingFileHandler('tfl_collector.log',
                                                       maxBytes=104857600,
                                                       backupCount=1)
        my_logger.addHandler(handler)
    for handler in my_logger.handlers:
        handler.setFormatter(formatter)
    return my_logger


def take_measurement():
    """
    Take one measurement. The script is called in periodic intervals. Either
    as cron job or via AWS CloudWatch timed trigger when running as AWS Lambda
    function. One call collects one set of measurements.
    """

    LOGGER.info('---------- script started ------------')
    LOGGER.info('run environment: \'{}\''.format(RUN_ENV))
    cfg = get_script_config()
    TfLbikepoints.measurement(cfg)
    LOGGER.info('---------- script completed ----------')


def get_script_config():
    """
    Read configuration parameters.

    @return: dictionary object with configuration parameters
    """

    cfg = None
    if RUN_ENV == 'local':
        # read from local config file, file needs to be in yaml format
        args = parse_args()
        cfg = load_file_config(args.config)
    elif RUN_ENV == 'AWS Lambda':
        # read from AWS Lambda environment variables
        cfg = load_env_config()
    return cfg


def parse_args():
    """
    parse the args from the command line call
    """

    parser = argparse.ArgumentParser(description='Collect data from Transport '
                                                 'for London (TfL) data portal.')
    parser.add_argument('-config', type=str, required=True,
                        default='tfl-collector_config.yml',
                        help='configuration file')
    return parser.parse_args()


def load_file_config(cfg_file):
    """
    Read the yaml configuration file.

    @param cfg_file: configuration file path and name
    @return: dictionary object with configuration parameters
    """

    LOGGER.info('reading configuration file')
    with open(cfg_file, 'r') as ymlfile:
        cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)
    return cfg


def load_env_config():
    """
    Read configuration parameters from AWS Lambda environment variables.

    @return: dictionary object with configuration parameters
    """

    cfg = {
        'TfL_API': {
            'app_key': env_decrypt(os.environ['TfLAPI_appkey']),
            'app_id': env_decrypt(os.environ['TfLAPI_appid']),
        },
        'database': {
            'host': env_decrypt(os.environ['database_host']),
            'port': env_decrypt(os.environ['database_port']),
            'user': env_decrypt(os.environ['database_user']),
            'password': env_decrypt(os.environ['database_password']),
            'name': env_decrypt(os.environ['database_name']),
            'measurement': env_decrypt(os.environ['database_measurement']),
        },
    }
    return cfg


def env_decrypt(var_encrypted):
    """
    Decrypt AWS Lambda environment variables.

    @param var_encrypted: encrypted environment variable
    @return: decrypted environment variable
    """

    cipher_text_blob = b64decode(var_encrypted)
    var_decrypted = boto3.client('kms').decrypt(CiphertextBlob=cipher_text_blob)['Plaintext']
    var_decrypted = var_decrypted.decode('utf-8')
    return var_decrypted


if __name__ == '__main__':
    main()
