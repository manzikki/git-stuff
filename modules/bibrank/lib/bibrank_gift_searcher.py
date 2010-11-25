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

#import sys #for debug..
import socket #for talking to the GIFT server
import xml.etree.ElementTree as ET
from invenio.config import CFG_PREFIX, CFG_PYLIBDIR, CFG_SITE_LANG, CFG_SITE_URL
#from invenio.bibtask import write_message
from invenio.messages import gettext_set_language #for error messages
from invenio.intbitset import intbitset

# variables : (keep them identical with those in bibrank_gift_indexer)
CFG_GIFTINDEX_PREFIX = CFG_PREFIX + "/var/gift-index-data"
CFG_PATH_URL2FTS = CFG_GIFTINDEX_PREFIX+"/url2fts.xml"
GIFT_HOST = "localhost"
GIFT_PORT = 12700
p_search = "8564_x:icon" #search records that can hold an image by this,
                         #verify using conf
prefix = "(" #things that surround the similarity figure
suffix = ")"
try:
    cfile = CFG_ETCDIR + "/bibrank/" + rank_method_code + ".cfg"
    config = ConfigParser.ConfigParser()
    config.readfp(open(cfile))
    myobj = config.get("gnuift_similarity", "icon_obj")
    mytag = config.get("gnuift_similarity", "icon_label_tag")
    myval = config.get("gnuift_similarity", "icon_label_value")
    p_search = myobj+mytag+":"+myval
    prefix = config.get("gnuift_similarity", \
                        "relevance_number_output_prologue")
    prefix = config.get("gnuift_similarity", \
                        "relevance_number_output_epilogue")
except:
    pass


def talk_to_gift(imgurl, ln=CFG_SITE_LANG):
    """
    This is simple GIFT communication by sockets, only one image.
    @param imgurl: an image that has been indexed by GIFT and in url2fts.xml
    @param ln: language
    @return ([[imageurl1, relevance1] [iurl2, rel2], ..], error_string)
    """
    data1 = """<?xml version="1.0" standalone="no"?>
    <!DOCTYPE mrml SYSTEM "http://isrpc85.epfl.ch/Charmer/code/mrml.dtd">
    <mrml session-id="d1">
    <open-session user-name="x" session-name="y"/>
    <get-collections/>
    </mrml>
    """
    _ = gettext_set_language(ln)
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((GIFT_HOST, GIFT_PORT))
    except:
        myerr = _("Cannot contact GIFT. Is it running in ")+str(GIFT_PORT)
        return ([], myerr)

    client_socket.send(data1)
    #read reply
    reply = client_socket.recv(1024) #a short buffer
    #because we only need to get the session id
    client_socket.close()
    #print reply
    #get session and collection
    startpos = reply.index(' session-id="')+13
    endpos = reply.index('"', startpos+1)
    session = reply[startpos:endpos]
    startpos = reply.index(' collection-id="')+16
    endpos = reply.index('"', startpos+1)
    collection = reply[startpos:endpos]

    data2 = """<mrml session-id="%(sessionid)s">
    <query-step
    result-size="500"
    result-cutoff="0"
    collection-id="%(collection)s"
    algorithm-id="%(algo)s">
    <user-relevance-element-list>
    <user-relevance-element
     user-relevance="1"
     image-location="%(image)s"/>
    </user-relevance-element-list>
    </query-step>
    </mrml>
    """ % { "sessionid" : session, "collection" : collection,
            "algo": "adefault", "image": imgurl }
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((GIFT_HOST, GIFT_PORT))
    client_socket.send(data2)
    reply = client_socket.recv(1024*1024) #the reply can be large
    client_socket.close()
    #parse calculated-similarity and thumbnail-location
    recnum_rel_pairs = []
    for line in reply.split("\n"):
        if (line.count("calculated-similarity=") > 0):
            startpos = line.index("calculated-similarity=")+23
            endpos = line.index('"', startpos+1)
            calc = line[startpos:endpos]
            startpos = line.index("thumbnail-location=")+20
            endpos = line.index('"', startpos+1)
            tloc = line[startpos:endpos]
            calc.strip()
            tloc.strip()
            #convert to nice data types
            numloc = int(tloc)
            numcalc = float(calc)
            pair = [numloc, numcalc]
            recnum_rel_pairs.append(pair)
    myerr = ""
    if not recnum_rel_pairs:
        myerr = _("Nothing found. Maybe your image has not been indexed yet "+imgurl)
    recnum_rel_pairs.reverse()
    return (recnum_rel_pairs, myerr)


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

def search_unit_similarimage(p=None):
    """
    Return all potential records that have an image. The "real" ones are ranked by
    get_img_ranking_for_bibrank
    """
    from invenio.search_engine import perform_request_search
    images_with_icon = perform_request_search(p=p_search)
    return intbitset(images_with_icon)

def get_img_ranking_for_bibrank(p, hitset=None):
    """
    Do the real search. Sort the stuff in hitset accordingly. Return a tuple
    that consist of
    * pairs [recnum, relevance]
    * opening parenthesis
    * closing parenthesis
    * an error message if needed
    @param p: looks like: similarimage:recid:N/foo.gif
    """
    retobj = ([], '', '', '')
    if p:
        p = p.strip()
        #remove recid: from the beginning..
        p = p.replace("similarimage:recid:","")
        p = p.strip()
        #get the record number
        recnum = 0
        parts = p.split("/") #the first part should be a number, second: filename
        if len(parts) < 2:
            return retobj
        try:
            recnum = int(parts[0])
        except:
            myerr = "Could not handle search term"+p
            retobj = ([], '', '', myerr)
            return retobj
        #ok.. construct
        myurl = CFG_SITE_URL+"/record/"+parts[0]+"/files/"+parts[1]+"?subformat=icon"
        #call gift
        (id_rel_pairs, myerr) = talk_to_gift(myurl)
        retobj = (id_rel_pairs, prefix, suffix, myerr)
    return retobj

