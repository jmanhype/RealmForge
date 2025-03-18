"""Tests for the world generation and management service."""

from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
import pytest
import numpy as np
from unittest.mock import AsyncMock, Mock

if True:  # TYPE_CHECKING
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture

from ....src.services.world import WorldService
from ....src.models.world import (
    TerrainType,
    Location,
    WorldSettings,
    BiomeType,
    Climate,
    Coordinates
)

@pytest.fixture
def world_settings() -> WorldSettings:
    """Create mock world settings for testing."""
    return WorldSettings(
        size=(100, 100),
        seed=12345,
        biome_distribution={
            BiomeType.FOREST: 0.3,
            BiomeType.PLAINS: 0.3,
            BiomeType.MOUNTAINS: 0.2,
            BiomeType.DESERT: 0.2
        },
        climate=Climate(
            temperature_range=(-10, 40),
            rainfall_range=(0, 1000),
            seasonal_variation=0.2
        ),
        terrain_complexity=0.7,
        water_level=0.4
    )

@pytest.fixture
def mock_heightmap() -> np.ndarray:
    """Create a mock heightmap for testing."""
    return np.random.rand(100, 100)

@pytest.fixture
async def world_service(
    world_settings: WorldSettings,
    mock_heightmap: np.ndarray,
    mocker: MockerFixture
) -> WorldService:
    """Create a WorldService instance with mocked dependencies."""
    # Mock the noise generator
    noise_mock = mocker.patch('noise.snoise2')
    noise_mock.return_value = 0.5
    
    # Create service instance
    service = WorldService(world_settings)
    
    # Mock internal heightmap
    service._heightmap = mock_heightmap
    
    return service

