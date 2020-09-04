
############################################################
#                       AUTH-LIB.PL
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
# Purpose: Provides a set of library routines to provide
# a standard authentication front_end to CGI Programs
#
# Main Procedures:
#   GetSessionInfo - Returns the session information or prompts
#   the user to log in.
#
# Special Notes: This script relies on mail-lib.pl for sending
# email (if the feature is activated)
#
# It also uses CRYPT inside the EncrytWrap routine.  If your 
# OS does not support Crypt, you can write your own inside
# EncryptWrap.  The routine resides in auth-extra-lib.pl file.
#
# The script is written to be compact for returning session
# information since that is what the script does 99% of the time
# When the script needs to do more, it does a require on
# a huge auth-extra-lib.pl file that has all sorts of routines
# and options.
#
# The environmental variables that the authentication library
# expects to set are the following:
#
#  These variables should be set in the define variables
#  part of whatever program you are calling the authentication
#  library routines from.
#
#  Path To The Where Auth Library Files are stored.
#$auth_lib = ".";
#  Are we doing server based authentication?
#$auth_server = 			"off";
#  Are we doing CGI based authentication? IE are 
#  we logging in eusing a CGI form
#$auth_cgi = 			"on";
#
#  NOTE: If neither CGI or Server auth is ON then
#  the program will return a session id with blank
#  information for the fields that the application
#  is looking for.
#
#  Where is the user file stored?
#$auth_user_file = 		"user.dat";
#  If alt_user_file is defined, when a user
#  registers, their information will be stored
#  in the alternate user file until the system
#  admin (you) copies them over.  Normally,
#  you will just let them register into the
#  main file.
#$auth_alt_user_file =		"altuser.dat";
#
#  Auth_allow_register turns on the ability of a
#  user to register to the system
#$auth_allow_register = "on";
#
#  Auth_allow_search turns on the ability of a
#  user to search through the userlist for their
#  username in case they forgot it.
#$auth_allow_search = "on";
#
#  Default group is the default name of the group
#  variable in the user file when the user gets added.
#  Groups are useful for controlling rights in a program
#  to certain things like being able to post events.
#$auth_default_group = 		"normal";
#
#  If auth_check_duplicates is on, then the program
#  will check for duplicate usernames when a person
#  tries to register for the system.  Duplicates are
#  checked in both the user file and the ALT user file
#  described above.
#$auth_check_duplicates = "on";
#
#  If auth_use_cleartext is on, then the passwords
#  will not be encrypted in the userfile.  This 
#  makes it easier for an admin to maintain their
#  own userfile at the risk of security.
# 
#$auth_use_cleartext = "off";
# 
#
#  If auth_generate_password is on, then the program
#  will generate a password for the user 
#
#$auth_generate_password = "on";
#
#  If add_register is on, then the program will
#  save the users registration to the user file or
#  the alternative user file, depending on the above
#  definitions.
#$auth_add_register = 		"on";
#  If email-register is on, then the program will
#  email the registration to the sys admin (you)
#  depending on the email definitions below.
#$auth_email_register = 		"on";
#  Address to send from.  Must be a valid address on the
#  machine the web server is on.
#$auth_admin_from_address = 	"gunther\@foobar.com";
#  Address to registration information to.
#$auth_admin_email_address = 	"gunther\@foobar.com";
#  Session files should be kept around until the user
#  will not need to get back in with the same id.  The
#  number is measured in days and keeping the files around
#  for 2 days is more than enough.
#$auth_session_length = 2;
#  session_dir is where the Sessions are stored.
#$auth_session_dir = "./Sessions";
#  register_message is the message that the user sees after
#  they have successfully registered onto the system.  You
#  will want to change this if the user information is not
#  stored in the main user data file right away.
#$auth_register_message =
#	"Thanks, you may now logon with your new username
#	and password.";
#
#  Auth_password_message is a message sent to users 
#  when they apply and their password needs to be sent to
#  them.  The final part of the message is the password
#  itself which gets appended to the message by the program
#  when the user registers.
#$auth_password_message =
#  "Thanks for applying to our site, your password is";
#
#  Auth_extra_fields is an array that contains the name
#  of any fields that are kept about the user other than
#  username, password, and group.
# 
#  Note that ALL the extra fields must have the word
#  "auth" in them.
#
#  Note also that there has to be an auth_email for the 
#  search function to work in the program.
# 
#@auth_extra_fields = ("auth_first_name", "auth_last_name",
#                      "auth_email");
#
#  Auth_extra_desc are the descriptive field names that
#  correspond to the same elements in auth_extra_fields.
#
#@auth_extra_desc = ("First Name", "Last Name", "Email");
#
#  Auth_logon_title is the title in the HTML for the initial
#  logon screen. You might want to change this since people
#  may bookmark this screen.
#
#$auth_logon_title = "Submit Logon";
#
#  Auth_logon_header is the header in the HTML for the
#  initial logon screen.
#
#$auth_logon_header = "Enter your logon information";
#
#  NOTE: $auth_logon_title and $auth_logon_header will
#  default to generic messages if they are not defined by
#  you.
############################################################

############################################################
#
# subroutine: GetSessionInfo 
#   Usage:
#   ($session, $username, $group, @extra_fields,
#    = &GetSessionInfo($session, "script name",
#    *in);
#
#   Parameters:
#     $session = session id.  Null if it is not defined yet
#     $main_script = the script you are calling
#                    &GetSessionInfo From
#     *in = A reference to the form data that was read
#           in with &ReadParse.
#
#   Output:
#     $session = session id
#     $username = user name
#     $group = group information
#     @extra_fields = an array of more fields usually 
#     consisting of the following:
#       $first_name = first name
#       $last_name = last name
#       $email = email address
############################################################

sub GetSessionInfo {
local($session, $main_script, *in) = @_;
local($session_file, @fields);
local(@fields);

# If the session is not defined, we load in all
# the routines and then call the VerifyUser routine
# which will log the person into the system
#
# If the session id IS defined, then we simply
# read the session file and return the information
# back to the program related to the session.
#
if ($session eq "") {
    require "$auth_lib/auth-extra-lib.pl";
    @fields = &VerifyUser($main_script, *in);
	} # End of if
else {
    $session_file = "$session.dat";
    open (SESSIONFILE, "$auth_session_dir/$session_file") || 
	    (require "$auth_lib/auth-lib-fail-html.pl" && exit);

	while (<SESSIONFILE>) {
            chop;
	    @fields = split(/\|/);
	    }
    close (SESSIONFILE);

    unshift(@fields, $session);
	} # End of else

# return the array of fields;

@fields;

} # End of GetSessionInfo

1;









