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
from os import mkdir, path, getcwd

import requests
import vk_api


USER_PHOTOS_ALBUM_ID = -9999999

__app__ = 'Spelt'
__author__ = 'Andrey Maksimov <meamka@ya.ru>'
__date__ = '23.02.16'
__version__ = '0.1'

LOGGER = logging.getLogger(__app__)


def init_logger():
    """Initialize logger instance for app. Default to INFO level.
    `logger` object have to be initialized before calling this function.

    """
    ch = logging.StreamHandler()

    formatter = logging.Formatter(
        '[%(asctime)s][%(name)s][%(levelname)-8s]  %(message)s')
    ch.setFormatter(formatter)

    LOGGER.addHandler(ch)
    LOGGER.setLevel(logging.INFO)


def connect(username, password):
    """Try to connect to VK.com and authenticate with given credentials.
    If it's OK return instance of :class:`vk_api.VkApi`.
    If it's not then call `sys.exit()`.

    :param username: VK username
    :type username: str
    :param password: VK username password
    :type password: str
    :return: None of :class:`vk_api.VkApi`
    :rtype: None or :class:`vk_api.VkApi`
    """
    vk_session = vk_api.VkApi(login=username, password=password)
    try:
        vk_session.auth()
    except vk_api.AuthError as error_msg:
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
        vk_response = vk_session.method(
            'photos.getAlbums',
            values={'owner_id': vk_session.token['user_id'], 'need_system': 1}
        )
        return vk_response['items']
    except Exception as e:
        logging.info("Couldn't get albums. Sorry.")
        LOGGER.debug(e.message)
        return None


def get_user_photos_album(vk_session):
    """Requests information about user photos from VK.

        :param vk_session: `VkApi`
        :type vk_session: `VkApi`
        :return: dict user photos virtual album
        :rtype: dict
        """
    vk_response = vk_session.method(
        'photos.getUserPhotos',
        values={'user_id': vk_session.token['user_id']}
    )
    return {'title': 'Photos with me', 'id': USER_PHOTOS_ALBUM_ID, 'size': vk_response['count']}


def get_album_photos(album, offset, vk_session):
    """Retrieves list of photos within given album from VK.com

    :param album: VKontakte album object
    :type album: dict
    :param offset: Offset needed to return a specific subset of photos. By default, 0.
    :type offset: int or None
    :param vk_session: instance of :class:`vk_api.VkApi`
    :type vk_session: :class:`vk_api.VkApi`
    :return: Returns a list of photo objects
    """

    def normpath(filename):
        """Normalize filename by removing unacceptable chars

        :param filename: file name
        :type filename: str
        :rtype: str
        """
        keepcharacters = [' ', '.', '_', ',']
        return "".join(c for c in filename if c.isalnum() or c in keepcharacters).rstrip()

    items = []
    try:
        if USER_PHOTOS_ALBUM_ID == album['id']:
            response = vk_session.method('photos.getUserPhotos', values={
                'user_id': vk_session.token['user_id'],
                'count': 1000,
                'offset': offset or 0
            })
        else:
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
    """Download single image from VK.com to given folder.
    `photo` objects have to be similar to:

        {
            'id': 13176195,
            'url': 'http://vk.com/…',
            'title': 'My Lovely Photo'
        }

    :param output: path to download folder
    :type output: str
    :param photo: dict containing vk photo information
    :type photo: dict
    :return: 0 if errors, 1 if OK.
    """

    # to keep neuteral order and avoid overwriting when few photos have the same description
    basename = u'%s%s' % (
        photo['id'], u'_' + photo.get('title') if photo.get('title') else '')
    # Filesystem naming limitation to avoid error 255 bytes for ext3,ext4
    if sys.getsizeof(basename) > 245:
        basename = photo['id']

    target_filename = u'%s%s' % (basename, path.splitext(photo['url'])[1])
    photo_filename = path.join(output, target_filename)
    if path.isfile(photo_filename):
        LOGGER.debug(u'Image %s already exist. Skipped.', basename)
        return 1
    LOGGER.debug(u'Begin download image %s to %s',
                 photo['url'], photo_filename)
    try:
        resp = requests.get(photo['url'], stream=True)
        with open(photo_filename, 'wb') as fd:
            for chunk in resp.iter_content(8192):
                fd.write(chunk)
        LOGGER.debug('Downloaded photo: %s', photo_filename)

    except Exception as e:
        LOGGER.exception(e)
        return 0

    return 1


