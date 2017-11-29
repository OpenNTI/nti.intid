#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904,W0603,W0703,W0221

from hamcrest import assert_that

from nti.testing.matchers import provides

import functools
import transaction

import zope.testing.cleanup

from zope import component

from zope.component.hooks import setHooks
from zope.component.hooks import site as currentSite

import ZODB

from ZODB.DemoStorage import DemoStorage

from nti.testing.layers import find_test
from nti.testing.layers import GCLayerMixin
from nti.testing.layers import ZopeComponentLayer
from nti.testing.layers import ConfiguringLayerMixin

current_mock_db = None
current_transaction = None

logger = __import__('logging').getLogger(__name__)


def init_db(db, conn=None):
    conn = db.open() if conn is None else conn
    global current_transaction
    if current_transaction != conn:
        current_transaction = conn
    return conn


class mock_db_trans(object):

    def __init__(self, db=None):
        self.conn = None
        self.db = db or current_mock_db

    def __enter__(self):
        transaction.begin()
        self.conn = conn = self.db.open()
        global current_transaction
        current_transaction = conn
        return conn

    def __exit__(self, t, unused_v, unused_tb):
        global current_transaction
        body_raised = t is not None
        try:
            try:
                if not transaction.isDoomed():
                    transaction.commit()
                else:
                    transaction.abort()
            except Exception:
                transaction.abort()
                raise
            finally:
                current_transaction = None
                self.conn.close()
        except Exception:  # pragma: no cover
            if not body_raised:
                raise
            logger.exception("Failed to cleanup trans")
        reset_db_caches(self.db)


def reset_db_caches(db=None):
    if db is not None:
        db.pool.map(lambda conn: conn.cacheMinimize())


def _mock_ds_wrapper_for(func, db, teardown=None):

    @functools.wraps(func)
    def f(*args):
        global current_mock_db
        current_mock_db = db
        init_db(db)

        try:
            func(*args)
        finally:
            current_mock_db = None
            if teardown:
                teardown()

    return f


def WithMockDS(*args, **kwargs):
    def teardown():
        return None
    db = ZODB.DB(DemoStorage(name='Users'))
    if len(args) == 1 and not kwargs:
        # Being used as a plain decorator
        func = args[0]
        return _mock_ds_wrapper_for(func, db, teardown)
    return lambda func: _mock_ds_wrapper_for(func, db, teardown)


class SharedConfiguringTestLayer(ZopeComponentLayer,
                                 GCLayerMixin,
                                 ConfiguringLayerMixin):

    set_up_packages = ('nti.initid',)

    @classmethod
    def db(cls):
        return current_mock_db

    @classmethod
    def setUp(cls):
        setHooks()
        cls.setUpPackages()

    @classmethod
    def tearDown(cls):
        cls.tearDownPackages()
        zope.testing.cleanup.cleanUp()

    @classmethod
    def testSetUp(cls, test=None):
        setHooks()
        test = test or find_test()
        test.db = cls.db()

    @classmethod
    def testTearDown(cls):
        pass


import unittest

class IntIdTestCase(unittest.TestCase):
    layer = SharedConfiguringTestLayer
