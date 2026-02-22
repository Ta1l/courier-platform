"""Run FastAPI admin server."""

from __future__ import annotations

import uvicorn

from api.app import app
from api.config import settings


if __name__ == "__main__":
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        log_level="info",
    )

