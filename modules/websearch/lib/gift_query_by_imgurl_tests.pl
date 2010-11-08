#!/usr/bin/perl

use strict;
use POSIX qw(WNOHANG);
use XML::Simple;



#----------------------------------------------------------------------	#
#  Mode debug:                                    						#
#                                                                      	#
#  PURPOSE:   print output to help to do the debug						#
#----------------------------------------------------------------------	#
my $arg1 = "perl";
my $arg2 = "gift_query_by_imgurl.pl";
my $arg3 = "+http://mediaarchive.cern.ch/MediaArchive/Photo/Public/1961/6103488/6103488/6103488-Icon.jpg&+http://mediaarchive.cern.ch/MediaArchive/Photo/Public/1961/6103486/6103486/6103486-Icon.jpg&-http://mediaarchive.cern.ch/MediaArchive/Photo/Public/1961/6103471/6103471/6103471-Icon.jpg";
my $arg4 = "/opt/cds-invenio/var/gift-index-data/url2fts.xml";
my $arg5 = "DEBUG";
system($arg1,$arg2,$arg3,$arg4,$arg5);
