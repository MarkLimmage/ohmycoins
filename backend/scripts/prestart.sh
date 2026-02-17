#! /usr/bin/env bash

set -e
set -x

# Ensure python is available
command -v python >/dev/null 2>&1 || { echo >&2 "Python not found"; exit 1; }

# Let the DB start
python app/backend_pre_start.py

# Run migrations
alembic upgrade head

# Create initial data in DB
python app/initial_data.py

echo "Prestart finished successfully"
exit 0
