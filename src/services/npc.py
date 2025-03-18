"""NPC generation and management service for Realm Forge."""

import asyncio
import json
from typing import Dict, Any, List, Optional, Union, Tuple
from uuid import UUID
from datetime import datetime

import openai
from loguru import logger

from ..config.settings import Settings
from ..models.npc import (
    NPCRequest,
    NPCResponse,
    NPCDetails,
    NPCInteraction,
    NPCInteractionRequest
)


class NPCService:
    """Service for generating and managing NPCs.
    
    This service handles the generation of NPCs, their behaviors, 
    and interactions using OpenAI's GPT models.
    """
    
    def __init__(
        self,
        settings: Settings,
        request_cache: Dict[str, Dict[str, Any]] = None,
        npc_cache: Dict[str, Dict[str, Any]] = None
    ) -> None:
        """Initialize the NPC service.
        
        Args:
            settings: Application settings
            request_cache: Cache for async requests
            npc_cache: Cache for generated NPCs
        """
        self.settings = settings
        self.request_cache = request_cache or {}
        self.npc_cache = npc_cache or {}
        openai.api_key = settings.openai.api_key
    
    @classmethod
    async def create(
        cls,
        settings: Optional[Settings] = None
    ) -> "NPCService":
        """Create a new NPCService instance.
        
        Args:
            settings: Application settings
            
        Returns:
            NPCService: Initialized NPC service
        """
        settings = settings or Settings.get_settings()
        return cls(settings=settings)
    
    async def generate_npc(self, request: NPCRequest) -> NPCResponse:
        """Generate NPC based on player and world context.
        
        Args:
            request: NPC generation request
            
        Returns:
            NPCResponse: Generated NPC content
        """
        try:
            logger.info(f"Generating NPC for player {request.player_id} in location {request.location_id}")
            
            # Prepare input for the model
            npc_prompt = self._build_npc_prompt(request)
            
            # Call OpenAI API
            response = await openai.chat.completions.create(
                model=self.settings.openai.model_name,
                messages=[
                    {"role": "system", "content": "You are an expert RPG game designer and writer, specializing in creating detailed and engaging NPCs."},
                    {"role": "user", "content": npc_prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            # Parse the result into an NPCResponse
            result = response.choices[0].message.content
            response = self._parse_npc_result(result, request.player_id, request.location_id)
            
            # Cache the generated NPC
            self._cache_npc(request.player_id, response)
            
            logger.info(f"NPC generation successful for player {request.player_id}")
            return response
            
        except Exception as e:
            logger.error(f"NPC generation failed: {str(e)}")
            raise
    
    async def generate_npc_async(self, request: NPCRequest) -> Dict[str, Any]:
        """Generate NPC content asynchronously.
        
        Args:
            request: NPC generation request
            
        Returns:
            Dict with request ID and status
        """
        # Generate a request ID
        request_id = str(UUID(int=len(self.request_cache) + 1))
        
        # Store initial request status
        self.request_cache[request_id] = {
            "player_id": request.player_id,
            "request": request.dict(),
            "status": "pending",
            "result": None
        }
        
        # Start background generation task
        asyncio.create_task(self._generate_npc_background(request_id, request))
        
        return {
            "request_id": request_id,
            "status": "pending"
        }
    
    async def _generate_npc_background(self, request_id: str, request: NPCRequest) -> None:
        """Background task for NPC generation.
        
        Args:
            request_id: Request ID
            request: NPC generation request
        """
        try:
            # Update status to processing
            self.request_cache[request_id]["status"] = "processing"
            
            # Generate NPC
            result = await self.generate_npc(request)
            
            # Update cache with result
            self.request_cache[request_id]["status"] = "completed"
            self.request_cache[request_id]["result"] = result.dict()
            
        except Exception as e:
            # Update cache with error
            logger.error(f"Async NPC generation failed: {str(e)}")
            self.request_cache[request_id]["status"] = "failed"
            self.request_cache[request_id]["error"] = str(e)
    
    def get_request_status(self, request_id: str) -> Dict[str, Any]:
        """Get the status of an async NPC generation request.
        
        Args:
            request_id: Request ID
            
        Returns:
            Dict with request status and result if available
        """
        if request_id not in self.request_cache:
            return {
                "status": "not_found",
                "message": f"Request {request_id} not found"
            }
        
        request_info = self.request_cache[request_id]
        response = {
            "request_id": request_id,
            "status": request_info["status"],
            "player_id": request_info["player_id"]
        }
        
        if request_info["status"] == "completed":
            response["result"] = request_info["result"]
        elif request_info["status"] == "failed":
            response["error"] = request_info.get("error", "Unknown error")
        
        return response
    
    def _build_npc_prompt(self, request: NPCRequest) -> str:
        """Build the prompt for NPC generation.
        
        Args:
            request: NPC generation request
            
        Returns:
            str: Prompt for the language model
        """
        prompt_parts = [
            f"Generate an NPC for an RPG game with the following parameters:",
            f"Player ID: {request.player_id}",
            f"Location ID: {request.location_id}",
            f"NPC Type: {request.npc_type or 'Any'}",
            f"Player Context: {request.player_context}",
            f"World Context: {request.world_context or 'Fantasy world'}"
        ]
        
        if request.story_relevance:
            prompt_parts.append(f"Story Relevance: {request.story_relevance}")
            
        if request.personality_traits:
            traits = ', '.join(request.personality_traits)
            prompt_parts.append(f"Personality Traits: {traits}")
            
        prompt_parts.append("\nGenerate a detailed NPC with name, description, background, personality, motivations, abilities, and potential dialogue options.")
        prompt_parts.append("\nProvide the response in JSON format with the following structure:")
        prompt_parts.append("""{
            "npc_id": "unique_id",
            "name": "NPC name",
            "type": "NPC type",
            "description": "Physical description",
            "background": "Character background",
            "personality": {
                "traits": ["trait1", "trait2"],
                "motivations": ["motivation1", "motivation2"],
                "quirks": ["quirk1", "quirk2"]
            },
            "abilities": {
                "combat": ["ability1", "ability2"],
                "social": ["ability1", "ability2"],
                "special": ["ability1", "ability2"]
            },
            "dialogue": {
                "greetings": ["greeting1", "greeting2"],
                "responses": {
                    "friendly": ["response1", "response2"],
                    "hostile": ["response1", "response2"],
                    "neutral": ["response1", "response2"]
                }
            }
        }""")
        
        return "\n".join(prompt_parts)
    
    def _parse_npc_result(self, result: str, player_id: str, location_id: str) -> NPCResponse:
        """Parse the model result into a structured NPC response.
        
        Args:
            result: Raw result from the language model
            player_id: ID of the player
            location_id: ID of the location
            
        Returns:
            NPCResponse: Structured NPC data
        """
        try:
            # Parse JSON response
            npc_data = json.loads(result)
            
            # Create an NPC ID if not provided
            npc_id = npc_data.get("npc_id") or f"npc_{player_id}_{location_id}_{len(self.npc_cache) + 1}"
            
            # Create NPCResponse
            response = NPCResponse(
                npc_id=npc_id,
                name=npc_data["name"],
                type=npc_data["type"],
                description=npc_data["description"],
                background=npc_data["background"],
                personality=npc_data["personality"],
                abilities=npc_data["abilities"],
                dialogue=npc_data["dialogue"],
                location_id=location_id,
                player_id=player_id,
                status="active",
                last_updated=datetime.now().isoformat()
            )
            
            return response
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse NPC result JSON: {e}")
            raise
        except KeyError as e:
            logger.error(f"Missing required field in NPC result: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to parse NPC result: {e}")
            raise
    
    def _cache_npc(self, player_id: str, npc: NPCResponse) -> None:
        """Cache a generated NPC.
        
        Args:
            player_id: ID of the player
            npc: Generated NPC response
        """
        try:
            if player_id not in self.npc_cache:
                self.npc_cache[player_id] = {}
            
            self.npc_cache[player_id][npc.npc_id] = npc.dict()
            
        except Exception as e:
            logger.error(f"Failed to cache NPC: {e}")
    
    def get_npc(self, player_id: str, npc_id: str) -> Optional[NPCDetails]:
        """Get details for a specific NPC.
        
        Args:
            player_id: ID of the player
            npc_id: ID of the NPC
            
        Returns:
            NPCDetails: NPC details or None if not found
        """
        if player_id not in self.npc_cache or npc_id not in self.npc_cache[player_id]:
            return None
        
        npc_data = self.npc_cache[player_id][npc_id]
        return NPCDetails(**npc_data)
    
    async def interact_with_npc(
        self, player_id: str, npc_id: str, request: NPCInteractionRequest
    ) -> NPCInteraction:
        """Generate an interaction with an NPC.
        
        Args:
            player_id: ID of the player
            npc_id: ID of the NPC
            request: Interaction request
            
        Returns:
            NPCInteraction: Result of the interaction
        """
        try:
            # Get the NPC details
            npc = self.get_npc(player_id, npc_id)
            if not npc:
                raise ValueError(f"NPC {npc_id} not found")
                
            logger.info(f"Generating interaction with NPC {npc_id} for player {player_id}")
            
            # Build the interaction prompt
            interaction_prompt = self._build_interaction_prompt(
                player_id, npc, request.interaction_type, request.player_input
            )
            
            # Call OpenAI API
            response = await openai.chat.completions.create(
                model=self.settings.openai.model_name,
                messages=[
                    {"role": "system", "content": "You are an expert RPG game designer and writer, specializing in creating detailed and engaging NPC interactions."},
                    {"role": "user", "content": interaction_prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            # Parse the result
            result = response.choices[0].message.content
            interaction = self._parse_interaction_result(
                result, player_id, npc_id, request.interaction_type
            )
            
            logger.info(f"Interaction generated successfully")
            return interaction
            
        except Exception as e:
            logger.error(f"NPC interaction failed: {str(e)}")
            raise
    
    def _build_interaction_prompt(
        self, player_id: str, npc: NPCDetails, interaction_type: str, player_input: str
    ) -> str:
        """Build the prompt for NPC interaction.
        
        Args:
            player_id: ID of the player
            npc: NPC details
            interaction_type: Type of interaction
            player_input: Player's input
            
        Returns:
            str: Prompt for the language model
        """
        prompt_parts = [
            f"Generate an interaction with an NPC with the following parameters:",
            f"NPC Name: {npc.name}",
            f"NPC Type: {npc.npc_type}",
            f"NPC Personality: {npc.personality}",
            f"NPC Motivations: {', '.join(npc.motivations)}",
            f"Interaction Type: {interaction_type}",
            f"Player Input: {player_input}"
        ]
        
        if npc.dialogue_options:
            prompt_parts.append(f"Available Dialogue: {', '.join(npc.dialogue_options)}")
            
        prompt_parts.append("\nGenerate a realistic and engaging interaction response that stays true to the NPC's character.")
        
        return "\n".join(prompt_parts)
    
    def _parse_interaction_result(
        self, result: str, player_id: str, npc_id: str, interaction_type: str
    ) -> NPCInteraction:
        """Parse the model result into a structured interaction response.
        
        Args:
            result: Raw result from the language model
            player_id: ID of the player
            npc_id: ID of the NPC
            interaction_type: Type of interaction
            
        Returns:
            NPCInteraction: Structured interaction data
        """
        # In a real implementation, this would parse structured output
        # Here we're simplifying for demonstration purposes
        
        # Get the NPC
        npc = self.get_npc(player_id, npc_id)
        
        # Create a sample interaction response
        if interaction_type == "dialogue":
            response_text = "The ancient tomes speak of a darkness rising in the east. If you seek to confront it, you'll need to find the Crystal of Clarity hidden in the Forgotten Caves."
        elif interaction_type == "trade":
            response_text = "I have rare herbs and scrolls to trade. The Scroll of Wisdom costs 50 gold, but its value is beyond measure."
        elif interaction_type == "quest":
            response_text = "If you're brave enough, I need someone to recover an ancient artifact from the ruins. Return it to me, and I'll reward you handsomely."
        else:
            response_text = "I'm afraid I can't help you with that. Perhaps try something else?"
        
        return NPCInteraction(
            player_id=player_id,
            npc_id=npc_id,
            npc_name=npc.name if npc else "Unknown",
            interaction_type=interaction_type,
            npc_response=response_text,
            available_actions=["accept_quest", "ask_more", "decline"],
            mood="helpful",
            quest_offered=interaction_type == "quest",
            items_offered=[] if interaction_type != "trade" else ["Scroll of Wisdom", "Healing Herbs"]
        )
    
    def get_npcs_in_location(self, player_id: str, location_id: str) -> List[NPCDetails]:
        """Get all NPCs in a specific location.
        
        Args:
            player_id: ID of the player
            location_id: ID of the location
            
        Returns:
            List[NPCDetails]: NPCs in the location
        """
        location_key = f"{player_id}_{location_id}"
        
        if "locations" not in self.npc_cache or location_key not in self.npc_cache["locations"]:
            return []
            
        npc_ids = self.npc_cache["locations"][location_key]
        npcs = []
        
        for npc_id in npc_ids:
            npc = self.get_npc(player_id, npc_id)
            if npc:
                npcs.append(npc)
                
        return npcs 