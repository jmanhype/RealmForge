"""Tests for the scene generator service."""

from typing import Any, Dict, List, Optional
from pathlib import Path
import json
import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch

if True:  # TYPE_CHECKING
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture

from ...models.visualization import (
    SceneRequest,
    SceneResponse,
    SceneDefinition,
    ObjectDefinition,
    Vector3
)
from ..assets.asset_manager import AssetManager
from ..assets.asset_types import Template, Texture
from ..services.visualization.scene_generator import SceneGenerator
from ..services.visualization.template_manager import TemplateManager
from ..services.visualization.animation_system import AnimationSystem

# Test Data
@pytest.fixture
def mock_template() -> Dict[str, Any]:
    """Create a mock template for testing."""
    return {
        "name": "test_template",
        "objects": [
            {
                "name": "ground",
                "geometry": {
                    "type": "PlaneGeometry",
                    "parameters": [50, 50]
                },
                "material": {
                    "type": "MeshStandardMaterial",
                    "color": 0x808080
                },
                "position": {"x": 0, "y": 0, "z": 0},
                "rotation": {"x": -3.14159/2, "y": 0, "z": 0}
            }
        ],
        "lights": [
            {
                "type": "ambient",
                "color": 0xffffff,
                "intensity": 0.5
            }
        ],
        "camera": {
            "position": {"x": 0, "y": 5, "z": 10},
            "target": {"x": 0, "y": 0, "z": 0}
        }
    }

@pytest.fixture
def mock_location_data() -> Dict[str, Any]:
    """Create mock location data for testing."""
    return {
        "type": "dungeon",
        "size": {"width": 50, "length": 50, "height": 10},
        "terrain": {
            "type": "stone",
            "roughness": 0.7,
            "features": ["cracks", "moss"]
        },
        "decorations": [
            {"type": "torch", "positions": [[2, 0], [8, 0]]},
            {"type": "chest", "position": [5, 8]}
        ]
    }

@pytest.fixture
def mock_quality_presets() -> Dict[str, Dict[str, Any]]:
    """Create mock quality presets for testing."""
    return {
        "low": {
            "shadows_enabled": False,
            "shadow_map_size": 512,
            "ssao_enabled": False,
            "bloom_enabled": False
        },
        "medium": {
            "shadows_enabled": True,
            "shadow_map_size": 1024,
            "ssao_enabled": True,
            "bloom_enabled": True
        },
        "high": {
            "shadows_enabled": True,
            "shadow_map_size": 2048,
            "ssao_enabled": True,
            "bloom_enabled": True
        }
    }

@pytest.fixture
async def scene_generator(
    tmp_path: Path,
    mock_quality_presets: Dict[str, Dict[str, Any]],
    mocker: MockerFixture
) -> SceneGenerator:
    """Create a SceneGenerator instance for testing."""
    # Create mock template file
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    template_file = template_dir / "test_template.json"
    template_file.write_text(json.dumps(mock_template()))
    
    # Mock asset manager
    mock_asset_manager = AsyncMock(spec=AssetManager)
    mock_asset_manager.get_texture.return_value = Texture(
        id=UUID('00000000-0000-0000-0000-000000000000'),
        name="test_texture",
        type="test"
    )
    
    return SceneGenerator(
        asset_manager=mock_asset_manager,
        template_path=template_dir,
        quality_presets=mock_quality_presets
    )

