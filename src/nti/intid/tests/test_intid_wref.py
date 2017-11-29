#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import none
from hamcrest import is_not
from hamcrest import not_none
from hamcrest import assert_that
from hamcrest import has_property

from nti.testing.matchers import validly_provides as verifiably_provides

import pickle

import BTrees.OOBTree

from persistent import Persistent

from zope import interface

from zope.location.interfaces import ILocation

from nti.intid import wref

from nti.intid.tests import root_name

from nti.intid.tests import WithMockDS
from nti.intid.tests import IntIdTestCase

from nti.intid.tests import mock_db_trans

from nti.wref.interfaces import IWeakRef
from nti.wref.interfaces import ICachingWeakRef
from nti.wref.interfaces import IWeakRefToMissing


@interface.implementer(ILocation)
class User(Persistent):

    __parent__ = None

    def __init__(self, username):
        self.__name__ = username


class TestIntidWref(IntIdTestCase):

    def _create_user(self, username, conn=None):
        user = User(username)
        if conn is not None:
            folder = conn.root()[root_name]
            folder[username] = user
        return user

    @WithMockDS
    def test_pickle(self):
        with mock_db_trans() as conn:
            user = self._create_user('sjohnson@nextthought.com', conn)
            ref = wref.WeakRef(user)

            assert_that(ref, has_property('_v_entity_cache', user))

            copy = pickle.loads(pickle.dumps(ref))

            assert_that(copy, has_property('_v_entity_cache', none()))

            assert_that(copy(), is_(user))
            assert_that(ref, is_(copy))
            assert_that(copy, is_(ref))
            assert_that(repr(copy), is_(repr(ref)))
            assert_that(hash(copy), is_(hash(ref)))

            assert_that(ref, verifiably_provides(IWeakRef))
            assert_that(ref, verifiably_provides(ICachingWeakRef))
            assert_that(ref, verifiably_provides(IWeakRefToMissing))

    @WithMockDS
    def test_missing(self):
        with mock_db_trans() as conn:
            user = self._create_user('sjohnson@nextthought.com', conn)
            # Cannot find with invalid intid
            ref = wref.WeakRef(user)
            setattr(ref, '_v_entity_cache', None)
            setattr(ref, '_entity_id', -1)
            assert_that(ref(), is_(none()))

            # cannot find with invalid oid
            ref = wref.WeakRef(user)
            assert_that(ref, has_property('_entity_oid', not_none()))
            setattr(ref, '_v_entity_cache', None)
            setattr(ref, '_entity_oid', -1)
            assert_that(ref(), is_(none()))

            # Find it with oid of None (but valid intid)
            ref = wref.WeakRef(user)
            assert_that(ref, has_property('_entity_oid', not_none()))
            setattr(ref, '_v_entity_cache', None)
            setattr(ref, '_entity_oid', None)
            assert_that(ref(), is_(user))

            # Caching can be controlled
            ref = wref.WeakRef(user)
            setattr(ref, '_entity_id', -1)
            setattr(ref, '_entity_oid', None)
            assert_that(ref(), is_(user))  # From cache

            assert_that(ref(allow_cached=False), is_(none()))  # not from cache

    @WithMockDS
    def test_in_btree(self):
        with mock_db_trans() as conn:
            user_1 = self._create_user('sjohnson@nextthought.com', conn)
            user_2 = self._create_user('sjohnson2@nextthought.com', conn)

            bt = BTrees.OOBTree.OOBTree()

            ref_1 = wref.ArbitraryOrderableWeakRef(user_1)
            ref_2 = wref.ArbitraryOrderableWeakRef(user_2)

            bt[ref_1] = 1
            bt[ref_2] = 2

            assert_that(bt[ref_1], is_(1))
            assert_that(bt[ref_2], is_(2))

    @WithMockDS
    def test_eq_ne(self):
        with mock_db_trans() as conn:
            user_1 = self._create_user('sjohnson@nextthought.com', conn)
            user_2 = self._create_user('sjohnson2@nextthought.com', conn)

            ref_1 = wref.ArbitraryOrderableWeakRef(user_1)
            ref_2 = wref.ArbitraryOrderableWeakRef(user_2)

            assert_that(ref_1, is_(ref_1))
            assert_that(ref_2, is_not(ref_1))
            assert_that(ref_1, is_not(ref_2))
