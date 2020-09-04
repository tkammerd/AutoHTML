#!/usr/local/bin/perl
############################################################
#                       CHANGE_AUTOHTML.CGI
#
# This script was written by Troy Kammerdiener
# Date Created: 8-29-98
#
#   You may copy this under the terms of the GNU General Public
#   License or the Artistic License which is distributed with
#   copies of Perl v5.x for UNIX
#
# Purpose: To re-create a meta-html file which includes variable text
# embedded between specially formatted comments of the form:
# <!-- ##MERGEFIELD## varname --> value <!-- ##/MERGEFIELD## -->
# (Note that each delimiting comment must appear on a single line,
# although value may span many lines if needed.)
#
# This script is invoked with a query string of variable/value pairs
# which correspond to the variable/value pairs in the formatted 
# comments (and also contain a variable/value pair for the path to
# the autoHTML source file).  Order is not important.  It then
# rebuilds the source file using the (possibly different) values
# passed in the query string.
#
# Main Procedures:
#   &WriteAutoHTML =
#     Creates a new version of the autoHTML file by replacing the
#     current values of the merge variables with values from the
#     corresponding variable/value pairs read from the AutoHTML source file
#   &UserResponse =
#     Creates an HTML file to confirm re-creation of autoHTML file
#
# Inputs:
#   Form Variables: 
#     source = path to AutoHTML source file
#     other dynamically created variables, corresponding to variables in $source
#
# Outputs:
#   A new version of $source.
#
############################################################

# Set up global variables common to all autoHTML scripts
require "./setup_autoHTML.cgi";

# Set up global variables
$SourceFile = "";
$SourcePath = "";
$DestFile = "";
$DestPath = "";
$DestURL = "";
$LeftAngleESC = "~LE~";    # Left Angle escape for hidden variables
$RightAngleESC = "~RE~";   # Right Angle escape for hidden variables
$DblQuoteESC = "~QE~";     # Double Quote escape for hidden variables
@SectionVals = ();
@SectionNames = ();
@SectionMerges = ();
$TotSections = 0;
$LeftDelim = "<!-- ##MERGEFIELD##";
$LeftDelimLen = length($LeftDelim);
$RightDelim = "<!-- ##/MERGEFIELD## -->";
$RightDelimLen = length($RightDelim);


# Set up debugging support
if ($debug_on)
{
  open(DEBUGFILE, ">>" . $DebugPath) ||
    die "Unable to open $DebugPath for debugging.";
  print DEBUGFILE "Running change_autoHTML.cgi\n\n";
}

# Import libraries
require "$lib/cgi-lib.pl";
if ($debug_on)
{
  print DEBUGFILE "Importing libraries\n";
}

# Get path to AutoHTML source file, along with section information
if (&ReadParse > 0)
{
  $SourceFile = $in{"sourcefile"};
  $SourceBase = $in{"sourcebase"};
  $SourcePath = $SourceBase . $SourceFile;
  $TotSections = $in{"totsections"};
  for ($cur_section = 0; $cur_section < $TotSections; $cur_section++)
  {
    ($SectionNames[$cur_section], $escaped_val, $SectionMerges[$cur_section])
      = split(/\0/, $in{"section" . $cur_section});
    $escaped_val =~ s/$DblQuoteESC/"/g;
    $escaped_val =~ s/$LeftAngleESC/</g;
    $escaped_val =~ s/$RightAngleESC/>/g;
    $SectionVals[$cur_section] = $escaped_val;
  }
}
else
{
  # Set $SourcePath path explicitly
  $SourceBase = "./";
  $SourceFile = "NewAutoHTMLTestfile.html";
  $SourcePath = $SourceBase . $SourceFile;
}
# Normally, the line below will be simply $DestFile = $SourceFile
$DestFile = $SourceFile;
$DestPath = $SourceBase . $DestFile;
# $DestURL construction assumes that $SourcePath starts with /~username/public_html/
$DestURL = $DestPath;
$DestURL =~ s:/home/:/~:g;
$DestURL =~ s:public_html/::g;
if ($debug_on)
{
  print DEBUGFILE "Source file set to $SourcePath\n";
  print DEBUGFILE "Destination file set to $DestPath\n";
  print DEBUGFILE "Destination URL set to $DestURL\n";
}

&WriteAutoHTML($SourcePath, $DestPath);
&UserResponse($DestFile);
close(DEBUGFILE);

############################################################
#
# subroutine: WriteAutoHTML
#   Usage: &WriteAutoHTML($AutoHTMLSource, $AutoHTMLDest);
#
#   Parameters:
#     $AutoHTMLSource = path to autoHTML source file
#     $AutoHTMLDest = path to autoHTML destination file
#     (These will usually be the same file.)
#
#   Output:
#     A file is created at $AutoHTMLDest holding the new
#       version of the autoHTML file with new values for
#       the variables drawn from the corresponding members
#       of %in.
#
############################################################

