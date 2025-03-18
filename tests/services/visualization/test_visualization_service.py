"""Tests for the visualization and scene generation service."""

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

from ....src.services.visualization import VisualizationService
from ....src.models.visualization import (
    SceneTemplate,
    AnimationConfig,
    RenderSettings,
    CameraConfig,
    LightingConfig,
    MaterialConfig,
    EffectConfig
)

@pytest.fixture
def mock_scene_template() -> SceneTemplate:
    """Create mock scene template for testing."""
    return SceneTemplate(
        name="test_scene",
        dimensions=(1920, 1080),
        background_color=(0.2, 0.3, 0.4),
        ambient_light=0.5,
        camera_position=(0, 5, -10),
        camera_target=(0, 0, 0),
        entities=[
            {
                "type": "character",
                "position": (0, 0, 0),
                "rotation": (0, 0, 0),
                "scale": (1, 1, 1),
                "model": "character_base"
            },
            {
                "type": "prop",
                "position": (2, 0, 2),
                "rotation": (0, 45, 0),
                "scale": (1, 1, 1),
                "model": "tree_01"
            }
        ]
    )

@pytest.fixture
def mock_animation_config() -> AnimationConfig:
    """Create mock animation configuration for testing."""
    return AnimationConfig(
        duration=5.0,  # seconds
        framerate=60,
        keyframes=[
            {
                "time": 0.0,
                "position": (0, 0, 0),
                "rotation": (0, 0, 0)
            },
            {
                "time": 2.5,
                "position": (5, 0, 0),
                "rotation": (0, 180, 0)
            },
            {
                "time": 5.0,
                "position": (0, 0, 0),
                "rotation": (0, 360, 0)
            }
        ],
        interpolation="smooth",
        loop=True
    )

@pytest.fixture
def mock_render_settings() -> RenderSettings:
    """Create mock render settings for testing."""
    return RenderSettings(
        resolution=(1920, 1080),
        quality="high",
        anti_aliasing=True,
        shadows=True,
        ambient_occlusion=True,
        bloom=True,
        depth_of_field=True,
        motion_blur=False
    )

@pytest.fixture
async def visualization_service(
    mock_scene_template: SceneTemplate,
    tmp_path: Path
) -> VisualizationService:
    """Create a VisualizationService instance with mocked dependencies."""
    # Create service instance
    service = VisualizationService()
    await service.initialize()
    
    return service

