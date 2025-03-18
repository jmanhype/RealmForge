"""Router for NPC generation and interaction endpoints."""

from fastapi import APIRouter, HTTPException, Depends
from loguru import logger
from typing import Dict, List, Any

from ...models.npc import (
    NPCRequest,
    NPCResponse,
    NPCDetails,
    NPCInteractionRequest,
    NPCInteraction
)
from ...services.npc import NPCService
from ..dependencies import get_npc_service

router = APIRouter(
    prefix="/npc",
    tags=["npc"],
    responses={404: {"description": "Not found"}}
)


@router.post("/generate", response_model=NPCResponse)
async def generate_npc(
    request: NPCRequest,
    npc_service: NPCService = Depends(get_npc_service)
) -> NPCResponse:
    """Generate an NPC based on request.
    
    Args:
        request: NPC generation request
        npc_service: NPC service instance
        
    Returns:
        Generated NPC response
    """
    try:
        logger.info(f"Generating NPC for player {request.player_id}")
        response = await npc_service.generate_npc(request)
        return response
    except Exception as e:
        logger.error(f"Error generating NPC: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"NPC generation failed: {str(e)}"
        )


@router.post("/generate/async")
async def generate_npc_async(
    request: NPCRequest,
    npc_service: NPCService = Depends(get_npc_service)
) -> Dict[str, Any]:
    """Generate an NPC asynchronously.
    
    Args:
        request: NPC generation request
        npc_service: NPC service instance
        
    Returns:
        Dict with request ID and status
    """
    try:
        response = await npc_service.generate_npc_async(request)
        return response
    except Exception as e:
        logger.error(f"Error starting async NPC generation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Async NPC generation failed: {str(e)}"
        )


@router.get("/status/{request_id}")
async def get_npc_status(
    request_id: str,
    npc_service: NPCService = Depends(get_npc_service)
) -> Dict[str, Any]:
    """Get status of an async NPC generation request.
    
    Args:
        request_id: ID of the request
        npc_service: NPC service instance
        
    Returns:
        Dict with status and result if available
    """
    try:
        return npc_service.get_request_status(request_id)
    except Exception as e:
        logger.error(f"Error getting NPC status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get NPC status: {str(e)}"
        )


@router.get("/{player_id}/{npc_id}", response_model=NPCDetails)
async def get_npc_details(
    player_id: str,
    npc_id: str,
    npc_service: NPCService = Depends(get_npc_service)
) -> NPCDetails:
    """Get details for a specific NPC.
    
    Args:
        player_id: ID of the player
        npc_id: ID of the NPC
        npc_service: NPC service instance
        
    Returns:
        NPC details
    """
    try:
        npc = npc_service.get_npc(player_id, npc_id)
        if not npc:
            raise HTTPException(
                status_code=404,
                detail=f"NPC {npc_id} not found"
            )
        return npc
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting NPC details: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get NPC details: {str(e)}"
        )


@router.post("/{player_id}/{npc_id}/interact", response_model=NPCInteraction)
async def interact_with_npc(
    player_id: str,
    npc_id: str,
    request: NPCInteractionRequest,
    npc_service: NPCService = Depends(get_npc_service)
) -> NPCInteraction:
    """Generate an interaction with an NPC.
    
    Args:
        player_id: ID of the player
        npc_id: ID of the NPC
        request: Interaction request
        npc_service: NPC service instance
        
    Returns:
        Result of the interaction
    """
    try:
        response = await npc_service.interact_with_npc(player_id, npc_id, request)
        return response
    except Exception as e:
        logger.error(f"Error generating NPC interaction: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"NPC interaction failed: {str(e)}"
        )


@router.get("/location/{player_id}/{location_id}", response_model=List[NPCDetails])
async def get_npcs_in_location(
    player_id: str,
    location_id: str,
    npc_service: NPCService = Depends(get_npc_service)
) -> List[NPCDetails]:
    """Get all NPCs in a specific location.
    
    Args:
        player_id: ID of the player
        location_id: ID of the location
        npc_service: NPC service instance
        
    Returns:
        List of NPCs in the location
    """
    try:
        npcs = npc_service.get_npcs_in_location(player_id, location_id)
        return npcs
    except Exception as e:
        logger.error(f"Error getting NPCs in location: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get NPCs in location: {str(e)}"
        ) 