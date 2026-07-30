#!/usr/bin/env bash
# gate: refuse a commit when the repo's own checks fail, or a secret is staged.
#
# Fires on PreToolUse, Bash matching `git commit`.
#
# The commands are not written here. They come from pipeline/profiles/<name>.sh, chosen by
# one word in the repo's .claude/profile. That indirection is the whole point: 20 code
# repos, 13 wikis and two workstreams cannot share a hook that hardcodes `npm run lint`.
#
# A wiki has no lint, no typecheck, no build and no tests. Installing a Node gate there
# blocks every commit until GATE_OVERRIDE is learned, and an override used routinely is
# the same as no gate at all. So the wiki profile defines a secret scan and nothing else,
# and that is a real gate rather than a broken one.
#
# Escape: GATE_OVERRIDE='a reason of at least ten characters'. Every use is logged.

HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
. "$HOOK_DIR/lib.sh"

PAYLOAD="$(read_payload)"
CMD="$(payload_command "$PAYLOAD")"
require_parsed "$CMD"

case "$CMD" in *"git commit"*) ;; *) allow ;; esac

ROOT="$(repo_root)"
[ -n "$ROOT" ] || allow

PROFILE="$(repo_profile)"
if [ -z "$PROFILE" ]; then
  warn "gate: no .claude/profile in this repo, so no build gate ran.
Add one naming a profile from ops/pipeline/profiles/ to turn the gate on."
  PROFILE="none"
fi

# --- override ----------------------------------------------------------------

if [ -n "${GATE_OVERRIDE:-}" ]; then
  if [ "${#GATE_OVERRIDE}" -lt 10 ]; then
    refuse "GATE_OVERRIDE is set but the reason is under ten characters.
State why the gate is being bypassed."
  fi
  mkdir -p "$ROOT/.claude/state"
  printf '%s\t%s\t%s\n' "$(git rev-parse --short HEAD 2>/dev/null || echo none)" \
    "$PROFILE" "$GATE_OVERRIDE" >> "$ROOT/.claude/state/overrides.log"
  warn "gate: bypassed. Reason logged to .claude/state/overrides.log"
  allow
fi

# --- secret scan: universal, every profile, no exceptions --------------------

if have gitleaks; then
  if ! gitleaks protect --staged --no-banner >/dev/null 2>&1; then
    refuse "gitleaks found a secret in the staged changes.
Run \`gitleaks protect --staged --verbose\` to see it. Do not commit and remove after:
history is the problem, not the working tree."
  fi
else
  # Cheap fallback so the absence of a tool is not the absence of a check.
  STAGED="$(git diff --cached --name-only 2>/dev/null || true)"
  for f in $STAGED; do
    case "$f" in
      *.env|*.env.*|*.pem|*.p12|*credentials*.json|*serviceaccount*.json|.ebay_credentials)
        refuse "staged file looks like credential material: $f
If this is genuinely safe, name it in .gitignore or override with a reason." ;;
    esac
  done
  warn "gate: gitleaks is not installed, so only the filename check ran."
fi

# --- profile checks ----------------------------------------------------------

[ "$PROFILE" = "none" ] && allow

PROFILE_FILE="$HOOK_DIR/../profiles/$PROFILE.sh"
if [ ! -f "$PROFILE_FILE" ]; then
  refuse "this repo names profile '$PROFILE' but ops/pipeline/profiles/$PROFILE.sh does not exist."
fi

# A profile defines GATE_STEPS as name=command pairs, one per line.
# shellcheck source=/dev/null
. "$PROFILE_FILE"

[ -n "${GATE_STEPS:-}" ] || allow

cd "$ROOT" || allow

FAILED=""
while IFS= read -r step; do
  [ -n "$step" ] || continue
  name="${step%%=*}"
  run="${step#*=}"
  if ! eval "$run" >/tmp/gate.$$ 2>&1; then
    FAILED="$FAILED\n\n--- $name ---\n$(tail -30 /tmp/gate.$$)"
  fi
done <<EOF
$(printf '%s' "$GATE_STEPS")
EOF
rm -f /tmp/gate.$$

if [ -n "$FAILED" ]; then
  refuse "the $PROFILE gate failed.$(printf '%b' "$FAILED")"
fi

allow
