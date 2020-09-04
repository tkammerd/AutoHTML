#!/usr/local/bin/perl

############################################################
#                       UPDATE_AUTOHTML.CGI
#
# This script was written by Troy Kammerdiener
# Date Created: 8-29-98
#
#   You may copy this under the terms of the GNU General Public
#   License or the Artistic License which is distributed with
#   copies of Perl v5.x for UNIX
#
# Purpose: To maintain a meta-html file which includes variable text
# embedded between specially formatted comments of the form:
# <!-- ##MERGEFIELD## varname --> value <!-- ##/MERGEFIELD## -->
# (Note that each delimiting comment must appear on a single line,
# although value may span many lines if needed.)
#
# This script creates an input form that uses the variable/value pairs
# encoded in the HTML file, and which when submitted uses those same
# variables with their new values to call the associated script,
# CHANGE_AUTOHTML.CGI, which re-creates the original meta-html file,
# using the new values.
#
# Some parts of the meta-html file may also be enclosed within
# <!-- ##SECTION## secname --> and <!-- ##/SECTION## --> comment
# tags.  When a simple input form is created, any sections will be
# displayed, along with a choice to keep it, remove it, or to add 
# copies of it, and an input field will also be provided for the
# number of copies to add.  Any copies of the section will have the
# same section name, but with a unique number appended to it. That
# same number will be appended to the varname of any mergefields
# contained within that section.  Adding additional sections would
# thus be a two stage process of running this script once to create
# the additional sections, and then running it again to change the
# values of any mergefield variables in the new sections.
#
# (Not implemented) Finally, a META tag with NAME of "AutoHTMLTitle"
# may be included in the HEAD section.  Its VALUE will contain a 
# string which may include mergefields, and is used to construct a
# new title by CHANGE_AUTOHTML.CGI. 
#
# Main Procedures:
#   &ReadAutoHTML =
#     Creates variables and initializes them from variable/value pairs
#     read from the AutoHTML source file
#   &CreateTop =
#     Creates the section of the output HTML file which precedes the
#     FORM section.  Often customized.
#   &CreateForm =
#     Creates the HTML FORM section from the variable/value pairs read by
#     ReadAutoHTML.  Usually custom written to conform to the AutoHTML
#     source file, but may simply call CreateSimpleForm.
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
#   An HTML page containing a FORM which invokes CHANGE_AUTOHTML.CGI.
#
############################################################

# Set up global variables common to all autoHTML scripts
require "./setup_autoHTML.cgi";

# Set up global variables
%var_val = ();
@ordering = ();
$tot_merges = 0;
$SourceFile = "";
$SourcePath = "";
$LeftAngleESC = "~LE~";    # Left Angle escape for hidden variables
$RightAngleESC = "~RE~";   # Right Angle escape for hidden variables
$DblQuoteESC = "~QE~";     # Double Quote escape for hidden variables
@SectionVals = ();
@SectionNames = ();
@SectionMerges = ();
$TotSections = 0;
$mergefield_rows = 2;
$mergefield_cols = 40;
$LeftDelim = "<!-- ##MERGEFIELD##";
$LeftDelimLen = length($LeftDelim);
$RightDelim = "<!-- ##/MERGEFIELD## -->";
$RightDelimLen = length($RightDelim);
$max_allowed_iters = 200;

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
#     Global associative array %var_val will hold the
#       variable/value pairs extracted from the autoHTML 
#       source file as a side effect.
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
  local($varname_pos);
  local($varname_len);
  local($varname);
  local($merge_num) = 0;
  local($value_pos);
  local($value_len);
  local($value);
  local($merge_endpos) = 0;

  # Open $AutoHTMLFile for input
  open(SOURCEFILE, $AutoHTMLFile) ||
    die "Unable to open $AutoHTMLFile";

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

      # Add remainder of value to $value
      $value = $value . substr($line_buf, $value_pos, $value_len);
      $merge_endpos = $value_pos + $value_len + $RightDelimLen;

      # Record variable/value pair
      @ordering[$merge_num] = $varname;
      if ($debug_on)
      {
        print DEBUGFILE "Recording ", $varname, " = \"", $value, "\"\n";
      }
      $merge_num++;
      $var_val{$varname} = $value;
    }
  }
  $tot_merges = $merge_num;

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
    <TITLE>Form to update autoHTML file $SourcePath</TITLE>
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
#   Parameters:
#
#   Output:
#
############################################################

