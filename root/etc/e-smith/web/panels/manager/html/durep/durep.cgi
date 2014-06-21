#!/usr/bin/perl -w

#############################################################################
# durep - Disk Usage Report Generator                                       #
#                                                                           #
# Copyright (C) 2004 Damian Kramer (psiren@hibernaculum.net)                #
#                                                                           #
# You may distribute this program under the terms of the Artistic License.  #
#                                                                           #
# This program is distributed in the hope that it will be useful, but       #
# WITHOUT ANY WARRANTY; without even the implied warranty of                #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the             #
# Artistic License for more details.                                        #
#############################################################################

use MLDBM qw(DB_File Storable);
use POSIX;

use strict;

## Set these variables as appropriate.
## --------------------------------------------------
our $datadir    = "/var/lib/durep";      # Filesystem path to the data files.
our $css_file   = "/server-manager/durep/style.css";    # URL to CSS file
our $bar_image  = "/server-manager/durep/bar.png";      # URL to image used in bar graph
our $show_mtime = 1;                     # Show file modifcation time
our $show_opts  = 0;                     # Show options used
## --------------------------------------------------


### NO USER-SERVICEABLE PARTS BEYOND THIS POINT ###

our ($me, $data, @ancestors, @records, %input, $temp, $version, $top_node, $collated);
our ($TYPE_FILE, $TYPE_DIR, $TYPE_EMPTY, $TYPE_COALESCED, $TYPE_COLLAPSED);

$me = $ENV{SCRIPT_NAME};

$TYPE_FILE        = 0;
$TYPE_DIR         = 1;
$TYPE_EMPTY       = 2;
$TYPE_COALESCED   = 4;
$TYPE_COLLAPSED   = 8;

$version = "0.9";

$ENV{PATH} = "/bin:/usr/bin";

$top_node = {};
$collated = loadCollateFile($datadir);

getInput();

if(%input) {
  fetchData();
  displayData();
}
else {
  displayList();
}

# Return to system
exit 0;

sub getInput {

  if($ENV{REQUEST_METHOD} eq 'POST') {
    chomp($_ = <STDIN>);
  }
  elsif($ENV{REQUEST_METHOD} eq 'GET') {
    $_ = $ENV{QUERY_STRING};
  }
  else {
    return;
  }

  for $temp (split("&", $_)) {
    my ($var, $val) = split ('=', $temp);
    $val =~ s/\+/ /g;
    $val =~ s/%(..)/pack("H2", $1)/eg;
    if(defined $input{$var}) {
      $input{$var} .= "\0$val";
    }
    else {
      $input{$var} = $val;
    }
  }
}


sub displayInput {
  print "Content-type: text/html\n\n";
 
  my ($key, $val);
  print "<html><head><title>SMESERVER Disk Usage Report</title></head>";
  print "<body bgcolor='#FFFFFF' text='#000000' link='#0000FF' vlink='#0000AA'><br><br>";
  
  print "<table cellpadding=0 cellspacing=0 border=1>";
  while(($key, $val) = each %input) {
    my $length = length $val;
    print "<tr><td><pre>$key</pre></td><td><pre>[$length]</pre></td><td><pre>[$val]</pre></td></tr>\n";
  }
  print "</table></pre>";
  print "</body></html>";
}

sub fetchData {
  my $root_node = {};
  my $node;

  tie %{$root_node}, 'MLDBM', "$datadir/$collated->{$input{fid}}->{FILENAME}", O_RDONLY, 0640 or errorPage();

  %{$data} = (%{$root_node->{DATA}});

  %{$top_node} = (%{$root_node->{$input{nid}}});

  $node = $top_node;
  while($node->{PARENT}) {
    my $tmp = {};
    %{$tmp} = (%{$root_node->{$node->{PARENT}}});
    unshift @ancestors, $tmp;
    $node = $tmp;
  }

  foreach $node (@{$top_node->{CHILDREN}}) {
    my $tmp = {};
    %{$tmp} = (%{$root_node->{$node}});
    push @records, $tmp;
  }

  @records = reverse sort sortBySize @records;

  untie %{$root_node};
}

