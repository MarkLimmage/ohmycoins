#! /usr/bin/env bash

set -e
set -x

# Ensure python is available
command -v python >/dev/null 2>&1 || { echo >&2 "Python not found"; exit 1; }

# Let the DB start
echo "Waiting for DB..."
python app/backend_pre_start.py || { echo "backend_pre_start.py failed with exit code $?"; exit 1; }

# Run migrations
echo "Running migrations..."
alembic upgrade head || { echo "alembic upgrade head failed with exit code $?"; exit 1; }

# Create initial data in DB
echo "Creating initial data..."
python app/initial_data.py || { echo "initial_data.py failed with exit code $?"; exit 1; }

echo "Prestart finished successfully"
exit 0
