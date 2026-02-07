# Migration Plan: Local Server Deployment

**Target Host**: 192.168.0.241 (Ubuntu/Linux)
**Start Date**: Immediate
**Goal**: Move all compute and data storage to valid local infrastructure to avoid cloud costs and latency.

---

## 🏃 Sprint 2.24: "Homecoming" (Infrastructure Migration)

### Objective
Establish the 192.168.0.241 server as the primary production environment and enable continuous delivery.

### Task List

#### 1. Server Preparation (Manual / One-off)
- [ ] **SSH Access**: Ensure you can SSH into `192.168.0.241` with sudo privileges.
- [ ] **Provisioning**: Copy and run the setup script:
    ```bash
    scp scripts/setup-local-server.sh user@192.168.0.241:~/
    ssh user@192.168.0.241 "chmod +x ~/setup-local-server.sh && ~/setup-local-server.sh"
    ```
- [ ] **GitHub Runner**: Install the GitHub Actions Runner on the server so it can receive builds.
    1. Go to GitHub Repo -> Settings -> Actions -> Runners -> New self-hosted runner.
    2. Choose Linux.
    3. Run the provided commands on the 192.168.0.241 server.
    4. Start the runner (recommend running as a service: `sudo ./svc.sh install && sudo ./svc.sh start`).

#### 2. Configuration Management
- [ ] **Secrets Migration**: Move `.env` secrets to GitHub Secrets (Repository Settings -> Secrets and variables -> Actions).
    - `POSTGRES_PASSWORD`, `SECRET_KEY`, `FIRST_SUPERUSER_PASSWORD`, etc. (See `.env.template`)
    - Create an Environment named `local-server` in GitHub if desired for approval gates.

#### 3. Deployment Pipeline
- [ ] **Verify Workflow**: Push a commit to `main`. The `.github/workflows/deploy-local.yml` workflow should pick it up.
- [ ] **Check Runner**: Ensure the self-hosted runner on 192.168.0.241 picks up the job.
- [ ] **Verify Services**:
    - `docker ps` on server.
    - `curl http://localhost:8000/api/v1/utils/health-check` on server.

#### 4. Data Migration (Optional)
- [ ] If existing data exists in AWS or another machine, dump and restore:
    ```bash
    # On source
    pg_dump -U postgres app > backup.sql
    # On 192.168.0.241
    cat backup.sql | docker compose exec -T db psql -U postgres app
    ```

---

## 🏃 Sprint 2.25: Local Optimization

### Objective
Tune the local server for performance now that it host the agents.

### Task List
- [ ] **Hardware Monitoring**: Install Prometheus/Grafana or Netdata on the local server.
- [ ] **Database Tuning**: Adjust Postgres `shared_buffers` for the specific RAM available on 192.168.0.241.
- [ ] **Local Model Hosting**: (If GPU available) Deploy Ollama or local LLM inference endpoint for agents to use.

---

## 🛠️ Immediate Action Items

1. **Run the Setup Script**: The `scripts/setup-local-server.sh` is ready.
2. **Install Runner**: Connect the server to GitHub.
3. **Push Code**: Trigger the first deployment.

