"""Main FastAPI application for Realm Forge."""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
import time
from typing import Dict, Any
import os
from pathlib import Path
from fastapi.staticfiles import StaticFiles

from ..config import get_settings
from .routers import narrative, world, npc, difficulty, optimizer, visualization

# Create settings instance
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="Realm Forge API",
    description="API for the procedurally generated RPG with AI-driven content",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add middleware for request logging and timing
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log request information and timing.
    
    Args:
        request: The incoming request
        call_next: Next middleware function
        
    Returns:
        The response from the next middleware
    """
    start_time = time.time()
    
    # Get client IP and request details
    client_host = request.client.host if request.client else "unknown"
    method = request.method
    url = str(request.url)
    
    logger.info(f"Request started: {method} {url} from {client_host}")
    
    # Process the request
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Log response details
        logger.info(f"Request completed: {method} {url} - Status: {response.status_code} - Duration: {process_time:.4f}s")
        
        # Add processing time header
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
    except Exception as e:
        # Log exception
        process_time = time.time() - start_time
        logger.error(f"Request failed: {method} {url} - Error: {str(e)} - Duration: {process_time:.4f}s")
        
        # Return error response
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error", "error": str(e)},
        )

# Import and include routers
app.include_router(narrative.router)
app.include_router(world.router)
app.include_router(npc.router)
app.include_router(difficulty.router)
app.include_router(optimizer.router)
app.include_router(visualization.router)

# Root endpoint
@app.get("/", tags=["root"])
async def root() -> Dict[str, Any]:
    """Root endpoint with API information.
    
    Returns:
        Dict with API information
    """
    return {
        "name": "Realm Forge API",
        "version": "0.1.0",
        "description": "API for the procedurally generated RPG with AI-driven content",
        "documentation": "/docs",
    }

# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check() -> Dict[str, Any]:
    """Health check endpoint.
    
    Returns:
        Dict with health status
    """
    return {
        "status": "ok",
        "api_version": "0.1.0",
        "config": {
            "debug": settings.api.debug,
            "narrative_llm": settings.llm.narrative_llm,
            "world_llm": settings.llm.world_llm,
            "npc_llm": settings.llm.npc_llm,
            "difficulty_llm": settings.llm.difficulty_llm,
        },
        "timestamp": time.time()
    }

# Mount static files
static_dir = Path(__file__).parent.parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Add frontend route
@app.get("/visualizer")
async def visualizer():
    """Redirect to the visualizer interface."""
    from fastapi.responses import HTMLResponse
    
    html_file = static_dir / "index.html"
    if html_file.exists():
        with open(html_file, "r") as f:
            content = f.read()
        return HTMLResponse(content=content)
    else:
        return {"error": "Visualizer not found"} 