# MyPy Technical Debt (Sprint 2.26)

This file lists the modules currently exempted from strict type checking to unblock `mypy` enforcement. Resolving these should be prioritized in upcoming tech debt sprints.

## 🧹 Debt Recovery Plan

To remove an ignore:
1. Delete `# mypy: ignore-errors` from the file header.
2. Run `docker run --rm -v $(pwd)/backend:/app backend:latest mypy --no-incremental path/to/file.py`.
3. Add missing type hints, fix null-safety issues (`Optional`), and resolve strict mode errors.

---

### 🟢 Low Complexity (Scripts & Utils)
*Status: ✅ Resolved*

### 🟡 Medium Complexity (Collectors & Integrations)
*Status: ✅ Resolved*

### 🔴 High Complexity (Agents & Trading Logic)
*Status: ✅ Resolved*

### ⚠️ API Routes (Validation)
*FastAPI routes often suffer from missing return type annotations (`-> Any`) or dependency injection complexity.*

- `backend/app/api/middleware/rate_limiting.py`
- `backend/app/api/routes/agent.py`
- `backend/app/api/routes/floor.py`
- `backend/app/api/routes/mock_ui.py`
- `backend/app/api/routes/risk.py`
- `backend/app/api/routes/trading.py`
- `backend/app/api/routes/websockets.py`
