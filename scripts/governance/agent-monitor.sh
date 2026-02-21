#!/bin/bash
# agent-monitor.sh: Provides a "God View" of all running dev agent Docker containers.
# It dumps logs to disk for the Watchdog AND aggregates them for the Architect.

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
LINES_TO_TAIL=50

mkdir -p "$LOG_DIR"
touch "$OUTPUT_FILE"

echo "--- Global Agent Status: $(date) ---" > "$OUTPUT_FILE"

echo "Scanning for active 'track-' and 'ohmycoins-' (Main) containers..." >> "$OUTPUT_FILE"

# Find containers: Dev Tracks OR Main Project
CONTAINERS=$(docker ps --format "{{.ID}} {{.Names}}" | grep -E "track-|ohmycoins-")

if [ -z "$CONTAINERS" ]; then
    echo "No active track or main containers found." >> "$OUTPUT_FILE"
else
    echo "$CONTAINERS" | while read -r id name; do
        # 1. Ensure log directory exists specific to this container
        CONTAINER_LOG_DIR="$LOG_DIR/$name"
        mkdir -p "$CONTAINER_LOG_DIR"
        
        # 2. Dump logs to disk for Watchdog
        docker logs --tail $LINES_TO_TAIL "$id" > "$CONTAINER_LOG_DIR/session.log" 2>&1
        
        # 3. Aggregate for Architect View
        echo "[$name Status]" >> "$OUTPUT_FILE"
        echo "Container ID: $id" >> "$OUTPUT_FILE"
        
        # Check health if available
        HEALTH=$(docker inspect --format='{{.State.Health.Status}}' "$id" 2>/dev/null)
        if [ "$HEALTH" ]; then
             echo "Health: $HEALTH" >> "$OUTPUT_FILE"
        fi

        echo "--- Recent Logs ---" >> "$OUTPUT_FILE"
        # Since we just dumped them, read from file or direct
        cat "$CONTAINER_LOG_DIR/session.log" >> "$OUTPUT_FILE"
        
        echo -e "\n-----------------------------------\n" >> "$OUTPUT_FILE"
    done
fi

echo "Update complete. Logs dumped to $LOG_DIR and aggregated to $OUTPUT_FILE"
