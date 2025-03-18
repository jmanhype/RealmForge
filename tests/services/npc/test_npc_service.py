"""Tests for the NPC generation and management service."""

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

from ....src.services.npc import NPCService
from ....src.models.npc import (
    NPC,
    NPCType,
    Personality,
    Schedule,
    Relationship,
    Profession,
    Stats,
    Inventory
)
from ....src.models.world import Location, Coordinates

@pytest.fixture
def mock_npc_templates() -> Dict[str, Dict[str, Any]]:
    """Create mock NPC templates for testing."""
    return {
        "merchant": {
            "type": NPCType.MERCHANT,
            "base_stats": {
                "charisma": 8,
                "intelligence": 7,
                "strength": 5
            },
            "possible_professions": ["trader", "shopkeeper"],
            "personality_traits": ["friendly", "shrewd"],
            "schedule_template": {
                "morning": "open_shop",
                "afternoon": "trade",
                "evening": "close_shop",
                "night": "sleep"
            }
        },
        "guard": {
            "type": NPCType.GUARD,
            "base_stats": {
                "strength": 8,
                "endurance": 7,
                "perception": 6
            },
            "possible_professions": ["city_guard", "patrol"],
            "personality_traits": ["dutiful", "alert"],
            "schedule_template": {
                "morning": "patrol",
                "afternoon": "guard_post",
                "evening": "patrol",
                "night": "guard_post"
            }
        }
    }

@pytest.fixture
def mock_location() -> Location:
    """Create a mock location for NPC placement."""
    return Location(
        name="Test Town",
        coordinates=Coordinates(x=50, y=0, z=50),
        type="town",
        size=20,
        population=100,
        resources=["food", "water"],
        buildings=["houses", "shops", "guard_post"]
    )

@pytest.fixture
async def npc_service(
    mock_npc_templates: Dict[str, Dict[str, Any]],
    tmp_path: Path,
    mocker: MockerFixture
) -> NPCService:
    """Create an NPCService instance with mocked dependencies."""
    # Create templates file
    templates_path = tmp_path / "npc_templates.json"
    with open(templates_path, "w") as f:
        json.dump(mock_npc_templates, f)
    
    # Mock random number generation for consistency
    mocker.patch("random.random", return_value=0.5)
    mocker.patch("random.choice", side_effect=lambda x: x[0])
    
    # Create service instance
    service = NPCService(templates_path=templates_path)
    await service.initialize()
    
    return service