def process_albums(albums, output, vk_session):
    """Init download processes in separated processes with multiprocessing.

    :param albums:
    :param output:
    :return:
    """

    LOGGER.info('Begin downloading %s album(s)', len(albums))
    for album in albums:
        offset = 0
        album_folder = path.join(output, album['title'])
        if not path.exists(album_folder):
            mkdir(album_folder)

        LOGGER.debug('Album Size: %s', album['size'])
        while offset <= album['size']:
            photo_urls = get_album_photos(
                album=album, offset=offset, vk_session=vk_session)
            LOGGER.debug('Got URLs for %s photo(s)', len(photo_urls))

            func = partial(download_photo, album_folder)
            pool = Pool(processes=8)
            pool.map_async(func, photo_urls)
            # And wait till end
            pool.close()
            pool.join()

            offset += 1000

        LOGGER.info(u'Album "%s" [%d] downloaded.',
                    album['title'], album['size'])

    LOGGER.info('%d photo(s) downloaded.', sum(
        [album['size'] for album in albums]))


def run_app():
    """Main function. Init app, parse input and call download methods.

    """

    init_logger()

    arg_parser = ArgumentParser(
        prog=__app__,
        description='Spelt is a small python application aimed to allow users '
                    'to backup their photo from https://vk.com to local storage',
    )

    arg_parser.add_argument('--username', '-U', help='vk.com username')
    arg_parser.add_argument('--password', '-P', help='vk.com password')
    arg_parser.add_argument('--output', '-O', default=path.abspath(path.join(getcwd(), 'Spelt')),
                            help='output path to store photos. Defaults to current directory.')

    arg_parser.add_argument(
        '--verbose', help='enable verbose mode', action='store_true')

    args = arg_parser.parse_args()

    if args.verbose:
        LOGGER.setLevel(logging.DEBUG)
        LOGGER.info('Run in verbose mode')

    # expand user path if necessary
    if args.output.startswith('~'):
        args.output = path.expanduser(args.output)

    if not path.exists(args.output):
        try:
            mkdir(args.output)
        except Exception as e:
            LOGGER.exception(e)
            sys.exit()
    LOGGER.info('Output path is set to: %s', args.output)

    start_time = datetime.datetime.now()

    try:
        username = args.username or raw_input('Username: ')
        password = args.password or getpass("Password (hidden): ")

        if not username or not password:
            LOGGER.info('Not enough auth data')
            return

        vk_session = connect(username=username, password=password)
        albums = get_albums(vk_session)
        albums.insert(0, get_user_photos_album(vk_session))

        LOGGER.info('Found these Albums:')
        for album_index, album in enumerate(albums):
            LOGGER.info('%3d. %-45s [Photos: %5d] [ID:%d]',
                        album_index, album['title'], album['size'], album['id'])


        msg = 'Enter space-separated album numbers to proceed: '
        if sys.version_info[0] < 3:
            selected_albums_indexes = raw_input(msg)
        else:
            selected_albums_indexes = input(msg)

        if not selected_albums_indexes:
            LOGGER.info('Nothing to export')
            return

        selected_albums = []
        for index in selected_albums_indexes.split():
            try:
                selected_albums.append(albums[int(index)])
            except (ValueError, TypeError):
                LOGGER.info('Skipped value: %s', index)

        LOGGER.debug(u'Selected Albums: %s', [u'%s' % album['title'] for album in selected_albums])

        process_albums(albums=selected_albums, output=args.output, vk_session=vk_session)

    except KeyboardInterrupt:
        LOGGER.info('Stopped by keyboard')
        sys.exit(0)

    finally:
        LOGGER.info("Done in %s", (datetime.datetime.now() - start_time))


if __name__ == '__main__':
    run_app()