sub displayList {
  print "Content-type: text/html\n\n";
  my $hash = sortCollateFile($collated);
  my ($key, $val);
  print qq{
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="en" xml:lang="en">
<head>
<title>Disk Usage Report</title>
<link rel="stylesheet" href="$css_file" type="text/css"/>
</head>
<body>
<h1>Disk Usage Report</h1>
<table class='list' cellpadding=0 cellspacing=0 border=0>
<tr><th>&nbsp;</th><th>Path</th><th>Description</th><th>Size</th><th>Dirs</th><th>Files</th><th>Date</th></tr>
};  
  foreach my $host (keys %{$hash}) {
    print "<tr><td colspan=7 class='dark'>$host</td></tr>\n";
    my $flip = 0;
    foreach my $e (reverse sort sortByDate @{$hash->{$host}}) {
      if($flip) { print "<tr class='mid'>"; }
      else { print "<tr class='light'>"; }
      $flip = !$flip;
      print "<td>&nbsp;</td>";
      print "<td><a href='$me?fid=$e->{ID}&nid=1'>$e->{PATH}</a></td>";
      printf "<td><a href='$me?fid=$e->{ID}&nid=1'>%s</a></td>", $e->{DESC} || "-";
      printf "<td>%s</td>", prettyFileSize($e->{SIZE});
      printf "<td>%s</td>", prettyNum($e->{DIR_COUNT});
      printf "<td>%s</td>", prettyNum($e->{FILE_COUNT});
      printf "<td>%s</td>", prettyDate($e->{LAST_UPDATE});
      print "</tr>\n";
    }
  }
# table to show df of all disk on main page
  print qq{
</table>
<table class='list' cellpadding=0 cellspacing=0 border=0>
<tr><th>Filesystem</th><th>Sized</th><th>Used</th><th>Available</th><th>Use %</th><th>Mounted on</th></tr>
};
my $dflist = `df -h|grep -v 'Use%'|sed 's#^#<tr><td>#g'|sed 's#\$#</td></tr>#g'`;
$dflist =~ s/[ ]+/<\/td><td>/g;
print $dflist;


  print qq{
</table>
</body>
</html>
};
}

sub displayData {
  print "Content-type: text/html\n\n";

  my ($key, $val);
print qq{
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="en" xml:lang="en">
<head>
<title>Disk Usage Report ($data->{HOSTNAME})</title>
<link rel="stylesheet" href="$css_file" type="text/css"/>
</head>
<body>
<h1>Disk Usage Report ($data->{HOSTNAME})</h1>
<div class='tbar'><table class='location'><tr><td>[<a href='$me'>Home</a>]
};
  foreach my $tmp (@ancestors) {
    printf "<a href='$me?fid=$input{fid}&nid=%d'>$tmp->{NAME}</a>%s", $tmp->{ID}, (($tmp->{NAME} =~ m|\/$|) ? "" : "/");
  }
  print "$top_node->{NAME}</td>";
  printf "<td class='right'>%s</td>", prettyFileSize($top_node->{SIZE});
  print "</tr></table></div>";

  print "<table class='report' cellpadding=0 cellspacing=0 border=0>\n";
  print "<tr class='dark'><th>Size</th><th colspan=2>Percentage</th>";
  print "<th class='right'>Dirs</th><th class='right'>Files</th>";
  print "<th>Modified</th>" if $show_mtime;
  print "<th>File</th></tr>";

  my $flip = 0;
  foreach my $node (@records) {
    my $percent = $top_node->{SIZE} ? ($node->{SIZE}/$top_node->{SIZE}*100) : 0;
    if($flip) { print "<tr class='mid'>"; }
    else { print "<tr class='light'>"; }
    $flip = !$flip;
    print "<td class='right'>";
    print prettyFileSize($node->{SIZE});
    print "</td><td>";
    print barChart($percent);
    printf("</td><td class='right'>%4.2f%%</td>", $percent);

    if($node->{TYPE} & $TYPE_DIR) {
      if($node->{TYPE} & $TYPE_EMPTY) {
	print "<td class='right'>0</td><td class='right'>0</td>";
	printf("<td>%s</td>", shortDate($node->{MTIME})) if $show_mtime;
	print "<td><span class='empty'>$node->{NAME}/</span></td>";
      }
      else {
	printf("<td class='right'>%d</td>", $node->{DCOUNT});
	printf("<td class='right'>%d</td>", $node->{FCOUNT});
	printf("<td>%s</td>", shortDate($node->{MTIME})) if $show_mtime;
	print "<td><span class='dir'><a href='$me?fid=$input{fid}&nid=$node->{ID}'>$node->{NAME}/</a></span></td>";
      }
    }
    elsif($node->{TYPE} & $TYPE_COALESCED) {
      printf "<td>&nbsp;</td><td class='right'>%d</td>", $node->{FCOUNT};
      printf("<td>%s</td>", shortDate($node->{MTIME})) if $show_mtime;
      print "<td><span class='coalesced'>$node->{NAME}</span></td>";
    }
    else {
      print "<td>&nbsp;</td><td>&nbsp;</td>";
      printf("<td>%s</td>", shortDate($node->{MTIME})) if $show_mtime;
      print "<td>$node->{NAME}</td>";
    }
    print "</tr>\n";
  }
  print "</table>\n";

  print "<div class='bbar'><table class='location'><tr>";
  printf "<td>%s</td>", scalar localtime($data->{LAST_UPDATE});
  print "<td class='right'>Generated by <a href='http://www.hibernaculum.net/'>durep</a> v. $version</td>";
  print "</tr></table></div>\n";

  if($show_opts && $data->{OPTIONS}) {
    print "<div class='options'><ul>";
    print "<li>Scanning files only.</li>" if $data->{OPTIONS}->{FILES};
    print "<li>Restricting to single filesystem.</li>" if $data->{OPTIONS}->{ONEFILESYSTEM};
    printf "<li>Collapsing paths matching <b>%s</b>.</li>", $data->{OPTIONS}->{COLLAPSEPATH} if $data->{OPTIONS}->{COLLAPSEPATH};
    printf "<li>Excluding paths matching <b>%s</b>.</li>", $data->{OPTIONS}->{EXCLUDEPATH} if $data->{OPTIONS}->{EXCLUDEPATH};
    printf "<li>Coalescing files below <b>%s</b>.</li>", prettyFileSize($data->{OPTIONS}->{COALESCEFILES}) if $data->{OPTIONS}->{COALESCEFILES};
    print "</ul></div>";
  }
  print "</body></html>";
}

