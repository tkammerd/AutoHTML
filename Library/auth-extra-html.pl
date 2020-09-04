
############################################################
#                       AUTH-EXTRA-HTML.PL
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
# routines related to the authentication routines.
#
# Main Procedures:
#   All the routines are ancillary to the auth-extra-lib.pl 
#   file.
#
# Special Notes: Nearly all the routines below accept
# some sort of parameter.  These parameters are only for
# printing out extra information.  They are not doing any
# significant processing.
#
#
############################################################

############################################################
#
# subroutine: PrintLogonPage
#
#  This routine outputs the logon HTML page along with
#  a bad logon message if one exists.  Hidden form tags
#  are generated automatically if we are passing previous
#  form data from the main script.
#
############################################################

sub PrintLogonPage {
    local($bad_logon_message, $main_script, *in) = @_;
    local($form_tags);
    local($register_tag);
    local($search_tag);

    if (length($auth_logon_title) < 1) {
        $auth_logon_title = "Submit Logon";
    }

    if (length($auth_logon_header) < 1) {
        $auth_logon_header = "Enter Your Logon Information";
    }

    $register_tag = "";
    $search_tag = "";

    if ($auth_allow_register eq "on") {
	$register_tag = <<__END_OF_REG_TAG__;
<input type=submit name=auth_register_screen_op 
value="Register For An Account"><p>
__END_OF_REG_TAG__
}

    if ($auth_allow_search eq "on") {
	$search_tag = <<__END_OF_SEARCH_TAG__;
<input type=submit name=auth_search_screen_op 
value="Search For Old Account"><p>
__END_OF_SEARCH_TAG__
    } 
   $form_tags = &PrintCurrentFormVars(*in);

    print <<__END_OF_LOGON__;
<HTML><HEAD>
<TITLE>$auth_logon_title</TITLE>
</HEAD>
<BODY>
<CENTER>
<H1>$auth_logon_header</h1>
<hr>
$bad_logon_message
<FORM METHOD=POST ACTION=$main_script>
$form_tags
<TABLE>
<TR><TH>Username</TH>
<TD><INPUT TYPE=TEXT NAME=auth_user_name></td></tr>
<tr><th>Password</th>
<td><input type=password name=auth_password></td></tr>
</TABLE><p>
<input type=submit name=auth_logon_op 
value="Logon To The System"><p>
$register_tag
$search_tag
<hr>
</center>
</form>
</body>
</HTML>
__END_OF_LOGON__

} # End of PrintLogonPage

############################################################
#
# subroutine: PrintSearchPage
#
#  This routine outputs the Search HTML page if one exists.  
#  Hidden form tags are generated automatically if we are 
#  passing previous form data from the main script.
#
############################################################

sub PrintSearchPage {
local($main_script,*in) = @_;
    local($form_tags);
    $form_tags = &PrintCurrentFormVars(*in);
    print <<__END_OF_SEARCH__;
<HTML><HEAD>
<TITLE>Search For An Account</TITLE>
</HEAD>
<BODY>
<CENTER>
<H1>Search For Matching Username</h1>
<hr>
<h2>Enter Your Email Address To Search For A Matching Username</h2>
<FORM METHOD=POST ACTION=$main_script>
$form_tags
<TABLE>
<TR><TH>Email</TH>
<TD><INPUT TYPE=TEXT NAME=auth_email></td></tr>
</TABLE>
<p>
<input type=submit name=auth_search_op value="Submit Search">
<input type=submit name=auth_logon_screen_op value="Return to Logon Screen">
<P>
</center>
</form>
</body>
</HTML>
__END_OF_SEARCH__

} # End of PrintSearchPage

############################################################
#
# subroutine: HTMLPrintSearchResults
#
#   This routine outputs the results of the search for 
#   usernames using an email address
#
############################################################

sub HTMLPrintSearchResults {
    local($main_script, $form_tags, $user_list) =
	@_;
	print <<__END_SEARCHRESULTS__;
<HTML><HEAD>
<TITLE>User Found</TITLE>
</HEAD>
<BODY>
<CENTER>
<H1>User Was Found In The Search</h1>
<hr>
<h2>List Of Users</h2>
<strong>$user_list</strong>
<FORM METHOD=POST ACTION=$main_script>
$form_tags
<input type=submit name=auth_logon_screen_op
value="Return to Logon Screen">
<hr>
</center>
</form>
</body>
</HTML>
__END_SEARCHRESULTS__

} # End of HTMLPrintSearchResults


############################################################
#
# subroutine: HTMLPrintNoSearchResults
#
#   This routine prints the HTML related to not having
#   found any results from the search on email address.
#
############################################################

sub HTMLPrintNoSearchResults {
    local($main_script, $form_tags) = @_;
	print <<__END_NOSEARCHRESULTS__;
<HTML><HEAD>
<TITLE>No Users Found</TITLE>
</HEAD>
<BODY>
<CENTER>
<H1>Sorry, No Users Found</h1>
<hr>
<h2>Sorry, No users were found that matched your email address</h2>
<FORM METHOD=POST ACTION=$main_script>
$form_tags
<input type=submit name=auth_logon_screen_op
value="Return to Logon Screen">
<hr>
</center>
</form>
</body>
</HTML>
__END_NOSEARCHRESULTS__

} # End HTMLPrintNoSearchResults


############################################################
#
# subroutine: PrintRegisterPage
#
#  This routine outputs the Register HTML page.  Hidden form 
#  tags are generated automatically if we are passing previous
#  form data from the main script.
#
############################################################

