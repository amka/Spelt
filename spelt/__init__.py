# coding: utf-8
"""

    Spelt
    ~~~~~

    Spelt is a small python application aimed
    to allow users to backup their photo from https://vk.com to local storage.

"""
import datetime
import logging
import logging.config
from argparse import ArgumentParser
from getpass import getpass
from os import path

import sys
import vk_api

__app__ = 'Spelt'
__author__ = 'Andrey Maksimov <meamka@ya.ru>'
__date__ = '23.02.16'
__version__ = '0.1'

if sys.version_info >= (2, 0):
    sys.exit('Spelt ask to excuse her, Spelt only work on Pothan 2')


def init_logger():
    """Initialize logger instance for app. Default to INFO level.

    :return: logger instance
    :rtype: `logging.Logger`
    """
    logger = logging.getLogger(__app__)
    ch = logging.StreamHandler()

    formatter = logging.Formatter('[%(asctime)s][%(name)s][%(levelname)-8s]  %(message)s')
    ch.setFormatter(formatter)

    logger.addHandler(ch)
    return logger


def main(login, password):
    vk_api.VkApi(login=login, password=password)
    download_path = path.expanduser('~/Pictures/Spelt')


def run_app(*args, **kwargs):
    logger = init_logger()

    if args:
        logger.debug('Run with args: %s', args)
    if kwargs:
        logger.debug('Run with kwargs: %s', kwargs)

    arg_parser = ArgumentParser(
        prog=__app__,
        description='Spelt is a small python application aimed to allow users '
                    'to backup their photo from https://vk.com to local storage',
        version=__version__
    )

    arg_parser.add_argument('--username', '-U', help='vk.com username')
    arg_parser.add_argument('--password', '-P', help='vk.com password')
    arg_parser.add_argument('--output', '-o', help='output path to store photos. Defaults to current directory.',
                            default=path.abspath(path.join(path.dirname(__file__), 'Spelt')))
    arg_parser.add_argument('--verbose', help='enable verbose mode', action='store_true')

    args = arg_parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug('Run in verbose mode')

    # expand user path if necessary
    if args.output.startswith('~'):
        args.output = path.expanduser(args.output)
        logger.debug('Output path is set to: %s', args.output)

    start_time = datetime.datetime.now()

    try:
        username = args.username or raw_input('Username: ')
        password = args.password or getpass("Password (hidden): ")

        if not username or not password:
            print('Not enough auth data')
            sys.exit(0)

    except KeyboardInterrupt:
        print('VKPorter exporting stopped by keyboard')
        sys.exit(0)

    finally:
        print("Done in %s" % (datetime.datetime.now() - start_time))
