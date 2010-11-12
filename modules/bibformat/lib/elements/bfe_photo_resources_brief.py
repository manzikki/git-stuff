# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
"""BibFormat element - Prints brief HTML picture and links to resources
"""
__revision__ = "$Id$"

import sys
from invenio.config import CFG_SITE_URL
from invenio.config import CFG_BIBRANK_ALLOW_GIFT
from invenio.messages import gettext_set_language

# variables :
CFG_GIFT_QUERY = CFG_SITE_URL + '/search?imgURL=+'

def format_element(bfo):
    """
    Prints html image and link to photo resources.
    """

    resources = bfo.fields("8564_", escape=1)
    resources.extend(bfo.fields("8567_", escape=1))

    _ = gettext_set_language(bfo.lang)
    label = _("Find similar images")
    label_similar = _("Similar")
    label_disimilar = _("Dissimilar")

    out = ""
    for resource in resources:
        #hunt for this in MARC:
        #8564_ $$uhttp://yourhost/record/7/files/9806033.gif?subformat=icon$$xicon
        iconres = resource.get("x", "")
        iconurl = resource.get("u", "").replace(" ","")
        if iconres == "icon" and iconurl != "":
            out += '<a href="'+CFG_SITE_URL+'/record/'+bfo.control_field("001")+ \
                   '?ln='+ bfo.lang + '"><img src="' + iconurl \
                   + '" alt="" border="0"/></a>'

            if CFG_BIBRANK_ALLOW_GIFT:
                out += '<br/><a href="' + CFG_GIFT_QUERY + iconurl + '">'+label+'</a><br/>'
                #similar/dissimilar links
                #out += '<div style="white-space: nowrap;">'
                #out += '<input name="imgURL" type="checkbox" value="+' + icon_url +'" />'
                #out += label_similar+'<input name="imgURL" type="checkbox"'
                #out +=  value="-' + icon_url +'" />'+label_disimilar+'</div></div>'
    return out

def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0
