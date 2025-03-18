"""World generation models for Realm Forge."""

from typing import Dict, List, Optional, Any, Tuple
from pydantic import BaseModel, Field


class WorldLocation(BaseModel):
    """A location in the game world.
    
    Attributes:
        location_id: Unique identifier for the location
        name: Name of the location
        description: Description of the location
        type: Type of location (e.g., town, dungeon, forest)
        coordinates: Coordinates in the world
        connected_locations: List of connected location IDs
        resources: Resources available at this location
        points_of_interest: Points of interest at this location
        npcs: NPCs present at this location
        quests: Quests available at this location
        metadata: Additional metadata about the location
    """
    
    location_id: str = Field(...)
    name: str = Field(...)
    description: str = Field(...)
    type: str = Field(...)
    coordinates: Tuple[float, float, float] = Field(...)
    connected_locations: List[str] = Field(default_factory=list)
    resources: Dict[str, int] = Field(default_factory=dict)
    points_of_interest: List[Dict[str, Any]] = Field(default_factory=list)
    npcs: List[str] = Field(default_factory=list)
    quests: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorldContext(BaseModel):
    """Context for world generation.
    
    Attributes:
        world_state: Current state of the game world
        player_character: Details about the player character
        world_theme: Theme of the world
        existing_locations: Existing locations in the world
        narrative_elements: Narrative elements to incorporate
        player_level: Current level of the player
        player_preferences: Player preferences for world content
    """
    
    world_state: Dict[str, Any] = Field(default_factory=dict)
    player_character: Dict[str, Any] = Field(default_factory=dict)
    world_theme: str = Field(default="fantasy")
    existing_locations: Dict[str, WorldLocation] = Field(default_factory=dict)
    narrative_elements: List[Dict[str, Any]] = Field(default_factory=list)
    player_level: int = Field(default=1)
    player_preferences: Dict[str, Any] = Field(default_factory=dict)


class WorldRequest(BaseModel):
    """Request for world generation.
    
    Attributes:
        player_id: Unique identifier for the player
        context: Context information for world generation
        location_type: Type of location to generate
        near_location_id: ID of a location to generate near
        world_options: Optional configuration for world generation
    """
    
    player_id: str = Field(...)
    context: WorldContext = Field(default_factory=WorldContext)
    location_type: Optional[str] = Field(default=None)
    near_location_id: Optional[str] = Field(default=None)
    world_options: Dict[str, Any] = Field(default_factory=dict)


class WorldResponse(BaseModel):
    """Response from world generation.
    
    Attributes:
        request_id: Identifier for the request
        player_id: Identifier for the player
        locations: Generated locations
        updated_context: Updated context after world generation
        three_js_data: Three.js compatible data for rendering
        cost: Cost of generating the world content
    """
    
    request_id: str = Field(...)
    player_id: str = Field(...)
    locations: List[WorldLocation] = Field(...)
    updated_context: WorldContext = Field(...)
    three_js_data: Dict[str, Any] = Field(...)
    cost: float = Field(default=0.0) 