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
- ⚠️  New dependencies require rebuilding (see below)

### Adding New Dependencies

When you add new Python packages to `pyproject.toml`:

1. **Rebuild the Docker image without cache:**
   ```bash
   docker compose build --no-cache backend
   ```

2. **Stop and restart the backend** (not just `restart`):
   ```bash
   docker compose stop backend
   docker compose up -d backend
   ```

**Why this is necessary:**
- Volume mounts provide live code changes but don't install Python packages
- `docker compose restart` may use cached layers from the old image
- A full stop/start cycle ensures the newly built image is used
- Without `--no-cache`, Docker may skip the package installation step

**Example workflow:**
```bash
# After adding 'apscheduler = "^3.10.4"' to pyproject.toml
docker compose build --no-cache backend
docker compose stop backend
docker compose up -d backend

# Verify the package is installed
docker compose logs backend --tail=20
```

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

## AWS Infrastructure for CI/CD

The project includes infrastructure for running GitHub Actions workflows on self-hosted runners in AWS EKS with intelligent autoscaling. This provides:

- **Controlled Environment**: Run CI/CD in a managed Kubernetes cluster
- **AWS Integration**: Direct access to AWS resources
- **Cost Optimization**: Scale-to-zero capability with runner nodes (40-60% cost savings)
- **Better Performance**: Dedicated compute resources with automatic scaling
- **High Availability**: Separate system and runner node groups for workload isolation

### Architecture Highlights

**Two-Node-Group Strategy:**
- **system-nodes**: Always-on group (1× t3.medium) hosting critical Kubernetes components
- **arc-runner-nodes**: Scalable group (0-10× t3.large) dedicated to GitHub Actions runners
  - Scales to **zero** when no workflows are running (major cost savings!)
  - Automatically provisions nodes when jobs are queued
  - Scales back down after jobs complete

**Cost Impact:**
- Baseline cost reduced by 15-30% compared to always-on configuration
- Runner nodes only incur costs during active CI/CD workflows
- Cluster Autoscaler optimizes resource utilization automatically

### Setting Up AWS EKS Test Server

See the comprehensive guides in `infrastructure/aws/eks/`:

1. **[README.md](infrastructure/aws/eks/README.md)** - Overview and quick start
2. **[STEP0_CREATE_CLUSTER.md](infrastructure/aws/eks/STEP0_CREATE_CLUSTER.md)** - Create EKS cluster with new VPC
3. **[STEP1_INSTALL_ARC.md](infrastructure/aws/eks/STEP1_INSTALL_ARC.md)** - Install Actions Runner Controller
4. **[STEP2_UPDATE_WORKFLOWS.md](infrastructure/aws/eks/STEP2_UPDATE_WORKFLOWS.md)** - Update workflows to use self-hosted runners
5. **[EKS_AUTOSCALING_CONFIGURATION.md](infrastructure/aws/eks/EKS_AUTOSCALING_CONFIGURATION.md)** - Autoscaling architecture and troubleshooting

**Quick Start:**
```bash
# 1. Create EKS cluster with two node groups (~20 minutes)
cd infrastructure/aws/eks
eksctl create cluster -f eks-cluster-new-vpc.yml

# 2. Install Actions Runner Controller (~10 minutes)
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.3/cert-manager.yaml
helm repo add actions-runner-controller https://actions-runner-controller.github.io/actions-runner-controller
helm install arc --namespace actions-runner-system --create-namespace actions-runner-controller/actions-runner-controller

# 3. Deploy runners with autoscaling
kubectl apply -f arc-manifests/runner-deployment.yaml
kubectl apply -f arc-manifests/cluster-autoscaler.yaml

# 4. Verify autoscaling is operational
kubectl get nodes  # Should show 1 system node, 0 runner nodes initially
kubectl get pods -n kube-system -l app=cluster-autoscaler  # Cluster Autoscaler running
```

**What Happens When Workflows Run:**
1. GitHub Actions workflow triggers
2. Runner pod is created but remains Pending (no nodes available)
3. Cluster Autoscaler detects pending pod and provisions a runner node (~2-3 minutes)
4. Runner pod schedules and executes workflow
5. After job completes, node scales back to zero (~10 minutes idle time)

## Next Steps

See [ROADMAP.md](ROADMAP.md) for the full development plan.
