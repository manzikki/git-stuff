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

import os, os.path, shutil, urllib, urllib2, xml.dom, sys
import time, csv, re, warnings
import distutils.dir_util as DU
import xml.etree.ElementTree as ET
import ConfigParser 
from sets import Set

from invenio.bibformat_engine import *
from invenio.shellutils import *
from invenio.search_engine import perform_request_search
from invenio.search_engine import get_fieldvalues
from invenio.bibtask import task_get_option
from invenio.dbquery import run_sql
from invenio.errorlib import register_exception
from invenio.bibtask import write_message
from invenio.config import CFG_PREFIX, CFG_TMPDIR, CFG_CERN_SITE, CFG_ETCDIR

""" below are the location variables for the gnuift config files.
    they are under the cds-invenio/var folder
    two folders are required to be created for gnuift :
    gift_config and gift-index-data :
    gift_config contains config file for each collection
    (by default we considered the cds-invenio as one collection)
    gift-index-data contains :
        - feature data extracted from each image (*.fts)
        - mapping file from image url to feature file (url2fts.xml)
        - 3 index files for query : 
            - InvertedFile.db, 
            - InvertedFileOffset.db,
            - InvertedFileFeatureDescription.db
"""
CFG_GIFTINDEX_PREFIX = CFG_PREFIX + "/var/gift-index-data"
CFG_PATH_URL2FTS  = CFG_GIFTINDEX_PREFIX+"/url2fts.xml"
CFG_GIFTINDEX_DESC= CFG_GIFTINDEX_PREFIX + "/InvertedFileFeatureDescription.db"
CFG_GIFTCONFIG_PREFIX = CFG_PREFIX + "/var/gift_config"
CFG_PATH_GIFTCONFIG = CFG_GIFTCONFIG_PREFIX+"/gift-config.mrml"

""" below are the location variables for the gnuift executables.
    they depends on where gnuift is installed
    - convert is part of ImageMagick executables, it is used
      to change images into standard ppm format.
    - gift-extract-features is to extract features from one image
    - gift-write-feature-descs is to write down what kind of 
      features are in use.
    - gift-generate-inverted-file generate index file from 
      feature files.
    To extract features from files, some temporary files 
    are needed
""" 
CFG_PATH_CONVERT = "/usr/bin/convert"
CFG_PATH_GIFTFTSEXTRACT = "/usr/bin/gift-extract-features"
CFG_PATH_GIFTWRITEFTSDESC = "/usr/bin/gift-write-feature-descs"
CFG_PATH_GIFTINDEXGENERATION = "/usr/bin/gift-generate-inverted-file"
CFG_PATH_GIFTCONFIG_TEMPLATE = "/usr/share/libmrml1/gift-config.mrml"
tmp_ppm = CFG_TMPDIR + "/gift_tmp.ppm"
tmp_desc = CFG_TMPDIR + "/gift_tmp.db"
tmp_fts = CFG_TMPDIR + "/gift_tmp.fts"

ext2conttype = {"jpg": "image/jpeg",
                "jpeg": "image/jpeg",
                "png": "image/png",
                "gif": "image/gif"}
imgurl2recid = {}

""" MyHTTPRedirect is used to dealing with 
    any redirection of the url. 
"""
redirect_handler = urllib2.HTTPRedirectHandler()
class MyHTTPRedirectHandler(urllib2.HTTPRedirectHandler):
    def http_error_302(self, req, fp, code, msg, headers):
        print "Cookie Manip Right Here"
        return urllib2.HTTPRedirectHandler.http_error_302(
               self, req, fp, code, msg, headers)
    http_error_301 = http_error_303 = http_error_307 = http_error_302

cookieprocessor = urllib2.HTTPCookieProcessor()

opener = urllib2.build_opener(MyHTTPRedirectHandler, cookieprocessor)
urllib2.install_opener(opener)

