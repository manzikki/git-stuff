# -*- coding: utf-8 -*-
##
## $Id: bibrank_record_sorter.py,v 1.93 2008/06/05 10:59:01 marko Exp $
## Ranking of records using different parameters and methods on the fly.
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
__revision__ = "$Id: bibrank_gift_indexer.py,v 1.93 2009/12/10 10:59:01 Xin Exp $"

import time, re, os, os.path, shutil, urllib, urllib2, webbrowser, xml.dom
import distutils.dir_util as DU
import xml.etree.ElementTree as ET

from invenio.search_engine import perform_request_search
from invenio.search_engine import get_fieldvalues
from invenio.bibtask import task_get_option
from invenio.dbquery import run_sql
from invenio.config import CFG_PREFIX, CFG_TMPDIR, CFG_PATH_WGET

# variables :
CFG_GIFTINDEX_PREFIX = CFG_PREFIX + "/var/gift-index-data"
CFG_PATH_URL2FTS = CFG_GIFTINDEX_PREFIX+"/url2fts.xml"
CFG_GIFTCONFIG_PREFIX = CFG_PREFIX + "/var/gift_config"
CFG_PATH_GIFTCONFIG = CFG_GIFTCONFIG_PREFIX+"/gift-config.mrml"
CFG_PATH_GIFTCONFIG_TEMPLATE = "/usr/share/libmrml1/gift-config.mrml"

CFG_PATH_GIFTFTSEXTRACT = "/usr/bin/gift-extract-features"
CFG_PATH_GIFTINDEXGENERATION = "/usr/bin/gift-generate-inverted-file"
CFG_PATH_CONVERT = "/usr/bin/convert"
tmp_ppm = CFG_TMPDIR+"/gift_tmp.ppm"
tmp_fts = CFG_TMPDIR+"/gift_tmp.fts"

#FIXME: add gift server stop and start
# 		make the port used for gift parametrable
def gift_indexer_run(tag):
    """Rank by the Gnu Image Finding Tools."""
    urls = []
    recids=[]
    op = task_get_option("quick")
    rank_method_code = "GIFTindexer"

    print op
    print CFG_GIFTINDEX_PREFIX
    print CFG_GIFTCONFIG_PREFIX

    if op and op=="no":
        DU.remove_tree(CFG_GIFTINDEX_PREFIX)
        recids = perform_request_search(p='8564_x:icon')
    else:
        last_updated = get_bibrankmethod_lastupdate(rank_method_code)
        print last_updated
        #last_updated = get_bibrankmethod_lastupdate(rank_method_code)
        recids = get_last_modified_rec(last_updated)

    for recid in recids:
        urls.extend(get_fieldvalues(recid, '8564_q'))
        #urls.extend(get_fieldvalues(recid, tag))

    DU.mkpath(CFG_GIFTINDEX_PREFIX)
    DU.mkpath(CFG_GIFTCONFIG_PREFIX)

    url2ftsET = ET.ElementTree()
    imagelist = ET.Element("image-list")

    if os.path.isfile(CFG_PATH_URL2FTS):
        url2ftsET.parse(CFG_PATH_URL2FTS)
        imagelist = url2ftsET.find("image-list")
    else :
        url2ftsET = ET.ElementTree(imagelist)

    urllist = []
    xmlnodes = url2ftsET.findall("//image")
    for xmlnode in xmlnodes:
        print xmlnode.attrib["url-postfix"]
        urllist.append(xmlnode.attrib["url-postfix"])

    for url in urls:
        if url not in urllist:
            ftfname = extract_features(url)
            imagexml = ET.SubElement(imagelist,'image')
            imagexml.set("url-postfix", url)
            imagexml.set("thumbnail-url-postfix", url)
            imagexml.set("feature-file-name", ftfname)

    print CFG_PATH_URL2FTS+"----------"
    url2ftsET.write(CFG_PATH_URL2FTS)
    os.system(CFG_PATH_GIFTINDEXGENERATION+" "+CFG_GIFTINDEX_PREFIX+"/")
    print "\nPROGRESS: 99%\n"

    if op=="no" or not os.path.isfile(CFG_PATH_GIFTCONFIG):
        generate_gift_config_file(len(urls))

    ndate = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    run_sql("UPDATE rnkMETHOD SET last_updated=%s WHERE name=%s",
            (ndate, rank_method_code))

