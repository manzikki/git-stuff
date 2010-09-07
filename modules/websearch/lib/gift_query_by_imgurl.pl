#!/usr/bin/perl

use strict;
use POSIX qw(WNOHANG);
use XML::Simple;
# use lib "/usr/local/bin/"; # for including CFeedbackClient
use lib "/usr/share/perl5/GIFT/"; # for including CFeedbackClient
use lib '/usr/lib/perl5/site_perl/5.005/i586-linux/';
use CFeedbackClient; # to make a query in MRML

my $lFeedbackClient = new CFeedbackClient();

my @cases = ();

my $boolean = 1;
my $relevance=1;
my $nbRes = 50;
my $nbResPerImg = 1000;
my %distTable =();
my %distMaxTable=();
my %hashmap = ();

#----------------------------------------------------------------------	#
#  Mode debug:                                    						#
#                                                                      	#
#  PURPOSE:   print output to help to do the debug						#
#----------------------------------------------------------------------	#
sub debugPrint
{
	my $s = shift;
	if (($ARGV[2]) and ($ARGV[2] eq "DEBUG"))
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
#  FUNCTION:  map_url_recid	                                  		   	#
#                                                                      	#
#  PURPOSE:   read file url2fts.xml, where recid is stocked in the 		#
#			  'thumbnail-url-postfix' field					            #
#----------------------------------------------------------------------	#
sub map_url_recid
{
	my $file = shift;
	%hashmap = ();

	my $xs1 = XML::Simple->new();
	my $doc = $xs1->XMLin($file);
	my @imglist = $doc->{'image'};

	foreach my $img ( @{ $doc->{'image'} } )
	{
	   $hashmap{$img->{'url-postfix'}}= $img->{'thumbnail-url-postfix'};
	}
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
#  FUNCTION:  process_query			                                  	#
#                                                                      	#
#  PURPOSE:   Read the code file to have a code table.     				#
#             inside it stocks the pair: image -- code          		#
#----------------------------------------------------------------------	#
sub process_query
{
  	%distTable =();
	my @lQuery = ();

  	while(@_)
  	{
		my $line = shift(@_);
		my $rel = substr($line, 0, 1);
		$line = substr($line, 1);

		if ($rel eq "-")
		{
			$relevance = -1;
		}

    	debugPrint("rel: $relevance, image: $line\n");
    	# create a new instance

    	push @lQuery,["$line","$relevance"];
  	}

    my $lQueryToSend=$lFeedbackClient->makeQueryString(\@lQuery);

    # Sending the query and printing the MRML we got back from the query
    debugPrint("MRML-----xx----------------------------------\n");
    my $info = $lFeedbackClient->sendQueryString($lQueryToSend);
    debugPrint($info);
    debugPrint("MRML-----xx-----------------------------------\n");

    $resultsList=$lFeedbackClient->getResultList();
}

sub fusion_by_combMAX
{
    my $n;
    my $lCount=0;
    %distMaxTable = ();

    foreach $n (@$resultsList)
    {
      	my($lImage,$lRelevance)=@$n;

      	debugPrint("$lImage $lRelevance\n");
      	my $myCase = $hashmap{$lImage};
      	debugPrint("$myCase\n");

      	if(!$distMaxTable{$myCase})
      	{
        	$distMaxTable{$myCase} = $lRelevance;
      	}
      	else
      	{
        	$distMaxTable{$myCase} = max($lRelevance,$distMaxTable{$myCase});
      	}
    }
    %distTable = %distMaxTable;
}

#----------------------------------------------------------------------	#
#  FUNCTION:  list_recids			                                  	#
#                                                                      	#
#  PURPOSE:   Print results in console so that can be     				#
#             catched inside python programs.			          		#
#----------------------------------------------------------------------	#
sub list_recids
{
	my @key = sort {
  		$distTable{$b} <=> $distTable{$a}
	} keys %distTable;

	my $keynb = scalar @key;
	my $maxSimilarity = $distTable{$key[0]};

	for (my $n=0; $n<$nbRes && $n<$keynb; $n++)
	{
		my $caseID = $key[$n];
                my $similarityPercentage = $distTable{$key[$n]};
    	print "$caseID $similarityPercentage\n";
	}
}

if (($ARGV[0]=~/http/) && ($ARGV[1]=~/url2fts/))
{
    map_url_recid($ARGV[1]);
    configure_gift_client;
    my @list_imgs = split('&',$ARGV[0]);
    process_query(@list_imgs);
    fusion_by_combMAX();
    list_recids;
}
