# -*- coding: utf-8 -*-
##
## $Id: bibindex_engine_tests.py,v 1.12 2008/03/23 16:15:40 tibor Exp $
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008 CERN.
##
## CDS Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Unit tests for the gift indexing engine."""

__revision__ = \
    "$Id: bibrank_gift_indexer_tests.py,v 1.12 2010/01/15 16:15:40 Xin Exp $"

import unittest

from invenio.bibrank_gift_indexer import generate_gift_config_file, extract_features
from invenio.testutils import make_test_suite, run_test_suite

class TestListSetOperations(unittest.TestCase):
    """Test list set operations."""

    def test_list_union(self):
        """bibindex engine - list union"""
        self.assertEqual([1, 2, 3, 4],
                         bibindex_engine.list_union([1, 2, 3],
                                                    [1, 3, 4]))

class TestWashIndexTerm(unittest.TestCase):
    """Test for washing index terms, useful for both searching and indexing."""

    def test_wash_index_term_short(self):
        """bibindex engine - wash index term, short word"""
        self.assertEqual("ellis",
                         bibindex_engine.wash_index_term("ellis"))

    def test_wash_index_term_long(self):
        """bibindex engine - wash index term, long word"""
        self.assertEqual(50*"e",
                         bibindex_engine.wash_index_term(1234*"e"))

    def test_wash_index_term_case(self):
        """bibindex engine - wash index term, lower the case"""
        self.assertEqual("ellis",
                         bibindex_engine.wash_index_term("Ellis"))

    def test_wash_index_term_unicode(self):
        """bibindex engine - wash index term, unicode"""
        self.assertEqual("ελληνικό αλφάβητο",
                         bibindex_engine.wash_index_term("Ελληνικό αλφάβητο"))

TEST_SUITE = make_test_suite(TestListSetOperations, TestWashIndexTerm,)

if __name__ == "__main__":
    # generate_gift_config_file(100)
    extract_features("http://192.168.111.129/record/7/files/9806033.jpeg")
