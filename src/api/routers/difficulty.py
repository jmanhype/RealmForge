"""Difficulty adjustment API endpoints for Realm Forge."""

import uuid
from typing import Dict, Any, List

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from loguru import logger

from ...models.difficulty import DifficultyRequest, DifficultyResponse, DifficultySettings, PlayerPerformance
from ...services.difficulty import DifficultyService
from ...config.settings import Settings

# Initialize router
router = APIRouter(
    prefix="/difficulty",
    tags=["difficulty"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"},
    },
)

# Service and settings instances
difficulty_service = None
settings = Settings.get_settings()


async def get_difficulty_service() -> DifficultyService:
    """Get or initialize the difficulty service.
    
    Returns:
        DifficultyService: The difficulty service instance
    """
    global difficulty_service
    if difficulty_service is None:
        difficulty_service = await DifficultyService.create(
            llm_name=settings.llm.difficulty_llm,
            round_number=settings.aflow.difficulty_round
        )
    return difficulty_service


@router.post("/adjust", response_model=DifficultyResponse)
async def adjust_difficulty(
    request: DifficultyRequest,
    difficulty_service: DifficultyService = Depends(get_difficulty_service)
) -> DifficultyResponse:
    """Adjust difficulty based on player performance.
    
    Args:
        request: Difficulty adjustment request
        difficulty_service: Difficulty service instance
        
    Returns:
        DifficultyResponse: Adjusted difficulty settings
    """
    try:
        logger.info(f"Adjusting difficulty for player {request.player_id}")
        response = await difficulty_service.adjust_difficulty(request)
        logger.info(f"Generated {len(response.difficulty_settings)} difficulty settings, cost: ${response.cost:.4f}")
        return response
    except Exception as e:
        logger.error(f"Error adjusting difficulty: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error adjusting difficulty: {str(e)}"
        )


@router.post("/adjust/async")
async def adjust_difficulty_async(
    request: DifficultyRequest,
    background_tasks: BackgroundTasks,
    difficulty_service: DifficultyService = Depends(get_difficulty_service)
) -> Dict[str, Any]:
    """Adjust difficulty asynchronously.
    
    Args:
        request: Difficulty adjustment request
        background_tasks: FastAPI background tasks
        difficulty_service: Difficulty service instance
        
    Returns:
        Dict with request ID and status
    """
    request_id = str(uuid.uuid4())
    
    # Add task to background tasks
    background_tasks.add_task(
        difficulty_service.adjust_difficulty_async,
        request,
        request_id
    )
    
    return {
        "request_id": request_id,
        "status": "processing",
        "message": "Difficulty adjustment started"
    }


@router.get("/status/{request_id}")
async def get_difficulty_status(
    request_id: str,
    difficulty_service: DifficultyService = Depends(get_difficulty_service)
) -> Dict[str, Any]:
    """Get status of an asynchronous difficulty adjustment request.
    
    Args:
        request_id: ID of the request
        difficulty_service: Difficulty service instance
        
    Returns:
        Dict with status and result if available
    """
    return await difficulty_service.get_request_status(request_id)


@router.get("/settings/{player_id}")
async def get_player_difficulty_settings(
    player_id: str,
    difficulty_service: DifficultyService = Depends(get_difficulty_service)
) -> Dict[str, List[DifficultySettings]]:
    """Get difficulty settings for a player.
    
    Args:
        player_id: ID of the player
        difficulty_service: Difficulty service instance
        
    Returns:
        Dict with list of difficulty settings
    """
    try:
        settings = await difficulty_service.get_player_difficulty_settings(player_id)
        return {"difficulty_settings": settings}
    except Exception as e:
        logger.error(f"Error getting difficulty settings: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=f"Difficulty settings not found: {str(e)}"
        )


@router.post("/performance")
async def update_player_performance(
    player_id: str,
    performance: PlayerPerformance,
    difficulty_service: DifficultyService = Depends(get_difficulty_service)
) -> Dict[str, Any]:
    """Update player performance metrics.
    
    Args:
        player_id: ID of the player
        performance: Player performance metrics
        difficulty_service: Difficulty service instance
        
    Returns:
        Dict with status and updated metrics
    """
    try:
        updated = await difficulty_service.update_player_performance(player_id, performance)
        return {
            "status": "success",
            "player_id": player_id,
            "updated_metrics": updated
        }
    except Exception as e:
        logger.error(f"Error updating player performance: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error updating player performance: {str(e)}"
        )


@router.get("/recommendations/{player_id}")
async def get_difficulty_recommendations(
    player_id: str,
    content_type: str = None,
    difficulty_service: DifficultyService = Depends(get_difficulty_service)
) -> Dict[str, Any]:
    """Get difficulty recommendations for a player.
    
    Args:
        player_id: ID of the player
        content_type: Type of content for recommendations
        difficulty_service: Difficulty service instance
        
    Returns:
        Dict with difficulty recommendations
    """
    try:
        recommendations = await difficulty_service.get_recommendations(player_id, content_type)
        return {"recommendations": recommendations}
    except Exception as e:
        logger.error(f"Error getting difficulty recommendations: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting difficulty recommendations: {str(e)}"
        ) 