sub PrintRegisterPage {
local($main_script,*in) = @_;
local($form_tags);
local($more_form_input,$password_input, $x);
    $form_tags = &PrintCurrentFormVars(*in);
local ($password_message);

#
# We also check for the extra fields and output HTML
# asking for input on the extra fields.
#
$more_form_input = "";
for ($x = 0; $x <= @auth_extra_fields - 1; $x++) {
    $more_form_input .= <<__END_OF_EXTRA_FIELDS__;
<TR><TH>$auth_extra_desc[$x]</TH>
<TD><INPUT TYPE=TEXT NAME=$auth_extra_fields[$x]></td></tr>
__END_OF_EXTRA_FIELDS__
}
$password_input = "";
if ($auth_generate_password ne "on") {
    $password_input = <<__END_OF_PASSWORD_FIELDS__;
<tr><th>Password</th>
<td><input type=password name=auth_password1></td></tr>
<tr><th>Password Again</th>
<td><input type=password name=auth_password2></td></tr>
__END_OF_PASSWORD_FIELDS__
} 
$password_message = "";
if ($auth_generate_password eq "on") {
$password_message = <<__PASSWORDMSG__;
Your password will be automatically generated and sent
to you via your E-Mail address.
__PASSWORDMSG__
} 
    print <<__END_OF_REGISTER__;
<HTML><HEAD>
<TITLE>Register For An Account</TITLE>
</HEAD>
<BODY>
<CENTER>
<H1>Enter The Registration Information</h1>
<hr>
<FORM METHOD=POST ACTION=$main_script>
$form_tags
<TABLE>
<tr><th>User Name</th>
<td><input type=Username name=auth_user_name></td></tr>
$password_input
$more_form_input
</TABLE>
<p>
<input type=submit name=auth_register_op value="Submit Information">
<input type=submit name=auth_logon_screen_op value="Return to Logon Screen">
<P>
$password_message
</center>
</form>
</body>
</HTML>
__END_OF_REGISTER__

} # End of PrintRegisterPage

############################################################
#
# subroutine: HTMLPrintRegisterSuccess
#
#  This routine prints the HTML for a successful user
#  registration.
#
############################################################

sub HTMLPrintRegisterSuccess {
    local($main_script, $form_tags) = 
	@_;
    print <<__END_OF_REGISTER_SUCCESS__;
<HTML><HEAD>
<TITLE>Registration Added</TITLE>
</HEAD>
<BODY>
<CENTER>
<H2>You Have been added to the user database</h2>
</center>
<hr>
<FORM METHOD=POST ACTION=$main_script>
$form_tags
<BLOCKQUOTE>
    $auth_register_message
</Blockquote>
<center>
<input type=submit name=auth_logon_screen_op value="Return to Logon Screen")
</center>
</form>
</body>
</HTML>
__END_OF_REGISTER_SUCCESS__

} # End of RegisterSuccess


############################################################
#
# subroutine: HTMLPrintRegisterFoundDuplicate
#
#  This routine prints the HTML for a failed user
#  registration because of finding a duplicate username
#
############################################################


sub HTMLPrintRegisterFoundDuplicate {
    local($main_script, $form_tags) = 
	@_;
print <<__END_OF_REGISTER_DUPLICATE__;
<HTML><HEAD>
<TITLE>Problem with Registration</TITLE>
</HEAD>
<BODY>
<CENTER>
<H1>Problem with Registration</h1>
</center>
<hr>
<FORM METHOD=POST ACTION=$main_script>
$form_tags
<BLOCKQUOTE>
Sorry, your username is already in the database
</Blockquote>
<center>
<input type=submit name=auth_logon_screen_op value="Return to Logon Screen")
</center>
</form>
</body>
</HTML>
__END_OF_REGISTER_DUPLICATE__

} # End of HTMLPrintRegisterFoundDuplicate

############################################################
#
# subroutine: HTMLPrintRegisterNoPasswordMatch
#
#  This routine prints the HTML for a failed user
#  registration because the two passwords did not match
#
############################################################

sub HTMLPrintRegisterNoPasswordMatch {
    local($main_script, $form_tags) = 
	@_;

    print <<__END_OF_REGISTER_NOMATCH__;
<HTML><HEAD>
<TITLE>Problem with Registration</TITLE>
</HEAD>
<BODY>
<CENTER>
<H1>Problem with Registration</h1>
</center>
<hr>
<FORM METHOD=POST ACTION=$main_script>
$form_tags
<BLOCKQUOTE>
Sorry, the two passwords you typed in did not match.
</Blockquote>
<center>
<input type=submit name=auth_logon_screen_op value="Return to Logon Screen")
</center>
</form>
</body>
</HTML>
__END_OF_REGISTER_NOMATCH__

} # End of HTMLPrintRegisterNoPasswordMatch

############################################################
#
# subroutine: HTMLPrintRegisterFoundDuplicate
#
#  This routine prints the HTML for a failed user
#  registration because of finding a missing value or
#  a value that has a PIPE in it.
#
############################################################

sub HTMLPrintRegisterNoValidValues {
    local ($main_script, $form_tags) =
	@_;
    print <<__END_OF_REGISTER_NOVALUE__;
<HTML><HEAD>
<TITLE>Problem with Registration</TITLE>
</HEAD>
<BODY>
<CENTER>
<H1>Problem with Registration</h1>
</center>
<hr>
<FORM METHOD=POST ACTION=$main_script>
$form_tags
<BLOCKQUOTE>
Sorry, you need to enter a valid value for every field
</Blockquote>
<center>
<input type=submit name=auth_logon_screen_op value="Return to Logon Screen")
</center>
</form>
</body>
</HTML>
__END_OF_REGISTER_NOVALUE__
 
} # End of HTMLPrintRegisterNoValidValues

1;

