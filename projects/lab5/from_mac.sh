#!/usr/bin/env bash

# run from Windows project directory: ~/Desktop/lab5
# copies only files newer on the source (skips unchanged)

# robocopy exits 1 on success ("files copied"), not 0 — normalise for set -e
rcopy() { MSYS_NO_PATHCONV=1 robocopy "$1" "$2" /XO /NP; (( $? <= 3 )); }

rcopy Z:/lab5/data data
rcopy Z:/lab5/output output
