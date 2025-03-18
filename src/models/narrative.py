"""Narrative models for Realm Forge."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class NarrativeContext(BaseModel):
    """Context for narrative generation.
    
    Attributes:
        player_character: Details about the player character
        world_state: Current state of the game world
        quest_history: List of completed quests
        character_relationships: Relationships with other characters
        current_location: Current location in the game world
        active_quests: Currently active quests
    """
    
    player_character: Dict[str, Any] = Field(default_factory=dict)
    world_state: Dict[str, Any] = Field(default_factory=dict)
    quest_history: List[Dict[str, Any]] = Field(default_factory=list)
    character_relationships: Dict[str, float] = Field(default_factory=dict)
    current_location: Dict[str, Any] = Field(default_factory=dict)
    active_quests: List[Dict[str, Any]] = Field(default_factory=list)


class NarrativeRequest(BaseModel):
    """Request for narrative generation.
    
    Attributes:
        player_id: Unique identifier for the player
        context: Context information for narrative generation
        player_choice: Recent choice made by the player
        narrative_type: Type of narrative element to generate
        narrative_options: Optional configuration for narrative generation
    """
    
    player_id: str = Field(...)
    context: NarrativeContext = Field(default_factory=NarrativeContext)
    player_choice: Optional[Dict[str, Any]] = Field(default=None)
    narrative_type: str = Field(default="quest")
    narrative_options: Dict[str, Any] = Field(default_factory=dict)


class NarrativeElement(BaseModel):
    """A single narrative element.
    
    Attributes:
        element_id: Unique identifier for the narrative element
        element_type: Type of narrative element
        content: Content of the narrative element
        metadata: Additional metadata about the element
    """
    
    element_id: str = Field(...)
    element_type: str = Field(...)
    content: str = Field(...)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class NarrativeResponse(BaseModel):
    """Response from narrative generation.
    
    Attributes:
        request_id: Identifier for the request
        player_id: Identifier for the player
        narrative_elements: Generated narrative elements
        updated_context: Updated context after narrative generation
        next_choices: Available choices for the player
        cost: Cost of generating the narrative
    """
    
    request_id: str = Field(...)
    player_id: str = Field(...)
    narrative_elements: List[NarrativeElement] = Field(...)
    updated_context: NarrativeContext = Field(...)
    next_choices: List[Dict[str, Any]] = Field(default_factory=list)
    cost: float = Field(default=0.0) 