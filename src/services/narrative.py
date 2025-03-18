"""Service for narrative generation and management in Realm Forge."""

import json
import logging
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

import aiohttp
from loguru import logger

from ..models.narrative import (
    NarrativeContext,
    NarrativeRequest,
    NarrativeResponse,
    NarrativeElement
)
from ..config.settings import Settings

class NarrativeService:
    """Service for generating and managing narrative content.
    
    This service handles story generation, quest management, and dialogue systems.
    It uses templates and AI to create dynamic narrative content that adapts to
    player choices and game state.
    """
    
    def __init__(self, settings: Settings):
        """Initialize the narrative service.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        self.story_templates: Dict[str, Any] = {}
        self.dialogue_templates: Dict[str, Any] = {}
        self.active_narratives: Dict[str, Dict[str, Any]] = {}
        self.load_templates()
        
    def load_templates(self) -> None:
        """Load story and dialogue templates from files."""
        try:
            templates_dir = Path(self.settings.aflow.templates_dir)
            
            # Load story templates
            story_path = templates_dir / "stories.json"
            if story_path.exists():
                with open(story_path) as f:
                    self.story_templates = json.load(f)
            
            # Load dialogue templates
            dialogue_path = templates_dir / "dialogues.json"
            if dialogue_path.exists():
                with open(dialogue_path) as f:
                    self.dialogue_templates = json.load(f)
                    
        except Exception as e:
            logger.error(f"Failed to load narrative templates: {e}")
            # Initialize with empty templates if loading fails
            self.story_templates = {}
            self.dialogue_templates = {}
    
    async def generate_story(
        self,
        context: NarrativeContext,
        story_type: str,
        options: Dict[str, Any]
    ) -> List[NarrativeElement]:
        """Generate a story based on context and type.
        
        Args:
            context: Current narrative context
            story_type: Type of story to generate
            options: Additional options for story generation
            
        Returns:
            List of narrative elements forming the story
        """
        try:
            # Get relevant template
            template = self.story_templates.get(story_type, {})
            
            # Generate story elements using template and context
            elements = []
            
            # Use template to create story structure
            story_id = str(uuid.uuid4())
            
            # Add introduction
            intro = NarrativeElement(
                element_id=f"{story_id}_intro",
                element_type="introduction",
                content=template.get("intro_template", "").format(**context.dict()),
                metadata={"story_id": story_id}
            )
            elements.append(intro)
            
            # Add story body elements
            for i, beat in enumerate(template.get("story_beats", [])):
                element = NarrativeElement(
                    element_id=f"{story_id}_beat_{i}",
                    element_type="story_beat",
                    content=beat.format(**context.dict()),
                    metadata={
                        "story_id": story_id,
                        "beat_number": i,
                        "requirements": template.get("requirements", {})
                    }
                )
                elements.append(element)
            
            # Add conclusion
            conclusion = NarrativeElement(
                element_id=f"{story_id}_conclusion",
                element_type="conclusion", 
                content=template.get("conclusion_template", "").format(**context.dict()),
                metadata={"story_id": story_id}
            )
            elements.append(conclusion)
            
            return elements
            
        except Exception as e:
            logger.error(f"Failed to generate story: {e}")
            return []
    
    async def generate_dialogue(
        self,
        context: NarrativeContext,
        npc_id: str,
        dialogue_type: str,
        options: Dict[str, Any]
    ) -> List[NarrativeElement]:
        """Generate dialogue for interaction with an NPC.
        
        Args:
            context: Current narrative context
            npc_id: ID of the NPC to generate dialogue for
            dialogue_type: Type of dialogue to generate
            options: Additional options for dialogue generation
            
        Returns:
            List of narrative elements forming the dialogue
        """
        try:
            # Get relevant template
            template = self.dialogue_templates.get(dialogue_type, {})
            
            # Generate dialogue elements
            elements = []
            dialogue_id = str(uuid.uuid4())
            
            # Create greeting
            greeting = NarrativeElement(
                element_id=f"{dialogue_id}_greeting",
                element_type="dialogue",
                content=template.get("greeting", "").format(
                    npc_id=npc_id,
                    **context.dict()
                ),
                metadata={
                    "dialogue_id": dialogue_id,
                    "npc_id": npc_id,
                    "is_greeting": True
                }
            )
            elements.append(greeting)
            
            # Add dialogue options
            for i, option in enumerate(template.get("options", [])):
                element = NarrativeElement(
                    element_id=f"{dialogue_id}_option_{i}",
                    element_type="dialogue_option",
                    content=option.get("text", "").format(
                        npc_id=npc_id,
                        **context.dict()
                    ),
                    metadata={
                        "dialogue_id": dialogue_id,
                        "npc_id": npc_id,
                        "option_number": i,
                        "requirements": option.get("requirements", {}),
                        "consequences": option.get("consequences", {})
                    }
                )
                elements.append(element)
            
            return elements
            
        except Exception as e:
            logger.error(f"Failed to generate dialogue: {e}")
            return []
    
    async def process_narrative_request(
        self,
        request: NarrativeRequest
    ) -> NarrativeResponse:
        """Process a narrative generation request.
        
        Args:
            request: The narrative generation request
            
        Returns:
            Response containing generated narrative elements
        """
        try:
            # Generate request ID
            request_id = str(uuid.uuid4())
            
            # Initialize response
            response = NarrativeResponse(
                request_id=request_id,
                player_id=request.player_id,
                narrative_elements=[],
                updated_context=request.context,
                next_choices=[],
                cost=0.0
            )
            
            # Generate narrative elements based on type
            if request.narrative_type == "quest":
                elements = await self.generate_story(
                    request.context,
                    "quest",
                    request.narrative_options
                )
                response.narrative_elements.extend(elements)
                
            elif request.narrative_type == "dialogue":
                npc_id = request.narrative_options.get("npc_id")
                if npc_id:
                    elements = await self.generate_dialogue(
                        request.context,
                        npc_id,
                        request.narrative_options.get("dialogue_type", "general"),
                        request.narrative_options
                    )
                    response.narrative_elements.extend(elements)
            
            # Update context based on narrative elements
            self._update_context(response)
            
            # Calculate next available choices
            response.next_choices = self._calculate_choices(response)
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to process narrative request: {e}")
            # Return empty response on error
            return NarrativeResponse(
                request_id=str(uuid.uuid4()),
                player_id=request.player_id,
                narrative_elements=[],
                updated_context=request.context,
                next_choices=[],
                cost=0.0
            )
    
    def _update_context(self, response: NarrativeResponse) -> None:
        """Update narrative context based on generated elements.
        
        Args:
            response: The narrative response to update context for
        """
        try:
            context = response.updated_context
            
            # Update based on narrative elements
            for element in response.narrative_elements:
                if element.element_type == "quest":
                    # Add quest to active quests
                    context.active_quests.append({
                        "quest_id": element.element_id,
                        "status": "active",
                        "progress": 0.0
                    })
                    
                elif element.element_type == "dialogue":
                    # Update character relationships
                    npc_id = element.metadata.get("npc_id")
                    if npc_id:
                        current_relation = context.character_relationships.get(npc_id, 0.0)
                        context.character_relationships[npc_id] = min(
                            1.0,
                            current_relation + 0.1
                        )
            
        except Exception as e:
            logger.error(f"Failed to update narrative context: {e}")
    
    def _calculate_choices(self, response: NarrativeResponse) -> List[Dict[str, Any]]:
        """Calculate available choices based on narrative elements.
        
        Args:
            response: The narrative response to calculate choices for
            
        Returns:
            List of available choices
        """
        try:
            choices = []
            
            # Extract choices from narrative elements
            for element in response.narrative_elements:
                if element.element_type == "dialogue_option":
                    # Add dialogue choice
                    choices.append({
                        "choice_id": element.element_id,
                        "type": "dialogue",
                        "text": element.content,
                        "requirements": element.metadata.get("requirements", {}),
                        "consequences": element.metadata.get("consequences", {})
                    })
                    
                elif element.element_type == "quest":
                    # Add quest acceptance choice
                    choices.append({
                        "choice_id": f"{element.element_id}_accept",
                        "type": "quest_accept",
                        "text": f"Accept quest: {element.content}",
                        "requirements": element.metadata.get("requirements", {}),
                        "consequences": {
                            "quest_status": "active",
                            "reputation": +0.1
                        }
                    })
            
            return choices
            
        except Exception as e:
            logger.error(f"Failed to calculate choices: {e}")
            return [] 