def gnuift_similarity(rank_method_code):
    """Rank records by the Gnu Image Finding Tools.
       It is the main entry of the whole file.
       It is called automatically by bibrank.py
    """
    
    """ Read bibrank config file"""
    config = cfgGetParameters(rank_method_code)
    icon_obj = config.get("gnuift_similarity", "icon_obj")
    icon_label_tag = config.get("gnuift_similarity", "icon_label_tag")
    icon_label_val = config.get("gnuift_similarity", "icon_label_value")
    icon_url_tag = config.get("gnuift_similarity", "icon_url_tag")

    recids = []
    imgurl2recid = {}
    op = task_get_option("quick")
    """ kill all running gift processes"""
    os.system("killall -9 gift") 

    write_message("Image urls are found at : %s" % 
        (icon_obj+"_"+icon_url_tag), stream=sys.stdout, verbose=3)
    #write_message("Redo all feature extraction?? : %s" %
    #    op, stream=sys.stdout, verbose=3)
    #code too tricky, just redo always
    op = "no"
    write_message("Gnuift features are stored in : %s" %
        CFG_GIFTINDEX_PREFIX, stream=sys.stdout, verbose=3)
    write_message("Gnuift config files are stored in: %s" %
        CFG_GIFTCONFIG_PREFIX, stream=sys.stdout, verbose=3)

    """ using perform_requrest_research to search all the records
        that contains the preseted value in label tag
    """
    icon_p = icon_obj+icon_label_tag+':'+icon_label_val
    #quote
    #icon_p = '"'+icon_p+'"'
    write_message("Querying by p="+icon_p, verbose=9)
    recids = perform_request_search(p=icon_p)
    recids = perform_request_search(p=icon_p) #I know, but the second call is more reliable.
    write_message("Query returned "+str(len(recids))+" records.", verbose=9)

    """ if bibrank option is -R, all features need to be rebuilt
        remove all extracted features
    """
    if op and op == "no":
        if os.path.isdir(CFG_GIFTINDEX_PREFIX):
            DU.remove_tree(CFG_GIFTINDEX_PREFIX)
    else:
        last_updated = get_bibrankmethod_lastupdate(rank_method_code)
        write_message("Last time Gnuift extracted features was : %s" %
            last_updated, stream=sys.stdout, verbose=3)
        modified_recids = get_last_modified_rec(last_updated)
        """ recids contains records that contains images.
            modified_recids contains the modified records.
            the intersection of these two collections are
            modified records which contains images.
        """
        recids = list(Set(recids) & Set(modified_recids))

    imgurl2recid = add_icon_recid(recids, icon_obj, icon_label_tag, 
                                  icon_label_val, icon_url_tag)

    write_message("The number of urls found is : %s" %
        (len(imgurl2recid.keys())), stream=sys.stdout, verbose=3)

    """ Create the two folders for config file and index files """
    DU.mkpath(CFG_GIFTINDEX_PREFIX)
    DU.mkpath(CFG_GIFTCONFIG_PREFIX)

    """ Build element tree for url2fts.xml"""
    url2ftsET = ET.ElementTree()
    imagelist = ET.Element("image-list")

    """ If url2fts.xml exists, read it into url2ftsET
        else, build a new one.
    """
    if os.path.isfile(CFG_PATH_URL2FTS):
        url2ftsET.parse(CFG_PATH_URL2FTS)
        imagelist = url2ftsET.find("image-list")
    else :
        url2ftsET = ET.ElementTree(imagelist)

    """ Read all existing image urls into urllist """
    urllist = []
    xmlnodes = url2ftsET.findall("//image")
    for xmlnode in xmlnodes:
        existingurl = xmlnode.attrib["url-postfix"]
        urllist.append(xmlnode.attrib["url-postfix"])

    write_message("The number of urls taken is : %s" %
        (len(imgurl2recid.keys())), verbose=3)

    if os.path.isfile(tmp_ppm):
        os.remove(tmp_ppm)
    if os.path.isfile(tmp_desc):
        os.remove(tmp_desc)

    for url in imgurl2recid.keys():
        if url not in urllist:
            try:
                ftfname = extract_features(url)
                imagexml = ET.SubElement(imagelist,'image')
                imagexml.set("url-postfix", url)
                imagexml.set("thumbnail-url-postfix", str(imgurl2recid[url]))
                imagexml.set("feature-file-name", ftfname)
            except:
                register_exception(prefix="imagexml error in GIFT indexing")

    """ write the xml tree into CFG_PATH_URL2FTS file """
    url2ftsET.write(CFG_PATH_URL2FTS)
    #check if CFG_PATH_GIFTINDEXGENERATION exists. If not, fail.
    if not os.path.isfile(CFG_PATH_GIFTINDEXGENERATION):
        register_exception(prefix="file "+CFG_PATH_GIFTINDEXGENERATION+" does not exist")
    os.system(CFG_PATH_GIFTINDEXGENERATION+" "+CFG_GIFTINDEX_PREFIX+"/")
    # TODO : using run_shell_command???
    # run_shell_command(CFG_PATH_GIFTINDEXGENERATION+" %s", 
    #                  (CFG_GIFTINDEX_PREFIX+"/",))

    """ only if option is -R or config file does not exist,
        build a new gift config file
    """
    if op == "no" or not os.path.isfile(CFG_PATH_GIFTCONFIG):
        generate_gift_config_file(len(imgurl2recid.keys()))

    ndate = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    run_sql("UPDATE rnkMETHOD SET last_updated=%s WHERE name=%s",
            (ndate, rank_method_code))
    os.system("gift --port 12700 --datadir "+CFG_GIFTCONFIG_PREFIX+" &")