class TestNPCService:
    """Test suite for NPCService class."""
    
    async def test_npc_generation(
        self,
        npc_service: NPCService,
        mock_location: Location
    ) -> None:
        """Test NPC generation from templates."""
        # Generate merchant NPC
        merchant = await npc_service.generate_npc(
            template_name="merchant",
            location=mock_location,
            name="John Smith"
        )
        
        # Verify NPC properties
        assert merchant.name == "John Smith"
        assert merchant.type == NPCType.MERCHANT
        assert merchant.location == mock_location
        assert merchant.profession in ["trader", "shopkeeper"]
        assert all(trait in merchant.personality.traits 
                  for trait in ["friendly", "shrewd"])
        
        # Verify stats generation
        assert merchant.stats.charisma >= 8  # Base stat
        assert all(0 <= stat <= 10 for stat in merchant.stats.__dict__.values())
    
    async def test_npc_scheduling(
        self,
        npc_service: NPCService,
        mock_location: Location
    ) -> None:
        """Test NPC schedule generation and management."""
        # Generate NPC with schedule
        guard = await npc_service.generate_npc(
            template_name="guard",
            location=mock_location,
            name="Guard Tom"
        )
        
        # Test schedule retrieval
        morning_activity = await npc_service.get_current_activity(
            guard, time_of_day="morning"
        )
        assert morning_activity == "patrol"
        
        night_activity = await npc_service.get_current_activity(
            guard, time_of_day="night"
        )
        assert night_activity == "guard_post"
        
        # Test schedule modification
        new_schedule = Schedule(
            morning="training",
            afternoon="guard_post",
            evening="patrol",
            night="sleep"
        )
        await npc_service.update_schedule(guard, new_schedule)
        
        updated_activity = await npc_service.get_current_activity(
            guard, time_of_day="morning"
        )
        assert updated_activity == "training"
    
    async def test_npc_relationships(
        self,
        npc_service: NPCService,
        mock_location: Location
    ) -> None:
        """Test NPC relationship system."""
        # Create two NPCs
        npc1 = await npc_service.generate_npc(
            template_name="merchant",
            location=mock_location,
            name="Merchant A"
        )
        npc2 = await npc_service.generate_npc(
            template_name="guard",
            location=mock_location,
            name="Guard B"
        )
        
        # Test relationship creation
        relationship = await npc_service.create_relationship(
            npc1, npc2, relationship_type="friendly",
            initial_value=75
        )
        
        # Verify relationship properties
        assert relationship.npc_id == npc1.id
        assert relationship.target_id == npc2.id
        assert relationship.type == "friendly"
        assert relationship.value == 75
        
        # Test relationship modification
        await npc_service.modify_relationship(
            npc1, npc2, change=10, reason="positive_interaction"
        )
        updated_rel = await npc_service.get_relationship(npc1, npc2)
        assert updated_rel.value == 85
    
    async def test_npc_behavior(
        self,
        npc_service: NPCService,
        mock_location: Location
    ) -> None:
        """Test NPC behavior and decision making."""
        npc = await npc_service.generate_npc(
            template_name="merchant",
            location=mock_location,
            name="Test Merchant"
        )
        
        # Test behavior calculation
        behavior = await npc_service.calculate_behavior(
            npc,
            situation="customer_haggling",
            context={"item_value": 100, "offer": 80}
        )
        
        # Verify behavior properties
        assert "action" in behavior
        assert "response" in behavior
        assert behavior["confidence"] > 0
        
        # Test personality influence
        npc.personality.traits.append("greedy")
        greedy_behavior = await npc_service.calculate_behavior(
            npc,
            situation="customer_haggling",
            context={"item_value": 100, "offer": 80}
        )
        assert greedy_behavior["acceptance_chance"] < behavior["acceptance_chance"]
    
    async def test_npc_inventory(
        self,
        npc_service: NPCService,
        mock_location: Location
    ) -> None:
        """Test NPC inventory management."""
        merchant = await npc_service.generate_npc(
            template_name="merchant",
            location=mock_location,
            name="Shop Owner"
        )
        
        # Test inventory initialization
        assert isinstance(merchant.inventory, Inventory)
        
        # Test item addition
        await npc_service.add_item_to_inventory(
            merchant,
            item_id="potion_health",
            quantity=5
        )
        
        # Verify inventory
        assert merchant.inventory.has_item("potion_health")
        assert merchant.inventory.get_quantity("potion_health") == 5
        
        # Test item removal
        await npc_service.remove_item_from_inventory(
            merchant,
            item_id="potion_health",
            quantity=2
        )
        assert merchant.inventory.get_quantity("potion_health") == 3
    
    async def test_npc_persistence(
        self,
        npc_service: NPCService,
        mock_location: Location,
        tmp_path: Path
    ) -> None:
        """Test NPC state persistence."""
        # Generate test NPC
        npc = await npc_service.generate_npc(
            template_name="merchant",
            location=mock_location,
            name="Save Test"
        )
        
        # Save NPC state
        save_path = tmp_path / "npc_save.json"
        await npc_service.save_npc_state(npc, save_path)
        
        # Load NPC state
        loaded_npc = await npc_service.load_npc_state(save_path)
        
        # Verify state preservation
        assert loaded_npc.name == npc.name
        assert loaded_npc.type == npc.type
        assert loaded_npc.stats.__dict__ == npc.stats.__dict__
        assert loaded_npc.personality.traits == npc.personality.traits
    
    async def test_error_handling(
        self,
        npc_service: NPCService,
        mock_location: Location,
        caplog: LogCaptureFixture
    ) -> None:
        """Test error handling in NPC management."""
        # Test invalid template
        with pytest.raises(ValueError):
            await npc_service.generate_npc(
                template_name="nonexistent",
                location=mock_location,
                name="Error Test"
            )
        
        # Test invalid schedule update
        npc = await npc_service.generate_npc(
            template_name="merchant",
            location=mock_location,
            name="Schedule Test"
        )
        
        with pytest.raises(ValueError):
            await npc_service.update_schedule(
                npc,
                Schedule(
                    morning="invalid_activity",
                    afternoon="trade",
                    evening="close_shop",
                    night="sleep"
                )
            )
        
        # Test inventory errors
        with pytest.raises(ValueError):
            await npc_service.remove_item_from_inventory(
                npc,
                item_id="nonexistent_item",
                quantity=1
            )
        
        # Verify error logging
        assert any("Invalid template" in record.message
                  for record in caplog.records)
        assert any("Invalid activity" in record.message
                  for record in caplog.records)
        assert any("Item not found" in record.message
                  for record in caplog.records) 