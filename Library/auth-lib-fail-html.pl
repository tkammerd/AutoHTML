############################################################
#                       AUTH-LIB-FAIL-HTML.PL
#
# This script was written by Selena Sol & Gunther Birznieks. 
# Date Created: 5-10-96
# Date Last Modified: 5-14-96
#
#   You may copy this under the terms of the GNU General Public
#   License or the Artistic License which is distributed with
#   copies of Perl v5.x for UNIX.
# 
# Selena Sol may be contacted at selena@eff.org
#
# Purpose: This script contains all the cosmetic HTML output
# routines related to a general program failure in the
# authentication scripts
#
# Main Procedures:
#   Only one procedure -- an output of HTML complaining of
#   a problem in accessing information or files.
#
#
############################################################

print <<__FAILHTML__;
<HTML><HEAD>
<TITLE>Error Occured</TITLE>
</HEAD>
<BODY>
<CENTER>
<BLOCKQUOTE>
Sorry, there appears to be a problem accessing a session file.
</BLOCKQUOTE>

</CENTER>
</BODY></HTML>


__FAILHTML__

1;

