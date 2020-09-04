#!/usr/local/bin/perl
############################################################
#                       CHGSEC_AUTOHTML.CGI
#
# This script was written by Troy Kammerdiener
# Date Created: 9-4-98
#
#   You may copy this under the terms of the GNU General Public
#   License or the Artistic License which is distributed with
#   copies of Perl v5.x for UNIX
#
# Purpose: To re-create a meta-html file which includes text
# embedded between specially formatted comments of the form:
# <!-- ##SECTION## secname --> section $RightDelim
# (Note that each delimiting comment must appear on a single line,
# although sectvalue may span many lines if needed.)
#
# This script is passed a list of section names and actions to take
# on each section.  The actions may be:
#   C<number>: Actually two values for a section name: the letter C
#              followed by a null character followed by an integer
#              number, indicating the number of additional copies to
#              make and place after the indicated section in the 
#              autoHTML source file.
#   "D":       Delete the indicated section from the autoHTML source
#              file.
#   "I":       Comment out (Ignore) the contents of the section.  
#              This will make the section not appear when the autoHTML
#              source is displayed in a browser, but it will still be
#              available for future inclusion.
#   "R":       Uncomment (Restore) a section that has been commented out.
#   "N":       No change should be made to this section.
# Any copies made of the section will have the same section name 
# (without any number), but with a unique number appended to it.
# That same number will be appended to the varnames of any merge-
# fields contained within that section.  It will then run
# UPDATE_AUTOHTML.CGI to change the values of any mergefield variables
# in the new sections.
#
# Main Procedures:
#   &WriteAutoHTML =
#     Creates a new version of the autoHTML file by removing or duplicating
#     sections identified by the section names passed in $in
#
# Inputs:
#   Form Variables: 
#     source = path to AutoHTML source file
#     other dynamically created variables, corresponding to section names
#     in $source, whose values indicate what action to take with each section
#
# Outputs:
#   A new version of $source.
#   A call to UPDATE_AUTOHTML.CGI, passing the path of the sourcefile to be
#   used as a command line parameter.
#
############################################################

# Set up global variables common to all autoHTML scripts
require "./setup_autoHTML.cgi";

# Set up debugging without server support
# $ENV{"QUERY_STRING"} = "source=AutoHTMLTestfile.html&notice=N&notice=2&notice_1=N&notice_1=0&assign=N&assign=1&assign_1=N&assign_1=1&assign_2=N&assign_2=1&assign_3=N&assign_3=1&study_aid=C&study_aid=2";

# Set up global variables
$SourceFile = "";
$SourcePath = "";
$DestPath = "";
$DestURL = "";
$LeftDelim = "<!-- ##SECTION##";
$LeftDelimLen = length($LeftDelim);
$RightDelim = "<!-- ##/SECTION## -->";
$RightDelimLen = length($RightDelim);
%MaxSectNums = ();
$LeftAnglePH = "~LB~";     # Left Angle placeholder for ignore command
$RightAnglePH = "~RB~";    # Right Angle placeholder for ignore command
$LeftAngleESC = "~LE~";    # Left Angle escape for hidden variables
$RightAngleESC = "~RE~";   # Right Angle escape for hidden variables
$DblQuoteESC = "~QE~";     # Double Quote escape for hidden variables
@SectionVals = ();
@SectionNames = ();
@SectionMerges = ();
$TotSections = 0;

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

&GetMaxSectNums($SourcePath);
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
#       version of the autoHTML file with sections uncommented,
#       commented out, copied, or left alone for each section
#       name drawn from the corresponding members of %in.
#
############################################################

