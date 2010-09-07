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

from invenio.config import CFG_PREFIX, CFG_LIBDIR
from invenio.shellutils import *

# variables : (keep them identical with those in bibrank_gift_indexer)
CFG_GIFTINDEX_PREFIX = CFG_PREFIX + "/var/gift-index-data"
CFG_PATH_URL2FTS = CFG_GIFTINDEX_PREFIX+"/url2fts.xml"

def get_similar_visual_recids(imgurls):
    imgurl =  '&'.join(imgurls)
    # executable_line = "/opt/cds-invenio/lib/perl/gift_query_by_imgurl.pl " + imgurl
    error_code, lines, erroroutput = run_shell_command(CFG_LIBDIR+"perl/invenio/gift_query_by_imgurl.pl %s %s", (imgurl, CFG_PATH_URL2FTS,))
    # output = subprocess.Popen([CFG_LIBDIR+"perl/invenio/gift_query_by_imgurl.pl", imgurl, CFG_PATH_URL2FTS], stdout = subprocess.PIPE)
    # lines = string.split(output.communicate()[0], '\n')
    # raise repr(lines)

    lines.reverse()
    results = {}
    results_gift_recIDs = []
    results_gift_rels = []

    for line in lines:
        if (line):
            ans = string.split(line)
            # results_gift_recIDs.append(int(ans[0]))
            # results_gift_rels.append(float(ans[1]))
            results[0] = results_gift_recIDs.append(int(ans[0]))
            results[1] = results_gift_rels.append(float(ans[1]))

    results[0] = results_gift_recIDs
    results[1] = results_gift_rels
    return results