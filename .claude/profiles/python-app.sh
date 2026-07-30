#!/usr/bin/env bash
# Profile: python-app
#
# Commands are named without a path. run-gate.sh resolves each through the repo's
# virtualenv first (venv/Scripts on Windows, .venv/bin on Linux) and only then PATH,
# because the tools are installed in the venv and invisible to `command -v`.
#
# Split by phase. ttx-engine's suite is 2288 tests at 6m02s, so it belongs at push. mypy
# over 113 files finishes in seconds, so it belongs at commit where it catches the error
# while the code is still in mind.
#
# ruff is not listed. It is neither installed nor configured in any of these repos, and a
# declared step whose tool is missing blocks. Add it per repo via .claude/profile.local
# once it is actually adopted.

GATE_COMMIT="typecheck=mypy"

GATE_PUSH="typecheck=mypy
test=pytest -q"
