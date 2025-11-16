from fastapi import APIRouter

from app.api.routes import agent, credentials, items, login, private, users, utils
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(items.router)
api_router.include_router(credentials.router, prefix="/credentials/coinspot", tags=["credentials"])
api_router.include_router(agent.router, prefix="/lab/agent", tags=["agent"])


if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