class TestSceneGenerator:
    """Test suite for SceneGenerator class."""
    
    async def test_generate_scene_basic(
        self,
        scene_generator: SceneGenerator,
        mock_location_data: Dict[str, Any],
        mocker: MockerFixture
    ) -> None:
        """Test basic scene generation with valid inputs."""
        # Mock location data retrieval
        mocker.patch.object(
            scene_generator,
            '_get_location_data',
            return_value=mock_location_data
        )
        
        # Create scene request
        request = SceneRequest(
            location_id=UUID('00000000-0000-0000-0000-000000000000'),
            template_name="test_template",
            quality_level="medium"
        )
        
        # Generate scene
        response = await scene_generator.generate_scene(request)
        
        # Verify basic scene structure
        assert isinstance(response, SceneResponse)
        assert response.scene_id == request.location_id
        assert isinstance(response.scene_definition, SceneDefinition)
        assert len(response.scene_definition.objects) > 0
        assert len(response.scene_definition.lights) > 0
        assert response.scene_definition.camera is not None
    
    async def test_generate_scene_with_terrain_features(
        self,
        scene_generator: SceneGenerator,
        mock_location_data: Dict[str, Any],
        mocker: MockerFixture
    ) -> None:
        """Test scene generation with terrain features (cracks and moss)."""
        mocker.patch.object(
            scene_generator,
            '_get_location_data',
            return_value=mock_location_data
        )
        
        request = SceneRequest(
            location_id=UUID('00000000-0000-0000-0000-000000000000'),
            template_name="test_template",
            quality_level="high"
        )
        
        response = await scene_generator.generate_scene(request)
        
        # Verify terrain features
        objects = response.scene_definition.objects
        assert any(obj.name.startswith("crack_decal_") for obj in objects)
        assert any(obj.name == "moss_patches" for obj in objects)
        
        # Verify moss patch configuration
        moss_obj = next(obj for obj in objects if obj.name == "moss_patches")
        assert moss_obj.geometry["type"] == "InstancedMesh"
        assert "instance_data" in moss_obj
        assert len(moss_obj.instance_data["positions"]) > 0
    
    async def test_generate_scene_with_interactive_objects(
        self,
        scene_generator: SceneGenerator,
        mock_location_data: Dict[str, Any],
        mocker: MockerFixture
    ) -> None:
        """Test scene generation with interactive objects."""
        # Add interactive objects to mock data
        mock_data = mock_location_data.copy()
        mock_data["interactive_objects"] = [
            {
                "type": "door",
                "position": [5, 0, 5],
                "style": "medieval"
            },
            {
                "type": "lever",
                "position": [3, 1, 3],
                "trigger_event": "open_door"
            }
        ]
        
        mocker.patch.object(
            scene_generator,
            '_get_location_data',
            return_value=mock_data
        )
        
        request = SceneRequest(
            location_id=UUID('00000000-0000-0000-0000-000000000000'),
            template_name="test_template",
            quality_level="medium"
        )
        
        response = await scene_generator.generate_scene(request)
        
        # Verify interactive objects
        objects = response.scene_definition.objects
        assert any(obj.name.startswith("door_") for obj in objects)
        assert any(obj.name.startswith("lever_") for obj in objects)
        
        # Verify interaction system setup
        assert "interaction_system" in response.scene_definition
        assert response.scene_definition.interaction_system["raycaster"]["enabled"]
    
    async def test_generate_scene_with_animations(
        self,
        scene_generator: SceneGenerator,
        mock_location_data: Dict[str, Any],
        mocker: MockerFixture
    ) -> None:
        """Test scene generation with animation sequences and chains."""
        # Add animations to mock data
        mock_data = mock_location_data.copy()
        mock_data["interactive_objects"] = [
            {
                "type": "chest",
                "position": [5, 0, 5],
                "animation_sequence": {
                    "name": "chest_open",
                    "animations": [
                        {
                            "name": "opening",
                            "duration": 0.5,
                            "keyframes": [
                                {
                                    "time": 0,
                                    "rotation": {"x": 0, "y": 0, "z": 0}
                                },
                                {
                                    "time": 0.5,
                                    "rotation": {"x": -1.57, "y": 0, "z": 0}
                                }
                            ]
                        }
                    ]
                }
            }
        ]
        
        mocker.patch.object(
            scene_generator,
            '_get_location_data',
            return_value=mock_data
        )
        
        request = SceneRequest(
            location_id=UUID('00000000-0000-0000-0000-000000000000'),
            template_name="test_template",
            quality_level="medium"
        )
        
        response = await scene_generator.generate_scene(request)
        
        # Verify animations
        assert "animations" in response.scene_definition
        animations = response.scene_definition.animations
        assert any(anim["type"] == "sequence" for anim in animations)
        
        # Verify animation code generation
        assert "Animations" in response.scene_code
        assert "Timeline" in response.scene_code
    
    async def test_generate_scene_error_handling(
        self,
        scene_generator: SceneGenerator,
        mocker: MockerFixture
    ) -> None:
        """Test error handling in scene generation."""
        # Test with invalid template
        request = SceneRequest(
            location_id=UUID('00000000-0000-0000-0000-000000000000'),
            template_name="nonexistent_template",
            quality_level="medium"
        )
        
        with pytest.raises(ValueError, match="Template not found"):
            await scene_generator.generate_scene(request)
        
        # Test with missing location data
        mocker.patch.object(
            scene_generator,
            '_get_location_data',
            return_value=None
        )
        
        request.template_name = "test_template"
        response = await scene_generator.generate_scene(request)
        
        # Should still generate basic scene without location-specific features
        assert isinstance(response, SceneResponse)
        assert len(response.scene_definition.objects) > 0
    
    async def test_quality_settings_application(
        self,
        scene_generator: SceneGenerator,
        mock_location_data: Dict[str, Any],
        mocker: MockerFixture
    ) -> None:
        """Test application of different quality settings."""
        mocker.patch.object(
            scene_generator,
            '_get_location_data',
            return_value=mock_location_data
        )
        
        # Test low quality
        request = SceneRequest(
            location_id=UUID('00000000-0000-0000-0000-000000000000'),
            template_name="test_template",
            quality_level="low"
        )
        
        response = await scene_generator.generate_scene(request)
        assert not any(
            effect["type"] == "ssao"
            for effect in response.scene_definition.post_processing
        )
        
        # Test high quality
        request.quality_level = "high"
        response = await scene_generator.generate_scene(request)
        assert any(
            effect["type"] == "ssao"
            for effect in response.scene_definition.post_processing
        )
        assert response.scene_definition.lights[0].shadow_map_size == 2048
    
    async def test_asset_management_integration(
        self,
        scene_generator: SceneGenerator,
        mock_location_data: Dict[str, Any],
        mocker: MockerFixture
    ) -> None:
        """Test integration with asset management system."""
        mocker.patch.object(
            scene_generator,
            '_get_location_data',
            return_value=mock_location_data
        )
        
        # Mock texture retrieval
        texture_id = UUID('11111111-1111-1111-1111-111111111111')
        mock_texture = Texture(id=texture_id, name="test", type="terrain_cracks")
        scene_generator.asset_manager.get_texture = AsyncMock(return_value=mock_texture)
        
        request = SceneRequest(
            location_id=UUID('00000000-0000-0000-0000-000000000000'),
            template_name="test_template",
            quality_level="medium"
        )
        
        response = await scene_generator.generate_scene(request)
        
        # Verify texture assignment
        crack_obj = next(
            obj for obj in response.scene_definition.objects
            if obj.name.startswith("crack_decal_")
        )
        assert crack_obj.material["map"] == texture_id
        
        # Verify asset tracking
        assert texture_id in response.assets_required
    
    async def test_template_inheritance(
        self,
        scene_generator: SceneGenerator,
        tmp_path: Path,
        mock_location_data: Dict[str, Any],
        mocker: MockerFixture
    ) -> None:
        """Test template inheritance system."""
        # Create base template
        base_template = {
            "name": "base_template",
            "objects": [
                {
                    "name": "base_object",
                    "geometry": {"type": "BoxGeometry", "parameters": [1, 1, 1]}
                }
            ],
            "lights": [
                {"type": "ambient", "intensity": 0.5}
            ]
        }
        
        # Create child template
        child_template = {
            "name": "child_template",
            "base_template": "base_template",
            "objects": [
                {
                    "name": "child_object",
                    "geometry": {"type": "SphereGeometry", "parameters": [1]}
                }
            ]
        }
        
        # Write templates to files
        template_dir = tmp_path / "templates"
        template_dir.mkdir(exist_ok=True)
        
        with open(template_dir / "base_template.json", "w") as f:
            json.dump(base_template, f)
        
        with open(template_dir / "child_template.json", "w") as f:
            json.dump(child_template, f)
        
        # Create new scene generator with these templates
        scene_generator = SceneGenerator(
            asset_manager=AsyncMock(spec=AssetManager),
            template_path=template_dir,
            quality_presets=mock_quality_presets()
        )
        
        mocker.patch.object(
            scene_generator,
            '_get_location_data',
            return_value=mock_location_data
        )
        
        # Test scene generation with inherited template
        request = SceneRequest(
            location_id=UUID('00000000-0000-0000-0000-000000000000'),
            template_name="child_template",
            quality_level="medium"
        )
        
        response = await scene_generator.generate_scene(request)
        
        # Verify template inheritance
        objects = response.scene_definition.objects
        assert any(obj.name == "base_object" for obj in objects)
        assert any(obj.name == "child_object" for obj in objects)
        assert len(response.scene_definition.lights) > 0 