#!/usr/local/bin/perl

############################################################
#                       UPDSEC_AUTOHTML.CGI
#
# This script was written by Troy Kammerdiener
# Date Created: 9-4-98
#
#   You may copy this under the terms of the GNU General Public
#   License or the Artistic License which is distributed with
#   copies of Perl v5.x for UNIX
#
# Purpose: To maintain a meta-html file which includes text
# embedded between specially formatted comments of the form:
# <!-- ##SECTION## secname --> value <!-- ##/SECTION## -->
# (Note that each delimiting comment must appear on a single line,
# although value may span many lines if needed.)
#
# This script creates an input form that will display the sections
# marked by the specially formatted comments.  For each section, a
# choice will be given to allow the user to keep it, remove it,
# comment it out, comment it back in, or
# to add copies of it, and an input field will also be provided for
# the number of copies to add.  When this form is submitted, the
# section names along with the action to take is passed to 
# CHGSEC_AUTOHTML.CGI, which performs the requested actions.
#
# Main Procedures:
#   &ReadAutoHTML =
#     Creates variables for each section and initializes them to the
#     text contained within the corresponding section tags from the
#     AutoHTML source file
#   &CreateTop =
#     Creates the section of the output HTML file which precedes the
#     FORM section.  Often customized.
#   &CreateForm =
#     Creates the HTML FORM section from the section names and section
#     contents read by ReadAutoHTML.  Usually custom written to conform
#     to the AutoHTML source file, but may simply call CreateSimpleForm.
#   &CreateSimpleForm =
#     Creates a basic form using one text field for each variable/value
#     pair.
#   &CreateBottom =
#     Creates the section of the output HTML file which follows the FORM
#     section.  Often customized.
#
# Inputs:
#   Form Variables: 
#     source = path to AutoHTML source file
#
# Outputs:
#   An HTML page containing a FORM which invokes CHGSEC_AUTOHTML.CGI.
#
############################################################

# Set up global variables common to all autoHTML scripts
require "./setup_autoHTML.cgi";

# Set up global variables
%name_sect = ();
@ordering = ();
$tot_sections = 0;
$SourceFile = "";
$SourcePath = "";
$LeftDelim = "<!-- ##SECTION##";
$LeftDelimLen = length($LeftDelim);
$RightDelim = "<!-- ##/SECTION## -->";
$RightDelimLen = length($RightDelim);

# Set up debugging support
if ($debug_on)
{
  open(DEBUGFILE, ">" . $DebugPath) ||
    die "Unable to open $DebugPath for debugging.";
}

# Import libraries
require "$lib/cgi-lib.pl";
if ($debug_on)
{
  print DEBUGFILE "Importing libraries\n";
}


# Get path to AutoHTML source file
if (&ReadParse > 0)
{
  $SourceFile = $in{"sourcefile"};
  $SourceBase = $in{"sourcebase"};
  $SourcePath = $SourceBase . $SourceFile;
}
else
{
  # Set $SourcePath path explicitly
  $SourceBase = "./";
  $SourceFile = "AutoHTMLTestfile.html";
  $SourcePath = $SourceBase . $SourceFile;
}
if ($debug_on)
{
  print DEBUGFILE "Source file set to $SourcePath\n";
}

&ReadAutoHTML($SourcePath);
print "Content-type: text/html\n\n";
&CreateTop;
&CreateForm;
&CreateBottom;
close(DEBUGFILE);

############################################################
#
# subroutine: ReadAutoHTML
#   Usage: &ReadAutoHTML($AutoHTMLFile);
#
#   Parameters:
#     $AutoHTMLFile = path to autoHTML source file
#
#   Output:
#     Global associative array %name_sect will hold the
#       name/section pairs extracted from the autoHTML 
#       source file as a side effect.
#     Global array @ordering will hold the section names
#       of every section in the order in which they were
#       read, starting with subscript 0.
#
############################################################

