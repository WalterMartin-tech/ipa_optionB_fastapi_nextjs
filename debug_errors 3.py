import logging
import os
import traceback

from fastapi import Request
from fastapi.responses import JSONResponse


def setup(app):
    log = logging.getLogger("uvicorn.error")
    DEBUG_ERRORS = os.getenv("DEBUG_ERRORS", "0") == "1"

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception):
        tb = traceback.format_exc()
        log.error("Unhandled error on %s %s\n%s", request.method, request.url.path, tb)
        return JSONResponse(
            status_code=500,
            content={
                "detail": str(exc) if DEBUG_ERRORS else "internal_error",
                "trace": tb if DEBUG_ERRORS else None,
            },
        )