class TestWorldService:
    """Test suite for WorldService class."""
    
    async def test_world_initialization(
        self,
        world_service: WorldService,
        world_settings: WorldSettings
    ) -> None:
        """Test world initialization with settings."""
        assert world_service.settings == world_settings
        assert world_service.size == world_settings.size
        assert isinstance(world_service._heightmap, np.ndarray)
        assert world_service._heightmap.shape == world_settings.size
    
    async def test_terrain_generation(
        self,
        world_service: WorldService,
        mock_heightmap: np.ndarray
    ) -> None:
        """Test terrain generation functionality."""
        # Generate terrain
        terrain_map = await world_service.generate_terrain()
        
        # Verify terrain properties
        assert isinstance(terrain_map, np.ndarray)
        assert terrain_map.shape == world_service.size
        assert np.all((terrain_map >= 0) & (terrain_map <= 1))
        
        # Test terrain type assignment
        terrain_types = await world_service.get_terrain_types()
        assert isinstance(terrain_types, np.ndarray)
        assert terrain_types.shape == world_service.size
        assert all(t in TerrainType for t in np.unique(terrain_types))
    
    async def test_biome_distribution(
        self,
        world_service: WorldService
    ) -> None:
        """Test biome distribution and climate influence."""
        # Generate biomes
        biome_map = await world_service.generate_biomes()
        
        # Verify biome distribution
        unique_biomes, counts = np.unique(biome_map, return_counts=True)
        distribution = {b: c/biome_map.size for b, c in zip(unique_biomes, counts)}
        
        # Check if distribution roughly matches settings
        for biome, target_ratio in world_service.settings.biome_distribution.items():
            if biome in distribution:
                # Allow for 10% deviation from target
                assert abs(distribution[biome] - target_ratio) < 0.1
    
    async def test_location_management(
        self,
        world_service: WorldService
    ) -> None:
        """Test location creation and management."""
        # Create test location
        location = Location(
            name="Test Village",
            coordinates=Coordinates(x=50, y=0, z=50),
            type="village",
            size=10,
            population=100,
            resources=["wood", "iron"],
            buildings=["house", "blacksmith"]
        )
        
        # Add location
        await world_service.add_location(location)
        
        # Verify location retrieval
        retrieved = await world_service.get_location("Test Village")
        assert retrieved == location
        
        # Test location search
        nearby = await world_service.find_locations_in_radius(
            center=location.coordinates,
            radius=20
        )
        assert len(nearby) >= 1
        assert location in nearby
    
    async def test_pathfinding(
        self,
        world_service: WorldService
    ) -> None:
        """Test pathfinding between locations."""
        # Create two test locations
        start = Location(
            name="Start Town",
            coordinates=Coordinates(x=20, y=0, z=20),
            type="town"
        )
        end = Location(
            name="End City",
            coordinates=Coordinates(x=80, y=0, z=80),
            type="city"
        )
        
        await world_service.add_location(start)
        await world_service.add_location(end)
        
        # Find path
        path = await world_service.find_path(
            start=start.coordinates,
            end=end.coordinates
        )
        
        # Verify path properties
        assert path is not None
        assert len(path) > 0
        assert path[0] == start.coordinates
        assert path[-1] == end.coordinates
        
        # Verify path is traversable
        for coord in path:
            terrain_type = await world_service.get_terrain_at(coord)
            assert terrain_type != TerrainType.WATER
            assert terrain_type != TerrainType.MOUNTAIN_PEAK
    
    async def test_climate_system(
        self,
        world_service: WorldService
    ) -> None:
        """Test climate system and weather patterns."""
        # Get climate data for a location
        coords = Coordinates(x=50, y=0, z=50)
        climate_data = await world_service.get_climate_at(coords)
        
        # Verify climate properties
        assert climate_data.temperature >= world_service.settings.climate.temperature_range[0]
        assert climate_data.temperature <= world_service.settings.climate.temperature_range[1]
        assert climate_data.rainfall >= world_service.settings.climate.rainfall_range[0]
        assert climate_data.rainfall <= world_service.settings.climate.rainfall_range[1]
        
        # Test seasonal variations
        summer_climate = await world_service.get_climate_at(coords, season="summer")
        winter_climate = await world_service.get_climate_at(coords, season="winter")
        assert summer_climate.temperature > winter_climate.temperature
    
    async def test_resource_distribution(
        self,
        world_service: WorldService
    ) -> None:
        """Test natural resource distribution and management."""
        # Generate resource map
        resources = await world_service.generate_resources()
        
        # Verify resource distribution
        assert isinstance(resources, dict)
        for resource_type, resource_map in resources.items():
            assert isinstance(resource_map, np.ndarray)
            assert resource_map.shape == world_service.size
            assert np.all((resource_map >= 0) & (resource_map <= 1))
    
    async def test_error_handling(
        self,
        world_service: WorldService,
        caplog: LogCaptureFixture
    ) -> None:
        """Test error handling in world generation and management."""
        # Test invalid coordinates
        invalid_coords = Coordinates(x=-1, y=0, z=101)
        with pytest.raises(ValueError):
            await world_service.get_terrain_at(invalid_coords)
        
        # Test nonexistent location
        assert await world_service.get_location("Nonexistent") is None
        assert any("Location not found" in record.message
                  for record in caplog.records)
        
        # Test invalid path
        unreachable_end = Coordinates(x=1000, y=0, z=1000)
        with pytest.raises(ValueError):
            await world_service.find_path(
                start=Coordinates(x=0, y=0, z=0),
                end=unreachable_end
            )
    
    async def test_world_persistence(
        self,
        world_service: WorldService,
        tmp_path: Path
    ) -> None:
        """Test world state saving and loading."""
        # Generate world state
        await world_service.generate_terrain()
        await world_service.generate_biomes()
        
        # Save world state
        save_path = tmp_path / "world_save.json"
        await world_service.save_world_state(save_path)
        
        # Create new service and load state
        new_service = WorldService(world_service.settings)
        await new_service.load_world_state(save_path)
        
        # Verify state was preserved
        assert np.array_equal(new_service._heightmap, world_service._heightmap)
        assert new_service.size == world_service.size
        
        # Verify locations were preserved
        test_location = Location(
            name="Test Town",
            coordinates=Coordinates(x=50, y=0, z=50),
            type="town"
        )
        await world_service.add_location(test_location)
        await world_service.save_world_state(save_path)
        await new_service.load_world_state(save_path)
        
        loaded_location = await new_service.get_location("Test Town")
        assert loaded_location == test_location 