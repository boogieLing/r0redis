import sys
import time
import traceback

import bg_helper as bh
import fs_helper as fh
import input_helper as ih
import settings_helper as sh
from redis import StrictRedis, ConnectionError, ConnectionPool
from time import sleep

__doc__ = """Create an instance of `redis_helper.Collection` and use it

import redis_helper as rh
model = rh.Collection(...)
"""

logger = fh.get_logger(__name__)
SETTINGS = sh.get_all_settings(__name__).get(sh.APP_ENV, {})
REDIS_URL = SETTINGS.get('redis_url')
REDIS = None


def zshow(key, start=0, end=-1, desc=True, withscores=True):
    """Wrapper to REDIS.zrange"""
    return REDIS.zrange(key, start, end, withscores=withscores, desc=desc)


def identity(x):
    """Return x, unmodified"""
    return x


def _settings_for_docker_ok(exception=False):
    """Return True if settings.ini has the required values set

    - exception: if True, raise an exception if settings are not ok (after
      optional sync attempt)

    If any are missing, prompt to sync settings with vimdiff
    """
    global SETTINGS
    missing_settings = set(['container_name', 'image_version', 'port', 'rm']) - set(SETTINGS.keys())
    if missing_settings != set():
        message = 'Update your settings.ini to have: {}'.format(sorted(list(missing_settings)))
        print(message)
        resp = ih.user_input('Sync settings.ini with vimdiff? (y/n)')
        if resp.lower().startswith('y'):
            sh.sync_settings_file(__name__)
            SETTINGS = sh.get_all_settings(__name__).get(sh.APP_ENV, {})
            missing_settings = set(['container_name', 'image_version', 'port', 'rm']) - set(SETTINGS.keys())
            if missing_settings == set():
                return True
            elif exception:
                message = 'Update your settings.ini to have: {}'.format(sorted(list(missing_settings)))
                raise Exception(message)
        else:
            if exception:
                raise Exception(message)
    else:
        return True


def start_docker(data_dir=None, aof=True, exception=False, show=False, force=False):
    """Start docker container for redis using values from settings.ini file

    - data_dir: directory that will map to container's /data
        - specify absolute path or subdirectory of current directory
    - aof: if True, use appendonly.aof file
    - exception: if True and docker has an error response, raise an exception
    - show: if True, show the docker commands and output
    - force: if True, stop the container and remove it before re-creating
    """
    ok = _settings_for_docker_ok(exception=exception)
    if not ok:
        return False
    return bh.tools.docker_redis_start(
        SETTINGS['container_name'],
        version=SETTINGS['image_version'],
        port=SETTINGS['port'],
        rm=SETTINGS['rm'],
        data_dir=data_dir,
        aof=aof,
        exception=exception,
        show=show,
        force=force
    )


def stop_docker(exception=False, show=False):
    """Stop docker container for redis using values from settings.ini file

    - exception: if True and docker has an error response, raise an exception
    - show: if True, show the docker commands and output
    """
    if 'container_name' not in SETTINGS:
        message = 'Update your settings.ini to have: container_name'
        if exception is True:
            raise Exception(message)
        elif show is True:
            print(message)
        return False
    return bh.tools.docker_stop(SETTINGS['container_name'], exception=exception, show=show)


def implicit_connect(url=REDIS_URL, attempt_docker=True, exception=False, show=False):
    """Connect to the redis server and set the REDIS variable

    - url: if no url is specified, use the redis_url from settings.ini (or check
      REDIS_URL environment variable)
        - redis://[:somepassword@]somehost:someport/dbnumber
    - attempt_docker: if True, and unable to connect initially, call start_docker
    - exception: if True and unable to connect, raise an exception
    - show: if True, show the docker commands and output

    If successful, return (True, dbsize); otherwise, if exception is False,
    return (False, float('inf'))
    """
    global REDIS_URL, REDIS
    REDIS_URL = url
    REDIS = StrictRedis.from_url(REDIS_URL)
    try:
        REDIS.ping()
        size = REDIS.dbsize()
    except (ConnectionError, AttributeError):
        if attempt_docker:
            start_docker(exception=exception, show=show)
            sleep(1)
            REDIS = StrictRedis.from_url(REDIS_URL)
            try:
                size = REDIS.dbsize()
            except (ConnectionError, AttributeError):
                REDIS = None
                if exception is True:
                    raise
                return False, -1
            else:
                return True, size
        else:
            REDIS = None
            if exception is True:
                raise
            return False, -1
    else:
        return True, size


def explicit_connect(redis_host: str, redis_port: int = 6379, redis_db: int = 0, health_check_interval=30,
                     attempt_docker: bool = False, exception: bool = False, show: bool = False):
    global REDIS
    pool = ConnectionPool(host=redis_host, port=redis_port)

    retry_num = 5
    while retry_num > 0:
        try:
            REDIS = StrictRedis(connection_pool=pool, db=redis_db, health_check_interval=health_check_interval)
            REDIS.ping()
            ans_size = REDIS.dbsize()
        except ConnectionError:
            # Unconditionally perform reconnection operation.
            print(f'redis connect failure, try again {retry_num}', file=sys.stderr)
            retry_num -= 1
            if retry_num == 0:
                print(traceback.print_exc(), file=sys.stderr)
                if exception is True:
                    raise
                return False, -1
            time.sleep(1)
            if attempt_docker is True:
                start_docker(exception=exception, show=show)
                time.sleep(1)
                REDIS = StrictRedis.from_url(REDIS_URL)
                try:
                    ans_size = REDIS.dbsize()
                except (ConnectionError, AttributeError):
                    REDIS = None
                    if exception is True:
                        raise
                    return False, -1
                else:
                    return True, ans_size

        except Exception as e:
            print(f"error: {e}\n{traceback.print_exc()}", file=sys.stderr)
            if exception is True:
                raise
            return False, -1
        else:
            return True, ans_size


from .collection import Collection
