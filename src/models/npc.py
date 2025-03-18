"""NPC models for Realm Forge."""

from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

class NPCType(str, Enum):
    """Types of NPCs."""
    MERCHANT = "merchant"
    GUARD = "guard"
    VILLAGER = "villager"
    QUEST_GIVER = "quest_giver"
    ENEMY = "enemy"
    COMPANION = "companion"

class NPCPersonality(BaseModel):
    """NPC personality traits."""
    friendliness: float = Field(ge=0, le=1, description="How friendly the NPC is")
    bravery: float = Field(ge=0, le=1, description="How brave the NPC is")
    intelligence: float = Field(ge=0, le=1, description="How intelligent the NPC is")
    loyalty: float = Field(ge=0, le=1, description="How loyal the NPC is")
    ambition: float = Field(ge=0, le=1, description="How ambitious the NPC is")

class NPCStats(BaseModel):
    """NPC base statistics."""
    level: int = Field(ge=1, description="NPC level")
    health: int = Field(ge=0, description="NPC health points")
    strength: int = Field(ge=0, description="Physical strength")
    dexterity: int = Field(ge=0, description="Agility and precision")
    intelligence: int = Field(ge=0, description="Mental capability")
    charisma: int = Field(ge=0, description="Social influence")

class NPCInventoryItem(BaseModel):
    """Item in NPC's inventory."""
    item_id: str = Field(description="Unique identifier for the item")
    name: str = Field(description="Item name")
    quantity: int = Field(ge=0, description="Number of items")
    value: int = Field(ge=0, description="Item value in gold")
    type: str = Field(description="Item type (weapon, armor, consumable, etc.)")
    properties: Dict[str, str] = Field(default_factory=dict, description="Item properties")

class NPCScheduleEntry(BaseModel):
    """Entry in NPC's daily schedule."""
    time: str = Field(description="Time of day (HH:MM format)")
    activity: str = Field(description="Activity description")
    location: str = Field(description="Location ID where activity takes place")
    duration: int = Field(ge=0, description="Duration in minutes")

class NPCRelationship(BaseModel):
    """NPC's relationship with another entity."""
    entity_id: str = Field(description="ID of related entity (NPC or player)")
    relationship_type: str = Field(description="Type of relationship")
    affinity: float = Field(ge=-1, le=1, description="Relationship score")
    history: List[str] = Field(default_factory=list, description="History of interactions")

class NPCRequest(BaseModel):
    """Request to generate an NPC.
    
    Attributes:
        player_id: ID of the player requesting the NPC
        location_id: ID of the location for the NPC
        npc_type: Type of NPC to generate
        player_context: Context about the player
        world_context: Context about the world
        story_relevance: Optional story relevance details
        personality_traits: Optional list of desired personality traits
    """
    player_id: str = Field(description="ID of the player requesting the NPC")
    location_id: str = Field(description="ID of the location for the NPC")
    npc_type: Optional[NPCType] = Field(None, description="Type of NPC to generate")
    player_context: str = Field(description="Context about the player")
    world_context: Optional[str] = Field(None, description="Context about the world")
    story_relevance: Optional[str] = Field(None, description="Story relevance details")
    personality_traits: Optional[List[str]] = Field(None, description="Desired personality traits")

class NPCDetails(BaseModel):
    """Detailed NPC information.
    
    Attributes:
        npc_id: Unique identifier for the NPC
        name: NPC name
        type: NPC type
        description: Physical description
        background: Character background
        personality: Personality traits and quirks
        abilities: NPC abilities
        dialogue: Available dialogue options
        location_id: Current location
        player_id: Associated player
        status: Current status
        last_updated: Last update timestamp
    """
    npc_id: str = Field(description="Unique identifier for the NPC")
    name: str = Field(description="NPC name")
    type: str = Field(description="NPC type")
    description: str = Field(description="Physical description")
    background: str = Field(description="Character background")
    personality: Dict[str, List[str]] = Field(description="Personality traits and quirks")
    abilities: Dict[str, List[str]] = Field(description="NPC abilities")
    dialogue: Dict[str, Any] = Field(description="Available dialogue options")
    location_id: str = Field(description="Current location")
    player_id: str = Field(description="Associated player")
    status: str = Field(description="Current status")
    last_updated: str = Field(description="Last update timestamp")

class NPCResponse(BaseModel):
    """Response containing generated NPC data.
    
    Attributes:
        npc_id: Unique identifier for the NPC
        name: NPC name
        type: NPC type
        description: Physical description
        background: Character background
        personality: Personality traits and quirks
        abilities: NPC abilities
        dialogue: Available dialogue options
        location_id: Current location
        player_id: Associated player
        status: Current status
        last_updated: Last update timestamp
    """
    npc_id: str = Field(description="Unique identifier for the NPC")
    name: str = Field(description="NPC name")
    type: str = Field(description="NPC type")
    description: str = Field(description="Physical description")
    background: str = Field(description="Character background")
    personality: Dict[str, List[str]] = Field(description="Personality traits and quirks")
    abilities: Dict[str, List[str]] = Field(description="NPC abilities")
    dialogue: Dict[str, Any] = Field(description="Available dialogue options")
    location_id: str = Field(description="Current location")
    player_id: str = Field(description="Associated player")
    status: str = Field(description="Current status")
    last_updated: str = Field(description="Last update timestamp")

class NPCInteractionRequest(BaseModel):
    """Request for NPC interaction.
    
    Attributes:
        interaction_type: Type of interaction
        player_input: Player's input for the interaction
    """
    interaction_type: str = Field(description="Type of interaction")
    player_input: str = Field(description="Player's input for the interaction")

class NPCInteraction(BaseModel):
    """Result of an NPC interaction.
    
    Attributes:
        player_id: ID of the player
        npc_id: ID of the NPC
        npc_name: Name of the NPC
        interaction_type: Type of interaction
        npc_response: NPC's response
        available_actions: List of available actions
        mood: NPC's mood during interaction
        quest_offered: Whether a quest was offered
        items_offered: List of items offered for trade
    """
    player_id: str = Field(description="ID of the player")
    npc_id: str = Field(description="ID of the NPC")
    npc_name: str = Field(description="Name of the NPC")
    interaction_type: str = Field(description="Type of interaction")
    npc_response: str = Field(description="NPC's response")
    available_actions: List[str] = Field(description="List of available actions")
    mood: str = Field(description="NPC's mood during interaction")
    quest_offered: bool = Field(description="Whether a quest was offered")
    items_offered: List[str] = Field(description="List of items offered for trade") 