def is_image(filename):
    """true if the filename's extension is in the content-type lookup"""
    filename = filename.lower()
    return filename[filename.rfind(".")+1:] in ext2conttype

def add_url_recid(recids, fieldname):
    """ Build a map of image url to recids. 
        Fieldname indicate the field where image url can be found.
        Deprecated !! Replaced by add_icon_recid
    """
    tmp_dict = {}
    for recid in recids:
        urls = get_fieldvalues(recid, fieldname)
        for url in urls:
            if is_image(url):
                if CFG_CERN_SITE and \
                    ('documents.cern.ch' in url or \
                    'doc.cern.ch' in url or \
                    'preprints.cern.ch' in url):
                    write_message("omitting url: %s" %url, verbose=9)    
                else:
                    write_message("including url : %s" %url, verbose=9)
                    tmp_dict[url] = recid
    write_message("Number of urls to be indexed by gift found: %s" %
        (len(tmp_dict.keys())) , verbose=3)
    return tmp_dict

def add_icon_recid(recids, icon_obj, icon_label_tag, 
                   icon_label_val, icon_url_tag):
    """ Building a map of image url to recids by the parameters 
        defined in configuration file.
        BibFormatObject is used to simplify the tasks.
    """
    tmp_dict = {}
    icon_url = ""
    for recid in recids:
        bfo = BibFormatObject(recid)
        write_message("in rec %d, getting %s" % (recid, icon_obj), verbose=9)
        resources = bfo.fields(icon_obj)
        for resource in resources:
            write_message("checking "+str(resource), verbose=9)
            icon_url = ""
            res_ilt = resource.get(icon_label_tag, "")
            write_message("resource's icon_label_tag is "+res_ilt+ \
                          " icon label val is "+icon_label_val, verbose=9)
            if (resource.get(icon_label_tag, "") == icon_label_val):
                icon_url = resource.get(icon_url_tag, "").replace(" ","")
            if icon_url != "": #should add some extra checking 
                tmp_dict[icon_url] = recid
    write_message("Number of valid url found: %s" %
        (len(tmp_dict.keys())), verbose=3)
    return tmp_dict

