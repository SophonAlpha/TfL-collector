#!/usr/bin/env python
# -*- coding: utf-8 -*-


import argparse
import yaml
import logging.handlers
import urllib3
import TfLbikepoints


# Disable warnings for "Unverified HTTPS request is being made. Adding
# certificate verification is strongly advised". We do this because we use a
# self-signed certificate for HTTPS.
urllib3.disable_warnings()


def main():
    logger.info('---------- script started ------------')
    args = parse_args()
    cfg = load_config(args.config)
    TfLbikepoints.measurement(cfg)
    logger.info('---------- script completed ----------')


def set_up_logging():
    # set up logging, rotating log file, max. file size
    my_logger = logging.getLogger('MyLogger')
    my_logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - '
                                  '%(filename)s - %(funcName)s - %(message)s')
    handler = logging.handlers.RotatingFileHandler('tfl_collector.log',
                                                   maxBytes=104857600,
                                                   backupCount=1)
    handler.setFormatter(formatter)
    my_logger.addHandler(handler)
    return my_logger


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
    logger = set_up_logging()
    main()
