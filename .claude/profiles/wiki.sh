#!/usr/bin/env bash
# Profile: wiki
#
# Deliberately empty at both phases. A wiki has no lint, no typecheck, no build and no
# tests, so there is nothing for a build gate to check.
#
# The universal checks still run: the secret scan in gate.sh, no-bulk-stage, and the
# identity hook. That last one is what actually matters here, because these repos carry
# client material under two different attributions and the wrong account must not push
# them.
#
# Declaring a fake step would produce a gate that blocks every wiki commit, teach
# GATE_OVERRIDE, and end with no gate anywhere.

GATE_COMMIT=""
GATE_PUSH=""
