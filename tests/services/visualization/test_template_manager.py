"""Tests for the template management system."""

from typing import Any, Dict, List, Optional
from pathlib import Path
import json
import pytest
from uuid import UUID

if True:  # TYPE_CHECKING
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture

from ...models.visualization import SceneDefinition, ObjectDefinition, Vector3
from ..services.visualization.template_manager import TemplateManager, SceneTemplate

@pytest.fixture
def template_dir(tmp_path: Path) -> Path:
    """Create a temporary directory for test templates."""
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    
    # Create patterns directory
    patterns_dir = template_dir / "patterns"
    patterns_dir.mkdir()
    
    return template_dir

@pytest.fixture
def base_template() -> Dict[str, Any]:
    """Create a base template for testing."""
    return {
        "name": "base_template",
        "objects": [
            {
                "name": "base_object",
                "geometry": {"type": "BoxGeometry", "parameters": [1, 1, 1]}
            }
        ],
        "lights": [
            {"type": "ambient", "intensity": 0.5}
        ],
        "camera": {
            "position": {"x": 0, "y": 5, "z": 10},
            "target": {"x": 0, "y": 0, "z": 0}
        },
        "environment": {
            "skybox": "default",
            "fog": {"type": "linear", "color": 0x000000}
        }
    }

@pytest.fixture
def object_pattern() -> Dict[str, Any]:
    """Create an object pattern for testing."""
    return {
        "type": "object_group",
        "name": "pillar_group",
        "objects": [
            {
                "name": "$prefix_pillar",
                "geometry": {
                    "type": "CylinderGeometry",
                    "parameters": [0.4, 0.4, 4, 8]
                },
                "material": {
                    "type": "MeshStandardMaterial",
                    "color": "$color"
                },
                "position": {
                    "x": "$position_x",
                    "y": 2,
                    "z": "$position_z"
                }
            }
        ]
    }

@pytest.fixture
def animation_pattern() -> Dict[str, Any]:
    """Create an animation pattern for testing."""
    return {
        "type": "animation_sequence",
        "name": "door_animation",
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
                        "rotation": {"x": 0, "y": "$rotation_y", "z": 0}
                    }
                ]
            }
        ]
    }

