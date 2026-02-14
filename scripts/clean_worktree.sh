#!/bin/bash

# clean_worktree.sh
# Fixes ownership of files created by Docker containers (which are often owned by root).
# Usage: ./scripts/clean_worktree.sh [path]

TARGET_DIR="${1:-.}"

echo "🔧 Fixing permissions for: $TARGET_DIR"

if [ ! -d "$TARGET_DIR" ]; then
    echo "Error: Directory $TARGET_DIR does not exist."
    exit 1
fi

# detailed explanation of what this does:
# 1. mounts the current directory (or target) to /mnt in a lightweight alpine container
# 2. runs chown recursively to set the owner to the current user's ID and Group ID
# 3. this works because the container runs as root (by default) and can modify the root-owned files
docker run --rm \
    -v "$PWD/$TARGET_DIR":/mnt \
    alpine \
    chown -R "$(id -u):$(id -g)" /mnt

if [ $? -eq 0 ]; then
    echo "✅ Permissions fixed. You can now delete or modify files in $TARGET_DIR."
else
    echo "❌ Failed to fix permissions."
    exit 1
fi