sub WriteAutoHTML
{
  # Set up named parameters
  local($AutoHTMLSource, $AutoHTMLDest) = @_;

  # Set up other local variables
# DOS version:
#    local($TempFile) = "./TempAutoHTML";
# Unix version:
    local($TempFile) = "./TempAutoHTML" . `date '+%H%M%S%m%d%y'`;
  chomp($TempFile);
  local($EOF_reached) = $false;
  local($line_buf);
  local($cur_line) = 0;
  local($varname_pos);
  local($varname_len);
  local($varname);
  local($value_pos);
  local($value_len);
  local($merge_endpos) = 0;

  # Open $AutoHTMLSource for input
  if (!open(SOURCEFILE, $AutoHTMLSource))
  {
    if ($debug_on)
    {
      print DEBUGFILE "Unable to open $AutoHTMLSource\n";
    }
    die "Unable to open $AutoHTMLSource";
  }

  # Open $TempFile for output
  if (!open(OUTPUTFILE, ">" . $TempFile))
  {
    if ($debug_on)
    {
      print DEBUGFILE "Unable to open $TempFile temporary file for output\n";
    }
    die "Unable to open $TempFile temporary file for output";
  }

  while (!$EOF_reached)
  {
    while (!$EOF_reached &&
      (($varname_pos = 
      index($line_buf, $LeftDelim, $merge_endpos)) == -1)) 
    {
      if ($debug2_on)
      {
        print DEBUGFILE "Searched for \"$LeftDelim\" from pos $merge_endpos with result of ";
        print DEBUGFILE index($line_buf, $LeftDelim, $merge_endpos);
        print DEBUGFILE " giving \$varname_pos of $varname_pos\n"
      }

      # Print remainder of line without change
      print OUTPUTFILE substr($line_buf, $merge_endpos);

      if ($line_buf = <SOURCEFILE>)
      {
        $cur_line++; # Count current line of source file being processed
        $merge_endpos = 0;
        if ($debug_on)
        {
          print DEBUGFILE $cur_line, ": ", $line_buf;
        }
      }
      else
      {
        $EOF_reached = true;
        if ($debug_on)
        {
          print DEBUGFILE "EOF reached.\n\n";
        }
      }
    }
    if ($debug2_on && !$EOF_reached)
    {
      print DEBUGFILE "Searched for \"$LeftDelim\" from pos $merge_endpos with result of ";
      print DEBUGFILE index($line_buf, $LeftDelim, $merge_endpos);
      print DEBUGFILE " giving \$varname_pos of $varname_pos\n"
    }

    if (!$EOF_reached)
    {
      # Adjust to first character after delimiter
      $varname_pos = $varname_pos + $LeftDelimLen;

      # Then skip over spaces
      while (substr($line_buf, $varname_pos, 1) eq " ")
      {
        $varname_pos++;
      }
      if ($debug2_on)
      {
        print DEBUGFILE "Varname found at pos $varname_pos\n";
        print DEBUGFILE "Sample at pos $varname_pos: \"", 
          substr($line_buf, $varname_pos, 20), "\"\n";
      }

      # Find length of variable name and extract variable name
      $varname_len = index($line_buf, " ", $varname_pos) - $varname_pos;
      if ($varname_len == -1 - $varname_pos)
      {
        die "Bad ##MERGEFIELD## at line number $cur_line in $AutoHTMLFile";
      }
      $varname = substr($line_buf, $varname_pos, $varname_len);
      if ($debug2_on)
      {
        print DEBUGFILE "Varname is \"$varname\" of length $varname_len\n";
      }

      # Skip to the end of the comment
      $value_pos = index($line_buf, "-->", $varname_pos + $varname_len) + 3;
      if ($value_pos == -1 + 3)
      {
        die "Bad ##MERGEFIELD## at line number $cur_line in $AutoHTMLFile";
      }
      if ($debug2_on)
      {
        print DEBUGFILE "Value starts at pos $value_pos of line $cur_line\n";
        print DEBUGFILE "Sample at pos $value_pos: \"", 
          substr($line_buf, $value_pos, 20), "\"\n";
      }

      # Print out unprinted portion of line up to $value_pos
      print OUTPUTFILE substr($line_buf, $merge_endpos, $value_pos - $merge_endpos);

      $value = ""; #Clear out $value
      $value_len = index($line_buf, $RightDelim, $value_pos)
        - $value_pos;
      if ($debug2_on)
      {
        print DEBUGFILE "Searched for \"$RightDelim\" with result of ";
        print DEBUGFILE index($line_buf, $RightDelim, $value_pos);
        print DEBUGFILE " giving \$value_len of $value_len\n"
      }
      while ($value_len == -1 - $value_pos) # Value does not end on this line
      {
        # Read in next line
        if (!($line_buf = <SOURCEFILE>))
        {
          die "Multiline value not terminated -- EOF reached prematurely";
        }
        $cur_line++; # Count current line of source file being processed
        if ($debug_on)
        {
          print DEBUGFILE $cur_line, ": ", $line_buf;
        }
        $merge_endpos = 0;
        $value_pos = 0;
        if ($debug2_on)
        {
          print DEBUGFILE "Value continues at pos $value_pos of line $cur_line\n";
          print DEBUGFILE "Sample at pos $value_pos: \"", 
            substr($line_buf, $value_pos, 20), "\"\n";
        }
        $value_len = index($line_buf, $RightDelim, $value_pos)
          - $value_pos;
        if ($debug2_on)
        {
          print DEBUGFILE "Searched for \"$RightDelim\" with result of ";
          print DEBUGFILE index($line_buf, $RightDelim, $value_pos);
          print DEBUGFILE " giving \$value_len of $value_len\n"
        }
      }

      # Output new value instead of old one
      print OUTPUTFILE $in{$varname};
      if ($debug_on)
      {
        print DEBUGFILE "Storing new value for ", $varname, " of \"", $in{$varname}, "\"\n";
      }

      # Print out right-hand mergefield delimiter
      print OUTPUTFILE $RightDelim;

      # Set end postion of old value in $line_buf
      $merge_endpos = $value_pos + $value_len + $RightDelimLen;
    }
  }

  close(SOURCEFILE);
  close(OUTPUTFILE);
# DOS version
#    $TempFile =~ s!\/!\\!g;
#    $AutoHTMLDest =~ s!\/!\\!g;
#    system("move $TempFile $AutoHTMLDest");
# Unix version:
    system("mv $TempFile $AutoHTMLDest");
}

