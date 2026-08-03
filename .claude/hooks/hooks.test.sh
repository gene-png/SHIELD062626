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
# `git add .` was matched as a substring, so every dotfile path read as a bulk stage. In
# this repo that is the whole ops pipeline and all of CI, and the only way past the
# refusal was the bulk stage it exists to prevent.
check "dotdir path"                 $ALLOW no-bulk-stage.sh '{"tool_input":{"command":"git add .claude/profile"}}'
check "dotfile path"                $ALLOW no-bulk-stage.sh '{"tool_input":{"command":"git add .gitignore"}}'
check "two dotdir paths"            $ALLOW no-bulk-stage.sh '{"tool_input":{"command":"git add .github/workflows/ci.yml .claude/profile"}}'
check "dot path among flags"        $ALLOW no-bulk-stage.sh '{"tool_input":{"command":"git add --verbose .env.example"}}'
check "empty payload"               $ALLOW no-bulk-stage.sh '{}'
check "non-Bash tool"               $ALLOW no-bulk-stage.sh '{"tool_input":{"file_path":"x.ts"}}'

echo "identity: stays out of the way"
check "non-publishing command"      $ALLOW identity.sh '{"tool_input":{"command":"ls"}}'
check "git commit is not a push"    $ALLOW identity.sh '{"tool_input":{"command":"git commit -m x"}}'
check "correct identity pushes"     $ALLOW identity.sh '{"tool_input":{"command":"git push origin main"}}'
# The guard matched "gh " anywhere in the string, so these all tripped it while running
# nothing. The first two are real commands from this repo's own session logs.
check "grep pattern containing gh"  $ALLOW identity.sh '{"tool_input":{"command":"bash .claude/setup.sh | grep -E \"gh account|identity\""}}'
check "a word ending in gh"         $ALLOW identity.sh '{"tool_input":{"command":"echo \"high priority\""}}'
check "commit message mentions gh"  $ALLOW identity.sh '{"tool_input":{"command":"git commit -m \"use gh for releases\""}}'
check "a path under .github"        $ALLOW identity.sh '{"tool_input":{"command":"cat .github/workflows/ci.yml"}}'

echo "identity: refuses"
saved="$(git config --local --get user.email || printf '')"
git config --local user.email "david.catarious@canmorecompany.com"
check "Canmore email, Spearhead repo" $BLOCK identity.sh '{"tool_input":{"command":"git push"}}'
check "same, via gh"                  $BLOCK identity.sh '{"tool_input":{"command":"gh pr create"}}'
git config --local user.email "dcatario@gmail.com"
check "personal email, Spearhead repo" $BLOCK identity.sh '{"tool_input":{"command":"git push"}}'
# The refusal has to leave a way out. It prints "gh auth switch --user ..." as the fix, and
# with `gh auth` inside the guard that command was refused too, so a session that tripped
# the hook could not recover inside itself. Nothing under `gh auth` publishes to a repo.
check "gh auth switch escapes"        $ALLOW identity.sh '{"tool_input":{"command":"gh auth switch --user SpearheadAnalytica"}}'
check "gh auth status escapes"        $ALLOW identity.sh '{"tool_input":{"command":"gh auth status"}}'
# Narrowing the matcher must not open a hole: a real invocation after a separator, or
# behind sudo, is still an invocation.
check "gh after &&"                   $BLOCK identity.sh '{"tool_input":{"command":"cd /tmp && gh pr create"}}'
check "gh after a pipe"               $BLOCK identity.sh '{"tool_input":{"command":"echo x | gh pr comment 1 -F -"}}'
check "gh after a semicolon"          $BLOCK identity.sh '{"tool_input":{"command":"ls; gh release create v1"}}'
check "push after &&"                 $BLOCK identity.sh '{"tool_input":{"command":"git add a.ts && git push"}}'
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

echo "run-gate: a step that reads stdin"
# The step list was fed to the read loop on stdin, so the first step that read stdin ate the
# rest of it. SHIELD's five-step commit gate ran one step, skipped four, and reported
# "passed (1 steps)". A skipped step reported as a passed step is the exact failure the
# missing-tool branch refuses rather than skips for. `docker compose exec -T` is the real
# case; `cat` reproduces it in one line.
sg_base="$(mktemp -d)"
sg_repo="$sg_base/repo"
mkdir -p "$sg_repo/.claude/profiles" "$sg_repo/.claude/hooks" "$sg_repo/bin"
cp "$HOOK_DIR"/*.sh "$HOOK_DIR"/json-field.pl "$sg_repo/.claude/hooks/"
printf 'slurptest\n' > "$sg_repo/.claude/profile"
printf 'GATE_COMMIT="slurp=cat\nsecond=marktool"\n' > "$sg_repo/.claude/profiles/slurptest.sh"
printf '#!/usr/bin/env bash\ntouch second-step-ran\nexit 0\n' > "$sg_repo/bin/marktool"
chmod +x "$sg_repo/bin/marktool" "$sg_repo/.claude/hooks"/*.sh
( cd "$sg_repo" && git init -q . >/dev/null 2>&1 \
  && PATH="$sg_repo/bin:$PATH" bash .claude/hooks/run-gate.sh commit ) >/dev/null 2>&1
if [ -f "$sg_repo/second-step-ran" ]; then
  pass=$((pass+1)); printf '  ok    %s\n' "step after a stdin reader still runs"
else
  fail=$((fail+1)); printf '  FAIL  %s\n        the second step never ran\n' "step after a stdin reader still runs"
fi
rm -rf "$sg_base"

echo "parser"
check "unreadable payload refuses"  $BLOCK no-bulk-stage.sh '{"tool_input":{"command":'
check "malformed json, no key"      $ALLOW no-bulk-stage.sh 'not json at all'

echo
printf '  %s passed, %s failed\n\n' "$pass" "$fail"
[ "$fail" -eq 0 ]
