#!/usr/bin/perl

use strict;
use POSIX qw(WNOHANG);
# use lib "/usr/local/bin/"; # for including CFeedbackClient
use lib "/usr/share/perl5/GIFT/"; # for including CFeedbackClient
use lib '/usr/lib/perl5/site_perl/5.005/i586-linux/';
use CFeedbackClient; # to make a query in MRML

my $lFeedbackClient = new CFeedbackClient();
my $DIRPrefix = "/opt/cds-invenio/var/gift-index-data";
my $url2fts = "/opt/cds-invenio/var/gift-index-data/url2fts.xml";

my @dir_files = <$DIRPrefix/*>;
my $URLPrefix = "http://arcgift.unige.ch/~xmzh/Fracture\_v2009";
my $thumbURLPrefix = "http://arcgift.unige.ch/~xmzh/Image_thumbnails/Fracture\_v2009\_thumbnails";
my $thumbURLPostfix= "\_thumbnail\_jpg.jpg";
my $resultDir = "/home/xmzh/results/caseRetrieval";
my $randomlist = "/home/xmzh/results/randomlist.txt";

my $range = scalar @dir_files;
my @cases = ();

my $boolean = 1;
my $relevance=1;
my $nbRes = 50;
my $nbResPerImg = 1000;
my %distTable =();

#----------------------------------------------------------------------	#
#  Mode debug:                                    						#
#                                                                      	#
#  PURPOSE:   print output to help to do the debug						#
#----------------------------------------------------------------------	#
sub debugPrint
{
	my $s = shift;
	if (($ARGV[1]) and ($ARGV[1] eq "DEBUG"))
	{
		print STDERR "$s";
	}
}

#----------------------------------------------------------------------	#
#  FUNCTION:  max			                                  		   	#
#                                                                      	#
#  PURPOSE:   Help to calculate the longest value among n values,  		#
#             it is used to calculate the longtest time token by      	#
#             a job.					                            	#
#----------------------------------------------------------------------	#
sub max {
  my($max_so_far) = shift @_;
  foreach (@_)
  {
    if($_>$max_so_far)
    {
      $max_so_far=$_;
    }
  }
  $max_so_far;
}
#----------------------------------------------------------------------	#
#  FUNCTION:  configure_gift_client                            			#
#                                                                      	#
#  PURPOSE:   configure the gift client with gift invenio setup    		#
#----------------------------------------------------------------------	#
sub configure_gift_client{
  # sets the host and the port number
  my $info = $lFeedbackClient->setAddress("localhost:12700");
  debugPrint("setAddress: $info\n");

  # set the size of the desired query result
  $info = $lFeedbackClient->setResultSize("$nbResPerImg");
  debugPrint("setResultSize: $info\n");

  $info = $lFeedbackClient->startSession("-perl-evaluation-");
  debugPrint("startSession: $info\n");

  $info = $lFeedbackClient->configureSession(
    undef,undef,"invenio",undef,"false","false","false","false","100");
  debugPrint("configureSession: $info\n");
}
#----------------------------------------------------------------------	#
#  FUNCTION:  query_regrouped_by_max                                  	#
#                                                                      	#
#  PURPOSE:   Read the code file to have a code table.     				#
#             inside it stocks the pair: image -- code          		#
#----------------------------------------------------------------------	#
sub query_regrouped_by_max{
  %distTable =();
  my $nb = 0;
  while(@_)
  {
    my $line = shift(@_);
    debugPrint("rel: $relevance, image: $line\n");

    # create a new instance
    my @lQuery = (["$line","$relevance"]);

    my $lQueryToSend=$lFeedbackClient->makeQueryString(\@lQuery);

    # Sending the query and printing the MRML we got back from the query
    debugPrint("MRML-----xx----------------------------------\n");
    my $info = $lFeedbackClient->sendQueryString($lQueryToSend);
    debugPrint($info);
    debugPrint("MRML-----xx-----------------------------------\n");

    my $resultsList=$lFeedbackClient->getResultList();

    my $n;
    my $lCount=0;
    my %distMaxTable = ();

    foreach $n (@$resultsList)
    {
      my($lImage,$lRelevance)=@$n;

      debugPrint("$lImage $lRelevance");
      $lImage =~/record\/(\d+)/;
      my $myCase = $1;
      debugPrint($myCase);

      if($distMaxTable{$myCase})
      {
        $distMaxTable{$myCase} = $lRelevance;
      }
      else
      {
        $distMaxTable{$myCase} = max($lRelevance,$distMaxTable{$myCase});
      }
    }

    my @cases = keys %distMaxTable;
    foreach my $caseID (@cases)
    {
      $distTable{$caseID} += $distMaxTable{$caseID}
    }
    $nb++;
  }
}

sub translate_url_recid
{
  my $url = shift;
  
}

sub list_recids
{
  my @key = sort { $distTable{$b} <=> $distTable{$a} } keys %distTable;
  my $keynb = scalar @key;
  # my $maxSimilarity = $distTable{$key[0]};

  for (my $n=0; $n<$nbRes && $n<$keynb; $n++)
  {
    my $caseID = $key[$n];
    print "$caseID $distTable{$key[$n]}\n";
  }
}

configure_gift_client;
query_regrouped_by_max($ARGV[0]);
list_recids;
