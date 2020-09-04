
############################################################
#                       AUTH-EXTRA-LIB.PL
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
# Purpose: Provides a supporting set of routines to the
# AUTH-LIB.PL library program.
#
# Main Procedures:
#   VerifyUser - Logs the user into the system, and registers the
#                user
#
# Special Notes: This script relies on mail-lib.pl for sending
# email (if the feature is activated)
#
# It also uses CRYPT inside the EncrytWrap routine.  If your 
# OS does not support Crypt, you can write your own inside
# EncryptWrap.
#
############################################################

# We keep the cosmetic HTML output in a seperate file
# that can be more easily modified outside of the logic 
# related to the code
#
require "$auth_lib/auth-extra-html.pl";

############################################################
#
# subroutine: VerifyUser 
#   Usage:
#   ($session, $username, $group, @extra_fields
#    = &VerifyUser("script name", *in);
#
# This routine is the heart of everything, it processes
# all the login and registration information if a valid
# session id has not yet been returned.  Finally, it 
# it will return a session id if the user successfully logs
# on.
#
#  Parameters:
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

sub VerifyUser {
    local ($main_script, *in) = @_;
    local ($session, $group, $username, 
	   @extra_fields,
	   $bad_logon_message);

#
# If the previous logon had failed, bad_logon_message
# will contain a message to print out
#
    $bad_logon_message = "";

#
# we have 2 ways of authenticating a user: CGI and Server
# based.  CGI Authentication uses this programs routines
# and HTML forms to log the user into the system.  Server
# based authentication uses the WWW Server's built in
# authentication and relies on the Environmental variable
# for the REMOTE_USER name being set.
#
    if ($auth_cgi eq "on") {
#
# CGI Authentication determines what to do on the
# basis of what the previous screen was.  This is
# determined by which operational (OP) variable
# was submited (which button was pressed) on each
# screen.
#

	if ($in{'auth_logon_op'} ne "") {
	    ($bad_logon_message, $session, 
	     $username, $group, @extra_fields) = 
		 &CgiLogon($main_script, *in);
	} # End of auth_logon processing

	if ($in{'auth_search_op'} ne "" &&
	    $auth_allow_search eq "on") {
	    &SearchUsers($main_script, *in);
	    exit;
	}

	if ($in{'auth_search_screen_op'} ne "" &&
	    $auth_allow_search eq "on") {
	    &PrintSearchPage($main_script, *in);
	    exit;
	}

	if ($in{'auth_register_op'} ne "" &&
	    $auth_allow_register eq "on") {
	    &RegisterUser($main_script, *in);
	    exit;
	} # End of register screen processing

	if ($in{'auth_register_screen_op'} ne "" &&
	    $auth_allow_register eq "on") {
            &PrintRegisterPage;
	    exit;
	} # End of register screen

	if ($in{'auth_logon_screen_op'} ne "" || ($session eq "")) {
	    &PrintLogonPage($bad_logon_message, $main_script, *in);
	    exit;
	} # End of Logon Screen

    } # End of Auth_CGI

    if ($auth_server eq "on") {
	$username = $ENV{'REMOTE_USER'};
	if ($username ne "") {
# The following calls a site-specific server based
# authentication routine
	    require "auth-server-lib.pl";

	} # End of if username ne ""

    }  # End of if AUTH_SERVER is on

# 
# If neither CGI or Server auth is used, then
# we make a session anyway and fill it with blanks.
#
    if ($auth_server ne "on" && $auth_cgi ne "on") {
	@extra_fields = ();
	$username = "";
	$group = $auth_default_group;
	foreach (@auth_extra_fields) {
	    push (@extra_fields, "");
	}
	$session = &MakeSessionFile(@extra_fields);
    } # End of if neither server or cgi auth is on

($session, $username, $group, @extra_fields);

} # End of VerifyUser

############################################################
#
# subroutine: CGILogon
#   Usage:
#   ($bad_logon_message,
#    $session, $username, $group, @extra_fields) 
#    = &VerifyUser("script name", *in);
#
#  This routine attempts to log the user in.  If the 
#  logon fails, bad_logon_message contains the reason
#  why.  If it is successful, the rest of the returned
#  variables will have valid information.
#
#  Parameters:
#     $main_script = the script you are calling
#                    &GetSessionInfo From
#     *in = A reference to the form data that was read
#           in with &ReadParse.
#
#   Output:
#     $bad_logon_message = in case the logon fails
#     $session = session id
#     $username = user name
#     $group = group information
#     @extra_fields = an array of more fields usually 
#     consisting of the following:
#       $first_name = first name
#       $last_name = last name
#       $email = email address
############################################################

