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
"""BibFormat element - Prints HTML picture and links to resources
"""
__revision__ = "$Id$"

from invenio.config import CFG_SITE_URL
from invenio.config import CFG_BIBRANK_ALLOW_GIFT

# variables :
CFG_GIFT_QUERY = CFG_SITE_URL + '/search?ln=fr&p=imgURL:'
CFG_RANK_METHOD = '&rm=img'


def format(bfo):
    """
    Prints html image and link to photo resources.
    """

    resources = bfo.fields("8564_", escape=1)
    resources.extend(bfo.fields("8567_", escape=1))

    out = ""
    for resource in resources:
        icon_url = ""
        if resource.get("x", "") == "icon" and resource.get("u", "") == "":
            icon_url = resource.get("q", "").replace(" ","")
        if resource.get("x", "") == "jpgIcon":
            icon_url = resource.get("u", "").replace(" ","")
        if icon_url != "":
            out += '<br /><br /><img src="' + icon_url + '" alt="" />'
            if CFG_BIBRANK_ALLOW_GIFT:
                out += '<br /><br /><a href="'+CFG_GIFT_QUERY+icon_url+CFG_RANK_METHOD+'"> find similar images </a><br /><br />'

        if resource.get("x", "") == "1":
            out += '<br />High resolution: <a href="'+resource.get("q", "") +'">'+ resource.get("q", "") +"</a>"

    out += '<br /><font size="-2"><b>© CERN Geneva</b></font>'
    out += '<br /> <a href="'+bfo.field("8564_u")+'">'+ bfo.field("8564_z") + "</a>"
    return out

def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0