### All this does is create an HTML table bar graph type thingy.
sub barChart {
  my $percent = int($_[0]*2+0.5);
  my $rv = "<div class='graph'>";
  if($percent) {
    $rv .= "<img src='$bar_image' style=\"width:${percent}px; height: 15px;\"/>";
  }
  else {
    $rv .= "&nbsp;";
  }
  $rv .= "</div>";
  return $rv;
}

# Generates a human readable file size string
sub prettyFileSize {
  my $val = $_[0];
  my $dtype = "b";

  if($val >= 1024) {
    $val /= 1024;
    $dtype = "K";
  }
  if($val >= 1024) {
    $val /= 1024;
    $dtype = "M";
  }
  if($val >= 1024) {
    $val /= 1024;
    $dtype = "G";
  }
  if($dtype eq "b") {
    return sprintf("%d%s", $val, $dtype);
  }
  else {
    return sprintf("%.1f%s", $val, $dtype);
  }
}


sub prettyDate {
  return POSIX::strftime("%T %a %b %e %Y", localtime $_[0]);
}

sub shortDate {
  if($_[0] < (time - 31536000)) {
    return POSIX::strftime("%b %e %Y", localtime $_[0]);
  }
  return POSIX::strftime("%b %e %H:%M", localtime $_[0]);
}

sub prettyNum {
  my $r = reverse shift;
  $r =~ s/(\d\d\d)(?=\d)(?!\d*\.)/$1,/g;
  return scalar reverse $r;
}

sub sortBySize {
  return $a->{SIZE} <=> $b->{SIZE};
}

sub sortByDate {
  return $a->{LAST_UPDATE} <=> $b->{LAST_UPDATE};
}

sub sortByPath {
  return $a->{PATH} cmp $b->{PATH};
}
 
sub loadCollateFile {
  my $dir = shift;
  my %db;
  my $r;
  tie %db, 'MLDBM', "$dir/durep.cds", O_RDONLY, 0640 or errorPage();

  foreach my $key (keys %db) {
    $r->{$key} = \%{$db{$key}};
  }
  untie %db;
  return $r;
}

sub sortCollateFile {
  my $hash = shift;
  my $r;
  foreach my $key (keys %{$hash}) {
    my $hostname = $hash->{$key}->{HOSTNAME};
    push @{$r->{$hostname}}, \%{$hash->{$key}};
  }
  return $r;
}


sub errorPage {
  print "Content-type: text/html\n\n";
  print qq{
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="en" xml:lang="en">
<head>
<title>Disk Usage Report</title>
<link rel="stylesheet" href="$css_file" type="text/css"/>
</head>
<body>
<h1>Durep encountered an error!</h1>
<p>Please check that you have collated the files and that the permissions on them are correct.</p>
</body>
</html>
};
exit 0;
}
