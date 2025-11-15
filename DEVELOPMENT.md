# Oh My Coins (OMC!) - Development Setup

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Git

### Initial Setup

1. **Start the development environment:**
   ```bash
   ./scripts/dev-start.sh
   ```

   This script will:
   - Check and clean up any ports in use
   - Start all Docker services
   - Create database migrations
   - Initialize the database
   - Create the default superuser

2. **Access the services:**
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Frontend: http://localhost:5173
   - Adminer (DB): http://localhost:8080

3. **Default credentials:**
   - Email: `admin@example.com`
   - Password: `changethis`

### Common Commands

```bash
# View logs
docker compose logs -f

# Stop services
docker compose down

# Restart fresh (removes all data)
docker compose down -v
./scripts/dev-start.sh

# Run backend commands
docker compose exec backend alembic upgrade head
docker compose exec backend python app/initial_data.py

# Access database
docker compose exec db psql -U postgres -d app
```

## Project Structure

```
ohmycoins/
├── backend/          # FastAPI backend application
│   ├── app/
│   │   ├── api/      # API endpoints
│   │   ├── core/     # Core configuration
│   │   ├── models.py # Database models
│   │   └── ...
│   └── tests/
├── frontend/         # Vue.js frontend application
├── scripts/          # Development scripts
└── docker-compose.yml
```

## Development Workflow

### Live Code Reloading

The development environment uses **volume mounts** for live code reloading:

**Backend** (`docker-compose.override.yml`):
```yaml
volumes:
  - ./backend/app:/app/app          # Live reload for code changes
  - ./backend/alembic.ini:/app/alembic.ini
```

This means:
- ✅ Code changes in `backend/app/` are immediately reflected in the running container
- ✅ No need to rebuild after editing Python files
- ✅ FastAPI's `--reload` flag automatically restarts on changes
- ⚠️  New dependencies require rebuilding: `docker compose build backend`

### Making Database Changes

1. Modify models in `backend/app/models.py`
2. Generate migration:
   ```bash
   docker compose exec backend alembic revision --autogenerate -m "Description"
   ```
3. Apply migration:
   ```bash
   docker compose exec backend alembic upgrade head
   ```

### Running Tests

```bash
# Backend tests
docker compose exec backend pytest

# Frontend tests  
docker compose exec frontend npm run test
```

## Next Steps

See [ROADMAP.md](ROADMAP.md) for the full development plan.
