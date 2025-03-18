"""Tests for the narrative generation and management service."""

from typing import Any, Dict, List, Optional
import pytest
from unittest.mock import AsyncMock, Mock
import json
from pathlib import Path

if True:  # TYPE_CHECKING
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture

from ....src.services.narrative import NarrativeService
from ....src.models.narrative import (
    Story,
    Quest,
    Dialogue,
    StoryNode,
    QuestState,
    DialogueNode,
    StoryEvent,
    QuestReward,
    DialogueChoice
)
from ....src.models.npc import NPC, NPCType
from ....src.models.world import Location, Coordinates

@pytest.fixture
def mock_story_templates() -> Dict[str, Dict[str, Any]]:
    """Create mock story templates for testing."""
    return {
        "rescue_mission": {
            "title": "The Missing Merchant",
            "description": "A merchant has gone missing on the road to {target_location}",
            "type": "rescue",
            "difficulty": "medium",
            "required_npcs": ["victim", "antagonist"],
            "locations": ["start_town", "bandit_camp", "target_location"],
            "events": [
                {"type": "introduction", "location": "start_town"},
                {"type": "investigation", "location": "road"},
                {"type": "confrontation", "location": "bandit_camp"},
                {"type": "resolution", "location": "start_town"}
            ]
        },
        "fetch_quest": {
            "title": "Rare Ingredients",
            "description": "Collect rare herbs from {target_location}",
            "type": "collection",
            "difficulty": "easy",
            "required_items": ["herb_moonflower", "herb_sunleaf"],
            "locations": ["herb_garden", "forest"],
            "time_limit": 48  # hours
        }
    }

@pytest.fixture
def mock_dialogue_templates() -> Dict[str, Dict[str, Any]]:
    """Create mock dialogue templates for testing."""
    return {
        "merchant_greeting": {
            "initial": "Welcome to my shop, {player_name}!",
            "responses": {
                "browse": {
                    "text": "I'd like to see your wares",
                    "action": "open_shop"
                },
                "quest": {
                    "text": "Do you have any work available?",
                    "action": "offer_quest",
                    "conditions": {"min_reputation": 10}
                },
                "leave": {
                    "text": "Goodbye",
                    "action": "end_dialogue"
                }
            }
        },
        "quest_offer": {
            "initial": "I need help with {quest_description}",
            "responses": {
                "accept": {
                    "text": "I'll help you",
                    "action": "accept_quest"
                },
                "decline": {
                    "text": "Not interested",
                    "action": "decline_quest"
                },
                "negotiate": {
                    "text": "Let's discuss the reward",
                    "action": "negotiate_reward",
                    "conditions": {"min_charisma": 7}
                }
            }
        }
    }

@pytest.fixture
def mock_location() -> Location:
    """Create a mock location for story placement."""
    return Location(
        name="Test Town",
        coordinates=Coordinates(x=50, y=0, z=50),
        type="town",
        size=20,
        population=100
    )

@pytest.fixture
def mock_npc() -> NPC:
    """Create a mock NPC for dialogue testing."""
    return NPC(
        name="Test Merchant",
        type=NPCType.MERCHANT,
        location=mock_location(),
        level=5
    )

@pytest.fixture
async def narrative_service(
    mock_story_templates: Dict[str, Dict[str, Any]],
    mock_dialogue_templates: Dict[str, Dict[str, Any]],
    tmp_path: Path,
    mocker: MockerFixture
) -> NarrativeService:
    """Create a NarrativeService instance with mocked dependencies."""
    # Create template files
    story_path = tmp_path / "story_templates.json"
    dialogue_path = tmp_path / "dialogue_templates.json"
    
    with open(story_path, "w") as f:
        json.dump(mock_story_templates, f)
    with open(dialogue_path, "w") as f:
        json.dump(mock_dialogue_templates, f)
    
    # Create service instance
    service = NarrativeService(
        story_templates_path=story_path,
        dialogue_templates_path=dialogue_path
    )
    await service.initialize()
    
    return service

