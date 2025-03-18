"""Main entry point for the Realm Forge API server."""

import uvicorn
from .app import app, settings

if __name__ == "__main__":
    uvicorn.run(
        "src.api.app:app",
        host=settings.api.host,
        port=settings.api.port,
        workers=settings.api.workers,
        reload=settings.api.debug
    ) 