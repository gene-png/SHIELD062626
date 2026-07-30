#!/usr/bin/env bash
# identity: refuse a push or a gh call made under the wrong account.
#
# Fires on PreToolUse, Bash matching `git push` or `gh`.
#
# This is the hook that replaces a sentence. The rule "never use Canmore credentials for
# Spearhead work" has been written in a global CLAUDE.md for months, and identity drift
# kept happening anyway: a 2026-04-22 aviation commit was authored as
# david.catarious@canmorecompany.com, and a June sweep found five repos defaulting to the
# Canmore global identity. A rule the model may choose to follow is a suggestion. This is
# not one.
#
# Two independent checks, because they fail in different ways:
#
#   git identity   who the commit will be attributed to. Always checkable.
#   gh account     who the push authenticates as. Only checkable where gh exists.
#
# In the cloud sandbox gh does not exist, so the gh check is skipped and says so. A skipped
# check that announces itself is honest. A skipped check that prints nothing is a hook
# nobody knows stopped working.

HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
. "$HOOK_DIR/lib.sh"

PAYLOAD="$(read_payload)"
CMD="$(payload_command "$PAYLOAD")"
require_parsed "$CMD"

# `gh auth ...` is the remediation, so it cannot be part of what gets refused. Without this
# carve-out the refusal is unrecoverable inside a session: the hook blocks every `gh` call,
# and the fix it prints ("gh auth switch --user ...") is a `gh` call. Nothing under
# `gh auth` publishes to a repo, so exempting it costs the guard nothing.
case "$CMD" in
  *"gh auth"*) allow ;;
esac

# Only guard the two commands that publish. Everything else passes untouched.
case "$CMD" in
  *"git push"*|*"gh "*) ;;
  *) allow ;;
esac

OWNER="$(expected_owner)"
[ -n "$OWNER" ] || allow      # no remote, nothing to be wrong about

ROOT="$(repo_root)"

# --- git identity ------------------------------------------------------------

EMAIL="$(git config --get user.email 2>/dev/null || printf '')"

if [ -z "$EMAIL" ]; then
  refuse "no git user.email is set in $ROOT.
Set it locally before pushing. A repo with no local identity inherits the global one,
which is how Canmore-authored commits reached Spearhead repos in April."
fi

# The mapping lives here rather than in the hook's logic so adding an account is an edit
# to one line. Owner is the GitHub account that owns the repo.
case "$OWNER" in
  SpearheadAnalytica|gene-png)
    WANT_EMAIL="davidcatarious@spearheadanalytica.com" ;;
  canmoreai)
    WANT_EMAIL="david.catarious@canmorecompany.com" ;;
  *)
    WANT_EMAIL="" ;;
esac

if [ -n "$WANT_EMAIL" ] && [ "$EMAIL" != "$WANT_EMAIL" ]; then
  refuse "git identity does not match the repo owner.

  repo owner      $OWNER
  expects         $WANT_EMAIL
  currently set   $EMAIL

Fix with:  git config --local user.email \"$WANT_EMAIL\"

This is a boundary, not a preference. Spearhead accounts do not author Canmore work and
Canmore accounts do not author Spearhead work."
fi

# --- gh account --------------------------------------------------------------

if ! have gh; then
  warn "identity: gh is not installed here, so the account check was skipped.
Git identity was verified and matches. This is expected in the cloud sandbox."
  allow
fi

ACTIVE="$(gh api user --jq .login 2>/dev/null || printf '')"

if [ -z "$ACTIVE" ]; then
  warn "identity: gh is installed but not authenticated, so the account check was skipped.
Git identity was verified and matches."
  allow
fi

# gene-png repos are reachable under the Spearhead account, which holds the collaborator
# grant. The owner and the account legitimately differ there.
case "$OWNER" in
  gene-png) WANT_ACCOUNT="SpearheadAnalytica" ;;
  *)        WANT_ACCOUNT="$OWNER" ;;
esac

if [ "$ACTIVE" != "$WANT_ACCOUNT" ]; then
  refuse "the active gh account cannot push this repo.

  repo owner      $OWNER
  expects         $WANT_ACCOUNT
  currently       $ACTIVE

Fix with:  gh auth switch --user $WANT_ACCOUNT

Switch back afterwards if you were mid-task on the other account."
fi

allow
