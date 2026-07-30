#!/usr/bin/env bash
# Tests for the ops hooks.
#
#   bash pipeline/hooks/hooks.test.sh
#
# Roughly half of these assert the hooks stay OUT of the way, because an over-blocking hook
# is one that gets switched off, and `pipeline-design.md` names that as the failure mode
# that ends with no gate anywhere.
#
# The suite exists because the first version of these hooks passed inspection and enforced
# nothing: jq is absent from Git Bash on Windows, so every payload parsed to an empty
# string and every refusal path was unreachable. Reading the code did not reveal it. Running
# it did, immediately.

set -uo pipefail
HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HOOK_DIR/../.." && pwd)"

pass=0; fail=0
BLOCK=2; ALLOW=0

check() { # check <desc> <expected_exit> <hook> <json>
  local desc="$1" want="$2" hook="$3" json="$4" got err
  err="$(printf '%s' "$json" | bash "$HOOK_DIR/$hook" 2>&1 >/dev/null)"; got=$?
  if [ "$got" -eq "$want" ]; then
    pass=$((pass+1)); printf '  ok    %s\n' "$desc"
  else
    fail=$((fail+1))
    printf '  FAIL  %s\n        wanted exit %s, got %s\n        %s\n' \
      "$desc" "$want" "$got" "$(printf '%s' "$err" | head -2)"
  fi
}

cd "$REPO" || exit 1

echo
echo "no-bulk-stage: refuses"
check "git add -A"                  $BLOCK no-bulk-stage.sh '{"tool_input":{"command":"git add -A"}}'
check "git add --all"               $BLOCK no-bulk-stage.sh '{"tool_input":{"command":"git add --all"}}'
check "git add ."                   $BLOCK no-bulk-stage.sh '{"tool_input":{"command":"git add ."}}'
check "git add -u"                  $BLOCK no-bulk-stage.sh '{"tool_input":{"command":"git add -u"}}'
check "extra whitespace"            $BLOCK no-bulk-stage.sh '{"tool_input":{"command":"git   add   -A"}}'
check "git commit -am"              $BLOCK no-bulk-stage.sh '{"tool_input":{"command":"git commit -am wip"}}'
check "hidden behind a quoted msg"  $BLOCK no-bulk-stage.sh '{"tool_input":{"command":"git commit -m \"a \\\" b\" && git add -A"}}'

echo "no-bulk-stage: stays out of the way"
check "named path"                  $ALLOW no-bulk-stage.sh '{"tool_input":{"command":"git add registry.yml"}}'
check "two named paths"             $ALLOW no-bulk-stage.sh '{"tool_input":{"command":"git add a.ts b.ts"}}'
check "git status"                  $ALLOW no-bulk-stage.sh '{"tool_input":{"command":"git status"}}'
check "unrelated command"           $ALLOW no-bulk-stage.sh '{"tool_input":{"command":"ls -la"}}'
check "a file merely named add"     $ALLOW no-bulk-stage.sh '{"tool_input":{"command":"cat src/git-add-helper.md"}}'
check "empty payload"               $ALLOW no-bulk-stage.sh '{}'
check "non-Bash tool"               $ALLOW no-bulk-stage.sh '{"tool_input":{"file_path":"x.ts"}}'

echo "identity: stays out of the way"
check "non-publishing command"      $ALLOW identity.sh '{"tool_input":{"command":"ls"}}'
check "git commit is not a push"    $ALLOW identity.sh '{"tool_input":{"command":"git commit -m x"}}'
check "correct identity pushes"     $ALLOW identity.sh '{"tool_input":{"command":"git push origin main"}}'

echo "identity: refuses"
saved="$(git config --local --get user.email || printf '')"
git config --local user.email "david.catarious@canmorecompany.com"
check "Canmore email, Spearhead repo" $BLOCK identity.sh '{"tool_input":{"command":"git push"}}'
check "same, via gh"                  $BLOCK identity.sh '{"tool_input":{"command":"gh pr create"}}'
git config --local user.email "dcatario@gmail.com"
check "personal email, Spearhead repo" $BLOCK identity.sh '{"tool_input":{"command":"git push"}}'
if [ -n "$saved" ]; then git config --local user.email "$saved"; else git config --local --unset user.email; fi
check "restored identity pushes"      $ALLOW identity.sh '{"tool_input":{"command":"git push"}}'

echo "gate"
check "not a commit"                $ALLOW gate.sh '{"tool_input":{"command":"ls"}}'
check "commit with no profile"      $ALLOW gate.sh '{"tool_input":{"command":"git commit -m x"}}'

echo "run-gate: resolved tool paths"
# The resolved path is spliced back into the step and the result goes through eval. When the
# splice was unquoted, `npm` resolving to /c/Program Files/nodejs/npm made eval split at the
# space and report "/c/Program: No such file or directory" as a lint failure. Nothing here
# covered it, because the only installed repo was python-app and venv/Scripts has no space.
# Build a repo under a directory with a space, put the tool in its venv, and run the gate.
rg_base="$(mktemp -d)"
rg_repo="$rg_base/dir with space"
mkdir -p "$rg_repo/.claude/profiles" "$rg_repo/.claude/hooks" "$rg_repo/.venv/bin"
cp "$HOOK_DIR"/*.sh "$HOOK_DIR"/json-field.pl "$rg_repo/.claude/hooks/"
printf 'spacetest\n' > "$rg_repo/.claude/profile"
printf 'GATE_COMMIT="probe=faketool --flag"\n' > "$rg_repo/.claude/profiles/spacetest.sh"
printf '#!/usr/bin/env bash\nexit 0\n' > "$rg_repo/.venv/bin/faketool"
chmod +x "$rg_repo/.venv/bin/faketool" "$rg_repo/.claude/hooks"/*.sh
( cd "$rg_repo" && git init -q . >/dev/null 2>&1 && bash .claude/hooks/run-gate.sh commit ) >/dev/null 2>&1
if [ $? -eq "$ALLOW" ]; then
  pass=$((pass+1)); printf '  ok    %s\n' "tool path with a space"
else
  fail=$((fail+1)); printf '  FAIL  %s\n' "tool path with a space"
fi
rm -rf "$rg_base"

echo "parser"
check "unreadable payload refuses"  $BLOCK no-bulk-stage.sh '{"tool_input":{"command":'
check "malformed json, no key"      $ALLOW no-bulk-stage.sh 'not json at all'

echo
printf '  %s passed, %s failed\n\n' "$pass" "$fail"
[ "$fail" -eq 0 ]
