#!/bin/sh
#
# Compatibility entry point. The live runner is suit-runner.sh.
dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec sh "$dir/suit-runner.sh" "$@"
