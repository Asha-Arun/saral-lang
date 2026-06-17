#!/bin/bash
# Saral uninstaller — delegates to install/uninstall_linux.sh
set -e
exec bash "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/install/uninstall_linux.sh" "$@"
