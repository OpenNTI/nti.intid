#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

import sys
import types
import unittest

from zope.dottedname import resolve as dottedname


class TestModules(unittest.TestCase):

    def test_import_interfaces(self):
        dottedname.resolve('nti.intid.interfaces')

    def test_import_containers(self):
        location = 'nti.containers'
        if location not in sys.modules:
            for name in ('', '.datastructures'):
                new_loc = location + name
                sys.modules[new_loc] = types.ModuleType(new_loc, "Created module")
        dottedname.resolve('nti.intid.containers')
