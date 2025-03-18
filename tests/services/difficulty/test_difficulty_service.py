"""Tests for the difficulty and challenge management service."""

from typing import Any, Dict, List, Optional
import pytest
from unittest.mock import AsyncMock, Mock
import json
from pathlib import Path
import numpy as np

if True:  # TYPE_CHECKING
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture

from ....src.services.difficulty import DifficultyService
from ....src.models.difficulty import (
    DifficultySettings,
    Challenge,
    PlayerStats,
    ChallengeType,
    DifficultyLevel,
    BalanceAdjustment,
    Performance
)

@pytest.fixture
def mock_difficulty_settings() -> DifficultySettings:
    """Create mock difficulty settings for testing."""
    return DifficultySettings(
        base_level=DifficultyLevel.NORMAL,
        scaling_factor=1.0,
        adaptive_difficulty=True,
        challenge_variety=0.7,
        learning_rate=0.1,
        balance_threshold=0.2
    )

@pytest.fixture
def mock_player_stats() -> PlayerStats:
    """Create mock player statistics for testing."""
    return PlayerStats(
        level=5,
        skill_rating=75,
        win_rate=0.6,
        average_completion_time=300,  # seconds
        preferred_challenge_types=[
            ChallengeType.COMBAT,
            ChallengeType.PUZZLE
        ],
        performance_history=[
            Performance(
                challenge_id="test_1",
                success=True,
                completion_time=280,
                attempts=1
            ),
            Performance(
                challenge_id="test_2",
                success=False,
                completion_time=350,
                attempts=3
            )
        ]
    )

@pytest.fixture
def mock_challenge_templates() -> Dict[str, Dict[str, Any]]:
    """Create mock challenge templates for testing."""
    return {
        "combat_basic": {
            "type": ChallengeType.COMBAT,
            "base_difficulty": 1.0,
            "scaling_attributes": ["enemy_level", "enemy_count"],
            "reward_scaling": {"experience": 100, "gold": 50},
            "completion_criteria": {
                "enemies_defeated": "all",
                "time_limit": 600
            }
        },
        "puzzle_advanced": {
            "type": ChallengeType.PUZZLE,
            "base_difficulty": 2.0,
            "scaling_attributes": ["complexity", "time_pressure"],
            "reward_scaling": {"experience": 150, "items": ["rare_key"]},
            "completion_criteria": {
                "solution_found": True,
                "time_limit": 300
            }
        }
    }

@pytest.fixture
async def difficulty_service(
    mock_difficulty_settings: DifficultySettings,
    mock_challenge_templates: Dict[str, Dict[str, Any]],
    tmp_path: Path
) -> DifficultyService:
    """Create a DifficultyService instance with mocked dependencies."""
    # Create templates file
    templates_path = tmp_path / "challenge_templates.json"
    with open(templates_path, "w") as f:
        json.dump(mock_challenge_templates, f)
    
    # Create service instance
    service = DifficultyService(
        settings=mock_difficulty_settings,
        templates_path=templates_path
    )
    await service.initialize()
    
    return service

