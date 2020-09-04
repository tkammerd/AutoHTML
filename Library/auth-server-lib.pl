############################################################
#                       AUTH-SERVER-LIB.PL
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
# Purpose: This script would contain the routines particular
# to your server if you were using server based authentication
# 
# We put this file out here as an example stub file, it really
# does not do anything valid since if you are using this
# library for an IntraNet there are a variety of business rules
# and databases you may want to integrate this with.
#
# Main Procedures:
#   One procedure to process server authentication
#   $username has been previously set to REMOTE_USER 
#   in auth-extra-lib.pl.
#
############################################################

# Note: $username is already set previously.
#
#
# Here you would call a routine to fill in the other
# variables, presumably from a previous database such
# as an address book in Sybase or Oracle.
# 
# Since this is a generic script, I am simply providing
# some base logic to show that it works.
#
$firstname = "Gunther";
$lastname = "Birznieks";
$email = "gunther\@gunther.com";
$group = "$auth_default_group";

$session = 
	&MakeSessionFile( ($username, $group, $firstname, 
	$lastname,$email));

1;

