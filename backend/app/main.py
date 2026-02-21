# mypy: ignore-errors
import asyncio
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from sqlmodel import Session
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.cors import CORSMiddleware

from app.api.main import api_router
from app.api.middleware import RateLimitMiddleware
from app.api.routes import websockets
from app.core.config import settings
from app.core.db import engine
from app.services.collectors.config import (
    setup_collectors,
    start_collection,
    stop_collection,
)
from app.services.scheduler import start_scheduler, stop_scheduler
from app.services.trading.executor import get_order_queue
from app.services.trading.scheduler import get_execution_scheduler


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Application lifespan manager for startup and shutdown events"""
    # Startup: Start the data collection scheduler
    await start_scheduler()

    # Startup: Start Phase 2.5 Data Collectors
    setup_collectors()
    start_collection()

    # Initialize and start Order Queue
    executor_session = Session(engine)
    queue = get_order_queue()
    # Use system settings for keys. In a multi-user system, the executor should
    # resolve credentials per order, but for now we initialize with system/default keys.
    queue.initialize(
        session=executor_session,
        api_key=settings.COINSPOT_API_KEY,
        api_secret=settings.COINSPOT_API_SECRET or "placeholder_secret_for_ghost_mode",
    )
    queue_task = asyncio.create_task(queue.start())

    # Initialize and start Execution Scheduler (Strategies)
    # Using the same session as the queue for now (or create another if needed)
    execution_scheduler = get_execution_scheduler(
        session=executor_session,
        api_key=settings.COINSPOT_API_KEY,
        api_secret=settings.COINSPOT_API_SECRET or "placeholder_secret_for_ghost_mode",
    )

    # Start scheduler FIRST so it can accept jobs
    execution_scheduler.start()

    # Load any active "Live" algorithms from the database
    execution_scheduler.load_deployed_algorithms()

    yield

    # Shutdown: Stop Phase 2.5 Collectors
    stop_collection()

    # Shutdown: Stop the scheduler gracefully
    await stop_scheduler()

    # Stop Execution Scheduler
    execution_scheduler.stop()

    # Stop Order Queue
    await queue.stop()
    executor_session.close()
    if not queue_task.done():
        queue_task.cancel()
        try:
            await queue_task
        except asyncio.CancelledError:
            pass


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
    sentry_sdk.init(dsn=str(settings.SENTRY_DSN), enable_tracing=True)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
    lifespan=lifespan,
)

# Set all CORS enabled origins
if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Add rate limiting middleware
if settings.RATE_LIMIT_ENABLED:
    app.add_middleware(RateLimitMiddleware)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(_request: Request, exc: StarletteHTTPException):
    """
    Global exception handler to ensure standard error response format.
    Returns: { "message": "User-facing", "detail": "Technical", "error_code": "CODE" }
    """
    # If detail is already a dict, assume it follows the structure
    if isinstance(exc.detail, dict):
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail,
        )

    # Map common status codes to user messages per API_CONTRACTS.md
    user_message = "An unexpected error occurred."
    error_code = f"HTTP_{exc.status_code}"

    if exc.status_code == 400:
        user_message = "Invalid request. Please check your input."
        error_code = "BAD_REQUEST"
    elif exc.status_code == 401:
        user_message = "Session expired. Please log in again."
        error_code = "UNAUTHORIZED"
    elif exc.status_code == 403:
        user_message = "You don't have permission for this action."
        error_code = "FORBIDDEN"
    elif exc.status_code == 404:
        user_message = "The requested resource was not found."
        error_code = "NOT_FOUND"
    elif exc.status_code == 429:
        user_message = "Too many requests. Please wait a moment."
        error_code = "RATE_LIMITED"
    elif exc.status_code >= 500:
        user_message = "Something went wrong. Please try again later."
        error_code = "SERVER_ERROR"

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "message": user_message,
            "detail": str(exc.detail),
            "error_code": error_code,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request: Request, exc: RequestValidationError):
    """
    Handle 422 Validation Errors
    """
    return JSONResponse(
        status_code=422,
        content=jsonable_encoder(
            {
                "message": "Some fields have errors. Please check your input.",
                "detail": exc.errors(),
                "error_code": "VALIDATION_ERROR",
            }
        ),
    )


app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(websockets.router, prefix="/ws", tags=["websockets"])