def extract_features(url):
    """ This function download image by url.
        Image is stored in a temporary file and features  
        are extracted from that file.
        When finished, temporary file will be deleted.
    """
    write_message("Feature extraction processing for %s " %
        url, stream=sys.stdout, verbose=3) 
    urlsegs = url.split("/")
    filename = urlsegs[len(urlsegs)-1]
    tmp_img = CFG_TMPDIR + "/" + filename
    write_message("tmp_img: "+tmp_img, verbose=3)
    """Downloading images by url"""
    f_resp = urllib2.urlopen(url)
    urllib.urlretrieve(f_resp.geturl(),tmp_img)
    f_resp.close()

    """ Change image size """
    os.system(CFG_PATH_CONVERT + " -geometry 256x256! " 
        + tmp_img + " " + tmp_ppm)
    """ Extract features from image """
    os.system(CFG_PATH_GIFTFTSEXTRACT + " " + tmp_ppm)
    """ If feature description is not written yet,
        write it now """   
    if(not os.path.isfile(tmp_desc)):
        os.system(CFG_PATH_GIFTWRITEFTSDESC + " <" + tmp_ppm + " >" + tmp_desc)
        column_filter(tmp_desc,CFG_GIFTINDEX_DESC,' ',[0,1])
    """ Move the feature file into gift index folder """
    featurefilename = CFG_GIFTINDEX_PREFIX+"/"+filename+".fts"
    """ Delete all temporary files """
    os.rename(tmp_fts, featurefilename)
    os.remove(tmp_img)
    os.remove(tmp_ppm)
    return featurefilename

def generate_gift_config_file(num_img):
    """ This function generate gift config file.
        Only one collection is set with name of "invenio"
    """
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
    collectionxml.set("cui-feature-description-location",
                      "InvertedFileFeatureDescription.db")
    collectionxml.set("cui-feature-file-location","url2fts.xml")

    queryparadigmlist = ET.SubElement(collectionxml,"query-paradigm-list")
    queryparadigmxml = ET.SubElement(queryparadigmlist,"query-paradigm")
    queryparadigmxml.set("type","inverted-file")
    queryparadigmxml2 = ET.SubElement(queryparadigmlist,"query-paradigm")
    queryparadigmxml2.set("type","perl-demo")

    configET.write(CFG_PATH_GIFTCONFIG, "UTF-8")
    replace_in_files(CFG_PATH_GIFTCONFIG, r'''__COLLECTION__''', r'''invenio''')

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
    """ return the list of recods which have been modified after the 
        last execution of bibrank method. The result is expected to 
        have ascending numerical order.
    """
    query = """SELECT id FROM bibrec
               WHERE modification_date >= '%s' """ % bibrank_method_lastupdate
    query += "order by id ASC"
    list = [row[0] for row in run_sql(query)]
    return list

def replace_in_files(filepath, searchregx, replacestring):
    """Read a file, replace regular expression by given string."""
    # cregex = re.compile(searchregx)
    input = open(filepath,'rb')
    s = unicode(input.read(),'utf-8')
    input.close()
    outtext = re.sub(searchregx, replacestring, s)
    output = open(filepath,'w')
    output.write(outtext)
    output.close()

def column_filter(filename, fileoutput, separator, selected_columns):
    """ Read a csv file, write the selected column into the output file."""
    output = csv.writer(open(fileoutput, 'w'), delimiter=separator)
    inputs = csv.reader(open(filename), delimiter=separator, skipinitialspace=True)
    for line in inputs:
        if line: # Make sure there's at least one entry.
            list = []
            for ind in selected_columns:
                list.append(line[ind])
            output.writerow(list)

def cfgGetParameters(rank_method_code):
    """ get parameters from cfg file, 
        the cfg file is named by rank_method_code.cfg
    """
    write_message("Running rank method: %s" % rank_method_code, verbose=0)
    try:
        file_ = CFG_ETCDIR + "/bibrank/" + rank_method_code + ".cfg"
        config = ConfigParser.ConfigParser()
        config.readfp(open(file_))
        return config
    except StandardError:
        write_message("Cannot find configuration file: %s" % file_, sys.stderr)
        raise StandardError