############################################################
#
# subroutine: UserResponse
#   Usage: &UserResponse($AutoHTMLDest);
#
#   Parameters:
#     $AutoHTMLDest = path to autoHTML destination file
#
#   Output:
#     An HTML file is sent to STDOUT informing the user that
#       the new file has been created, and containing a link
#       to that file.
#
############################################################

sub UserResponse
{
  # Set up named parameters
  local($AutoHTMLDest) = @_;

  # Set up other local variables
  local($URL) = $DestURL;
  local($action) = $autoHTML_base_URL . "/update_autoHTML.cgi";
  local($cur_section) = 0;

  print "Content-type: text/html\n\n";

print <<__END_OF_HTML__;
<HTML>
  <HEAD>
    <TITLE>AutoHTML file re-created</TITLE>
  </HEAD>
  <BODY>
    <H1>Success!</H1>
    You have successfully updated $AutoHTMLDest.  You can see it <A HREF="$URL">here</A>.
    <FORM METHOD="POST" ACTION="$action">
      <INPUT TYPE="hidden" NAME="sourcefile" VALUE="$DestFile">
      <INPUT TYPE="hidden" NAME="sourcebase" VALUE="$SourceBase">
      <INPUT TYPE="hidden" NAME="totsections" VALUE="$TotSections">
__END_OF_HTML__
  for ($cur_section = 0; $cur_section < $TotSections; $cur_section++)
  {
    print "      <INPUT TYPE=\"hidden\" NAME=\"section" . $cur_section .
      "\" VALUE=\"" . $SectionNames[$cur_section] . "\">\n";
    $escaped_val = $SectionVals[$cur_section];
    $escaped_val =~ s/"/$DblQuoteESC/g;
    $escaped_val =~ s/</$LeftAngleESC/g;
    $escaped_val =~ s/>/$RightAngleESC/g;
    print "      <INPUT TYPE=\"hidden\" NAME=\"section" . $cur_section .
      "\" VALUE=\"" . $escaped_val . "\">\n";
    print "      <INPUT TYPE=\"hidden\" NAME=\"section" . $cur_section .
      "\" VALUE=\"" . $SectionMerges[$cur_section] . "\">\n";
  }
print <<__END_OF_HTML__;
      You can edit it's mergefields by clicking this button:
      <INPUT TYPE="submit" VALUE="Edit Mergefields">
    </FORM>
  </BODY>
</HTML>
__END_OF_HTML__
}

sub Old_UserResponse
{
  # Set up named parameters
  local($AutoHTMLDest) = @_;

  # Set up other local variables
  local($URL) = $autoHTML_base_URL . "/" . $AutoHTMLDest;
  local($CGI_call) = $autoHTML_base_URL . "/update_autoHTML.cgi?source=" . $AutoHTMLDest;

  print "Content-type: text/html\n\n";

print <<__END_OF_HTML__;
<HTML>
  <HEAD>
    <TITLE>AutoHTML file re-created</TITLE>
  </HEAD>
  <BODY>
    <H1>Success!</H1>
    You have successfully updated $AutoHTMLDest.  You can see it <A HREF="$URL">here</A>.
    You can edit it's mergefields <A HREF="$CGI_call">here</A>.
  </BODY>
</HTML>
__END_OF_HTML__
}