sub CgiLogon {
    local ($main_script, *in) = @_;
    local($password, $username, $group, @extra_fields);
    local($form_password, $session, @fields);
    local($bad_logon_message);
    local($user_matched);

    $bad_logon_message = "";
    $session = "";
    @fields = ();
    $form_password = $in{"auth_password"};
    open (USERFILE, "$auth_user_file") ||
      &CgiDie("Could Not Open User File\n");;

    $user_matched = 0;
    while (<USERFILE>) {
	chop($_);
	($password, $username, $group, $first_name,
	 $last_name, $email) = split(/\|/, $_);
	if ($in{'auth_user_name'} eq $username) {
	    $user_matched = 1;
	if (&AuthEncryptWrap ($form_password, $password) eq 
	    $password) {
	    @fields = split(/\|/, $_);
	    shift(@fields); # Get rid of password field
	    $session = &MakeSessionFile(@fields);
	} # End of if passwords match
	} # End of if username matches
    } # End of While
    close (USERFILE);

    if ($user_matched == 1 && $session eq "") {
	$bad_logon_message = 
	    "<p><strong>Sorry, Your password did not";
	$bad_logon_message .= 
	    " match the username.</strong><p>";
    }
    if ($user_matched == 0) {
	$bad_logon_message = 
	    "<p><strong>Sorry, Your username was not";
	$bad_logon_message .= 
	    " found.</strong><p>";

    }
($bad_logon_message, $session, @fields);

} # End of CgiLogon

############################################################
#
# subroutine: MakeSessionFile 
#   Usage:
#   $session = &MakeSessionFile(@fields);
#
#  This routine makes a session file on the basis of the
#  fields that make up a user such as first name and last
#  name.
#
#  Parameters:
#   @fields = a list of fields that make up the user
#
#   Output:
#     $session = session id
#
############################################################

sub MakeSessionFile
{
local(@fields) = @_;
local($session, $session_file);

&RemoveOldSessions; 

# Seed the random generator
srand($$|time);
$session = int(rand(60000));
# pack the time, process id, and random $session into a
# hex number which will make up the session id.
$session = unpack("H*", pack("Nnn", time, $$, $session));

$session_file = "$session.dat";

open (SESSIONFILE,">$auth_session_dir/$session_file")
    || &CgiDie("Could Not Create Session File\n");

print SESSIONFILE join ("\|", @fields);
print SESSIONFILE "\n";

close (SESSIONFILE);

$session;

} # End of MakeSessionFile

############################################################
#
# subroutine: RemoveOldSessions
#   Usage:
#     &RemoveOldSessions;
#
# This routine removes old session files based on the
# age determined by the defined variables.
#
#  Parameters:
#    None.
#
#  Output:
#     None.
############################################################

sub RemoveOldSessions
{
local(@files, $file);
# Open up the session directory.
opendir(SESSIONDIR, "$auth_session_dir") ||
	&CgiDie("Session Directory Would Not Open\n");
# read all entries except "." and ".."
@files = grep(!/^\.\.?$/,readdir(SESSIONDIR));
closedir(SESSIONDIR);

# Go through each file
foreach $file (@files)
        {
# If it is older than auth_session_length, delete it
        if (-M "$auth_session_dir/$file" > 
               $auth_session_length)
                {
                unlink("$auth_session_dir/$file");
                }

        }
} # End of RemoveOldSessions

############################################################
#
# subroutine: SearchUsers 
#   Usage:
#     &SearchUsers($main_script, *in);
#
#  This routine performs the search on the users in the user
#  file to allow a user to find his userid if it gets lost.
#  The search is performed on email address.
#
#  Parameters:
#     $main_script = the script you are calling
#                    &GetSessionInfo From
#     *in = A reference to the form data that was read
#           in with &ReadParse.
#
#   Output:
#     HTML printed out indicating failure or, if successful,
#     indicating the username(s) that matched the email
#     address.
############################################################

sub SearchUsers {
    local($main_script, *in) = @_;
    local($user_match);
    local($field_num, $username, @extra_fields);
    local($auth_email);
    local($user_list);

    local($form_tags);

    $form_tags = &PrintCurrentFormVars(*in);
    open (USERFILE, "$auth_user_file") ||
        &CgiDie("Could Not Open User File\n");

    $auth_email = $in{'auth_email'};
    $auth_email =~ tr/A-Z/a-z/;
    $auth_email =~ s/ //g;
    $user_match = "";

    $field_num = 0;
    foreach (@auth_extra_fields) {
	if ($_ eq "auth_email") {
	    last;
	}
	$field_num++;
    }

    while (<USERFILE>) {
	chop($_);
	tr/A-Z/a-z/;
	@extra_fields = split(/\|/, $_);
	$username = $extra_fields[1];
	# Get rid of the first three fields
	shift(@extra_fields);	
	shift(@extra_fields);
	shift(@extra_fields);
	if ($auth_email eq $extra_fields[$field_num]) {
	    $user_match .= $username . "|";
	} # End of email match
    } # End of While
    close (USERFILE);
    if ($user_match ne "") {
	$user_list = $user_match;
	$user_list =~ s/\|/<p>/g;
    } 

    if ($user_match eq "") {
	&HTMLPrintNoSearchResults($main_script, 
				  $form_tags);
    } else {
	&HTMLPrintSearchResults ($main_script,
				 $form_tags,
				 $user_list);

    } # End of no users matched

} # End of SearchUsers

