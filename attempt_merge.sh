#!/bin/bash
set -e

# Start from clean state
git checkout main
git pull

# Create release branch
BRANCH_NAME="release/v2.0-lab"
if git show-ref --verify --quiet refs/heads/$BRANCH_NAME; then
    echo "Branch $BRANCH_NAME already exists. Deleting..."
    git branch -D $BRANCH_NAME
fi
git checkout -b $BRANCH_NAME

# Helper to merge and resolve metadata conflicts
merge_stream() {
    BRANCH=$1
    MSG=$2
    echo "🔄 Merging $BRANCH..."
    # Try merge, if it fails, resolve specific files
    if ! git merge --no-ff "$BRANCH" -m "$MSG"; then
        echo "⚠️ Conflict detected. Resolving metadata files using --ours..."
        git checkout --ours WORKER_MISSION.md CLAUDE.md CURRENT_SPRINT.md AGENT_INSTRUCTIONS.md API_CONTRACTS.md 2>/dev/null || true
        git add WORKER_MISSION.md CLAUDE.md CURRENT_SPRINT.md AGENT_INSTRUCTIONS.md API_CONTRACTS.md 2>/dev/null || true
        # If there are still conflicts (code), this will fail and stop
        CONFLICTS=$(git diff --name-only --diff-filter=U)
        if [ -n "$CONFLICTS" ]; then
            echo "❌ Code conflicts remain:"
            echo "$CONFLICTS"
            exit 1
        fi
        git commit --no-edit
    fi
}

merge_stream integration/bridge-msg "Merge Stream A: Messaging Bridge"
merge_stream integration/bridge-hitl "Merge Stream B: Resilience Bridge"
merge_stream integration/bridge-prod "Merge Stream C: Production Bridge"
merge_stream integration/bridge-safe "Merge Stream D: Safety Bridge"

echo "✅ ALL STREAMS MERGED SUCCESSFULLY"
