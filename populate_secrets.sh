#!/bin/bash
# populate_secrets.sh
# Purpose: Initialize a new developer worktree with a secure .env file
# Usage: ./populate_secrets.sh <target-worktree-directory>

TARGET_DIR="$1"
# Hardcoded to user's home structure for security
SECRETS_FILE="$HOME/omc/secrets.safe"
TEMPLATE_FILE=".env.template"

if [ -z "$TARGET_DIR" ]; then
    echo "Usage: $0 <target-worktree-directory>"
    echo "Example: $0 ../omc-track-a"
    exit 1
fi

if [ ! -d "$TARGET_DIR" ]; then
    echo "Error: Directory $TARGET_DIR does not exist."
    echo "Please create the worktree first using: git worktree add $TARGET_DIR ..."
    exit 1
fi

if [ ! -f "$SECRETS_FILE" ]; then
    echo "Error: Master secrets file $SECRETS_FILE not found."
    echo "Please create $SECRETS_FILE with your API keys (e.g., COINSPOT_API_KEY=...)"
    exit 1
fi

echo "Initializing $TARGET_DIR..."

if [ ! -f "$TEMPLATE_FILE" ]; then
    echo "Warning: .env.template not found in current directory. Using default."
    touch "$TARGET_DIR/.env"
else
    echo "  - Copying .env.template to $TARGET_DIR/.env..."
    cp "$TEMPLATE_FILE" "$TARGET_DIR/.env"
fi

# Define port allocations based on track folder name
# Default ports to avoid collision
STACK="dev-$(date +%s)"
BACKEND_PORT=8000
DB_PORT=5432
FRONTEND_PORT=5173

if [[ "$TARGET_DIR" == *"track-a"* ]]; then
    STACK="track-a"
    BACKEND_PORT=8010
    DB_PORT=5433
    FRONTEND_PORT=3001
elif [[ "$TARGET_DIR" == *"track-b"* ]]; then
    STACK="track-b"
    BACKEND_PORT=8020
    DB_PORT=5434
    FRONTEND_PORT=3002
elif [[ "$TARGET_DIR" == *"track-c"* ]]; then
    STACK="track-c"
    BACKEND_PORT=8030
    DB_PORT=5435
    FRONTEND_PORT=3003
fi

echo "  - Configuring Track: $STACK"
echo "    Backend Port: $BACKEND_PORT"
echo "    DB Port: $DB_PORT"

# Update generic environment variables in the new .env
# Use | as delimiter for sed to handle URLs
sed -i "s|^PROJECT_NAME=.*|PROJECT_NAME=\"OMC $STACK\"|" "$TARGET_DIR/.env"
sed -i "s|^STACK_NAME=.*|STACK_NAME=$STACK|" "$TARGET_DIR/.env"
sed -i "s|^POSTGRES_PORT=.*|POSTGRES_PORT=$DB_PORT|" "$TARGET_DIR/.env"
sed -i "s|^FRONTEND_HOST=.*|FRONTEND_HOST=http://localhost:$FRONTEND_PORT|" "$TARGET_DIR/.env"

# Inject secrets from master file
echo "  - Injecting secrets from $SECRETS_FILE..."

while IFS='=' read -r key value || [ -n "$key" ]; do
    # Skip comments and empty lines
    [[ $key =~ ^#.* ]] && continue
    [[ -z $key ]] && continue
    
    # Trim whitespace
    key=$(echo "$key" | xargs)
    value=$(echo "$value" | xargs)

    if [ -n "$key" ] && [ -n "$value" ]; then
        # Check if key exists in target .env (even if commented out)
        if grep -q "^# $key=" "$TARGET_DIR/.env"; then
            # Uncomment and set value
            sed -i "s|^# $key=.*|$key=$value|" "$TARGET_DIR/.env"
        elif grep -q "^$key=" "$TARGET_DIR/.env"; then
            # Update existing value
            sed -i "s|^$key=.*|$key=$value|" "$TARGET_DIR/.env"
        else
            # Append if not found (optional, but safer to stick to template)
            echo "$key=$value" >> "$TARGET_DIR/.env"
        fi
    fi
done < "$SECRETS_FILE"

echo "Success! Worktree $TARGET_DIR is configured with secrets for $STACK."
