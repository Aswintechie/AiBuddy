"""
app.py - aiohttp web server entry point for AiBuddy.

Exposes three HTTP endpoints:
  POST /api/messages  — Microsoft Bot Framework message handler
  GET  /health        — Liveness probe (used by Koyeb)
  GET  /              — Alias for /health

Architecture decisions:
- BotFrameworkAdapter handles authentication (JWT validation) and serialisation.
- The on_turn_error callback is the single place where unexpected errors are
  caught, logged, and converted into user-friendly messages.
- aiohttp was chosen over Flask/FastAPI because botbuilder-integration-aiohttp
  provides a first-class adapter integration that handles the request/response
  lifecycle correctly with async activity processing.
"""

import json
import logging
import sys
import traceback
from typing import Callable

from aiohttp import web
from aiohttp.web import Request, Response, json_response
from botbuilder.core import BotFrameworkAdapterSettings, BotFrameworkAdapter
from botbuilder.schema import Activity

from bot import AiBuddyBot
from config import Config

# ---------------------------------------------------------------------------
# Logging setup – done before anything else so all modules inherit the config
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,  # Overridden below once Config is loaded
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Load configuration
# ---------------------------------------------------------------------------

try:
    CONFIG = Config()
except ValueError as cfg_err:
    logger.critical("Configuration error: %s", cfg_err)
    sys.exit(1)

# Apply the configured log level to the root logger
logging.getLogger().setLevel(getattr(logging, CONFIG.LOG_LEVEL, logging.INFO))

# ---------------------------------------------------------------------------
# Bot Framework adapter
# ---------------------------------------------------------------------------

SETTINGS = BotFrameworkAdapterSettings(CONFIG.APP_ID, CONFIG.APP_PASSWORD)
ADAPTER = BotFrameworkAdapter(SETTINGS)


async def on_turn_error(turn_context, error: Exception) -> None:
    """Global error handler for unexpected exceptions during a bot turn.

    Logs the full traceback server-side while returning a friendly message
    to the user so that internal details are never exposed.

    Args:
        turn_context: The current turn context.
        error: The exception that was raised.
    """
    logger.error(
        "Unhandled exception in bot turn:\n%s",
        "".join(traceback.format_exception(type(error), error, error.__traceback__)),
    )
    # Notify the user without leaking implementation details
    from botbuilder.core import MessageFactory  # local import to avoid circular

    await turn_context.send_activity(
        MessageFactory.text("Sorry, something went wrong. Please try again.")
    )


ADAPTER.on_turn_error = on_turn_error  # type: ignore[assignment]

# ---------------------------------------------------------------------------
# Bot instance
# ---------------------------------------------------------------------------

BOT = AiBuddyBot(CONFIG)

# ---------------------------------------------------------------------------
# Route handlers
# ---------------------------------------------------------------------------


async def messages(req: Request) -> Response:
    """Handle POST /api/messages — the main Bot Framework endpoint.

    Validates the Content-Type, deserialises the activity, and delegates
    processing to the adapter which authenticates the request and calls the
    bot's turn handler.

    Args:
        req: The incoming aiohttp request.

    Returns:
        An aiohttp Response (204 No Content on success, or an error response).
    """
    if "application/json" not in req.content_type:
        return Response(status=415, text="Unsupported Media Type: expected application/json")

    body = await req.json()
    activity = Activity().deserialize(body)
    auth_header: str = req.headers.get("Authorization", "")

    try:
        response = await ADAPTER.process_activity(activity, auth_header, BOT.on_turn)
        if response:
            return json_response(data=response.body, status=response.status)
        return Response(status=201)
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Error processing activity: %s", exc, exc_info=True)
        return Response(status=500, text="Internal Server Error")


async def health(_req: Request) -> Response:
    """Handle GET /health — liveness probe for Koyeb and monitoring tools.

    Args:
        _req: The incoming aiohttp request (unused).

    Returns:
        200 JSON response with service metadata.
    """
    return json_response(
        {"status": "ok", "service": "AiBuddy", "version": "1.0.0"}
    )


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------


def create_app() -> web.Application:
    """Build and return the configured aiohttp Application.

    Returns:
        A ready-to-run :class:`aiohttp.web.Application` instance.
    """
    app = web.Application()
    app.router.add_post("/api/messages", messages)
    app.router.add_get("/health", health)
    app.router.add_get("/", health)  # Root alias for convenience
    return app


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    try:
        logger.info("Starting AiBuddy bot...")
        logger.info("Listening on port %d", CONFIG.PORT)
        logger.info("Bot endpoint : POST http://0.0.0.0:%d/api/messages", CONFIG.PORT)
        logger.info("Health check : GET  http://0.0.0.0:%d/health", CONFIG.PORT)
        logger.info("AI model     : %s", CONFIG.GROQ_MODEL)

        web.run_app(
            create_app(),
            host="0.0.0.0",
            port=CONFIG.PORT,
        )
    except Exception as startup_err:  # pylint: disable=broad-except
        logger.critical("Failed to start AiBuddy: %s", startup_err, exc_info=True)
        sys.exit(1)
