"""Router for visualization endpoints in Realm Forge."""

from typing import Dict, Any, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from loguru import logger

from ...services.visualization import VisualizationService
from ...models.visualization import (
    SceneRequest,
    SceneResponse,
    CharacterRequest,
    CharacterResponse,
    SceneTemplateRequest,
    SceneTemplateResponse
)
from ...config import get_settings
from ..dependencies import get_visualization_service

router = APIRouter(
    prefix="/visualization",
    tags=["visualization"],
    responses={404: {"description": "Not found"},
               500: {"description": "Internal server error"}}
)

@router.post("/scene", response_model=SceneResponse)
async def generate_scene(
    request: SceneRequest,
    visualization_service: VisualizationService = Depends(get_visualization_service)
) -> SceneResponse:
    """Generate a Three.js scene based on request.
    
    Args:
        request: Scene generation request
        visualization_service: Visualization service instance
        
    Returns:
        Generated scene response
    """
    try:
        logger.info(f"Generating scene for location {request.location_id}")
        response = await visualization_service.generate_scene(request)
        return response
    except Exception as e:
        logger.error(f"Error generating scene: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Scene generation failed: {str(e)}"
        )

@router.post("/character", response_model=CharacterResponse)
async def generate_character(
    request: CharacterRequest,
    visualization_service: VisualizationService = Depends(get_visualization_service)
) -> CharacterResponse:
    """Generate a Three.js character model based on request.
    
    Args:
        request: Character generation request
        visualization_service: Visualization service instance
        
    Returns:
        Generated character response
    """
    try:
        logger.info(f"Generating character model for {request.character_id}")
        response = await visualization_service.generate_character_model(request)
        return response
    except Exception as e:
        logger.error(f"Error generating character model: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Character generation failed: {str(e)}"
        )

@router.post("/template", response_model=SceneTemplateResponse)
async def get_scene_template(
    request: SceneTemplateRequest,
    visualization_service: VisualizationService = Depends(get_visualization_service)
) -> SceneTemplateResponse:
    """Get a Three.js scene template based on request.
    
    Args:
        request: Template request
        visualization_service: Visualization service instance
        
    Returns:
        Scene template response
    """
    try:
        logger.info(f"Getting scene template: {request.template_type}")
        response = await visualization_service.get_scene_template(request)
        return response
    except Exception as e:
        logger.error(f"Error getting scene template: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Template retrieval failed: {str(e)}"
        )

@router.get("/quality-presets")
async def get_quality_presets(
    visualization_service: VisualizationService = Depends(get_visualization_service)
) -> Dict[str, Any]:
    """Get available quality presets for scene generation.
    
    Args:
        visualization_service (VisualizationService): The visualization service.
        
    Returns:
        Dict[str, Any]: The available quality presets.
        
    Raises:
        HTTPException: If preset retrieval fails.
    """
    try:
        return visualization_service.quality_presets
    except Exception as e:
        logger.error(f"Failed to get quality presets: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get quality presets: {str(e)}"
        ) 