class TestDifficultyService:
    """Test suite for DifficultyService class."""
    
    async def test_difficulty_calculation(
        self,
        difficulty_service: DifficultyService,
        mock_player_stats: PlayerStats
    ) -> None:
        """Test difficulty calculation based on player stats."""
        # Calculate base difficulty
        difficulty = await difficulty_service.calculate_difficulty(
            player_stats=mock_player_stats,
            challenge_type=ChallengeType.COMBAT
        )
        
        # Verify difficulty properties
        assert isinstance(difficulty, float)
        assert 0.5 <= difficulty <= 2.0  # Reasonable range
        
        # Test difficulty scaling with different stats
        higher_stats = PlayerStats(
            level=10,
            skill_rating=90,
            win_rate=0.8,
            average_completion_time=250
        )
        
        higher_difficulty = await difficulty_service.calculate_difficulty(
            player_stats=higher_stats,
            challenge_type=ChallengeType.COMBAT
        )
        
        assert higher_difficulty > difficulty
    
    async def test_challenge_generation(
        self,
        difficulty_service: DifficultyService,
        mock_player_stats: PlayerStats
    ) -> None:
        """Test challenge generation and scaling."""
        # Generate combat challenge
        challenge = await difficulty_service.generate_challenge(
            template_name="combat_basic",
            player_stats=mock_player_stats
        )
        
        # Verify challenge properties
        assert challenge.type == ChallengeType.COMBAT
        assert challenge.difficulty > 0
        assert len(challenge.objectives) > 0
        assert challenge.time_limit == 600
        
        # Test reward scaling
        assert challenge.rewards["experience"] >= 100  # Base reward
        assert challenge.rewards["gold"] >= 50
        
        # Test challenge scaling
        scaled_challenge = await difficulty_service.scale_challenge(
            challenge,
            scaling_factor=1.5
        )
        
        assert scaled_challenge.difficulty > challenge.difficulty
        assert scaled_challenge.rewards["experience"] > challenge.rewards["experience"]
    
    async def test_adaptive_difficulty(
        self,
        difficulty_service: DifficultyService,
        mock_player_stats: PlayerStats
    ) -> None:
        """Test adaptive difficulty adjustments."""
        # Track initial difficulty
        initial_difficulty = difficulty_service.settings.base_level
        
        # Simulate successful challenges
        for _ in range(5):
            await difficulty_service.record_performance(
                player_stats=mock_player_stats,
                performance=Performance(
                    challenge_id="test",
                    success=True,
                    completion_time=250,  # Better than average
                    attempts=1
                )
            )
        
        # Verify difficulty increase
        new_difficulty = await difficulty_service.get_current_difficulty(
            player_stats=mock_player_stats
        )
        assert new_difficulty > initial_difficulty
        
        # Simulate failures
        for _ in range(3):
            await difficulty_service.record_performance(
                player_stats=mock_player_stats,
                performance=Performance(
                    challenge_id="test",
                    success=False,
                    completion_time=400,
                    attempts=3
                )
            )
        
        # Verify difficulty decrease
        adjusted_difficulty = await difficulty_service.get_current_difficulty(
            player_stats=mock_player_stats
        )
        assert adjusted_difficulty < new_difficulty
    
    async def test_balance_adjustments(
        self,
        difficulty_service: DifficultyService,
        mock_player_stats: PlayerStats
    ) -> None:
        """Test balance adjustments and tuning."""
        # Generate initial challenge
        challenge = await difficulty_service.generate_challenge(
            template_name="combat_basic",
            player_stats=mock_player_stats
        )
        
        # Create balance adjustment
        adjustment = BalanceAdjustment(
            attribute="enemy_count",
            change=-0.2,
            reason="excessive_difficulty"
        )
        
        # Apply balance adjustment
        adjusted_challenge = await difficulty_service.apply_balance_adjustment(
            challenge,
            adjustment
        )
        
        # Verify adjustments
        assert adjusted_challenge.parameters["enemy_count"] < challenge.parameters["enemy_count"]
        
        # Test automatic balance detection
        imbalance = await difficulty_service.detect_imbalance(
            player_stats=mock_player_stats,
            challenge_type=ChallengeType.COMBAT
        )
        
        assert isinstance(imbalance, dict)
        assert "severity" in imbalance
        assert "recommended_adjustments" in imbalance
    
    async def test_challenge_variety(
        self,
        difficulty_service: DifficultyService,
        mock_player_stats: PlayerStats
    ) -> None:
        """Test challenge variety and selection."""
        # Generate multiple challenges
        challenges = []
        for _ in range(10):
            challenge = await difficulty_service.generate_varied_challenge(
                player_stats=mock_player_stats
            )
            challenges.append(challenge)
        
        # Verify variety
        challenge_types = {c.type for c in challenges}
        assert len(challenge_types) > 1
        
        # Test challenge selection based on player preference
        preferred_challenge = await difficulty_service.select_challenge(
            player_stats=mock_player_stats,
            available_challenges=challenges
        )
        
        assert preferred_challenge.type in mock_player_stats.preferred_challenge_types
    
    async def test_performance_analysis(
        self,
        difficulty_service: DifficultyService,
        mock_player_stats: PlayerStats
    ) -> None:
        """Test performance analysis and feedback."""
        # Record multiple performances
        performances = [
            Performance(
                challenge_id="test_1",
                success=True,
                completion_time=280,
                attempts=1
            ),
            Performance(
                challenge_id="test_2",
                success=False,
                completion_time=350,
                attempts=2
            ),
            Performance(
                challenge_id="test_3",
                success=True,
                completion_time=300,
                attempts=1
            )
        ]
        
        for perf in performances:
            await difficulty_service.record_performance(
                player_stats=mock_player_stats,
                performance=perf
            )
        
        # Generate performance analysis
        analysis = await difficulty_service.analyze_performance(
            player_stats=mock_player_stats
        )
        
        # Verify analysis
        assert "success_rate" in analysis
        assert "average_completion_time" in analysis
        assert "trend" in analysis
        assert isinstance(analysis["success_rate"], float)
        
        # Test feedback generation
        feedback = await difficulty_service.generate_feedback(
            player_stats=mock_player_stats,
            analysis=analysis
        )
        
        assert isinstance(feedback, dict)
        assert "recommendations" in feedback
        assert "areas_for_improvement" in feedback
    
    async def test_error_handling(
        self,
        difficulty_service: DifficultyService,
        mock_player_stats: PlayerStats,
        caplog: LogCaptureFixture
    ) -> None:
        """Test error handling in difficulty management."""
        # Test invalid template
        with pytest.raises(ValueError):
            await difficulty_service.generate_challenge(
                template_name="nonexistent",
                player_stats=mock_player_stats
            )
        
        # Test invalid scaling factor
        challenge = await difficulty_service.generate_challenge(
            template_name="combat_basic",
            player_stats=mock_player_stats
        )
        
        with pytest.raises(ValueError):
            await difficulty_service.scale_challenge(
                challenge,
                scaling_factor=-1.0
            )
        
        # Test invalid performance data
        with pytest.raises(ValueError):
            await difficulty_service.record_performance(
                player_stats=mock_player_stats,
                performance=Performance(
                    challenge_id="test",
                    success=True,
                    completion_time=-100,  # Invalid time
                    attempts=0  # Invalid attempts
                )
            )
        
        # Verify error logging
        assert any("Template not found" in record.message
                  for record in caplog.records)
        assert any("Invalid scaling factor" in record.message
                  for record in caplog.records)
        assert any("Invalid performance data" in record.message
                  for record in caplog.records) 