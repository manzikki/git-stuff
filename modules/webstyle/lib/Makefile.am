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

pylibdir=$(libdir)/python/invenio
wsgiwebdir=$(localstatedir)/www-wsgi/

pylib_DATA = webdoc.py \
             webdoc_tests.py \
             webdoc_webinterface.py \
             webpage.py \
             template.py \
             webstyle_templates.py \
             webstyle_regression_tests.py \
             webinterface_handler.py \
             webinterface_tests.py \
             webinterface_layout.py \
             fckeditor_invenio_connector.py \
             webinterface_handler_wsgi.py \
             webinterface_handler_wsgi_utils.py \
             webinterface_handler_config.py \
             httptest_webinterface.py

wsgiweb_DATA = invenio.wsgi

EXTRA_DIST = $(pylib_DATA) $(wsgiweb_DATA)

CLEANFILES = *~ *.tmp *.pyc