class TestTemplateManager:
    """Test suite for TemplateManager class."""
    
    async def test_template_loading(
        self,
        template_dir: Path,
        base_template: Dict[str, Any]
    ) -> None:
        """Test loading templates from files."""
        # Write template to file
        template_file = template_dir / "base_template.json"
        with open(template_file, "w") as f:
            json.dump(base_template, f)
        
        # Create template manager
        manager = TemplateManager(template_dir)
        
        # Verify template loading
        template = manager.get_template("base_template")
        assert template is not None
        assert template.name == "base_template"
        assert len(template.objects) == 1
        assert len(template.lights) == 1
        assert template.camera is not None
        assert template.environment is not None
    
    async def test_template_inheritance(
        self,
        template_dir: Path,
        base_template: Dict[str, Any]
    ) -> None:
        """Test template inheritance system."""
        # Create child template
        child_template = {
            "name": "child_template",
            "base_template": "base_template",
            "objects": [
                {
                    "name": "child_object",
                    "geometry": {"type": "SphereGeometry", "parameters": [1]}
                }
            ],
            "environment": {
                "skybox": "custom",
                "fog": {"type": "exponential", "color": 0xffffff}
            }
        }
        
        # Write templates to files
        with open(template_dir / "base_template.json", "w") as f:
            json.dump(base_template, f)
        
        with open(template_dir / "child_template.json", "w") as f:
            json.dump(child_template, f)
        
        # Create template manager
        manager = TemplateManager(template_dir)
        
        # Get merged template
        template = manager.get_template("child_template")
        assert template is not None
        
        # Verify inheritance
        assert len(template.objects) == 1  # Child objects override base
        assert len(template.lights) == 1  # Inherited from base
        assert template.camera is not None  # Inherited from base
        assert template.environment["skybox"] == "custom"  # Overridden
        assert template.environment["fog"]["type"] == "exponential"  # Overridden
    
    async def test_pattern_loading(
        self,
        template_dir: Path,
        object_pattern: Dict[str, Any],
        animation_pattern: Dict[str, Any]
    ) -> None:
        """Test loading patterns from files."""
        # Write patterns to files
        patterns_dir = template_dir / "patterns"
        
        with open(patterns_dir / "pillar_group.json", "w") as f:
            json.dump(object_pattern, f)
        
        with open(patterns_dir / "door_animation.json", "w") as f:
            json.dump(animation_pattern, f)
        
        # Create template manager
        manager = TemplateManager(template_dir)
        
        # Verify pattern loading
        assert "pillar_group" in manager.patterns
        assert "door_animation" in manager.patterns
        assert manager.patterns["pillar_group"]["type"] == "object_group"
        assert manager.patterns["door_animation"]["type"] == "animation_sequence"
    
    async def test_object_pattern_application(
        self,
        template_dir: Path,
        object_pattern: Dict[str, Any]
    ) -> None:
        """Test applying object patterns to scene definitions."""
        # Write pattern to file
        patterns_dir = template_dir / "patterns"
        with open(patterns_dir / "pillar_group.json", "w") as f:
            json.dump(object_pattern, f)
        
        # Create template manager
        manager = TemplateManager(template_dir)
        
        # Create scene definition
        scene_def = SceneDefinition(
            objects=[],
            lights=[],
            camera=None,
            environment={}
        )
        
        # Apply pattern
        parameters = {
            "prefix": "north",
            "color": 0x808080,
            "position_x": 5,
            "position_z": 5
        }
        manager.apply_pattern(scene_def, "pillar_group", parameters)
        
        # Verify pattern application
        assert len(scene_def.objects) == 1
        obj = scene_def.objects[0]
        assert obj.name == "north_pillar"
        assert obj.material["color"] == 0x808080
        assert obj.position.x == 5
        assert obj.position.z == 5
    
    async def test_animation_pattern_application(
        self,
        template_dir: Path,
        animation_pattern: Dict[str, Any]
    ) -> None:
        """Test applying animation patterns to scene definitions."""
        # Write pattern to file
        patterns_dir = template_dir / "patterns"
        with open(patterns_dir / "door_animation.json", "w") as f:
            json.dump(animation_pattern, f)
        
        # Create template manager
        manager = TemplateManager(template_dir)
        
        # Create scene definition with target object
        scene_def = SceneDefinition(
            objects=[
                ObjectDefinition(
                    name="test_door",
                    geometry={"type": "BoxGeometry", "parameters": [1, 2, 0.2]},
                    position=Vector3(x=0, y=1, z=0)
                )
            ],
            lights=[],
            camera=None,
            environment={}
        )
        
        # Apply pattern
        parameters = {
            "targets": ["test_door"],
            "rotation_y": 1.5708  # 90 degrees in radians
        }
        manager.apply_pattern(scene_def, "door_animation", parameters)
        
        # Verify pattern application
        door = scene_def.objects[0]
        assert hasattr(door, "animations")
        assert len(door.animations) == 1
        anim = door.animations[0]
        assert anim["name"] == "opening"
        assert anim["keyframes"][1]["rotation"]["y"] == 1.5708
    
    async def test_parameter_substitution(
        self,
        template_dir: Path
    ) -> None:
        """Test parameter substitution in data structures."""
        manager = TemplateManager(template_dir)
        
        # Test data structure with parameters
        data = {
            "name": "$object_name",
            "position": {
                "x": "$pos_x",
                "y": 0,
                "z": "$pos_z"
            },
            "properties": {
                "color": "$color",
                "scale": ["$scale_x", "$scale_y", "$scale_z"]
            }
        }
        
        # Parameters to substitute
        parameters = {
            "object_name": "test_object",
            "pos_x": 5,
            "pos_z": -3,
            "color": 0xff0000,
            "scale_x": 1,
            "scale_y": 2,
            "scale_z": 1
        }
        
        # Perform substitution
        result = manager._substitute_parameters(data, parameters)
        
        # Verify substitution
        assert result["name"] == "test_object"
        assert result["position"]["x"] == 5
        assert result["position"]["z"] == -3
        assert result["properties"]["color"] == 0xff0000
        assert result["properties"]["scale"] == [1, 2, 1]
    
    async def test_transform_application(
        self,
        template_dir: Path
    ) -> None:
        """Test applying transforms to object definitions."""
        manager = TemplateManager(template_dir)
        
        # Test object definition
        obj_def = {
            "position": {"x": 1, "y": 1, "z": 1},
            "rotation": {"x": 0, "y": 0, "z": 0},
            "scale": {"x": 1, "y": 1, "z": 1}
        }
        
        # Transform to apply
        transform = {
            "position": {"x": 2, "y": -1, "z": 3},
            "rotation": {"y": 1.5708},
            "scale": {"x": 2, "y": 2, "z": 2}
        }
        
        # Apply transform
        result = manager._apply_transform(obj_def, transform)
        
        # Verify transformation
        assert result["position"]["x"] == 3  # 1 + 2
        assert result["position"]["y"] == 0  # 1 + (-1)
        assert result["position"]["z"] == 4  # 1 + 3
        assert result["rotation"]["y"] == 1.5708
        assert result["scale"]["x"] == 2
        assert result["scale"]["y"] == 2
        assert result["scale"]["z"] == 2
    
    async def test_error_handling(
        self,
        template_dir: Path,
        caplog: LogCaptureFixture
    ) -> None:
        """Test error handling in template and pattern loading."""
        # Create invalid template file
        with open(template_dir / "invalid.json", "w") as f:
            f.write("invalid json")
        
        # Create template manager
        manager = TemplateManager(template_dir)
        
        # Verify error logging
        assert any("Failed to load scene templates" in record.message
                  for record in caplog.records)
        
        # Test nonexistent pattern
        scene_def = SceneDefinition(
            objects=[],
            lights=[],
            camera=None,
            environment={}
        )
        manager.apply_pattern(scene_def, "nonexistent", {})
        
        # Verify warning logging
        assert any("Pattern not found" in record.message
                  for record in caplog.records) 