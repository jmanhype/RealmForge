"""Router for narrative generation endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from typing import Dict, List, Any

from ...services.narrative import NarrativeService
from ...models.narrative import (
    NarrativeRequest,
    NarrativeResponse,
    NarrativeContext,
    NarrativeElement
)
from ..dependencies import get_narrative_service

router = APIRouter(
    prefix="/narrative",
    tags=["narrative"],
    responses={404: {"description": "Not found"}}
)


@router.post("/generate")
async def generate_narrative(
    request: NarrativeRequest,
    narrative_service: NarrativeService = Depends(get_narrative_service)
) -> NarrativeResponse:
    """Generate narrative content based on request.
    
    Args:
        request: Narrative generation request
        narrative_service: Narrative service instance
        
    Returns:
        Generated narrative response
    """
    try:
        response = await narrative_service.process_narrative_request(request)
        return response
    except Exception as e:
        logger.error(f"Error generating narrative: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Narrative generation failed: {str(e)}"
        )


@router.get("/elements/{player_id}")
async def get_narrative_elements(
    player_id: str,
    narrative_service: NarrativeService = Depends(get_narrative_service)
) -> Dict[str, List[NarrativeElement]]:
    """Get narrative elements for a player.
    
    Args:
        player_id: ID of the player
        narrative_service: Narrative service instance
        
    Returns:
        Dict with list of narrative elements
    """
    try:
        elements = await narrative_service.get_player_narrative_elements(player_id)
        return {"narrative_elements": elements}
    except Exception as e:
        logger.error(f"Error getting narrative elements: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=f"Narrative elements not found: {str(e)}"
        )


@router.get("/context/{player_id}")
async def get_narrative_context(
    player_id: str,
    narrative_service: NarrativeService = Depends(get_narrative_service)
) -> Dict[str, NarrativeContext]:
    """Get narrative context for a player.
    
    Args:
        player_id: ID of the player
        narrative_service: Narrative service instance
        
    Returns:
        Dict with narrative context
    """
    try:
        context = await narrative_service.get_player_narrative_context(player_id)
        return {"narrative_context": context}
    except Exception as e:
        logger.error(f"Error getting narrative context: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=f"Narrative context not found: {str(e)}"
        ) 