import json

import redis
import redis.sentinel
from flask import current_app

from labonneboite.conf import settings


# Here we define caches to store results provided by vendor APIs, so that
# we don't exceed our allowed quotas. The various classes have different storage
# backends.


class BaseCache(object):
    def get(self, key, default=None):
        raise NotImplementedError

    def set(self, key, value):
        raise NotImplementedError

    def clear(self):
        raise NotImplementedError


class DummyCache(BaseCache):
    """
    This cache does not do anything: in effect all it does is say "no this data is not in my cache".
    """

    def get(self, key, default=None):
        return default

    def set(self, key, value):
        pass

    def clear(self):
        pass


class LocalCache(BaseCache):
    """
    Store data in-memory for process. This is highly inefficient in
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
    """
    Store data in redis or redis sentinel (depending if REDIS_SENTINELS is defined). This allows us to auto-expire
    content after a certain time (defined in EXPIRES_IN_SECONDS setting).
    """

    CONNECTION_POOL = None
    SENTINEL = None
    EXPIRES_IN_SECONDS = 3600 * 24 * 30

    def __init__(self):
        self._redis_instance = None

    @property
    def __redis(self):
        if self._redis_instance is None:
            self._redis_instance = self.connect()
        return self._redis_instance

    def __safe(self, func, *args, **kwargs):
        """
        Run `func` and catch connection errors, so that the wrapped function does not raise Redis-related exceptions.
        """
        # TODO write unit tests for this
        try:
            return func(*args, **kwargs)
        # Note that this also catches MasterNotFoundError exceptions
        except redis.ConnectionError:
            # Attempt to reconnect and re-run: this may happen with redis sentinel, when
            # one of the nodes becomes unavailable.
            self._redis_instance = self.connect()
            try:
                return func(*args, **kwargs)
            except redis.ConnectionError as e:
                # Fail! Cluster is utterly unavailable
                current_app.logger.exception(e)
                return None

    @classmethod
    def connect(cls):
        """
        Connect to either a Redis Sentinel or Redis server, depending on the settings.
        Return the corresponding redis client.
        """
        # Try to connect to sentinel instance
        if settings.REDIS_SENTINELS:
            if cls.SENTINEL is None:
                cls.SENTINEL = redis.sentinel.Sentinel(settings.REDIS_SENTINELS)
            return cls.SENTINEL.master_for(settings.REDIS_SERVICE_NAME)

        # Connect directly to redis
        if cls.CONNECTION_POOL is None:
            # Share one connection pool for all RedisCache instances
            cls.CONNECTION_POOL = redis.ConnectionPool(host=settings.REDIS_HOST, port=settings.REDIS_PORT)
        return redis.StrictRedis(connection_pool=cls.CONNECTION_POOL)

    def get(self, key, default=None):
        value = self.__safe(self.__redis.get, key)
        if value is None:
            return default
        # Push back expire date, so that recently-accessed keys disappear last. Kind-of
        # like an LRU cache.
        self.__safe(self.__redis.expire, key, self.EXPIRES_IN_SECONDS)
        return json.loads(value)

    def set(self, key, value):
        self.__safe(self.__redis.set, key, json.dumps(value), ex=self.EXPIRES_IN_SECONDS)

    def clear(self):
        self.__safe(self.__redis.flushdb)


if settings.TRAVEL_CACHE == "dummy":
    Cache = DummyCache
elif settings.TRAVEL_CACHE == "local":
    Cache = LocalCache
elif settings.TRAVEL_CACHE == "redis":
    Cache = RedisCache
else:
    raise ValueError("Invalid TRAVEL_CACHE setting: {}".format(settings.TRAVEL_CACHE))
