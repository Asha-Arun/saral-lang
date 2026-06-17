#!/bin/bash
# Saral installer — run from the core/ directory
# For the full repo installer, use ../install_linux.sh instead.
set -e
exec bash "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/install_linux.sh" "$@"
