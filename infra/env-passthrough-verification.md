# Collector API Key Pass-Through Verification

**Status: VERIFIED - No changes required to docker-compose.yml**

---

## Analysis

### How `env_file` Works in Docker Compose

The `env_file: - .env` directive in docker-compose.yml loads **all** variables from `.env`
into the container's environment. This is equivalent to passing every key-value pair from
`.env` as an explicit `-e KEY=VALUE` flag.

The explicit `environment:` block is used to:
1. **Override** values from `env_file` (e.g., `POSTGRES_SERVER=db` overrides the `.env` default of `localhost`)
2. **Force failure** if required vars are unset (e.g., `${SECRET_KEY?Variable not set}`)
3. **Set service-specific flags** (e.g., `RUN_COLLECTORS=True` on orchestrator, `False` on backend)

### Services with `env_file: - .env`

The following services ALL have `env_file: - .env`:
- `db`
- `prestart`
- `backend`
- `orchestrator`
- `watcher`
- `celery_worker`

This means **all variables from `.env` are available** in all these containers.

---

## Collector API Keys — Verdict

| Variable | In `.env.template` | In `Settings` (config.py) | How collector reads it |
|---|---|---|---|
| `CRYPTOPANIC_API_KEY` | Yes | **No** (not in Settings class) | `os.getenv("CRYPTOPANIC_API_KEY")` directly |
| `NEWSCATCHER_API_KEY` | Yes | Yes (`str | None = None`) | `os.getenv("NEWSCATCHER_API_KEY")` directly |
| `NANSEN_API_KEY` | Yes | Yes (`str | None = None`) | `os.getenv("NANSEN_API_KEY")` directly |
| `COINSPOT_USE_WEB_SCRAPING` | Yes | Yes (`bool = False`) | Via `settings.COINSPOT_USE_WEB_SCRAPING` |

All collector classes (`CryptoPanicCollector`, `NewscatcherCollector`, `NansenCollector`) read
their API keys directly from `os.getenv()`, not from the `Settings` pydantic model. Since
`env_file: - .env` is present on all backend services, these environment variables ARE available
in containers.

**Explicit `environment:` entries for these keys are redundant and NOT needed.**

---

## Gap Found: CRYPTOPANIC_API_KEY Missing from Settings

`CRYPTOPANIC_API_KEY` is used in two places:
- `backend/app/services/collectors/human/cryptopanic.py` — via `os.getenv("CRYPTOPANIC_API_KEY")`
- `backend/app/utils/seed_data.py` — via `os.getenv("CRYPTOPANIC_API_KEY", "free")`

But it is **not declared** in `Settings` (config.py), while `NEWSCATCHER_API_KEY` and
`NANSEN_API_KEY` are.

This inconsistency is cosmetic (it works via `os.getenv`), but it's tracked as task #3 to ensure
all collector API keys are centralized in `Settings`.

---

## docker-compose.yml Assessment

### Current State: CORRECT

- `orchestrator` service: has `env_file: - .env` + `RUN_COLLECTORS=True` — collectors run, API keys available
- `backend` service: has `env_file: - .env` + `RUN_COLLECTORS=False` — collectors disabled, keys irrelevant
- `celery_worker` service: has `env_file: - .env` + `RUN_COLLECTORS=False` — same

### No Changes Required

The docker-compose.yml correctly passes all collector API keys to containers via `env_file`.
Adding explicit `environment:` entries for `CRYPTOPANIC_API_KEY`, `NEWSCATCHER_API_KEY`,
`NANSEN_API_KEY`, and `COINSPOT_USE_WEB_SCRAPING` would be redundant (though harmless).

---

## Pre-boot Checklist

Before running `docker compose up`:

- [ ] `traefik-public` external Docker network exists: `docker network create traefik-public || true`
- [ ] `.env` file exists at project root with all required variables populated
- [ ] `.env` contains `CRYPTOPANIC_API_KEY`, `NEWSCATCHER_API_KEY`, `NANSEN_API_KEY`
- [ ] `DOCKER_IMAGE_BACKEND` and `DOCKER_IMAGE_FRONTEND` are set in `.env`
- [ ] `SECRET_KEY`, `POSTGRES_PASSWORD`, `FIRST_SUPERUSER_PASSWORD` are set

See `/infra/README.md` for full startup commands.
