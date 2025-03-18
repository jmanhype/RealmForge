"""Difficulty adjustment models for Realm Forge."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class PlayerPerformance(BaseModel):
    """Player performance metrics.
    
    Attributes:
        combat_metrics: Metrics related to combat performance
        puzzle_metrics: Metrics related to puzzle solving
        exploration_metrics: Metrics related to exploration
        progress_rate: Rate of progress through content
        death_count: Number of player deaths
        challenge_completion: Rate of challenge completion
    """
    
    combat_metrics: Dict[str, float] = Field(default_factory=dict)
    puzzle_metrics: Dict[str, float] = Field(default_factory=dict)
    exploration_metrics: Dict[str, float] = Field(default_factory=dict)
    progress_rate: float = Field(default=1.0)
    death_count: int = Field(default=0)
    challenge_completion: Dict[str, float] = Field(default_factory=dict)


class DifficultyContext(BaseModel):
    """Context for difficulty adjustment.
    
    Attributes:
        player_character: Details about the player character
        player_performance: Player performance metrics
        current_difficulty: Current difficulty settings
        player_preferences: Player preferences for difficulty
        game_stage: Current stage in the game
        recent_challenges: Recently encountered challenges
    """
    
    player_character: Dict[str, Any] = Field(default_factory=dict)
    player_performance: PlayerPerformance = Field(default_factory=PlayerPerformance)
    current_difficulty: Dict[str, float] = Field(default_factory=dict)
    player_preferences: Dict[str, Any] = Field(default_factory=dict)
    game_stage: str = Field(default="early")
    recent_challenges: List[Dict[str, Any]] = Field(default_factory=list)


class DifficultyRequest(BaseModel):
    """Request for difficulty adjustment.
    
    Attributes:
        player_id: Unique identifier for the player
        context: Context information for difficulty adjustment
        adjustment_type: Type of difficulty to adjust
        target_content_id: ID of content to adjust difficulty for
        difficulty_options: Optional configuration for difficulty adjustment
    """
    
    player_id: str = Field(...)
    context: DifficultyContext = Field(default_factory=DifficultyContext)
    adjustment_type: Optional[str] = Field(default=None)
    target_content_id: Optional[str] = Field(default=None)
    difficulty_options: Dict[str, Any] = Field(default_factory=dict)


class DifficultySettings(BaseModel):
    """Difficulty settings.
    
    Attributes:
        setting_id: Unique identifier for the difficulty settings
        target_id: ID of target content for these settings
        type: Type of difficulty settings
        combat_settings: Combat-related difficulty settings
        puzzle_settings: Puzzle-related difficulty settings
        exploration_settings: Exploration-related difficulty settings
        reward_settings: Reward-related settings
        adaptive_rules: Rules for adaptive difficulty adjustment
    """
    
    setting_id: str = Field(...)
    target_id: Optional[str] = Field(default=None)
    type: str = Field(...)
    combat_settings: Dict[str, float] = Field(default_factory=dict)
    puzzle_settings: Dict[str, float] = Field(default_factory=dict)
    exploration_settings: Dict[str, float] = Field(default_factory=dict)
    reward_settings: Dict[str, float] = Field(default_factory=dict)
    adaptive_rules: Dict[str, Any] = Field(default_factory=dict)


class DifficultyResponse(BaseModel):
    """Response from difficulty adjustment.
    
    Attributes:
        request_id: Identifier for the request
        player_id: Identifier for the player
        difficulty_settings: Generated difficulty settings
        updated_context: Updated context after difficulty adjustment
        recommendations: Recommendations for content presentation
        cost: Cost of generating the difficulty settings
    """
    
    request_id: str = Field(...)
    player_id: str = Field(...)
    difficulty_settings: List[DifficultySettings] = Field(...)
    updated_context: DifficultyContext = Field(...)
    recommendations: Dict[str, Any] = Field(default_factory=dict)
    cost: float = Field(default=0.0) 