############################################################
#
# subroutine: RegisterUser 
#   Usage:
#     &RegisterUser($main_script, *in);
#
# This routine registers the user and goes through
# many checks before it finally writes the user information
# down into a user data file or emails it to the system
# admin depending on how previous variables were set.
#
#  Parameters:
#     $main_script = the script you are calling
#                    &GetSessionInfo From
#     *in = A reference to the form data that was read
#           in with &ReadParse.
#
#   Output:
#     HTML indicating Registration success or failure
############################################################

sub RegisterUser {
    local($main_script, *in) = @_;
    local($x, @form_vars, $group, @f);
    local(@write_fields, $password);
    local($form_tags, $user_matched);
    local($userfile,$user_email,$real_password);
    local($random,$salt);
    $form_tags = &PrintCurrentFormVars(*in);
    $group = $auth_default_group;

# These variables must have stuff defined in 
# them and they can not contain PIPE symbols
# or they will be rejected.
@form_vars = ('auth_user_name', @auth_extra_fields);

    if ($auth_generate_password ne "on") {
	push(@form_vars, "auth_password1");
	push(@form_vars, "auth_password2");
    }

    foreach $x (@form_vars) {
	if ($in{"$x"} eq "" || $in{"$x"} =~ /\|/) {
	    &HTMLPrintRegisterNoValidValues($main_script, 
					    $form_tags);
	    exit;
	} # End of if
	if ($x eq "auth_email") {
	    $user_email = $in{"$x"};
	}
    } # End of Foreach form variable

# Passwords that are entered must match
if ($in{'auth_password1'} ne $in{'auth_password2'}) {
    &HTMLPrintRegisterNoPasswordMatch($main_script, 
				      $form_tags);
    exit;
}

#
# Check for duplicates with $auth_check_duplicates
# is turned on
# 

# Check for duplicates
    if ($auth_check_duplicates eq "on") {

	open (USERFILE, "$auth_user_file");
	$user_matched = 0;
	while (<USERFILE>) {
	    chop($_);
	    @f = split(/\|/, $_);
	    if ($f[1] eq $in{'auth_user_name'}) {
		$user_matched = 1;
		last;
	    }
	} # End of while userfile open
	close (USERFILE);

# Check for duplicates in the alternative
# file if it is defined.
	if ($auth_alt_user_file ne "") {
	    open (USERFILE, "$auth_alt_user_file");

	    while (<USERFILE>) {
		chop($_);
		@f = split(/\|/, $_);
		if ($f[1] eq $in{'auth_user_name'}) {
		    $user_matched = 1;
		    last;
		}
	    } # End of while userfile open
	    close (USERFILE);
	} # End of auth_alt_user_file

	if ($user_matched == 1) {
	    &HTMLPrintRegisterFoundDuplicate($main_script, 
				     $form_tags);
	    exit;
	} # End of user matched (found duplicate)
    } # End of if check duplicates on
#
# Generate the password if one is not
# entered.  Encrypt the password and make up
# the record that would be written to the user data
# file or sent in email to an administrator
#

# we seed the random generator for random stuff below
    srand(time|$$);
    $random = "abcdefghijklmnopqrstuvwxyz1234567890";

    if ($auth_generate_password ne "on") {
	$password = $in{"auth_password1"};
    } else {


	$password = "";
	for (1..6) {
            $password .= substr($random,int(rand(36)),1);
        }
    }
    $real_password = $password;
    $salt = "";
# Note We do not reseed the random generator from above
    for (1..2) {
	$salt .= substr($random,int(rand(36)),1);
    }
    $password = &AuthEncryptWrap ($password, 
				  $salt);
    @write_fields = ($password, $in{'auth_user_name'}, 
		     $group);
    foreach (@auth_extra_fields) {
	push(@write_fields, $in{"$_"});
    }

# Add the user to the data file
if ($auth_add_register eq "on") {

# Lock the file to make sure no one else will write to
# it if anyone else registers at the same time
#
&AuthGetFileLock ("$auth_user_file.lock");
    $user_file = $auth_user_file;
    if ($auth_alt_user_file ne "") {
	$user_file = $auth_alt_user_file;
    }
open (USERFILE, ">>$user_file") ||
  &CgiDie("Could Not Append To User File\n");

print USERFILE join("\|", @write_fields) . "\n";
close (USERFILE);
&AuthReleaseFileLock ("$auth_user_file.lock");

} # End of auth_add_register

# The following emails the registration information
# if that option has been previously defined.
#
if ($auth_email_register eq "on" &&
    $auth_admin_from_address ne "" &&
    $auth_admin_email_address ne "") {
    require "$auth_lib/mail-lib.pl";
local($subject, $message);
$subject = "Register User";

$message = join(",", @write_fields) . "\n";
&send_mail($auth_admin_from_address, 
	$auth_admin_email_address,
	$subject, $message);


} # End of Email Register

# Email password to user if password is auto
# generated.

    if ($auth_generate_password eq "on") {
	if ($auth_email_register ne "on") {
	    require "$auth_lib/mail-lib.pl";
	}
	$subject = "Registered User Password";
	$message = $auth_password_message;
	$message .= " $real_password.\n\n\n";
	&send_mail($auth_admin_from_address, 
	           $user_email,
	           $subject, $message);
    }
    &HTMLPrintRegisterSuccess ($main_script, 
			       $form_tags);

} # End of RegisterUser

