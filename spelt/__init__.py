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
import sys
from argparse import ArgumentParser
from functools import partial
from getpass import getpass
from multiprocessing import Pool
from os import mkdir, path

import requests
import vk_api

from spelt.picker import Picker

__app__ = 'Spelt'
__author__ = 'Andrey Maksimov <meamka@ya.ru>'
__date__ = '23.02.16'
__version__ = '0.1'

if sys.version_info >= (3, 0):
    sys.exit('Spelt ask to excuse her, Spelt only work on Pothan 2')

logger = logging.getLogger(__app__)


def init_logger():
    """Initialize logger instance for app. Default to INFO level.

    :return: logger instance
    :rtype: `logging.Logger`
    """
    ch = logging.StreamHandler()

    formatter = logging.Formatter('[%(asctime)s][%(name)s][%(levelname)-8s]  %(message)s')
    ch.setFormatter(formatter)

    logger.addHandler(ch)
    logger.setLevel(logging.INFO)


def connect(username, password):
    """

    :param username:
    :param password:
    :return:
    """
    vk_session = vk_api.VkApi(login=username, password=password)
    try:
        vk_session.authorization()
    except vk_api.AuthorizationError as error_msg:
        sys.exit(error_msg)

    return vk_session


def get_albums(vk_session):
    """Requests accessible photo albums from VK.

    :param vk_session: `VkApi`
    :type vk_session: `VkApi`
    :return: list of albums or None
    :rtype: list or None
    """
    try:
        vk_response = vk_session.method('photos.getAlbums', values={'owner_id': vk_session.token['user_id']})
        return vk_response['items']
    except Exception as e:
        logging.info("Couldn't get albums. Sorry.")
        return None


def get_album_photos(album, offset, vk_session):

    def normpath(filename):
        keepcharacters = [' ', '.', '_', ',']
        return "".join(c for c in filename if c.isalnum() or c in keepcharacters).rstrip()

    items = []
    try:
        response = vk_session.method('photos.get', values={
            'owner_id': vk_session.token['user_id'],
            'album_id': album['id'],
            'offset': offset or 0
        })
    except Exception as e:
        logging.error(e)
        return items

    if 'items' in response:
        for item in response['items']:
            image = {
                'id': item['id'],
                'date': datetime.datetime.fromtimestamp(item['date']),
                'url':
                    item.get('photo_2560') or
                    item.get('photo_1280') or
                    item.get('photo_807') or
                    item.get('photo_604') or
                    item.get('photo_130') or
                    item.get('photo_75')
            }
            if item.get('text'):
                image['title'] = normpath(item['text'])

            items.append(image)

    return items


def download_photo(output, photo):
    """

    :param photo:
    :return:
    """
    target_filename = u'%s%s' % (photo.get('title') or photo['id'], path.splitext(photo['url'])[1])
    photo_filename = path.join(output, target_filename)
    logger.debug(u'Begin download image %s to %s', photo['url'], photo_filename)
    try:
        r = requests.get(photo['url'], stream=True)
        with open(photo_filename, 'wb') as fd:
            for chunk in r.iter_content(8192):
                fd.write(chunk)
        logger.debug('Downloaded photo: %s', photo_filename)

    except Exception as e:
        logger.exception(e)
        return 0

    return 1


def process_albums(albums, output, vk_session):
    """

    :param albums:
    :param output:
    :return:
    """

    logger.info('Begin downloading %s album(s)', len(albums))
    for album in albums:
        offset = 0
        album_folder = path.join(output, album['title'])
        if not path.exists(album_folder):
            mkdir(album_folder)

        logger.debug('Album Size: %s', album['size'])
        while offset <= album['size']:
            photo_urls = get_album_photos(album=album, offset=offset, vk_session=vk_session)
            logger.debug('Got URLs for %s photo(s)', len(photo_urls))

            f = partial(download_photo, album_folder)
            pool = Pool(processes=8)
            pool.map_async(f, photo_urls)
            # And wait till end
            pool.close()
            pool.join()

            offset += 1000

        logger.info(u'Album "%s" [%d] downloaded.', album['title'], album['size'])

    logger.info('%d photo(s) downloaded.' % sum([album['size'] for album in albums]))


def run_app():
    """

    :return:
    """

    init_logger()

    arg_parser = ArgumentParser(
        prog=__app__,
        description='Spelt is a small python application aimed to allow users '
                    'to backup their photo from https://vk.com to local storage',
        version=__version__
    )

    arg_parser.add_argument('--username', '-U', help='vk.com username')
    arg_parser.add_argument('--password', '-P', help='vk.com password')
    arg_parser.add_argument('--output', '-O', help='output path to store photos. Defaults to current directory.',
                            default=path.abspath(path.join(path.dirname(__file__), 'Spelt')))
    arg_parser.add_argument('--verbose', help='enable verbose mode', action='store_true')

    args = arg_parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.info('Run in verbose mode')

    # expand user path if necessary
    if args.output.startswith('~'):
        args.output = path.expanduser(args.output)

    if not path.exists(args.output):
        try:
            mkdir(args.output)
        except Exception as e:
            logger.exception(e)
            sys.exit()
    logger.info('Output path is set to: %s', args.output)

    start_time = datetime.datetime.now()

    try:
        username = args.username or raw_input('Username: ')
        password = args.password or getpass("Password (hidden): ")

        if not username or not password:
            logger.info('Not enough auth data')
            return

        vk_session = connect(username=username, password=password)
        albums = get_albums(vk_session)

        selected_albums_titles = Picker(
            title='Select Albums to Process',
            options=[u'%-50s [ID:%d]' % (album['title'], album['id']) for album in albums]
        ).get_selected()

        if not selected_albums_titles:
            logger.info('Nothing to export')
            return

        selected_albums_ids = []
        for title in selected_albums_titles:
            id_ = int(title[title.find("[ID:") + 4:-1])
            selected_albums_ids.append(id_)
            logger.debug('Adds %s to selection', id_)

        selected_albums = [album for album in albums if album['id'] in selected_albums_ids]
        logger.debug(u'Selected Albums: %s' % [u'%s' % album['title'] for album in selected_albums])

        process_albums(albums=selected_albums, output=args.output, vk_session=vk_session)

    except KeyboardInterrupt:
        logger.info('Stopped by keyboard')
        sys.exit(0)

    finally:
        logger.info("Done in %s" % (datetime.datetime.now() - start_time))


if __name__ == '__main__':
    run_app()
