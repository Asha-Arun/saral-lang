#!/bin/bash
# Saral installer - delegates to parent install script
set -e
exec bash "$(cd "$(dirname "${BASH_SOURCE[0]}")/..&& pwd)/install_linux.sh" "$@"
