"""Player-related models for Realm Forge."""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field


class PlayerCharacter(BaseModel):
    """Player character model.
    
    Attributes:
        character_id: Unique identifier for the character
        name: Name of the character
        class_type: Character class
        level: Character level
        stats: Character statistics
        inventory: Items in the character's inventory
        abilities: Character abilities
        experience: Experience points
        history: Character backstory and history
        appearance: Description of appearance
    """
    
    character_id: str = Field(...)
    name: str = Field(...)
    class_type: str = Field(...)
    level: int = Field(default=1)
    stats: Dict[str, float] = Field(default_factory=dict)
    inventory: List[Dict[str, Any]] = Field(default_factory=list)
    abilities: List[Dict[str, Any]] = Field(default_factory=list)
    experience: int = Field(default=0)
    history: str = Field(default="")
    appearance: str = Field(default="")


class PlayerChoice(BaseModel):
    """Player choice model.
    
    Attributes:
        choice_id: Unique identifier for the choice
        player_id: ID of the player
        context_id: ID of the context where the choice was made
        choice_type: Type of choice
        selected_option: Selected option
        timestamp: When the choice was made
        metadata: Additional metadata about the choice
    """
    
    choice_id: str = Field(...)
    player_id: str = Field(...)
    context_id: str = Field(...)
    choice_type: str = Field(...)
    selected_option: Dict[str, Any] = Field(...)
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PlayerEvent(BaseModel):
    """Player event model.
    
    Attributes:
        event_id: Unique identifier for the event
        player_id: ID of the player
        event_type: Type of event
        event_data: Data associated with the event
        timestamp: When the event occurred
        location_id: ID of the location where the event occurred
        related_entities: Entities related to the event
    """
    
    event_id: str = Field(...)
    player_id: str = Field(...)
    event_type: str = Field(...)
    event_data: Dict[str, Any] = Field(...)
    timestamp: datetime = Field(default_factory=datetime.now)
    location_id: Optional[str] = Field(default=None)
    related_entities: List[Dict[str, str]] = Field(default_factory=list)


class EngagementMetrics(BaseModel):
    """Player engagement metrics.
    
    Attributes:
        session_duration: Duration of play sessions
        interaction_frequency: Frequency of player interactions
        content_completion: Rates of content completion
        return_frequency: How often the player returns
        feature_usage: Usage rates of different features
        social_interaction: Metrics about social interactions
    """
    
    session_duration: List[int] = Field(default_factory=list)
    interaction_frequency: Dict[str, float] = Field(default_factory=dict)
    content_completion: Dict[str, float] = Field(default_factory=dict)
    return_frequency: float = Field(default=0.0)
    feature_usage: Dict[str, float] = Field(default_factory=dict)
    social_interaction: Dict[str, float] = Field(default_factory=dict)


class PlayerMetrics(BaseModel):
    """Combined player metrics.
    
    Attributes:
        player_id: Unique identifier for the player
        performance: Performance metrics
        engagement: Engagement metrics
        preferences: Inferred player preferences
        play_style: Detected play style
        skill_progression: Progression of skills over time
    """
    
    player_id: str = Field(...)
    performance: Dict[str, Union[float, Dict[str, float]]] = Field(default_factory=dict)
    engagement: EngagementMetrics = Field(default_factory=EngagementMetrics)
    preferences: Dict[str, float] = Field(default_factory=dict)
    play_style: Dict[str, float] = Field(default_factory=dict)
    skill_progression: Dict[str, List[float]] = Field(default_factory=dict)


class PlayerState(BaseModel):
    """Complete player state.
    
    Attributes:
        player_id: Unique identifier for the player
        character: Player's character
        current_location_id: ID of the player's current location
        quest_log: Active and completed quests
        choices: History of player choices
        events: History of player events
        metrics: Player metrics
        last_updated: Last time the state was updated
    """
    
    player_id: str = Field(...)
    character: PlayerCharacter = Field(...)
    current_location_id: str = Field(...)
    quest_log: Dict[str, Any] = Field(default_factory=dict)
    choices: List[PlayerChoice] = Field(default_factory=list)
    events: List[PlayerEvent] = Field(default_factory=list)
    metrics: PlayerMetrics = Field(...)
    last_updated: datetime = Field(default_factory=datetime.now) 