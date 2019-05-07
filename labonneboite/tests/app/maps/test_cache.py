# coding: utf8
import unittest

from unittest import mock
import redis.sentinel

from labonneboite.tests.test_base import AppTest
from labonneboite.common.maps import cache


class LocalCacheTests(unittest.TestCase):

    def setUp(self):
        self.cache = cache.LocalCache()

    def test_get_unset_value(self):
        self.assertIsNone(self.cache.get("new key"))

    def test_set_get(self):
        self.cache.set("key", "value")
        self.assertEqual("value", self.cache.get("key"))


class RedisCacheTest(AppTest):

    def setUp(self):
        super(RedisCacheTest, self).setUp()
        self.cache = cache.RedisCache()

    def test_access_cache_with_disconnected_redis(self):
        with self.test_request_context:
            self.assertIsNone(self.cache.get("new key"))
            self.assertIsNone(self.cache.set("new key", 1))
            self.assertIsNone(self.cache.get("new key"))
            self.cache.clear()

    def test_master_not_found(self):
        # Mock sentinel such that the cache redis instance raises
        # MasterNotFoundError
        self.cache.SENTINEL = mock.Mock(
            master_for=mock.Mock(
                get=mock.Mock(
                    side_effect=redis.sentinel.MasterNotFoundError
                ),
                set=mock.Mock(
                    side_effect=redis.sentinel.MasterNotFoundError
                )
            )
        )

        with self.test_request_context:
            self.assertIsNone(self.cache.get('somekey'))
