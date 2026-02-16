#!/bin/bash
set -e

# Directories that need to be writable by appuser
WRITABLE_DIRS=(
    /workspace/storage
)

if [ "$(id -u)" = '0' ]; then
    # Fix permissions for mounted volumes
    for dir in "${WRITABLE_DIRS[@]}"; do
        if [ -d "$dir" ]; then
            chown -R appuser:appuser "$dir"
        fi
    done

    # Drop privileges and exec the command as appuser
    exec gosu appuser "$@"
fi

# If already running as non-root, just exec the command
exec "$@"
