# -*- coding: utf-8 -*-
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

__revision__ = "$Id$"

import xml.etree.ElementTree as ET
from invenio.config import CFG_PREFIX, CFG_PYLIBDIR
from invenio.shellutils import *
from invenio.bibtask import write_message

# variables : (keep them identical with those in bibrank_gift_indexer)
CFG_GIFTINDEX_PREFIX = CFG_PREFIX + "/var/gift-index-data"
CFG_PATH_URL2FTS = CFG_GIFTINDEX_PREFIX+"/url2fts.xml"
CFG_LIBDIR = CFG_PYLIBDIR + "/../"
# The perl executable is used to run the query with GIFT perl API
CFG_PERL_QUERY_SCRIPT = CFG_LIBDIR+"perl/invenio/gift_query_by_imgurl.pl"

def get_similar_visual_recids(imgurls):
    """ This function is used to perform the query for image retrieval
        @param imgurls: a list of image urls.
                        Those started with '+' are similar images
                        Those with '-' are disimilar images
        This function just use '&' to join them into one string
        It is in perl script CFG_PERL_QUERY_SCRIPT the query is executed
    """
    imgurl =  '&'.join(imgurls)
    # executable_line = "/opt/cds-invenio/lib/perl/gift_query_by_imgurl.pl " + imgurl
    error_code, output, error_output = run_shell_command(
        "CFG_PERL_QUERY_SCRIPT %s %s", (imgurl, CFG_PATH_URL2FTS,))
    if (error_code != 0):
        write_message("Image urls are found at : %s" % 
            (icon_obj+"_"+icon_url_tag), stream=sys.sterr, verbose=0)

    """ First 100 similar records are returned by pairs.
        It is in this form :
           recid1  similarityValue1\n
           recid2  similarityValue2\n 
           ......
        The number of records returned is not parameterable.
        But it can be done by editing the perl script directly.
        In general 100 is enough as the max number of records 
        in the graphical interface is 100
    """
    lines = str.split(output, '\n')
    lines.reverse()
    results = {}
    results_gift_recIDs = []
    results_gift_rels = []

    for line in lines:
        if (line):
            ans = str.split(line)
            results[0] = results_gift_recIDs.append(int(ans[0]))
            results[1] = results_gift_rels.append(float(ans[1]))

    results[0] = results_gift_recIDs
    results[1] = results_gift_rels
    return results

def gift_read_url2fts():
    """ read url2fts.xml file, which is the mapping 
        file of feature file to image url and recid.
        One can check whether a certain image has 
        extracted features by searching in this list. 
    """
    url2ftsTable = {}
    url2ftsET = ET.ElementTree()
    url2ftsET.parse(CFG_PATH_URL2FTS)
    xmlnodes = url2ftsET.findall("//image")
    for xmlnode in xmlnodes:
        urlpostfix = xmlnode.attrib["url-postfix"]
        recpostfix = xmlnode.attrib["thumbnail-url-postfix"]
        url2ftsTable[urlpostfix] = recpostfix
    return url2ftsTable