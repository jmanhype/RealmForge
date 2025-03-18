"""Service for difficulty adjustment and challenge management in Realm Forge."""

import json
import logging
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

import numpy as np
from loguru import logger

from ..models.difficulty import (
    DifficultyContext,
    DifficultyRequest,
    DifficultyResponse,
    DifficultySettings,
    PlayerPerformance
)
from ..config.settings import Settings

class DifficultyService:
    """Service for managing game difficulty and challenges.
    
    This service handles difficulty scaling, challenge generation, and adaptive
    difficulty adjustments based on player performance and preferences.
    """
    
    def __init__(self, settings: Settings):
        """Initialize the difficulty service.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        self.difficulty_templates: Dict[str, Any] = {}
        self.challenge_templates: Dict[str, Any] = {}
        self.active_settings: Dict[str, DifficultySettings] = {}
        self.load_templates()
        
    def load_templates(self) -> None:
        """Load difficulty and challenge templates from files."""
        try:
            templates_dir = Path(self.settings.aflow.templates_dir)
            
            # Load difficulty templates
            difficulty_path = templates_dir / "difficulty.json"
            if difficulty_path.exists():
                with open(difficulty_path) as f:
                    self.difficulty_templates = json.load(f)
            
            # Load challenge templates
            challenge_path = templates_dir / "challenges.json"
            if challenge_path.exists():
                with open(challenge_path) as f:
                    self.challenge_templates = json.load(f)
                    
        except Exception as e:
            logger.error(f"Failed to load difficulty templates: {e}")
            # Initialize with empty templates if loading fails
            self.difficulty_templates = {}
            self.challenge_templates = {}
    
    def _calculate_base_difficulty(
        self,
        context: DifficultyContext,
        adjustment_type: str
    ) -> float:
        """Calculate base difficulty level from context.
        
        Args:
            context: Current difficulty context
            adjustment_type: Type of difficulty to calculate
            
        Returns:
            Base difficulty value
        """
        try:
            # Get base difficulty from player level
            base = context.player_character.get("level", 1) * 0.1
            
            # Adjust based on performance metrics
            if adjustment_type == "combat":
                metrics = context.player_performance.combat_metrics
                win_rate = metrics.get("win_rate", 0.5)
                damage_taken = metrics.get("damage_taken", 0.0)
                damage_dealt = metrics.get("damage_dealt", 0.0)
                
                # Calculate combat performance score
                performance = (
                    win_rate * 0.4 +
                    min(damage_dealt / (damage_taken + 1), 1.0) * 0.6
                )
                base *= (2.0 - performance)
                
            elif adjustment_type == "puzzle":
                metrics = context.player_performance.puzzle_metrics
                completion_rate = metrics.get("completion_rate", 0.5)
                avg_time = metrics.get("average_time", 60.0)
                optimal_time = metrics.get("optimal_time", 30.0)
                
                # Calculate puzzle performance score
                time_factor = min(optimal_time / (avg_time + 1), 1.0)
                performance = (completion_rate * 0.6 + time_factor * 0.4)
                base *= (2.0 - performance)
                
            elif adjustment_type == "exploration":
                metrics = context.player_performance.exploration_metrics
                discovery_rate = metrics.get("discovery_rate", 0.5)
                completion_rate = metrics.get("completion_rate", 0.5)
                
                # Calculate exploration performance score
                performance = (discovery_rate * 0.5 + completion_rate * 0.5)
                base *= (2.0 - performance)
            
            return max(0.1, min(base, 1.0))
            
        except Exception as e:
            logger.error(f"Failed to calculate base difficulty: {e}")
            return 0.5
    
    def _apply_adaptive_adjustments(
        self,
        base_difficulty: float,
        context: DifficultyContext,
        adjustment_type: str
    ) -> float:
        """Apply adaptive difficulty adjustments based on context.
        
        Args:
            base_difficulty: Base difficulty value
            context: Current difficulty context
            adjustment_type: Type of difficulty to adjust
            
        Returns:
            Adjusted difficulty value
        """
        try:
            # Get current settings
            current = context.current_difficulty.get(adjustment_type, base_difficulty)
            
            # Calculate target difficulty based on performance
            performance = context.player_performance
            progress_rate = performance.progress_rate
            completion_rate = performance.challenge_completion.get(adjustment_type, 0.5)
            
            # Adjust target based on rates
            if progress_rate > 1.2 and completion_rate > 0.8:
                # Player is progressing too fast and completing most challenges
                target = current * 1.2
            elif progress_rate < 0.8 or completion_rate < 0.2:
                # Player is struggling
                target = current * 0.8
            else:
                # Keep current difficulty
                target = current
            
            # Smooth adjustment
            alpha = 0.2  # Learning rate
            adjusted = current + alpha * (target - current)
            
            return max(0.1, min(adjusted, 1.0))
            
        except Exception as e:
            logger.error(f"Failed to apply adaptive adjustments: {e}")
            return base_difficulty
    
    def _generate_challenge_settings(
        self,
        difficulty: float,
        challenge_type: str,
        context: DifficultyContext
    ) -> Dict[str, float]:
        """Generate specific settings for a challenge type.
        
        Args:
            difficulty: Target difficulty value
            challenge_type: Type of challenge
            context: Current difficulty context
            
        Returns:
            Dictionary of challenge settings
        """
        try:
            # Get base settings from template
            template = self.challenge_templates.get(challenge_type, {})
            base_settings = template.get("settings", {})
            
            # Scale settings based on difficulty
            settings = {}
            for key, base_value in base_settings.items():
                # Apply difficulty scaling
                if key.endswith("_count"):
                    # Integer values (e.g., enemy count)
                    scaled = int(base_value * difficulty * 1.5)
                    settings[key] = max(1, scaled)
                    
                elif key.endswith("_time"):
                    # Time values (e.g., time limit)
                    if "min" in key:
                        # Minimum times increase with difficulty
                        scaled = base_value * (1 + difficulty)
                    else:
                        # Maximum times decrease with difficulty
                        scaled = base_value * (2 - difficulty)
                    settings[key] = max(1.0, scaled)
                    
                elif key.endswith("_rate"):
                    # Rate values (e.g., spawn rate)
                    scaled = base_value * difficulty
                    settings[key] = max(0.1, min(scaled, 1.0))
                    
                else:
                    # Default linear scaling
                    scaled = base_value * difficulty
                    settings[key] = scaled
            
            return settings
            
        except Exception as e:
            logger.error(f"Failed to generate challenge settings: {e}")
            return {}
    
    def _calculate_rewards(
        self,
        difficulty: float,
        challenge_type: str,
        settings: Dict[str, float]
    ) -> Dict[str, float]:
        """Calculate rewards based on difficulty and challenge settings.
        
        Args:
            difficulty: Challenge difficulty value
            challenge_type: Type of challenge
            settings: Challenge settings
            
        Returns:
            Dictionary of reward values
        """
        try:
            # Get base rewards from template
            template = self.challenge_templates.get(challenge_type, {})
            base_rewards = template.get("rewards", {})
            
            # Scale rewards based on difficulty and settings
            rewards = {}
            for key, base_value in base_rewards.items():
                # Calculate reward multiplier
                multiplier = 1.0
                
                # Adjust based on difficulty
                multiplier *= (1 + difficulty)
                
                # Adjust based on relevant settings
                if key == "experience":
                    # More experience for more enemies/objectives
                    count_factor = sum(
                        v for k, v in settings.items()
                        if k.endswith("_count")
                    )
                    multiplier *= (1 + count_factor * 0.1)
                    
                elif key == "gold":
                    # More gold for faster completion
                    time_factor = sum(
                        1/v for k, v in settings.items()
                        if k.endswith("_time") and v > 0
                    )
                    multiplier *= (1 + time_factor * 0.1)
                
                # Calculate final reward
                rewards[key] = base_value * multiplier
            
            return rewards
            
        except Exception as e:
            logger.error(f"Failed to calculate rewards: {e}")
            return {}
    
    async def process_difficulty_request(
        self,
        request: DifficultyRequest
    ) -> DifficultyResponse:
        """Process a difficulty adjustment request.
        
        Args:
            request: The difficulty adjustment request
            
        Returns:
            Response containing difficulty settings
        """
        try:
            # Generate request ID
            request_id = str(uuid.uuid4())
            
            # Initialize response
            response = DifficultyResponse(
                request_id=request_id,
                player_id=request.player_id,
                difficulty_settings=[],
                updated_context=request.context,
                recommendations={},
                cost=0.0
            )
            
            # Process adjustment if requested
            if request.adjustment_type:
                # Calculate base difficulty
                base_difficulty = self._calculate_base_difficulty(
                    request.context,
                    request.adjustment_type
                )
                
                # Apply adaptive adjustments
                adjusted_difficulty = self._apply_adaptive_adjustments(
                    base_difficulty,
                    request.context,
                    request.adjustment_type
                )
                
                # Generate settings
                settings = DifficultySettings(
                    setting_id=str(uuid.uuid4()),
                    target_id=request.target_content_id,
                    type=request.adjustment_type,
                    combat_settings=self._generate_challenge_settings(
                        adjusted_difficulty,
                        "combat",
                        request.context
                    ) if request.adjustment_type == "combat" else {},
                    puzzle_settings=self._generate_challenge_settings(
                        adjusted_difficulty,
                        "puzzle",
                        request.context
                    ) if request.adjustment_type == "puzzle" else {},
                    exploration_settings=self._generate_challenge_settings(
                        adjusted_difficulty,
                        "exploration",
                        request.context
                    ) if request.adjustment_type == "exploration" else {},
                    reward_settings=self._calculate_rewards(
                        adjusted_difficulty,
                        request.adjustment_type,
                        {}  # Use generated settings once available
                    ),
                    adaptive_rules={
                        "base_difficulty": base_difficulty,
                        "adjusted_difficulty": adjusted_difficulty,
                        "adjustment_factors": {
                            "performance": request.context.player_performance.dict(),
                            "preferences": request.context.player_preferences
                        }
                    }
                )
                
                response.difficulty_settings.append(settings)
                
                # Store active settings
                self.active_settings[settings.setting_id] = settings
                
                # Update context
                self._update_context(response)
                
                # Generate recommendations
                response.recommendations = self._generate_recommendations(response)
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to process difficulty request: {e}")
            # Return empty response on error
            return DifficultyResponse(
                request_id=str(uuid.uuid4()),
                player_id=request.player_id,
                difficulty_settings=[],
                updated_context=request.context,
                recommendations={},
                cost=0.0
            )
    
    def _update_context(self, response: DifficultyResponse) -> None:
        """Update difficulty context based on generated settings.
        
        Args:
            response: The difficulty response to update context for
        """
        try:
            context = response.updated_context
            
            # Update current difficulty settings
            for settings in response.difficulty_settings:
                context.current_difficulty[settings.type] = (
                    settings.adaptive_rules["adjusted_difficulty"]
                )
            
        except Exception as e:
            logger.error(f"Failed to update difficulty context: {e}")
    
    def _generate_recommendations(
        self,
        response: DifficultyResponse
    ) -> Dict[str, Any]:
        """Generate recommendations based on difficulty settings.
        
        Args:
            response: The difficulty response to generate recommendations for
            
        Returns:
            Dictionary of recommendations
        """
        try:
            recommendations = {
                "content_types": [],
                "challenge_types": [],
                "learning_opportunities": []
            }
            
            # Analyze settings
            for settings in response.difficulty_settings:
                difficulty = settings.adaptive_rules["adjusted_difficulty"]
                
                if difficulty < 0.3:
                    # Easy content recommendations
                    recommendations["content_types"].extend([
                        "tutorial",
                        "practice",
                        "guided"
                    ])
                    recommendations["challenge_types"].extend([
                        "basic",
                        "introductory",
                        "learning"
                    ])
                    recommendations["learning_opportunities"].extend([
                        "skill_tutorials",
                        "basic_mechanics",
                        "guided_practice"
                    ])
                    
                elif difficulty < 0.7:
                    # Medium content recommendations
                    recommendations["content_types"].extend([
                        "standard",
                        "balanced",
                        "progressive"
                    ])
                    recommendations["challenge_types"].extend([
                        "normal",
                        "varied",
                        "engaging"
                    ])
                    recommendations["learning_opportunities"].extend([
                        "skill_improvement",
                        "tactical_learning",
                        "strategy_development"
                    ])
                    
                else:
                    # Hard content recommendations
                    recommendations["content_types"].extend([
                        "advanced",
                        "challenging",
                        "expert"
                    ])
                    recommendations["challenge_types"].extend([
                        "complex",
                        "demanding",
                        "mastery"
                    ])
                    recommendations["learning_opportunities"].extend([
                        "advanced_techniques",
                        "mastery_challenges",
                        "expert_content"
                    ])
            
            # Remove duplicates
            for key in recommendations:
                recommendations[key] = list(set(recommendations[key]))
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to generate recommendations: {e}")
            return {} 