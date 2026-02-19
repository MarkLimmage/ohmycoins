#!/bin/bash
# Development startup script for Oh My Coins
# Ensures clean environment before starting Docker services

set -e

echo "🚀 Starting Oh My Coins Development Environment"
echo "=============================================="

# Check for required ports and kill conflicting processes
REQUIRED_PORTS=(5432 8000 8080 80 5173)

for port in "${REQUIRED_PORTS[@]}"; do
    echo "Checking port $port..."
    
    # Find PIDs using the port (excluding docker-proxy as we'll handle that with docker compose down)
    PIDS=$(lsof -ti :$port 2>/dev/null | grep -v "^$" || true)
    
    if [ ! -z "$PIDS" ]; then
        echo "⚠️  Port $port is in use by process(es): $PIDS"
        
        # Check if it's a docker-proxy process
        for pid in $PIDS; do
            PROCESS_NAME=$(ps -p $pid -o comm= 2>/dev/null || echo "unknown")
            if [[ "$PROCESS_NAME" == *"docker"* ]]; then
                echo "   Docker process detected on port $port - will clean with docker compose down"
            else
                echo "   Killing non-Docker process $pid ($PROCESS_NAME) on port $port"
                sudo kill -9 $pid 2>/dev/null || true
            fi
        done
    fi
done

echo ""
echo "🛑 Stopping any existing Docker containers..."
docker compose down 2>/dev/null || true

echo ""
echo "🗑️  Cleaning up Docker volumes (fresh start)..."
docker compose down -v 2>/dev/null || true

echo ""
echo "🏗️  Building backend image..."
docker compose build backend

echo ""
echo "🔧 Starting database..."
docker compose up -d db

echo ""
echo "⏳ Waiting for database to be healthy..."
sleep 8

echo ""
echo "📝 Creating database migrations..."
docker compose run --rm --no-deps backend alembic revision --autogenerate -m "Initial models" || {
    echo "⚠️  Migration creation failed or migration already exists"
}

# Copy migration files from container to host (if any were created)
docker compose cp backend:/app/app/alembic/versions/. backend/app/alembic/versions/ 2>/dev/null || true

echo ""
echo "⬆️  Applying database migrations..."
docker compose up -d db && sleep 5
docker compose exec backend alembic upgrade head || {
    echo "⚠️  Running migration in standalone container..."
    docker run --rm --network ohmycoins_default \
      -v $(pwd)/backend/app/alembic:/app/app/alembic \
      -e PROJECT_NAME="Oh My Coins (OMC!)" \
      -e POSTGRES_SERVER=ohmycoins-db-1 \
      -e POSTGRES_PORT=5432 \
      -e POSTGRES_DB=app \
      -e POSTGRES_USER=postgres \
      -e POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-postgres} \
      -e SECRET_KEY=${SECRET_KEY:-changethis} \
      -e FIRST_SUPERUSER=admin@example.com \
      -e FIRST_SUPERUSER_PASSWORD=changethis \
      backend:latest alembic upgrade head
}

echo ""
echo "👤 Creating initial superuser..."
docker compose exec backend python app/initial_data.py || {
    echo "⚠️  Running initial data in standalone container..."
    docker run --rm --network ohmycoins_default \
      -e PROJECT_NAME="Oh My Coins (OMC!)" \
      -e POSTGRES_SERVER=ohmycoins-db-1 \
      -e POSTGRES_PORT=5432 \
      -e POSTGRES_DB=app \
      -e POSTGRES_USER=postgres \
      -e POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-postgres} \
      -e SECRET_KEY=${SECRET_KEY:-changethis} \
      -e FIRST_SUPERUSER=admin@example.com \
      -e FIRST_SUPERUSER_PASSWORD=changethis \
      backend:latest python app/initial_data.py
}

echo ""
echo "🚀 Starting all services..."
docker compose up -d

echo ""
echo "✅ Development environment started successfully!"
echo ""
echo "Services available at:"
echo "  Backend API: http://localhost:8000"
echo "  Frontend:    http://localhost:5173"
echo "  Adminer:     http://localhost:8080"
echo "  API Docs:    http://localhost:8000/docs"
echo ""
echo "Default login:"
echo "  Email:    admin@example.com"
echo "  Password: changethis"
echo ""
echo "To view logs: docker compose logs -f"
echo "To stop:      docker compose down"