sub WriteAutoHTML
{
  # Set up named parameters
  local($AutoHTMLSource, $AutoHTMLDest) = @_;

  # Set up other local variables
# DOS version:
#   local($TempFile) = "./TempAutoHTML";
# Unix version:
    local($TempFile) = "./TempAutoHTML" . `date '+%H%M%S%m%d%y'`;

  chomp($TempFile);
  local($EOF_reached) = $false;
  local($line_buf);
  local($cur_line) = 0;
  local($sectname_pos);
  local($sectname_len);
  local($sectname);
  local($sectval_pos);
  local($sectval_len);
  local($sect_endpos) = 0;

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
      (($leftdelim_pos = index($line_buf, $LeftDelim, $sect_endpos)) == -1)) 
    {
      if ($debug2_on)
      {
        print DEBUGFILE "Searched for \"$LeftDelim\" from pos $sect_endpos with result of ";
        print DEBUGFILE index($line_buf, $LeftDelim, $sect_endpos);
        print DEBUGFILE " giving \$leftdelim_pos of $leftdelim_pos\n"
      }

      # Print remainder of line without change
      print OUTPUTFILE substr($line_buf, $sect_endpos);

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
      print DEBUGFILE index($line_buf, $LeftDelim, $sect_endpos);
      print DEBUGFILE " giving \$leftdelim_pos of $leftdelim_pos\n"
    }

    if (!$EOF_reached)
    {
      # Adjust to first character after delimiter
      $sectname_pos = $leftdelim_pos + $LeftDelimLen;

      # Then skip over spaces
      while (substr($line_buf, $sectname_pos, 1) eq " ")
      {
        $sectname_pos++;
      }
      if ($debug2_on)
      {
        print DEBUGFILE "Sectname found at pos $sectname_pos\n";
        print DEBUGFILE "Sample at pos $sectname_pos: \"", 
          substr($line_buf, $sectname_pos, 20), "\"\n";
      }

      # Find length of section name and extract section name
      $sectname_len = index($line_buf, " ", $sectname_pos) - $sectname_pos;
      if ($sectname_len == -1 - $sectname_pos)
      {
        die "Bad ##SECTION## at line number $cur_line in $AutoHTMLSource";
      }
      $sectname = substr($line_buf, $sectname_pos, $sectname_len);
      if ($debug2_on)
      {
        print DEBUGFILE "sectname is \"$sectname\" of length $sectname_len\n";
      }
      # Skip to the end of the comment
      $sectval_pos = index($line_buf, "-->", $sectname_pos + $sectname_len) + 3;
      if ($sectval_pos == -1 + 3)
      {
        die "Bad ##SECTION## at line number $cur_line in $AutoHTMLSource";
      }
      if ($debug2_on)
      {
        print DEBUGFILE "sectvalue starts at pos $sectval_pos of line $cur_line\n";
        print DEBUGFILE "Sample at pos $sectval_pos: \"", 
          substr($line_buf, $sectval_pos, 20), "\"\n";
      }

      # Extract section root and section number from $sectname
      if ($sectname =~ /(.*)_(\d+)$/)
      {
        $sectroot = $1;
        $sectnum = $2;
      }
      else
      {
        $sectroot = $sectname;
        $sectnum = 0;
      }

      # Print out unprinted portion of line up to $leftdelim_pos
      print OUTPUTFILE substr($line_buf, $sect_endpos, $leftdelim_pos - $sect_endpos);

      # Extract original entire beginning section tag
      $sect_begintag = substr($line_buf, $leftdelim_pos, $sectval_pos - $leftdelim_pos);

      # Extract section value
      $sectvalue = ""; #Clear out $sectvalue
      $sectval_len = index($line_buf, $RightDelim, $sectval_pos)
        - $sectval_pos;
      if ($debug2_on)
      {
        print DEBUGFILE "Searched for \"$RightDelim\" with result of ";
        print DEBUGFILE index($line_buf, $RightDelim, $sectval_pos);
        print DEBUGFILE " giving \$sectval_len of $sectval_len\n"
      }
      while ($sectval_len == -1 - $sectval_pos) # sectvalue does not end on this line
      {
        # Concatenate section value from current line to sectvalue
        $sectvalue = $sectvalue . substr($line_buf, $sectval_pos, 
          length($line_buf) - $sectval_pos);

        # Read in next line
        if (!($line_buf = <SOURCEFILE>))
        {
          die "Multiline sectvalue not terminated -- EOF reached prematurely";
        }
        $cur_line++; # Count current line of source file being processed
        if ($debug_on)
        {
          print DEBUGFILE $cur_line, ": ", $line_buf;
        }
        $sect_endpos = 0;
        $sectval_pos = 0;
        if ($debug2_on)
        {
          print DEBUGFILE "sectvalue continues at pos $sectval_pos of line $cur_line\n";
          print DEBUGFILE "Sample at pos $sectval_pos: \"", 
            substr($line_buf, $sectval_pos, 20), "\"\n";
        }
        $sectval_len = index($line_buf, $RightDelim, $sectval_pos)
          - $sectval_pos;
        if ($debug2_on)
        {
          print DEBUGFILE "Searched for \"$RightDelim\" with result of ";
          print DEBUGFILE index($line_buf, $RightDelim, $sectval_pos);
          print DEBUGFILE " giving \$sectval_len of $sectval_len\n"
        }
      }
      # Concatenate remaining section value onto sectvalue
      $sectvalue = $sectvalue . substr($line_buf, $sectval_pos, $sectval_len);

      # Set end postion of old sectvalue in $line_buf
      $sect_endpos = $sectval_pos + $sectval_len + $RightDelimLen;

      # At this point, the input file is finished reading all info for the current
      # section, and is ready to start on the next one, so we need to process the
      # command for the current section.

      ($command, $desired_copies) = split(/\0/, $in{$sectname});

      if ($command eq "C") # Copy
      {
        # Finish the original section:
          # Print out unprinted portion of line up to $sectval_pos
          print OUTPUTFILE $sect_begintag;
          # Print section value
          print OUTPUTFILE $sectvalue;
          # Print out right-hand mergefield delimiter
          print OUTPUTFILE $RightDelim;

          # Record section values, names, and mergefields in arrays
          $SectionVals[$TotSections] = $sectvalue;
          $SectionNames[$TotSections] = $sectname;
          @mergefields = split(m\<!-- ##/MERGEFIELD## -->\, $sectvalue);
          $num_mergefields = 0;
          $SectionMerges[$TotSections] = "";
          foreach $curfield (@mergefields)
          {
            ($junk, $curfield) = split(/##MERGEFIELD##\s*/, $curfield);
            if ($curfield)
              {
                ($varname, $fieldval) = split(/\s*-->/, $curfield);
                if ($num_mergefields > 0)
                {
                  $SectionMerges[$TotSections] =
                    $SectionMerges[$TotSections] . ",";
                }
                $SectionMerges[$TotSections] =
                  $SectionMerges[$TotSections] . $varname;
                $num_mergefields++;
              }
          }
          $OriginalMerges = $SectionMerges[$TotSections];
          $TotSections++;

        for ($copynum = 0; $copynum < $desired_copies; $copynum++)
        # Then, for each desired copy:
        {
          # Print out left delimiter
          print OUTPUTFILE $LeftDelim;
          # Find next available subscript for section name, and print it
          # out (concatenated after an underscore onto the section name)
          $MaxSectNums{$sectroot} = $MaxSectNums{$sectroot} + 1;
          print OUTPUTFILE " $sectroot\_$MaxSectNums{$sectroot} -->";

          $SectionVals[$TotSections] = $sectvalue;
          $SectionMerges[$TotSections] = $OriginalMerges;
          foreach $curfield (split(/,/, $OriginalMerges))
          {
            # Extract root and mergefield number from $curfield
            if ($curfield =~ /(.*)_(\d+)$/)
            {
              $curroot = $1;
            }
            else
            {
              $curroot = $curfield;
            }
            $newfield = "$curroot\_$MaxSectNums{$sectroot}";
            $SectionVals[$TotSections] =~ s/ $curfield / $newfield /;
            $SectionMerges[$TotSections] =~ s/$curfield/$newfield/;
          }
          $SectionNames[$TotSections] = "$sectroot\_$MaxSectNums{$sectroot}";
          $TotSections++;

          # Print section value
          print OUTPUTFILE $SectionVals[$TotSections - 1];
          # Print "$RightDelim
          print OUTPUTFILE $RightDelim;
        }
      }
      elsif ($command eq "I") # Ignore (Comment Out)
      {
        # Print out unprinted portion of line up to $sectval_pos
        print OUTPUTFILE $sect_begintag;
        # Replace any angle brackets with double brace placeholders, to
        # prevent interference with the comment delimiters that will be added.
        $sectvalue =~ s/</$LeftAnglePH/g;
        $sectvalue =~ s/>/$RightAnglePH/g;
        # Print section value within comment delimiters
        print OUTPUTFILE "<!-- $sectvalue -->";
        # Print $RightDelim
        print OUTPUTFILE $RightDelim;

        # Record section values, names, and mergefields in arrays
        $SectionVals[$TotSections] = "<!-- $sectvalue -->";
        $SectionNames[$TotSections] = $sectname;
        @mergefields = split(m\$LeftAnglePH!-- ##/MERGEFIELD## --$RightAnglePH\, $sectvalue);
        $num_mergefields = 0;
        $SectionMerges[$TotSections] = "";
        foreach $curfield (@mergefields)
        {
          ($junk, $curfield) = split(/##MERGEFIELD##\s*/, $curfield);
          if ($curfield)
            {
              ($varname, $fieldval) = split(/\s*--$RightAnglePH/, $curfield);
              if ($num_mergefields > 0)
              {
                $SectionMerges[$TotSections] =
                  $SectionMerges[$TotSections] . ",";
              }
              $SectionMerges[$TotSections] =
                $SectionMerges[$TotSections] . $varname;
              $num_mergefields++;
            }
        }
        $OriginalMerges = $SectionMerges[$TotSections];
        $TotSections++;
      }
      elsif ($command eq "R") # Restore (Uncomment)
      {
        # Print out unprinted portion of line up to $sectval_pos
        print OUTPUTFILE $sect_begintag;
        # Remove comment delimiters
        $sectvalue =~ s/<!--//g;
        $sectvalue =~ s/-->//g;
        # Replace any angle bracket placeholders with angle brackets
        $sectvalue =~ s/$LeftAnglePH/</g;
        $sectvalue =~ s/$RightAnglePH/>/g;
        # Print section value
        print OUTPUTFILE $sectvalue;
        # Print out right-hand mergefield delimiter
        print OUTPUTFILE $RightDelim;

        # Record section values, names, and mergefields in arrays
        $SectionVals[$TotSections] = $sectvalue;
        $SectionNames[$TotSections] = $sectname;
        @mergefields = split(m\<!-- ##/MERGEFIELD## -->\, $sectvalue);
        $num_mergefields = 0;
        $SectionMerges[$TotSections] = "";
        foreach $curfield (@mergefields)
        {
          ($junk, $curfield) = split(/##MERGEFIELD##\s*/, $curfield);
          if ($curfield)
            {
              ($varname, $fieldval) = split(/\s*-->/, $curfield);
              if ($num_mergefields > 0)
              {
                $SectionMerges[$TotSections] =
                  $SectionMerges[$TotSections] . ",";
              }
              $SectionMerges[$TotSections] =
                $SectionMerges[$TotSections] . $varname;
              $num_mergefields++;
            }
        }
        $OriginalMerges = $SectionMerges[$TotSections];
        $TotSections++;
      }
      elsif ($command eq "N") # Do Nothing
      {
        # Print out unprinted portion of line up to $sectval_pos
        print OUTPUTFILE $sect_begintag;
        # Print section value
        print OUTPUTFILE $sectvalue;
        # Print out right-hand mergefield delimiter
        print OUTPUTFILE $RightDelim;

        # Record section values, names, and mergefields in arrays
        $SectionVals[$TotSections] = $sectvalue;
        $SectionNames[$TotSections] = $sectname;
        @mergefields = split(m\<!-- ##/MERGEFIELD## -->\, $sectvalue);
        $num_mergefields = 0;
        $SectionMerges[$TotSections] = "";
        foreach $curfield (@mergefields)
        {
          ($junk, $curfield) = split(/##MERGEFIELD##\s*/, $curfield);
          if ($curfield)
            {
              ($varname, $fieldval) = split(/\s*-->/, $curfield);
              if ($num_mergefields > 0)
              {
                $SectionMerges[$TotSections] =
                  $SectionMerges[$TotSections] . ",";
              }
              $SectionMerges[$TotSections] =
                $SectionMerges[$TotSections] . $varname;
              $num_mergefields++;
            }
        }
        $OriginalMerges = $SectionMerges[$TotSections];
        $TotSections++;
      }
      elsif ($command eq "D") # Delete
      {
        # Portion up to beginning of section tag has already been printed,
        # so do nothing with the left delimiter, section value, or right 
        # delimiter -- just skip them.
      }
      else
      {
        die "Bad command \"$command\" given for section $sectname";
      }

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
# subroutine: GetMaxSectNums
#   Usage: &GetMaxSectNums($AutoHTMLSource);
#
#   Parameters:
#     $AutoHTMLSource = path to autoHTML source file
#
#   Output:
#     An associative array called MaxSectNums whose keys are
#       section name roots, and whose values are the current
#       maximum number appended to each root in AutoHTMLSource.
#       Section name roots are separated from their appended
#       numbers by an underscore ('_').  A value of zero 
#       actually indicates a root with no appended number.
#
############################################################

sub GetMaxSectNums
{
  # Set up named parameters
  local($AutoHTMLSource) = @_;

  # Set up other local variables
  local($EOF_reached) = $false;
  local($line_buf);
  local($cur_line) = 0;
  local($sectname_pos);
  local($sectname_len);
  local($sectname);
  local($sectval_pos);
  local($sectval_len);
  local($sect_endpos) = 0;

  # Open $AutoHTMLSource for input
  if (!open(SOURCEFILE, $AutoHTMLSource))
  {
    if ($debug_on)
    {
      print DEBUGFILE "Unable to open $AutoHTMLSource\n";
    }
    die "Unable to open $AutoHTMLSource";
  }

  while (!$EOF_reached)
  {
    while (!$EOF_reached &&
      (($sectname_pos = 
      index($line_buf, $LeftDelim, $sect_endpos)) == -1)) 
    {
      if ($debug2_on)
      {
        print DEBUGFILE "Searched for \"$LeftDelim\" from pos $sect_endpos with result of ";
        print DEBUGFILE index($line_buf, $LeftDelim, $sect_endpos);
        print DEBUGFILE " giving \$sectname_pos of $sectname_pos\n"
      }

      # Skip remainder of line

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

    # Either a section tag has now been found, or we've reached the
    # end of the source file.

    if ($debug2_on && !$EOF_reached)
    {
      print DEBUGFILE "Searched for \"$LeftDelim\" from pos $sect_endpos with result of ";
      print DEBUGFILE index($line_buf, $LeftDelim, $sect_endpos);
      print DEBUGFILE " giving \$sectname_pos of $sectname_pos\n"
    }

    if (!$EOF_reached)
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
        print DEBUGFILE "Sectname found at pos $sectname_pos\n";
        print DEBUGFILE "Sample at pos $sectname_pos: \"", 
          substr($line_buf, $sectname_pos, 20), "\"\n";
      }

      # Find length of section name and extract section name
      $sectname_len = index($line_buf, " ", $sectname_pos) - $sectname_pos;
      if ($sectname_len == -1 - $sectname_pos)
      {
        die "Bad ##SECTION## at line number $cur_line in $AutoHTMLSource";
      }
      $sectname = substr($line_buf, $sectname_pos, $sectname_len);
      if ($debug2_on)
      {
        print DEBUGFILE "sectname is \"$sectname\" of length $sectname_len\n";
      }
      # Skip to the end of the comment
      $sectval_pos = index($line_buf, "-->", $sectname_pos + $sectname_len) + 3;
      if ($sectval_pos == -1 + 3)
      {
        die "Bad ##SECTION## at line number $cur_line in $AutoHTMLSource";
      }

      # Extract section root and section number from $sectname
      if ($sectname =~ /(.*)_(\d+)$/)
      {
        $sectroot = $1;
        $sectnum = $2;
      }
      else
      {
        $sectroot = $sectname;
        $sectnum = 0;
      }


      # Update the associative array with largest value
      if ($MaxSectNums{$sectroot}) #if this sectroot is in the associative array
      {
        if ($MaxSectNums{$sectroot} < $sectnum)
        {
          $MaxSectNums{$sectroot} = $sectnum;
        }
      }
      else
      {
        $MaxSectNums{$sectroot} = $sectnum;
      }

      if ($debug2_on)
      {
        print DEBUGFILE "sectvalue starts at pos $sectval_pos of line $cur_line\n";
        print DEBUGFILE "Sample at pos $sectval_pos: \"", 
          substr($line_buf, $sectval_pos, 20), "\"\n";
      }

      $sectvalue = ""; #Clear out $sectvalue
      $sectval_len = index($line_buf, $RightDelim, $sectval_pos)
        - $sectval_pos;
      if ($debug2_on)
      {
        print DEBUGFILE "Searched for \"$RightDelim\" with result of ";
        print DEBUGFILE index($line_buf, $RightDelim, $sectval_pos);
        print DEBUGFILE " giving \$sectval_len of $sectval_len\n"
      }
      while ($sectval_len == -1 - $sectval_pos) # sectvalue does not end on this line
      {
        # Read in next line
        if (!($line_buf = <SOURCEFILE>))
        {
          die "Multiline sectvalue not terminated -- EOF reached prematurely";
        }
        $cur_line++; # Count current line of source file being processed
        if ($debug_on)
        {
          print DEBUGFILE $cur_line, ": ", $line_buf;
        }
        $sect_endpos = 0;
        $sectval_pos = 0;
        if ($debug2_on)
        {
          print DEBUGFILE "sectvalue continues at pos $sectval_pos of line $cur_line\n";
          print DEBUGFILE "Sample at pos $sectval_pos: \"", 
            substr($line_buf, $sectval_pos, 20), "\"\n";
        }
        $sectval_len = index($line_buf, $RightDelim, $sectval_pos)
          - $sectval_pos;
        if ($debug2_on)
        {
          print DEBUGFILE "Searched for \"$RightDelim\" with result of ";
          print DEBUGFILE index($line_buf, $RightDelim, $sectval_pos);
          print DEBUGFILE " giving \$sectval_len of $sectval_len\n"
        }
      }

      # Set end postion of old sectvalue in $line_buf
      $sect_endpos = $sectval_pos + $sectval_len + $RightDelimLen;
    }
  }
  close(SOURCEFILE);
}

############################################################
#
# subroutine: UserResponse
#   Usage: &UserResponse($AutoHTMLDest);
#
#   Parameters:
#     $AutoHTMLDest = autoHTML destination file name
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