sub ReadAutoHTML
{
  # Set up named parameters
  local($AutoHTMLFile) = @_;

  # Set up other local variables
  local($EOF_reached) = $false;
  local($line_buf);
  local($cur_line) = 0;
  local($sectname_pos);
  local($sectname_len);
  local($sectname);
  local($sect_num) = 0;
  local($value_pos);
  local($value_len);
  local($value);
  local($sect_endpos) = 0;

  # Open $AutoHTMLFile for input
  open(SOURCEFILE, $AutoHTMLFile) ||
    die "Unable to open $AutoHTMLFile";

  while (!$EOF_reached)
  {
    # Find the start of a new section
    while (!$EOF_reached &&
      (($sectname_pos = 
      index($line_buf, "$LeftDelim", $sect_endpos)) == -1)) 
    {
      if ($debug2_on)
      {
        print DEBUGFILE "Searched for \"$LeftDelim\" from pos $sect_endpos with result of ";
        print DEBUGFILE index($line_buf, "$LeftDelim", $sect_endpos);
        print DEBUGFILE " giving \$sectname_pos of $sectname_pos\n"
      }
      if ($line_buf = <SOURCEFILE>)
      {
        $cur_line++; # Count current line of source file being processed
        $sect_endpos = 0;
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
      print DEBUGFILE "Searched for \"$LeftDelim\" from pos $sect_endpos with result of ";
      print DEBUGFILE index($line_buf, "$LeftDelim", $sect_endpos);
      print DEBUGFILE " giving \$sectname_pos of $sectname_pos\n"
    }

    if (!$EOF_reached) # if a new section was found
    {
      # Adjust to first character after delimiter
      $sectname_pos = $sectname_pos + $LeftDelimLen;

      # Then skip over spaces
      while (substr($line_buf, $sectname_pos, 1) eq " ")
      {
        $sectname_pos++;
      }
      if ($debug2_on)
      {
        print DEBUGFILE "sectname found at pos $sectname_pos\n";
        print DEBUGFILE "Sample at pos $sectname_pos: \"", 
          substr($line_buf, $sectname_pos, 20), "\"\n";
      }

      # Find length of section name and extract section name
      $sectname_len = index($line_buf, " ", $sectname_pos) - $sectname_pos;
      if ($sectname_len == -1 - $sectname_pos)
      {
        die "Bad ##SECTION## at line number $cur_line in $AutoHTMLFile";
      }
      $sectname = substr($line_buf, $sectname_pos, $sectname_len);
      if ($debug2_on)
      {
        print DEBUGFILE "sectname is \"$sectname\" of length $sectname_len\n";
      }

      # Skip to the end of the comment
      $value_pos = index($line_buf, "-->", $sectname_pos + $sectname_len) + 3;
      if ($value_pos == -1 + 3)
      {
        die "Bad ##SECTION## at line number $cur_line in $AutoHTMLFile";
      }
      if ($debug2_on)
      {
        print DEBUGFILE "Value starts at pos $value_pos of line $cur_line\n";
        print DEBUGFILE "Sample at pos $value_pos: \"", 
          substr($line_buf, $value_pos, 20), "\"\n";
      }

      $value = ""; #Clear out $value
      $value_len = index($line_buf, "$RightDelim", $value_pos)
        - $value_pos;
      if ($debug2_on)
      {
        print DEBUGFILE "Searched for \"$RightDelim\" with result of ";
        print DEBUGFILE index($line_buf, "$RightDelim", $value_pos);
        print DEBUGFILE " giving \$value_len of $value_len\n"
      }
      while ($value_len == -1 - $value_pos) # Value does not end on this line
      {
        # Add remainder of line to $value
        $value = $value . substr($line_buf, $value_pos);

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
        $sect_endpos = 0;
        $value_pos = 0;
        if ($debug2_on)
        {
          print DEBUGFILE "Value continues at pos $value_pos of line $cur_line\n";
          print DEBUGFILE "Sample at pos $value_pos: \"", 
            substr($line_buf, $value_pos, 20), "\"\n";
        }
        $value_len = index($line_buf, "$RightDelim", $value_pos)
          - $value_pos;
        if ($debug2_on)
        {
          print DEBUGFILE "Searched for \"$RightDelim\" with result of ";
          print DEBUGFILE index($line_buf, "$RightDelim", $value_pos);
          print DEBUGFILE " giving \$value_len of $value_len\n"
        }
      }

      # Add remainder of value to $value
      $value = $value . substr($line_buf, $value_pos, $value_len);
      $sect_endpos = $value_pos + $value_len + $RightDelimLen;

      # Record name/section pair
      @ordering[$sect_num] = $sectname;
      if ($debug_on)
      {
        print DEBUGFILE "Recording ", $sectname, " = \"", $value, "\"\n";
      }
      $sect_num = $sect_num + 1;
      $name_sect{$sectname} = $value;
    }
  }
  $tot_sections = $sect_num;

  close(SOURCEFILE);
}

############################################################
#
# subroutine: CreateTop
#   Usage:
#
#   Parameters:
#
#   Output:
#
############################################################

sub CreateTop
{
print <<__END_OF_HTML__;
<HTML>
  <HEAD>
    <TITLE>Form to update sections of autoHTML file $SourcePath</TITLE>
  </HEAD>
  <BODY>
__END_OF_HTML__
}

############################################################
#
# subroutine: CreateForm
#   Usage:
#
#   Parameters:
#
#   Output:
#
############################################################

sub CreateForm
{
  &CreateSimpleForm;
}

############################################################
#
# subroutine: CreateSimpleForm
#   Usage:
#     &CreateSimpleForm;
#
#   Parameters: None
#
#   Output:
#     Sends output to stdout (back to the browser) consisting
#     of the FORM that will allow the user to specify what
#     happens to each section.
#
############################################################

sub CreateSimpleForm
{
  # Set up other local variables
  local($sectname);
  local($value);
  local($cur_sect);

print <<__END_OF_HTML__;
    <FORM ACTION="$autoHTML_base_URL/chgsec_autoHTML.cgi" METHOD="post"> 
      <INPUT TYPE="hidden" NAME="sourcefile" VALUE="$SourceFile">
      <INPUT TYPE="hidden" NAME="sourcebase" VALUE="$SourceBase">
__END_OF_HTML__

  print "      <TABLE BORDER=1>\n";
  for ($cur_sect = 0; $cur_sect < $tot_sections; $cur_sect++)
  {
    $sectname = @ordering[$cur_sect];
    $value = $name_sect{$sectname};
    if ($debug_on)
    {
      print DEBUGFILE "\@ordering[$cur_sect] or $sectname = \"$value\"\n";
    }
print <<__END_OF_HTML__;
        <TR>
          <TD WIDTH="10%" BGCOLOR="orange">
            <INPUT TYPE="radio" NAME="$sectname" VALUE="N" CHECKED> No&nbsp;Change<BR>
            <INPUT TYPE="radio" NAME="$sectname" VALUE="D"> Delete<BR>
            <INPUT TYPE="radio" NAME="$sectname" VALUE="I"> Ignore<BR>
            <INPUT TYPE="radio" NAME="$sectname" VALUE="R"> Restore<BR>
            <INPUT TYPE="radio" NAME="$sectname" VALUE="C">&nbsp;Make&nbsp;<INPUT TYPE="text" NAME="$sectname" VALUE=1 SIZE="2">&nbsp;Copies
              &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;of&nbsp;Section
          </TD>
          <TD VALIGN="top">
            <TABLE BORDER=1 WIDTH="100%">
              <TR><TD BGCOLOR="lightblue" COLSPAN=2>Section name: <B>$sectname</B></TD></TR>
              <TR><TD COLSPAN=2>$value</TD></TR>
__END_OF_HTML__

@mergefields = split(m\<!-- ##/MERGEFIELD## -->\, $value);
$num_mergefields = 0;
foreach $curfield (@mergefields)
{
  ($junk, $curfield) = split(/##MERGEFIELD##\s*/, $curfield);
  if ($curfield)
  {
    ($varname, $fieldval) = split(/\s*-->/, $curfield);
    $fieldval =~ s/</&lt;/g;
    $fieldval =~ s/>/&gt;/g;
    print "              <TR>\n";
    print "                <TD WIDTH=\"20%\" BGCOLOR=\"lightblue\">Mergefield name:<BR><B>$varname</B></TD>\n";
    print "                <TD><TABLE><TR><TD>$fieldval</TD></TR></TABLE></TD>\n";
    print "              </TR>\n";
    $num_mergefields++;
  }
}
if ($num_mergefields == 0)
{
  print "              <TR>\n";
  print "                <TD WIDTH=\"20%\" BGCOLOR=\"lightblue\"><B>No Mergefields Present</B></TD>\n";
  print "                <TD>&nbsp;</TD>\n";
  print "              </TR>\n";
}

print <<__END_OF_HTML__;             
            </TABLE>
          </TD>
        </TR>
__END_OF_HTML__
  }
  print "      </TABLE>\n";

print <<__END_OF_HTML__;
      <INPUT TYPE="submit" VALUE="Generate new page">
      <INPUT TYPE="reset" VALUE="Start over"><BR>
    </FORM> 
__END_OF_HTML__

}

############################################################
#
# subroutine: CreateBottom
#   Usage:
#
#   Parameters:
#
#   Output:
#
############################################################

sub CreateBottom
{
print <<__END_OF_HTML__;
  </BODY>
</HTML>
__END_OF_HTML__
}
