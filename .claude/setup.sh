#!/usr/bin/env bash
# SessionStart provisioning. Safe to run repeatedly: every step checks before acting.
#
# A SessionStart hook blocks the session until it returns, so everything here is guarded
# and nothing here waits on input. Give it a timeout in settings.json as well.
#
# What this replaces, and why it matters:
#
# The previous version looked for the Playwright browser cache at $HOME/.cache/ms-playwright
# and /root/.cache/ms-playwright only. On Windows that cache is at
# %LOCALAPPDATA%\ms-playwright, so the check concluded "not installed" on every Windows
# session and reinstalled. It then ran `npx playwright install chromium --with-deps`, and
# --with-deps shells out to apt-get, which does not exist outside Debian-family Linux.
#
# A 2026-06-30 session handoff recorded this as fixed in ttx-engine and pushed as e38232c.
# That commit does not exist in the repository, and .claude/setup.sh there has exactly one
# commit in its history: the 2026-03-31 extraction. The claim survived a month unchecked,
# and was believed twice more while writing the registry. Hence the evidence rule.

set -u

echo "=== session setup ==="

case "$(uname -s 2>/dev/null || echo unknown)" in
  Linux*)               OS=linux   ;;
  Darwin*)              OS=macos   ;;
  MINGW*|MSYS*|CYGWIN*) OS=windows ;;
  *)                    OS=unknown ;;
esac
echo "platform: $OS"

# --- node --------------------------------------------------------------------
# Conditional on package.json. Most repos this installs into are Python, and running
# npm install in one prints an error at every session start for no reason.

if [ -f package.json ]; then
  if [ ! -d node_modules ]; then
    echo "installing npm dependencies"
    npm install
  else
    echo "node_modules present"
  fi
fi

# --- python ------------------------------------------------------------------
# Report only. Provisioning a virtualenv unattended turns a session start into a
# multi-minute download, and SessionStart blocks the session while it runs.

for v in .venv venv env; do
  if [ -d "$v" ]; then
    echo "virtualenv present: $v"
    break
  fi
done

# --- playwright --------------------------------------------------------------

# Detection has to look past the root. In a workspaces monorepo Playwright is declared in
# the app packages, not at the top: spearhead-business has it in apps/portal/package.json
# and apps/site/package.json and none at the root, so grepping the root package.json alone
# reported "not used" and skipped provisioning entirely. A playwright.config.* anywhere is
# the reliable signal that the suite exists.
PW_USED=""
if [ -n "$(find . -maxdepth 3 -name 'playwright.config.*' -not -path './node_modules/*' -print -quit 2>/dev/null)" ]; then
  PW_USED=1
elif [ -f package.json ] && grep -q '"@playwright/test"\|"playwright"' package.json 2>/dev/null; then
  PW_USED=1
fi

if [ -n "$PW_USED" ]; then
  FOUND=""
  for d in \
    "${PLAYWRIGHT_BROWSERS_PATH:-}" \
    "$HOME/.cache/ms-playwright" \
    "/root/.cache/ms-playwright" \
    "${LOCALAPPDATA:-}/ms-playwright" \
    "${USERPROFILE:-}/AppData/Local/ms-playwright" \
    "$HOME/AppData/Local/ms-playwright" \
    "$HOME/Library/Caches/ms-playwright"
  do
    [ -n "$d" ] && [ -d "$d" ] && { FOUND="$d"; break; }
  done

  if [ -n "$FOUND" ]; then
    echo "playwright browsers present: $FOUND"
  else
    echo "installing playwright chromium"
    # --with-deps shells out to apt-get. Linux only.
    if [ "$OS" = linux ]; then
      npx playwright install chromium --with-deps
    else
      npx playwright install chromium
    fi
  fi
fi

echo "=== ready ==="
echo "branch: $(git branch --show-current 2>/dev/null || echo 'not a git repo')"
echo "head:   $(git log --oneline -1 2>/dev/null || echo 'no commits yet')"
