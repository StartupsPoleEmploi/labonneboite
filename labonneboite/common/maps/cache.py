import json
import redis

from labonneboite.conf import settings

# Here we define caches to store results provided by vendor APIs, so that
# we don't exceed our allowed quotas. The various classes have different storage backends.

logger = logging.getLogger(__name__)


class BaseCache(object):

    def get(self, key, default=None):
        raise NotImplementedError

    def set(self, key, value):
        raise NotImplementedError

    def clear(self):
        raise NotImplementedError


class DummyCache(BaseCache):
    """
    This cache does not do anything.
    """

    def get(self, key, default=None):
        return default

    def set(self, key, value):
        pass

    def clear(self):
        pass


class LocalCache(BaseCache):
    """Store data in-memory for process. This is highly inefficient in
    production, as it will result in a lot of cache miss. Also, it does not
    have any cache expiration. However, it should be sufficient for
    development.
    """

    def __init__(self):
        self.__cache = {}

    def get(self, key, default=None):
        return self.__cache.get(key, default)

    def set(self, key, value):
        self.__cache[key] = value

    def clear(self):
        self.__cache.clear()


class RedisCache(BaseCache):

    CONNECTION_POOL = None
    EXPIRES_IN_SECONDS = 3600*24*30

    def __init__(self):
        # Share one connection pool for all RedisCache instances
        if self.CONNECTION_POOL is None:
            self.CONNECTION_POOL = redis.ConnectionPool(host=settings.REDIS_HOST, port=settings.REDIS_PORT)

        self.__redis = redis.StrictRedis(connection_pool=self.CONNECTION_POOL)

    def get(self, key, default=None):
        try:
            value = self.__redis.get(key)
        except redis.ConnectionError as e:
            logger.exception(e)
            return None

        if value is None:
            return default
        return json.loads(value)

    def set(self, key, value):
        try:
            self.__redis.set(key, json.dumps(value), ex=self.EXPIRES_IN_SECONDS)
        except redis.ConnectionError as e:
            logger.exception(e)


    def clear(self):
        try:
            self.__redis.flushdb()
        except redis.ConnectionError as e:
            logger.exception(e)


if settings.TRAVEL_CACHE == 'dummy':
    Cache = DummyCache
elif settings.TRAVEL_CACHE == 'local':
    Cache = LocalCache
elif settings.TRAVEL_CACHE == 'redis':
    Cache = RedisCache
else:
    raise ValueError("Invalid TRAVEL_CACHE setting: {}".format(settings.TRAVEL_CACHE))