class TestVisualizationService:
    """Test suite for VisualizationService class."""
    
    async def test_scene_generation(
        self,
        visualization_service: VisualizationService,
        mock_scene_template: SceneTemplate
    ) -> None:
        """Test scene generation from templates."""
        # Generate scene
        scene = await visualization_service.generate_scene(
            template=mock_scene_template
        )
        
        # Verify scene properties
        assert scene.dimensions == mock_scene_template.dimensions
        assert scene.background_color == mock_scene_template.background_color
        assert len(scene.entities) == len(mock_scene_template.entities)
        
        # Test entity placement
        character = scene.get_entity_by_type("character")
        assert character is not None
        assert character.position == mock_scene_template.entities[0]["position"]
        
        # Test scene modifications
        await visualization_service.update_scene_lighting(
            scene_id=scene.id,
            ambient_light=0.7
        )
        
        updated_scene = await visualization_service.get_scene(scene.id)
        assert updated_scene.ambient_light == 0.7
    
    async def test_template_management(
        self,
        visualization_service: VisualizationService,
        mock_scene_template: SceneTemplate
    ) -> None:
        """Test template management system."""
        # Register template
        template_id = await visualization_service.register_template(
            template=mock_scene_template
        )
        
        # Retrieve template
        retrieved = await visualization_service.get_template(template_id)
        assert retrieved.name == mock_scene_template.name
        assert retrieved.dimensions == mock_scene_template.dimensions
        
        # Modify template
        modified = SceneTemplate(
            **{**mock_scene_template.dict(), "ambient_light": 0.8}
        )
        await visualization_service.update_template(
            template_id=template_id,
            template=modified
        )
        
        # Verify modifications
        updated = await visualization_service.get_template(template_id)
        assert updated.ambient_light == 0.8
        
        # Test template listing
        templates = await visualization_service.list_templates()
        assert template_id in templates
        assert len(templates) > 0
    
    async def test_animation_system(
        self,
        visualization_service: VisualizationService,
        mock_scene_template: SceneTemplate,
        mock_animation_config: AnimationConfig
    ) -> None:
        """Test animation system functionality."""
        # Create animated scene
        scene = await visualization_service.generate_scene(
            template=mock_scene_template
        )
        
        # Apply animation
        animation_id = await visualization_service.create_animation(
            scene_id=scene.id,
            entity_id=scene.entities[0].id,
            config=mock_animation_config
        )
        
        # Test animation playback
        await visualization_service.play_animation(animation_id)
        state = await visualization_service.get_animation_state(animation_id)
        assert state["playing"] is True
        assert state["current_time"] >= 0
        
        # Test keyframe interpolation
        frame = await visualization_service.get_animation_frame(
            animation_id=animation_id,
            time=2.5  # middle keyframe
        )
        assert frame["position"] == mock_animation_config.keyframes[1]["position"]
        
        # Test animation control
        await visualization_service.pause_animation(animation_id)
        state = await visualization_service.get_animation_state(animation_id)
        assert state["playing"] is False
    
    async def test_camera_control(
        self,
        visualization_service: VisualizationService,
        mock_scene_template: SceneTemplate
    ) -> None:
        """Test camera control system."""
        # Generate scene
        scene = await visualization_service.generate_scene(
            template=mock_scene_template
        )
        
        # Configure camera
        camera_config = CameraConfig(
            position=(0, 10, -15),
            target=(0, 0, 0),
            fov=60,
            near=0.1,
            far=1000
        )
        
        await visualization_service.configure_camera(
            scene_id=scene.id,
            config=camera_config
        )
        
        # Verify camera settings
        scene_camera = await visualization_service.get_camera_config(scene.id)
        assert scene_camera.position == camera_config.position
        assert scene_camera.fov == camera_config.fov
        
        # Test camera movement
        await visualization_service.move_camera(
            scene_id=scene.id,
            position=(5, 10, -15),
            target=(5, 0, 0)
        )
        
        updated_camera = await visualization_service.get_camera_config(scene.id)
        assert updated_camera.position == (5, 10, -15)
        assert updated_camera.target == (5, 0, 0)
    
    async def test_lighting_system(
        self,
        visualization_service: VisualizationService,
        mock_scene_template: SceneTemplate
    ) -> None:
        """Test lighting system functionality."""
        # Generate scene
        scene = await visualization_service.generate_scene(
            template=mock_scene_template
        )
        
        # Configure lighting
        lighting_config = LightingConfig(
            ambient_intensity=0.3,
            directional_lights=[
                {
                    "direction": (1, -1, -1),
                    "intensity": 0.8,
                    "color": (1, 1, 1)
                }
            ],
            point_lights=[
                {
                    "position": (5, 5, 0),
                    "intensity": 0.6,
                    "color": (1, 0.8, 0.8),
                    "range": 10
                }
            ]
        )
        
        await visualization_service.configure_lighting(
            scene_id=scene.id,
            config=lighting_config
        )
        
        # Verify lighting settings
        scene_lighting = await visualization_service.get_lighting_config(scene.id)
        assert scene_lighting.ambient_intensity == lighting_config.ambient_intensity
        assert len(scene_lighting.directional_lights) == 1
        assert len(scene_lighting.point_lights) == 1
        
        # Test light modification
        await visualization_service.update_light(
            scene_id=scene.id,
            light_id=scene_lighting.point_lights[0]["id"],
            intensity=0.8
        )
        
        updated_lighting = await visualization_service.get_lighting_config(scene.id)
        assert updated_lighting.point_lights[0]["intensity"] == 0.8
    
    async def test_material_system(
        self,
        visualization_service: VisualizationService,
        mock_scene_template: SceneTemplate
    ) -> None:
        """Test material system functionality."""
        # Generate scene
        scene = await visualization_service.generate_scene(
            template=mock_scene_template
        )
        
        # Configure material
        material_config = MaterialConfig(
            type="pbr",
            base_color=(0.8, 0.8, 0.8),
            metallic=0.5,
            roughness=0.3,
            normal_map="normal_map.png",
            ao_map="ao_map.png"
        )
        
        entity_id = scene.entities[0].id
        await visualization_service.apply_material(
            scene_id=scene.id,
            entity_id=entity_id,
            config=material_config
        )
        
        # Verify material settings
        entity_material = await visualization_service.get_material_config(
            scene_id=scene.id,
            entity_id=entity_id
        )
        assert entity_material.type == material_config.type
        assert entity_material.base_color == material_config.base_color
        assert entity_material.metallic == material_config.metallic
        
        # Test material modification
        await visualization_service.update_material(
            scene_id=scene.id,
            entity_id=entity_id,
            properties={"roughness": 0.5}
        )
        
        updated_material = await visualization_service.get_material_config(
            scene_id=scene.id,
            entity_id=entity_id
        )
        assert updated_material.roughness == 0.5
    
    async def test_effect_system(
        self,
        visualization_service: VisualizationService,
        mock_scene_template: SceneTemplate
    ) -> None:
        """Test visual effects system."""
        # Generate scene
        scene = await visualization_service.generate_scene(
            template=mock_scene_template
        )
        
        # Configure effect
        effect_config = EffectConfig(
            type="particle",
            position=(0, 1, 0),
            properties={
                "particle_count": 1000,
                "emission_rate": 100,
                "lifetime": 2.0,
                "size": 0.1,
                "color": (1, 0.5, 0),
                "velocity": (0, 1, 0)
            }
        )
        
        effect_id = await visualization_service.create_effect(
            scene_id=scene.id,
            config=effect_config
        )
        
        # Verify effect settings
        scene_effect = await visualization_service.get_effect_config(effect_id)
        assert scene_effect.type == effect_config.type
        assert scene_effect.properties["particle_count"] == 1000
        
        # Test effect modification
        await visualization_service.update_effect(
            effect_id=effect_id,
            properties={"emission_rate": 200}
        )
        
        updated_effect = await visualization_service.get_effect_config(effect_id)
        assert updated_effect.properties["emission_rate"] == 200
    
    async def test_error_handling(
        self,
        visualization_service: VisualizationService,
        mock_scene_template: SceneTemplate,
        caplog: LogCaptureFixture
    ) -> None:
        """Test error handling in visualization processes."""
        # Test invalid scene template
        invalid_template = SceneTemplate(
            **{**mock_scene_template.dict(), "dimensions": (-1, -1)}
        )
        
        with pytest.raises(ValueError):
            await visualization_service.generate_scene(template=invalid_template)
        
        # Test invalid animation configuration
        invalid_animation = AnimationConfig(
            duration=-1.0,
            framerate=-30,
            keyframes=[],
            interpolation="invalid",
            loop=True
        )
        
        with pytest.raises(ValueError):
            scene = await visualization_service.generate_scene(
                template=mock_scene_template
            )
            await visualization_service.create_animation(
                scene_id=scene.id,
                entity_id=scene.entities[0].id,
                config=invalid_animation
            )
        
        # Test nonexistent scene/entity operations
        with pytest.raises(ValueError):
            await visualization_service.update_scene_lighting(
                scene_id="nonexistent",
                ambient_light=0.5
            )
        
        # Verify error logging
        assert any("Invalid scene template" in record.message
                  for record in caplog.records)
        assert any("Invalid animation configuration" in record.message
                  for record in caplog.records)
        assert any("Scene not found" in record.message
                  for record in caplog.records) 