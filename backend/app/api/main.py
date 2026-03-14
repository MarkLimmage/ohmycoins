from fastapi import APIRouter

from app.api.routes import (
    admin,
    agent,
    alerts,
    algorithms,
    backtests,
    collectors,
    credentials,
    enrichment,
    floor,
    login,
    pnl,
    private,
    risk,
    signals,
    strategy_promotions,
    trade_audit,
    trading,
    users,
    utils,
    websockets,
)
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(algorithms.router, prefix="/algorithms", tags=["algorithms"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
api_router.include_router(risk.router, prefix="/risk", tags=["risk"])
api_router.include_router(trade_audit.router, prefix="/audit", tags=["audit"])
api_router.include_router(websockets.router, prefix="/ws", tags=["websockets"])
api_router.include_router(
    credentials.router, prefix="/credentials/coinspot", tags=["credentials"]
)
api_router.include_router(agent.router, prefix="/lab/agent", tags=["agent"])
api_router.include_router(
    strategy_promotions.router, prefix="/promotions", tags=["promotions"]
)
api_router.include_router(pnl.router, prefix="/floor/pnl", tags=["pnl"])
api_router.include_router(trading.router, prefix="/floor/trading", tags=["trading"])
api_router.include_router(
    backtests.router, prefix="/floor/backtests", tags=["backtests"]
)
api_router.include_router(floor.router, prefix="/floor", tags=["floor"])
api_router.include_router(collectors.router, prefix="/collectors", tags=["collectors"])
api_router.include_router(enrichment.router, prefix="/enrichment", tags=["enrichment"])
api_router.include_router(signals.router, prefix="/signals", tags=["signals"])


if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)

    # Mock endpoints for UI component development (Storybook)
    from app.api.routes import mock_ui

    api_router.include_router(mock_ui.router, prefix="/mock", tags=["mock"])