class TestNarrativeService:
    """Test suite for NarrativeService class."""
    
    async def test_story_generation(
        self,
        narrative_service: NarrativeService,
        mock_location: Location
    ) -> None:
        """Test story generation from templates."""
        # Generate rescue mission story
        story = await narrative_service.generate_story(
            template_name="rescue_mission",
            start_location=mock_location,
            parameters={
                "target_location": "Forest Outpost",
                "difficulty_modifier": 1.0
            }
        )
        
        # Verify story properties
        assert story.title == "The Missing Merchant"
        assert "Forest Outpost" in story.description
        assert story.type == "rescue"
        assert story.difficulty == "medium"
        assert len(story.events) == 4
        assert story.start_location == mock_location
    
    async def test_quest_management(
        self,
        narrative_service: NarrativeService,
        mock_location: Location,
        mock_npc: NPC
    ) -> None:
        """Test quest generation and management."""
        # Generate fetch quest
        quest = await narrative_service.generate_quest(
            template_name="fetch_quest",
            giver=mock_npc,
            location=mock_location
        )
        
        # Verify quest properties
        assert quest.title == "Rare Ingredients"
        assert quest.giver == mock_npc
        assert quest.state == QuestState.AVAILABLE
        assert quest.time_limit == 48
        assert len(quest.required_items) == 2
        
        # Test quest state management
        await narrative_service.update_quest_state(
            quest,
            new_state=QuestState.ACTIVE,
            progress={"collected_items": ["herb_moonflower"]}
        )
        
        assert quest.state == QuestState.ACTIVE
        assert quest.progress["collected_items"] == ["herb_moonflower"]
        
        # Test quest completion
        reward = QuestReward(
            experience=100,
            gold=50,
            items=["potion_healing"]
        )
        await narrative_service.complete_quest(quest, reward)
        
        assert quest.state == QuestState.COMPLETED
        assert quest.reward == reward
    
    async def test_dialogue_system(
        self,
        narrative_service: NarrativeService,
        mock_npc: NPC
    ) -> None:
        """Test dialogue generation and flow."""
        # Start dialogue
        dialogue = await narrative_service.start_dialogue(
            template_name="merchant_greeting",
            npc=mock_npc,
            parameters={"player_name": "Adventurer"}
        )
        
        # Verify dialogue properties
        assert isinstance(dialogue, Dialogue)
        assert "Welcome to my shop, Adventurer!" in dialogue.current_node.text
        assert len(dialogue.current_node.choices) == 3
        
        # Test dialogue progression
        next_node = await narrative_service.make_dialogue_choice(
            dialogue,
            choice="browse"
        )
        assert next_node.action == "open_shop"
        
        # Test conditional responses
        choices = dialogue.current_node.choices
        quest_choice = next(c for c in choices if c.text == "Do you have any work available?")
        assert quest_choice.conditions["min_reputation"] == 10
    
    async def test_story_branching(
        self,
        narrative_service: NarrativeService,
        mock_location: Location
    ) -> None:
        """Test story branching and consequence system."""
        # Create branching story
        story = await narrative_service.generate_story(
            template_name="rescue_mission",
            start_location=mock_location,
            parameters={"allow_branching": True}
        )
        
        # Add story branch
        branch_event = StoryEvent(
            type="alternative_resolution",
            location=mock_location,
            description="Negotiate with bandits",
            conditions={"charisma": 8}
        )
        
        await narrative_service.add_story_branch(
            story,
            branch_point="confrontation",
            branch_event=branch_event
        )
        
        # Verify branching
        assert len(story.branches) > 0
        assert any(b.event.type == "alternative_resolution" 
                  for b in story.branches)
        
        # Test consequence system
        consequence = await narrative_service.calculate_consequence(
            story,
            choice="negotiate",
            context={"player_charisma": 9}
        )
        
        assert consequence["success"] is True
        assert "reputation" in consequence["effects"]
    
    async def test_dynamic_dialogue(
        self,
        narrative_service: NarrativeService,
        mock_npc: NPC
    ) -> None:
        """Test dynamic dialogue generation based on context."""
        # Generate dialogue with context
        context = {
            "reputation": 20,
            "previous_interactions": ["completed_quest"],
            "time_of_day": "morning"
        }
        
        dialogue = await narrative_service.generate_dynamic_dialogue(
            npc=mock_npc,
            context=context
        )
        
        # Verify context influence
        assert dialogue.context == context
        assert any(c.conditions.get("min_reputation", 0) <= context["reputation"]
                  for c in dialogue.current_node.choices)
        
        # Test response generation
        response = await narrative_service.generate_npc_response(
            npc=mock_npc,
            player_input="Tell me about the town",
            context=context
        )
        
        assert isinstance(response, DialogueNode)
        assert response.text is not None
        assert len(response.choices) > 0
    
    async def test_quest_integration(
        self,
        narrative_service: NarrativeService,
        mock_location: Location,
        mock_npc: NPC
    ) -> None:
        """Test integration between quests and dialogue."""
        # Generate quest
        quest = await narrative_service.generate_quest(
            template_name="fetch_quest",
            giver=mock_npc,
            location=mock_location
        )
        
        # Generate quest dialogue
        dialogue = await narrative_service.generate_quest_dialogue(
            quest=quest,
            stage="offer"
        )
        
        # Verify quest-dialogue integration
        assert quest.title in dialogue.current_node.text
        assert any(c.action == "accept_quest" 
                  for c in dialogue.current_node.choices)
        
        # Test quest updates through dialogue
        await narrative_service.make_dialogue_choice(
            dialogue,
            choice="accept"
        )
        assert quest.state == QuestState.ACTIVE
    
    async def test_error_handling(
        self,
        narrative_service: NarrativeService,
        mock_location: Location,
        mock_npc: NPC,
        caplog: LogCaptureFixture
    ) -> None:
        """Test error handling in narrative systems."""
        # Test invalid template
        with pytest.raises(ValueError):
            await narrative_service.generate_story(
                template_name="nonexistent",
                start_location=mock_location
            )
        
        # Test invalid dialogue choice
        dialogue = await narrative_service.start_dialogue(
            template_name="merchant_greeting",
            npc=mock_npc,
            parameters={"player_name": "Adventurer"}
        )
        
        with pytest.raises(ValueError):
            await narrative_service.make_dialogue_choice(
                dialogue,
                choice="invalid_choice"
            )
        
        # Test invalid quest state transition
        quest = await narrative_service.generate_quest(
            template_name="fetch_quest",
            giver=mock_npc,
            location=mock_location
        )
        
        with pytest.raises(ValueError):
            await narrative_service.update_quest_state(
                quest,
                new_state=QuestState.COMPLETED  # Can't complete without being active
            )
        
        # Verify error logging
        assert any("Template not found" in record.message
                  for record in caplog.records)
        assert any("Invalid dialogue choice" in record.message
                  for record in caplog.records)
        assert any("Invalid quest state transition" in record.message
                  for record in caplog.records) 