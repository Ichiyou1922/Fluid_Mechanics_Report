#!/bin/sh
# Run a FreeCAD-Python script headless via the snap interpreter.
#   scripts/run_freecad.sh <script.py> <config.json>
# The snap sandbox prints harmless mount warnings to stderr; we keep stdout.
set -e
SCRIPT="$1"
CONFIG="$2"
export PROP_CONFIG="$CONFIG"
exec freecad.cmd -c "exec(open('$SCRIPT').read())" 2> >(grep -v -E 'update.go|mount namespace|gtk-common-themes|snap-specific PYTHONPATH' >&2)