def extract_features(url):
    print url+'\n'
    urlsegs = url.split("/")
    filename= urlsegs[len(urlsegs)-1]
    print "filename: %s\n" %filename
    tmp_img = CFG_TMPDIR+"/"+filename
    urllib.urlretrieve(url,tmp_img)
    #system(CFG_PATH_WGET + " -P "+CFG_TMPDIR+" "+url)
    os.system(CFG_PATH_CONVERT+" -geometry 256x256! "+tmp_img+" "+tmp_ppm)
    os.system(CFG_PATH_GIFTFTSEXTRACT+" "+tmp_ppm)
    featurefilename = CFG_GIFTINDEX_PREFIX+"/"+filename+".fts"
    os.rename(tmp_fts, featurefilename)
    os.remove(tmp_img)
    os.remove(tmp_ppm)
    return featurefilename

def generate_gift_config_file(num_img):
    configET = ET.ElementTree()
    configET.parse(CFG_PATH_GIFTCONFIG_TEMPLATE)

    collectionlist = configET.find(".//collection-list")
    collectionxml = ET.SubElement(collectionlist,'collection')
    collectionxml.set("collection-id", "invenio")
    collectionxml.set("collection-name", "invenio")
    collectionxml.set("cui-algorithm-id-list-id", "ail-inverted-file")
    collectionxml.set("cui-number-of-images", "%s" %num_img)
    collectionxml.set("cui-base-dir","%s" %(CFG_GIFTINDEX_PREFIX+'/'))
    collectionxml.set("cui-inverted-file-location","InvertedFile.db")
    collectionxml.set("cui-offset-file-location","InvertedFileOffset.db")
    collectionxml.set("cui-feature-description-location","InvertedFileFeatureDescription.db")
    collectionxml.set("cui-feature-file-location","url2fts.xml")

    queryparadigmlist = ET.SubElement(collectionxml,"query-paradigm-list")
    queryparadigmxml = ET.SubElement(queryparadigmlist,"query-paradigm")
    queryparadigmxml.set("type","inverted-file")
    queryparadigmxml2 = ET.SubElement(queryparadigmlist,"query-paradigm")
    queryparadigmxml2.set("type","perl-demo")

    configET.write(CFG_PATH_GIFTCONFIG, "UTF-8")
    replace_in_files(CFG_PATH_GIFTCONFIG, r'''__COLLECTION__''', r'''invenio''')

def get_cited_by(recordid):
    """Return a list of records that cite recordid"""
    ret = []
    cache_cited_by_dictionary = get_citation_dict("citationdict")
    if cache_cited_by_dictionary.has_key(recordid):
        ret = cache_cited_by_dictionary[recordid]
    return ret

def gift_update_image_list():
       result = find_citations(rank_method_code, p, hitset, verbose)

#def get_lastupdated(rank_method_code):
#    """Get the last time the rank method was updated"""
#    res = run_sql("SELECT rnkMETHOD.last_updated FROM rnkMETHOD WHERE name=%s", (rank_method_code, ))
#    if res:
#        return res[0][0]
#    else:
#        raise Exception("Is this the first run? Please do a complete update.")

def get_bibrankmethod_lastupdate(rank_method_code):
    """return the last excution date of bibrank method
    """
    query = """select last_updated from rnkMETHOD where name ='%s'""" % rank_method_code
    last_update_time = run_sql(query)
    r = last_update_time[0][0]
    if r is None:
        return "0000-00-00 00:00:00"
    return r

def get_last_modified_rec(bibrank_method_lastupdate):
    """ return the list of recods which have been modified after the last execution
        of bibrank method. The result is expected to have ascending numerical order.
    """
    query = """SELECT id FROM bibrec
               WHERE modification_date >= '%s' """ % bibrank_method_lastupdate
    query += "order by id ASC"
    list = [row[0] for row in run_sql(query)]
    return list

def replace_in_files(filepath, searchregx, replacestring):
    cregex=re.compile(searchregx)
    input = open(filepath,'rb')
    s=unicode(input.read(),'utf-8')
    input.close()
    outtext = re.sub(searchregx,replacestring, s)
    output = open(filepath,'w')
    output.write(outtext)
    output.close()

