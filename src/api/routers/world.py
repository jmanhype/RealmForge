"""World generation API endpoints for Realm Forge."""

import uuid
from typing import Dict, Any, List

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from loguru import logger

from ...models.world import WorldRequest, WorldResponse, WorldLocation
from ...services.world import WorldService
from ...config.settings import Settings

# Initialize router
router = APIRouter(
    prefix="/world",
    tags=["world"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"},
    },
)

# Service and settings instances
world_service = None
settings = Settings.get_settings()


async def get_world_service() -> WorldService:
    """Get or initialize the world service.
    
    Returns:
        WorldService: The world service instance
    """
    global world_service
    if world_service is None:
        world_service = await WorldService.create(
            llm_name=settings.llm.world_llm,
            round_number=settings.aflow.world_round
        )
    return world_service


@router.post("/generate", response_model=WorldResponse)
async def generate_world(
    request: WorldRequest,
    world_service: WorldService = Depends(get_world_service)
) -> WorldResponse:
    """Generate world content based on player context.
    
    Args:
        request: World generation request
        world_service: World service instance
        
    Returns:
        WorldResponse: Generated world content
    """
    try:
        logger.info(f"Generating world content for player {request.player_id}")
        response = await world_service.generate_world(request)
        logger.info(f"Generated world with {len(response.locations)} locations, cost: ${response.cost:.4f}")
        return response
    except Exception as e:
        logger.error(f"Error generating world: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating world: {str(e)}"
        )


@router.post("/generate/async")
async def generate_world_async(
    request: WorldRequest,
    background_tasks: BackgroundTasks,
    world_service: WorldService = Depends(get_world_service)
) -> Dict[str, Any]:
    """Generate world content asynchronously.
    
    Args:
        request: World generation request
        background_tasks: FastAPI background tasks
        world_service: World service instance
        
    Returns:
        Dict with request ID and status
    """
    request_id = str(uuid.uuid4())
    
    # Add task to background tasks
    background_tasks.add_task(
        world_service.generate_world_async,
        request,
        request_id
    )
    
    return {
        "request_id": request_id,
        "status": "processing",
        "message": "World generation started"
    }


@router.get("/status/{request_id}")
async def get_world_status(
    request_id: str,
    world_service: WorldService = Depends(get_world_service)
) -> Dict[str, Any]:
    """Get status of an asynchronous world generation request.
    
    Args:
        request_id: ID of the request
        world_service: World service instance
        
    Returns:
        Dict with status and result if available
    """
    return await world_service.get_request_status(request_id)


@router.get("/location/{location_id}")
async def get_location(
    location_id: str,
    player_id: str,
    world_service: WorldService = Depends(get_world_service)
) -> WorldLocation:
    """Get details for a specific location.
    
    Args:
        location_id: ID of the location
        player_id: ID of the player
        world_service: World service instance
        
    Returns:
        WorldLocation: Location details
    """
    try:
        location = await world_service.get_location(location_id, player_id)
        return location
    except Exception as e:
        logger.error(f"Error getting location: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=f"Location not found: {str(e)}"
        )


@router.get("/connected/{location_id}")
async def get_connected_locations(
    location_id: str,
    player_id: str,
    world_service: WorldService = Depends(get_world_service)
) -> Dict[str, List[WorldLocation]]:
    """Get connected locations for a specific location.
    
    Args:
        location_id: ID of the location
        player_id: ID of the player
        world_service: World service instance
        
    Returns:
        Dict with list of connected locations
    """
    try:
        locations = await world_service.get_connected_locations(location_id, player_id)
        return {"connected_locations": locations}
    except Exception as e:
        logger.error(f"Error getting connected locations: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=f"Error getting connected locations: {str(e)}"
        ) 