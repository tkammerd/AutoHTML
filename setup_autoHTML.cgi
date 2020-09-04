# Set up utility values for boolean conditions -- do not change!
$false = 0;
$true = !$false;

# Set server path for debugging logfile and level of debugging
$DebugPath = "./AutoHTML.log";
$debug_on = $true;
$debug2_on = $debug_on && $true;

# Set server path for CGI libraries
$lib = "./Library";

# Set server path for AutoHTML source file
$SourceBase = ""; # Usually entire path is provided by invoking
                  # web page, so this is usually null

# Set base URL for directory containing autoHTML files (no trailing slash!)
$autoHTML_base_URL = "/~tkammerd/cgi-bin/AutoHTML";
