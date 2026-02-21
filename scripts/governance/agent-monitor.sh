#!/bin/bash
# agent-monitor.sh: Provides a "God View" of all running dev agent Docker containers.
# It tails logs and checks port status.

# Configuration
# Default to Hub path if not set
LOG_HUB_HOST="/home/mark/omc/logs/hub"
LOG_HUB_CONTAINER="/var/log/omc-agents"

if [ -d "$LOG_HUB_CONTAINER" ]; then
    LOG_DIR="$LOG_HUB_CONTAINER"
else
    LOG_DIR="$LOG_HUB_HOST"
fi

OUTPUT_FILE="$LOG_DIR/../architect_view.log"
LINES_TO_TAIL=20

mkdir -p "$LOG_DIR"
touch "$OUTPUT_FILE"

echo "--- Global Agent Status: $(date) ---" > "$OUTPUT_FILE"

# List of expected agent containers or folders
# We assume folders like `track-a`, `track-b` exist in the logs hub or parallel to the project.
# Since we are using `git worktree`, the folders are likely `../sprint-2.29/track-a`.
# Let's adjust to scan `docker ps` for any container with name containing `track-`.

echo "Scanning for active 'track-' containers..." >> "$OUTPUT_FILE"

CONTAINERS=$(docker ps --format "{{.ID}} {{.Names}}" | grep "track-")

if [ -z "$CONTAINERS" ]; then
    echo "No active track containers found." >> "$OUTPUT_FILE"
else
    echo "$CONTAINERS" | while read -r id name; do
        echo "[$name Status]" >> "$OUTPUT_FILE"
        echo "Container ID: $id" >> "$OUTPUT_FILE"
        
        # Check if healthy (if healthcheck exists)
        HEALTH=$(docker inspect --format='{{.State.Health.Status}}' "$id" 2>/dev/null)
        if [ "$HEALTH" ]; then
             echo "Health: $HEALTH" >> "$OUTPUT_FILE"
        fi

        echo "--- Recent Logs ---" >> "$OUTPUT_FILE"
        docker logs --tail $LINES_TO_TAIL "$id" >> "$OUTPUT_FILE" 2>&1
        
        echo -e "\n-----------------------------------\n" >> "$OUTPUT_FILE"
    done
fi

echo "Update complete. Architect can now read $OUTPUT_FILE"