############################################################
#
# subroutine: PrintCurrentFormVars
#   Usage:
#     $form_tags = &PrintCurrentFormVars(*formvars);
#
#  This routine takes the pre-existing form variables and 
#  makes them into hidden variables for inserting into the
#  form.  This is how the routine keeps old form variables
#  related to the program intact while all the CGI forms
#  relating to login get passed around.
#  All variables with AUTH in them are not duplicated since
#  they are related to this script.
#
#  Parameters:
#    *form_vars = a reference to the form variables related
#    to the main script that called the authentication
#    routines in the first place.
#
#   Output:
#     Hidden field tags related to the form information we
#     want to preserve.
############################################################

sub PrintCurrentFormVars {
    local(*form_vars) = @_;
    local($x,$y,$form_tags);
    $form_tags = "";
    foreach $x (keys %form_vars) {
	if (!($x =~ /auth_/i)) {
	    $y = $form_vars{"$x"};
	    $form_tags .= qq!<input type=hidden name=$x 
		value="$y">\n!;
	}
    }
    $form_tags;
} # PrintCurrentFormTags

############################################################
#
# subroutine: AuthGetFileLock 
#   Usage:
#     &AuthGetFileLock("lockfilename");
# 
#  This routine locks a file so that no one else
#  can get to it while it is being written to.
# 
#  Parameters:
#     $lock_file = filename to use as a temporary lock file
#
#   Output:
#      None.  It checks for the existance of a lock file
#      and if it finds it, it waits until the lock file
#      disappears.  After the lock file is gone, it opens
#      the lock file up itself.
#
#   Note: we do not use FLOCK because FLOCK is not
#   implemented on some systems.  You may use it be
#   uncommenting the flock lines if you so desire.
#
############################################################

sub AuthGetFileLock {  
    local ($lock_file) = @_;

    local ($endtime);  
    $endtime = 60;
    $endtime = time + $endtime;
#   We set endtime to wait 60 seconds

# The $endtime is used for a timeout of how long we 
# want to keep waiting for the lock if someone else
# already has it open.
    while (-e $lock_file && time < $endtime) {
        # Do Nothing
    }
    open(LOCK_FILE, ">$lock_file");    
#    flock(LOCK_FILE, 2); # 2 exclusively locks the file
} # end of AuthGetFileLock

############################################################
#
# subroutine: AuthReleaseFileLock
#   Usage:
#     &AuthReleaseFileLock($lock_file);
#
#  This routine releases the lock file when we are
#  done with the original file.
#
#  Parameters:
#     $lock_file = filename to use as a temporary lock file
#
#   Output:
#      None. Removes the lock file.
# 
#  Note: FLOCK is not used because it is not implemented on
#  Some systems.  You may use it by uncommenting the flock
#  lines if you desire.
############################################################

sub AuthReleaseFileLock {
    local ($lock_file) = @_;
       
# 8 unlocks the file
#    flock(LOCK_FILE, 8);
    close(LOCK_FILE);
    unlink($lock_file);

} # end of ReleaseFileLock   
 
############################################################
#
# subroutine: AuthEncryptWrap
#   Usage:
#     $cryptedpassword = &AuthEncryptWrap(
#      $password, $salt);
#
#  This routine wraps the crypt routine around 
#  a wrapper routine so that if a system does not
#  support the CRYPT routine, you may implement your own
#  in here.
#
#  Parameters:
#    $field = field to encrypt
#    $salt = salt value to use for encryption
#
#   Output:
#     Encrypted password
############################################################

sub AuthEncryptWrap {
    local ($field, $salt) = @_;

# If auth_use_cleartext is on, then we do not
# encrypt the password.
    if ($auth_use_cleartext ne "on") { 
    $field = crypt ($field, $salt);
    }

    $field;
 
} # end of encrypt
 

1;



