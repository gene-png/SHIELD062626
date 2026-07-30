#!/usr/bin/env perl
# Extract one string field from a PreToolUse payload's tool_input, given on stdin.
#
#   perl json-field.pl command  < payload.json
#
# This lives in its own file rather than inline in lib.sh because the pattern needs
# backslashes that do not survive being written through a shell string. The inline version
# truncated `git commit -m "a \" b"` at the escape, which would have let a compound command
# hide a `git add -A` behind a quoted message.
#
# Prints the decoded value, or nothing when the key is absent. Exits 0 either way; the
# caller distinguishes absent from unreadable.

use strict;
use warnings;

my $key = shift // '';
exit 0 unless length $key;

my $json = do { local $/; <STDIN> };
exit 0 unless defined $json && length $json;

# Confine the search to tool_input so a "command" key elsewhere in the payload cannot be
# mistaken for the one being guarded.
my $scope = $json;
if ($json =~ /"tool_input"\s*:\s*(\{.*)/s) {
    $scope = $1;
}

my $qk = quotemeta $key;
exit 0 unless $scope =~ /"$qk"\s*:\s*"((?:[^"\\]|\\.)*)"/s;

my $v = $1;

# JSON string unescaping, enough for the fields we read.
$v =~ s/\\u([0-9a-fA-F]{4})/chr(hex($1))/ge;
$v =~ s/\\n/\n/g;
$v =~ s/\\r//g;
$v =~ s/\\t/\t/g;
$v =~ s/\\b//g;
$v =~ s/\\f//g;
$v =~ s/\\(["\\\/])/$1/g;

print $v;