sub CreateSimpleForm
{
  # Set up other local variables
  local($varname);
  local($value);
  local($cur_merge);
  local($cur_sect);
  local($count_iters);

print <<__END_OF_HTML__;
    <FORM ACTION="$autoHTML_base_URL/change_autoHTML.cgi" METHOD="post"> 
      <INPUT TYPE="hidden" NAME="sourcefile" VALUE="$SourceFile">
      <INPUT TYPE="hidden" NAME="sourcebase" VALUE="$SourceBase">
__END_OF_HTML__

  print "      <TABLE BORDER=1>\n";
  $cur_sect = 0;
  $cur_merge = 0;
  $count_iters = 0;
  while ($cur_merge < $tot_merges)
  {
    $count_iters++;
    if ($count_iters == $max_allowed_iters)
    {
print <<__END_OF_HTML__;
        </TABLE>
      <H1>Too many iterations on output</H1>
      <INPUT TYPE="submit" VALUE="Generate new page">
      <INPUT TYPE="reset" VALUE="Start over"><BR>
    </FORM>
  </BODY>
</HTML>
__END_OF_HTML__
      die "Too many iterations on output";
    }
    $varname = $ordering[$cur_merge];
    if ($cur_sect < $TotSections && !$SectionMerges[$cur_sect]) # Section with no mergefields
    {
      # print section
print <<__END_OF_HTML__;
        <TR>
          <TD WIDTH="10%" BGCOLOR="orange">
            Section not changeable here
          </TD>
          <TD VALIGN="top">
            <TABLE BORDER=1 WIDTH="100%">
              <TR><TD BGCOLOR="lightblue" COLSPAN=2>Section name: <B>$SectionNames[$cur_sect]</B></TD></TR>
              <TR><TD COLSPAN=2>$SectionVals[$cur_sect]</TD></TR>
__END_OF_HTML__
      $cur_sect++;
    }
    elsif (($cur_sect < $TotSections) 
      && (index($SectionMerges[$cur_sect] . ",", $varname . ",") > -1))
    {
      # print section
print <<__END_OF_HTML__;
        <TR>
          <TD WIDTH="10%" BGCOLOR="orange">
            Section not changeable here
          </TD>
          <TD VALIGN="top">
            <TABLE BORDER=1 WIDTH="100%">
              <TR><TD BGCOLOR="lightblue" COLSPAN=2>Section name: <B>$SectionNames[$cur_sect]</B></TD></TR>
              <TR><TD COLSPAN=2>$SectionVals[$cur_sect]</TD></TR>
__END_OF_HTML__
      # print mergefields in the section, and add to $cur_merge
      @mergefields = split(/,/, $SectionMerges[$cur_sect]);
      $num_mergefields = 0;
      foreach $varname (@mergefields)
      {
        $fieldval = $var_val{$varname};
        print "              <TR>\n";
        print "                <TD WIDTH=\"20%\" BGCOLOR=\"lightblue\">Mergefield name:<BR><B>$varname</B></TD>\n";
        print "                <TD><TABLE><TR><TD><TEXTAREA NAME=\"$varname\" ROWS=$mergefield_rows COLS=$mergefield_cols>$fieldval</TEXTAREA></TD></TR></TABLE></TD>\n";
        print "              </TR>\n";
        $num_mergefields++;
      }
      if ($num_mergefields == 0)
      {
        print "              <TR>\n";
        print "                <TD WIDTH=\"20%\" BGCOLOR=\"lightblue\"><B>No Mergefields Present</B></TD>\n";
        print "                <TD>&nbsp;</TD>\n";
        print "              </TR>\n";
      }
      $cur_merge = $cur_merge + $num_mergefields;
      $cur_sect++;
    }
    else # must be an orphan mergefield
    {
      # print non-section
print <<__END_OF_HTML__;
        <TR>
          <TD WIDTH="10%" BGCOLOR="orange">
            Not a Section
          </TD>
          <TD VALIGN="top">
            <TABLE BORDER=1 WIDTH="100%">
__END_OF_HTML__
      # print mergefield and inc $cur_merge
      $fieldval = $var_val{$varname};
      print "              <TR>\n";
      print "                <TD WIDTH=\"20%\" BGCOLOR=\"lightblue\">Mergefield name:<BR><B>$varname</B></TD>\n";
      print "                <TD><TABLE><TR><TD><TEXTAREA NAME=\"$varname\" ROWS=$mergefield_rows COLS=$mergefield_cols>$fieldval</TEXTAREA></TD></TR></TABLE></TD>\n";
      print "              </TR>\n";
      $cur_merge++
    }
print <<__END_OF_HTML__;             
            </TABLE>
          </TD>
        </TR>
__END_OF_HTML__
  }
  print "      </TABLE>\n";

print <<__END_OF_HTML__;
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
