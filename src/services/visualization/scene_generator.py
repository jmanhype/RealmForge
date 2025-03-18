"""Scene generator for creating Three.js scenes."""

from typing import Dict, List, Optional, Union, Any, Tuple, Callable, Sequence
from uuid import UUID
import logging
from pathlib import Path
import json
import random
from math import sin, cos, pi, sqrt
import numpy as np
from dataclasses import dataclass
from enum import Enum

from ..assets.asset_manager import AssetManager
from ..assets.asset_types import (
    Model3D,
    Texture,
    Material,
    Template,
    Animation
)
from ...models.visualization import (
    SceneRequest,
    SceneResponse,
    SceneDefinition,
    ObjectDefinition,
    LightDefinition,
    CameraDefinition,
    Vector3,
    Color
)
from .code_generator import ThreeJSCodeGenerator
from .template_manager import TemplateManager
from .animation_system import AnimationSystem, AnimationSequence, AnimationChain

logger = logging.getLogger(__name__)

class AnimationType(Enum):
    """Types of animations available in the system."""
    KEYFRAME = "keyframe"
    PROCEDURAL = "procedural"
    PHYSICS = "physics"
    PARTICLE = "particle"
    STATE = "state"

@dataclass
class KeyframeData:
    """Data for keyframe animations."""
    time: float
    position: Optional[Vector3] = None
    rotation: Optional[Vector3] = None
    scale: Optional[Vector3] = None
    opacity: Optional[float] = None
    color: Optional[Color] = None
    easing: str = "linear"

@dataclass
class AnimationState:
    """State data for state-based animations."""
    name: str
    duration: float
    keyframes: List[KeyframeData]
    transitions: Dict[str, Dict[str, Any]]
    conditions: Optional[Dict[str, Any]] = None

@dataclass
class AnimationSequence:
    """Represents a sequence of animations that play in order."""
    name: str
    animations: List[AnimationState]
    loop: bool = False
    transition_time: float = 0.0
    events: Optional[Dict[str, Any]] = None

@dataclass
class AnimationChain:
    """Represents a chain of animations with dependencies."""
    name: str
    stages: List[Dict[str, Any]]  # Each stage has animations and conditions
    parallel: bool = False  # Whether stages can run in parallel if conditions met
    events: Optional[Dict[str, Any]] = None

@dataclass
class SceneTemplate:
    """Template for scene generation."""
    name: str
    base_template: Optional[str] = None  # For template inheritance
    objects: List[Dict[str, Any]] = None
    lights: List[Dict[str, Any]] = None
    camera: Dict[str, Any] = None
    environment: Dict[str, Any] = None
    animations: List[Dict[str, Any]] = None
    patterns: List[Dict[str, Any]] = None
    variables: Dict[str, Any] = None

class SceneGenerator:
    """Generator for Three.js scenes.
    
    This class handles:
    - Scene composition from templates
    - Asset placement and optimization
    - Lighting setup
    - Camera configuration
    - Scene code generation
    """
    
    def __init__(
        self,
        asset_manager: AssetManager,
        template_path: Path,
        quality_presets: Dict[str, Dict[str, Any]]
    ) -> None:
        """Initialize the scene generator.
        
        Args:
            asset_manager: Asset manager instance
            template_path: Path to scene templates
            quality_presets: Quality preset configurations
        """
        self.asset_manager = asset_manager
        self.template_manager = TemplateManager(template_path)
        self.animation_system = AnimationSystem()
        self.quality_presets = quality_presets
        
        # Load default templates
        self._default_templates = self._load_default_templates()
    
    def _load_default_templates(self) -> Dict[str, Template]:
        """Load default scene templates.
        
        Returns:
            Dict[str, Template]: Dictionary of loaded templates
        """
        templates = {}
        try:
            template_files = self.template_path.glob("*.json")
            for template_file in template_files:
                with open(template_file, 'r') as f:
                    template_data = json.load(f)
                    template = Template.parse_obj(template_data)
                    templates[template.template_type] = template
            logger.info(f"Loaded {len(templates)} default templates")
        except Exception as e:
            logger.error(f"Failed to load default templates: {str(e)}")
        return templates
    
    async def generate_scene(self, request: SceneRequest) -> SceneResponse:
        """Generate a Three.js scene based on the request.
        
        Args:
            request: Scene generation request
            
        Returns:
            SceneResponse: Generated scene data
            
        Raises:
            ValueError: If scene generation fails
        """
        try:
            # Get base template
            template = self.template_manager.get_template(request.template_name)
            if not template:
                raise ValueError(f"Template not found: {request.template_name}")
            
            # Apply quality settings
            quality_settings = self._get_quality_settings(request.quality_level)
            
            # Generate scene structure
            scene_def = await self._generate_scene_definition(
                template,
                request,
                quality_settings
            )
            
            # Generate Three.js code
            scene_code = self._generate_threejs_code(scene_def, quality_settings)
            
            return SceneResponse(
                scene_id=request.location_id,
                scene_definition=scene_def,
                scene_code=scene_code,
                assets_required=self._get_required_assets(scene_def)
            )
            
        except Exception as e:
            logger.error(f"Failed to generate scene: {str(e)}")
            raise ValueError(f"Scene generation failed: {str(e)}")
    
    async def _generate_scene_definition(
        self,
        template: Template,
        request: SceneRequest,
        quality_settings: Dict[str, Any]
    ) -> SceneDefinition:
        """Generate scene definition from template.
        
        Args:
            template: Scene template
            request: Scene generation request
            quality_settings: Quality settings to apply
            
        Returns:
            SceneDefinition: Generated scene definition
        """
        # Start with template structure
        scene_def = SceneDefinition(
            objects=[],
            lights=template.default_lighting.get("lights", []),
            camera=self._generate_camera_definition(request, template),
            environment=template.environment_settings,
            post_processing=self._get_post_processing(quality_settings)
        )
        
        # Apply template patterns
        for pattern in template.patterns or []:
            self.template_manager.apply_pattern(
                scene_def,
                pattern["name"],
                pattern.get("parameters", {})
            )
        
        # Add scene objects
        await self._add_scene_objects(scene_def, template, request)
        
        # Apply quality settings
        self._apply_quality_settings(scene_def, quality_settings)
        
        return scene_def
    
    def _generate_camera_definition(
        self,
        request: SceneRequest,
        template: Template
    ) -> CameraDefinition:
        """Generate camera definition for the scene.
        
        Args:
            request: Scene generation request
            template: Scene template
            
        Returns:
            CameraDefinition: Generated camera definition
        """
        camera_type = request.camera_type or "perspective"
        camera_settings = template.scene_structure.get("camera", {})
        
        return CameraDefinition(
            type=camera_type,
            position=Vector3(**camera_settings.get("position", {"x": 0, "y": 5, "z": 10})),
            target=Vector3(**camera_settings.get("target", {"x": 0, "y": 0, "z": 0})),
            fov=camera_settings.get("fov", 75),
            near=camera_settings.get("near", 0.1),
            far=camera_settings.get("far", 1000)
        )
    
    async def _add_scene_objects(
        self,
        scene_def: SceneDefinition,
        template: Template,
        request: SceneRequest
    ) -> None:
        """Add objects to the scene definition.
        
        Args:
            scene_def: Scene definition to modify
            template: Scene template
            request: Scene generation request
        """
        # Get location data
        location_data = await self._get_location_data(request.location_id)
        if not location_data:
            logger.warning(f"No location data found for ID: {request.location_id}")
            return
        
        # Add base objects from template
        for obj in template.objects or []:
            scene_def.objects.append(ObjectDefinition(**obj))
        
        # Add location-specific objects
        await self._add_location_objects(scene_def, location_data)
        
        # Add animations
        await self._add_animations(scene_def, template, location_data)
    
    async def _add_location_objects(
        self,
        scene_def: SceneDefinition,
        location_data: Dict[str, Any]
    ) -> None:
        """Add location-specific objects to the scene.
        
        Args:
            scene_def: Scene definition to modify
            location_data: Location data
        """
        # Add terrain and ground
        await self._add_terrain(scene_def, location_data)
        
        # Add architectural elements
        await self._add_architecture(scene_def, location_data)
        
        # Add decorative elements
        await self._add_decorations(scene_def, location_data)
        
        # Add interactive objects
        await self._add_interactive_objects(scene_def, location_data)
        
        # Add ambient life
        await self._add_ambient_life(scene_def, location_data)
        
        # Add environment effects
        await self._add_environment_effects(scene_def, location_data)
    
    async def _add_animations(
        self,
        scene_def: SceneDefinition,
        template: Template,
        location_data: Dict[str, Any]
    ) -> None:
        """Add animations to the scene.
        
        Args:
            scene_def: Scene definition to modify
            template: Scene template
            location_data: Location data
        """
        # Add template animations
        for anim_def in template.animations or []:
            if anim_def["type"] == "sequence":
                sequence = self.animation_system.create_sequence(
                    name=anim_def["name"],
                    animations=anim_def["animations"],
                    loop=anim_def.get("loop", False),
                    transition_time=anim_def.get("transition_time", 0.0),
                    events=anim_def.get("events")
                )
                scene_def.animations.append({
                    "type": "sequence",
                    "data": sequence
                })
            elif anim_def["type"] == "chain":
                chain = self.animation_system.create_chain(
                    name=anim_def["name"],
                    stages=anim_def["stages"],
                    parallel=anim_def.get("parallel", False),
                    events=anim_def.get("events")
                )
                scene_def.animations.append({
                    "type": "chain",
                    "data": chain
                })
        
        # Add location-specific animations
        for obj_def in location_data.get("objects", []):
            if "animations" in obj_def:
                for anim_def in obj_def["animations"]:
                    if anim_def["type"] == "sequence":
                        sequence = self.animation_system.create_sequence(
                            name=f"{obj_def['name']}_{anim_def['name']}",
                            animations=anim_def["animations"],
                            loop=anim_def.get("loop", False),
                            transition_time=anim_def.get("transition_time", 0.0),
                            events=anim_def.get("events")
                        )
                        scene_def.animations.append({
                            "type": "sequence",
                            "target": obj_def["name"],
                            "data": sequence
                        })
                    elif anim_def["type"] == "chain":
                        chain = self.animation_system.create_chain(
                            name=f"{obj_def['name']}_{anim_def['name']}",
                            stages=anim_def["stages"],
                            parallel=anim_def.get("parallel", False),
                            events=anim_def.get("events")
                        )
                        scene_def.animations.append({
                            "type": "chain",
                            "target": obj_def["name"],
                            "data": chain
                        })
    
    def _generate_threejs_code(
        self,
        scene_def: SceneDefinition,
        quality_settings: Dict[str, Any]
    ) -> str:
        """Generate Three.js code for the scene.
        
        Args:
            scene_def: Scene definition
            quality_settings: Quality settings
            
        Returns:
            str: Generated Three.js code
        """
        code_generator = ThreeJSCodeGenerator()
        
        # Generate base scene code
        code = code_generator.generate_code(scene_def, quality_settings)
        
        # Generate animation code
        animation_code = []
        for anim in scene_def.animations:
            if anim["type"] in ["sequence", "chain"]:
                target = anim.get("target", "scene")
                animation_code.append(
                    self.animation_system.generate_threejs_code(
                        anim["data"],
                        target
                    )
                )
        
        # Combine code
        if animation_code:
            code += "\n\n// Animations\n" + "\n".join(animation_code)
        
        return code

    async def _get_location_data(self, location_id: UUID) -> Optional[Dict[str, Any]]:
        """Get location data from the world service.
        
        Args:
            location_id: ID of the location
            
        Returns:
            Optional[Dict[str, Any]]: Location data or None if not found
        """
        try:
            # TODO: Implement actual world service integration
            # For now, return mock data
            return {
                "type": "dungeon",
                "size": {"width": 50, "length": 50, "height": 10},
                "terrain": {
                    "type": "stone",
                    "roughness": 0.7,
                    "features": ["cracks", "moss"]
                },
                "architecture": {
                    "style": "gothic",
                    "elements": [
                        {"type": "wall", "positions": [[0, 0], [10, 0]]},
                        {"type": "pillar", "positions": [[5, 5], [15, 5]]}
                    ]
                },
                "decorations": [
                    {"type": "torch", "positions": [[2, 0], [8, 0]]},
                    {"type": "chest", "position": [5, 8]}
                ],
                "ambient": {
                    "particles": ["dust"],
                    "sounds": ["dripping_water"]
                }
            }
        except Exception as e:
            logger.error(f"Failed to get location data: {str(e)}")
            return None

    async def _add_terrain(
        self,
        scene_def: SceneDefinition,
        location_data: Dict[str, Any]
    ) -> None:
        """Add terrain objects to the scene.
        
        Args:
            scene_def: Scene definition to modify
            location_data: Location data
        """
        terrain = location_data.get("terrain", {})
        size = location_data.get("size", {})
        
        # Create ground plane
        ground = ObjectDefinition(
            name="ground",
            geometry={
                "type": "PlaneGeometry",
                "parameters": [size.get("width", 50), size.get("length", 50)]
            },
            material={
                "type": "MeshStandardMaterial",
                "color": 0x808080,
                "roughness": terrain.get("roughness", 0.8),
                "metalness": 0.1
            },
            position=Vector3(x=0, y=0, z=0),
            rotation=Vector3(x=-pi/2, y=0, z=0),
            scale=Vector3(x=1, y=1, z=1),
            receive_shadows=True
        )
        scene_def.objects.append(ground)
        
        # Add terrain features
        if "features" in terrain:
            for feature in terrain["features"]:
                if feature == "cracks":
                    await self._add_terrain_cracks(scene_def, size)
                elif feature == "moss":
                    await self._add_terrain_moss(scene_def, size)

    async def _add_architecture(
        self,
        scene_def: SceneDefinition,
        location_data: Dict[str, Any]
    ) -> None:
        """Add architectural elements to the scene.
        
        Args:
            scene_def: Scene definition to modify
            location_data: Location data
        """
        architecture = location_data.get("architecture", {})
        
        for element in architecture.get("elements", []):
            element_type = element.get("type")
            positions = element.get("positions", [])
            
            if element_type == "wall":
                await self._add_walls(scene_def, positions, architecture.get("style"))
            elif element_type == "pillar":
                await self._add_pillars(scene_def, positions, architecture.get("style"))

    async def _add_decorations(
        self,
        scene_def: SceneDefinition,
        location_data: Dict[str, Any]
    ) -> None:
        """Add decorative elements to the scene.
        
        Args:
            scene_def: Scene definition to modify
            location_data: Location data
        """
        for decoration in location_data.get("decorations", []):
            decoration_type = decoration.get("type")
            
            if decoration_type == "torch":
                for pos in decoration.get("positions", []):
                    model_id = await self._get_model_id("torch", location_data.get("architecture", {}).get("style"))
                    torch = ObjectDefinition(
                        name=f"torch_{pos[0]}_{pos[1]}",
                        model_id=model_id,
                        position=Vector3(x=pos[0], y=2.0, z=pos[1]),
                        rotation=Vector3(x=0, y=0, z=0),
                        scale=Vector3(x=1, y=1, z=1),
                        cast_shadows=True,
                        animation={
                            "type": "flame",
                            "intensity": random.uniform(0.8, 1.2)
                        }
                    )
                    scene_def.objects.append(torch)
                    
                    # Add point light for torch
                    torch_light = LightDefinition(
                        type="point",
                        color=0xff6600,
                        intensity=0.8,
                        position=Vector3(x=pos[0], y=2.2, z=pos[1]),
                        cast_shadows=True,
                        shadow_map_size=512
                    )
                    scene_def.lights.append(torch_light)
            
            elif decoration_type == "chest":
                pos = decoration.get("position", [0, 0])
                model_id = await self._get_model_id("chest", location_data.get("architecture", {}).get("style"))
                chest = ObjectDefinition(
                    name=f"chest_{pos[0]}_{pos[1]}",
                    model_id=model_id,
                    position=Vector3(x=pos[0], y=0.5, z=pos[1]),
                    rotation=Vector3(x=0, y=0, z=0),
                    scale=Vector3(x=1, y=1, z=1),
                    cast_shadows=True,
                    receive_shadows=True,
                    interactive=True
                )
                scene_def.objects.append(chest)

    async def _add_interactive_objects(
        self,
        scene_def: SceneDefinition,
        location_data: Dict[str, Any]
    ) -> None:
        """Add interactive objects to the scene.
        
        Args:
            scene_def: Scene definition to modify
            location_data: Location data
        """
        # Add interaction system setup
        scene_def.interaction_system = {
            "raycaster": {
                "enabled": True,
                "layers": ["interactive", "pickable", "ui"]
            },
            "pointer_events": {
                "enabled": True,
                "capture_movement": True
            },
            "highlight": {
                "enabled": True,
                "color": 0xffff00,
                "intensity": 0.5
            }
        }
        
        # Add interactive objects based on location data
        for obj in location_data.get("interactive_objects", []):
            obj_type = obj.get("type", "")
            pos = obj.get("position", [0, 0, 0])
            
            if obj_type == "door":
                await self._add_interactive_door(scene_def, pos, obj)
            elif obj_type == "lever":
                await self._add_interactive_lever(scene_def, pos, obj)
            elif obj_type == "button":
                await self._add_interactive_button(scene_def, pos, obj)
            elif obj_type == "chest":
                await self._add_interactive_chest(scene_def, pos, obj)

        # Add animation sequences and chains
        for obj in location_data.get("interactive_objects", []):
            if "animation_sequence" in obj:
                await self._add_animation_sequence(scene_def, obj)
            if "animation_chain" in obj:
                await self._add_animation_chain(scene_def, obj)
    
    async def _add_interactive_door(
        self,
        scene_def: SceneDefinition,
        position: List[float],
        config: Dict[str, Any]
    ) -> None:
        """Add an interactive door to the scene.
        
        Args:
            scene_def: Scene definition to modify
            position: Door position
            config: Door configuration
        """
        model_id = await self._get_model_id("door", config.get("style"))
        
        # Create door states
        closed_state = AnimationState(
            name="closed",
            duration=0,
            keyframes=[KeyframeData(
                time=0,
                rotation=Vector3(x=0, y=0, z=0)
            )],
            transitions={
                "opening": {
                    "target": "open",
                    "duration": 1.0,
                    "easing": "easeInOutQuad"
                }
            }
        )
        
        open_state = AnimationState(
            name="open",
            duration=0,
            keyframes=[KeyframeData(
                time=0,
                rotation=Vector3(x=0, y=pi/2, z=0)
            )],
            transitions={
                "closing": {
                    "target": "closed",
                    "duration": 1.0,
                    "easing": "easeInOutQuad"
                }
            }
        )
        
        # Create door object
        door = ObjectDefinition(
            name=f"door_{position[0]}_{position[2]}",
            model_id=model_id,
            position=Vector3(x=position[0], y=position[1], z=position[2]),
            rotation=Vector3(x=0, y=0, z=0),
            scale=Vector3(x=1, y=1, z=1),
            cast_shadows=True,
            receive_shadows=True,
            interactive=True,
            interaction_data={
                "type": "door",
                "states": [closed_state, open_state],
                "current_state": "closed",
                "highlight": True,
                "events": {
                    "onClick": {
                        "type": "toggle_state",
                        "states": ["open", "closed"]
                    },
                    "onHover": {
                        "type": "highlight",
                        "intensity": 0.5
                    }
                }
            }
        )
        scene_def.objects.append(door)

    async def _add_interactive_lever(
        self,
        scene_def: SceneDefinition,
        position: List[float],
        config: Dict[str, Any]
    ) -> None:
        """Add an interactive lever to the scene.
        
        Args:
            scene_def: Scene definition to modify
            position: Lever position
            config: Lever configuration
        """
        model_id = await self._get_model_id("lever", config.get("style"))
        
        # Create lever animation keyframes
        off_keyframes = [
            KeyframeData(
                time=0,
                rotation=Vector3(x=0, y=0, z=0)
            )
        ]
        
        on_keyframes = [
            KeyframeData(
                time=0,
                rotation=Vector3(x=0, y=0, z=-pi/3)
            )
        ]
        
        # Create lever states
        off_state = AnimationState(
            name="off",
            duration=0,
            keyframes=off_keyframes,
            transitions={
                "activate": {
                    "target": "on",
                    "duration": 0.5,
                    "easing": "easeOutBounce"
                }
            }
        )
        
        on_state = AnimationState(
            name="on",
            duration=0,
            keyframes=on_keyframes,
            transitions={
                "deactivate": {
                    "target": "off",
                    "duration": 0.5,
                    "easing": "easeOutBounce"
                }
            }
        )
        
        # Create lever object
        lever = ObjectDefinition(
            name=f"lever_{position[0]}_{position[2]}",
            model_id=model_id,
            position=Vector3(x=position[0], y=position[1], z=position[2]),
            rotation=Vector3(x=0, y=0, z=0),
            scale=Vector3(x=1, y=1, z=1),
            cast_shadows=True,
            receive_shadows=True,
            interactive=True,
            interaction_data={
                "type": "lever",
                "states": [off_state, on_state],
                "current_state": "off",
                "highlight": True,
                "events": {
                    "onClick": {
                        "type": "toggle_state",
                        "states": ["on", "off"],
                        "sound": "lever_click"
                    },
                    "onStateChange": {
                        "type": "trigger_event",
                        "event": config.get("trigger_event", "none")
                    },
                    "onHover": {
                        "type": "highlight",
                        "intensity": 0.5
                    }
                }
            }
        )
        scene_def.objects.append(lever)

    async def _add_interactive_chest(
        self,
        scene_def: SceneDefinition,
        position: List[float],
        config: Dict[str, Any]
    ) -> None:
        """Add an interactive chest to the scene.
        
        Args:
            scene_def: Scene definition to modify
            position: Chest position
            config: Chest configuration
        """
        model_id = await self._get_model_id("chest", config.get("style"))
        
        # Create chest animation keyframes
        closed_keyframes = [
            KeyframeData(
                time=0,
                rotation=Vector3(x=0, y=0, z=0)
            )
        ]
        
        opening_keyframes = [
            KeyframeData(
                time=0,
                rotation=Vector3(x=0, y=0, z=0),
                easing="easeOutQuad"
            ),
            KeyframeData(
                time=0.5,
                rotation=Vector3(x=-pi/3, y=0, z=0),
                easing="easeOutBounce"
            )
        ]
        
        open_keyframes = [
            KeyframeData(
                time=0,
                rotation=Vector3(x=-pi/3, y=0, z=0)
            )
        ]
        
        # Create chest states
        closed_state = AnimationState(
            name="closed",
            duration=0,
            keyframes=closed_keyframes,
            transitions={
                "open": {
                    "target": "opening",
                    "duration": 0.5,
                    "conditions": {"is_locked": False}
                }
            }
        )
        
        opening_state = AnimationState(
            name="opening",
            duration=0.5,
            keyframes=opening_keyframes,
            transitions={
                "complete": {
                    "target": "open",
                    "duration": 0
                }
            }
        )
        
        open_state = AnimationState(
            name="open",
            duration=0,
            keyframes=open_keyframes,
            transitions={
                "close": {
                    "target": "closed",
                    "duration": 0.3,
                    "easing": "easeInQuad"
                }
            }
        )
        
        # Create chest object
        chest = ObjectDefinition(
            name=f"chest_{position[0]}_{position[2]}",
            model_id=model_id,
            position=Vector3(x=position[0], y=position[1], z=position[2]),
            rotation=Vector3(x=0, y=0, z=0),
            scale=Vector3(x=1, y=1, z=1),
            cast_shadows=True,
            receive_shadows=True,
            interactive=True,
            interaction_data={
                "type": "chest",
                "states": [closed_state, opening_state, open_state],
                "current_state": "closed",
                "variables": {
                    "is_locked": config.get("locked", False),
                    "loot_table": config.get("loot_table", "common")
                },
                "highlight": True,
                "events": {
                    "onClick": [
                        {
                            "type": "check_condition",
                            "condition": "is_locked",
                            "success": {
                                "type": "play_sound",
                                "sound": "chest_locked"
                            },
                            "failure": {
                                "type": "change_state",
                                "target": "opening"
                            }
                        }
                    ],
                    "onStateChange": {
                        "open": {
                            "type": "generate_loot",
                            "table": "loot_table"
                        }
                    },
                    "onHover": {
                        "type": "highlight",
                        "intensity": 0.5
                    }
                }
            }
        )
        scene_def.objects.append(chest)

    async def _add_interactive_button(
        self,
        scene_def: SceneDefinition,
        position: List[float],
        config: Dict[str, Any]
    ) -> None:
        """Add an interactive button to the scene.
        
        Args:
            scene_def: Scene definition to modify
            position: Button position
            config: Button configuration
        """
        model_id = await self._get_model_id("button", config.get("style"))
        
        # Create button animation keyframes
        up_keyframes = [
            KeyframeData(
                time=0,
                position=Vector3(x=position[0], y=position[1], z=position[2])
            )
        ]
        
        down_keyframes = [
            KeyframeData(
                time=0,
                position=Vector3(x=position[0], y=position[1] - 0.05, z=position[2]),
                easing="easeOutElastic"
            )
        ]
        
        # Create button states
        up_state = AnimationState(
            name="up",
            duration=0,
            keyframes=up_keyframes,
            transitions={
                "press": {
                    "target": "down",
                    "duration": 0.1,
                    "easing": "easeInQuad"
                }
            }
        )
        
        down_state = AnimationState(
            name="down",
            duration=0.2,
            keyframes=down_keyframes,
            transitions={
                "release": {
                    "target": "up",
                    "duration": 0.2
                }
            }
        )
        
        # Create button object
        button = ObjectDefinition(
            name=f"button_{position[0]}_{position[2]}",
            model_id=model_id,
            position=Vector3(x=position[0], y=position[1], z=position[2]),
            rotation=Vector3(x=0, y=0, z=0),
            scale=Vector3(x=1, y=1, z=1),
            cast_shadows=True,
            receive_shadows=True,
            interactive=True,
            interaction_data={
                "type": "button",
                "states": [up_state, down_state],
                "current_state": "up",
                "highlight": True,
                "events": {
                    "onClick": [
                        {
                            "type": "change_state",
                            "target": "down"
                        },
                        {
                            "type": "trigger_event",
                            "event": config.get("trigger_event", "none")
                        },
                        {
                            "type": "play_sound",
                            "sound": "button_click"
                        }
                    ],
                    "onHover": {
                        "type": "highlight",
                        "intensity": 0.5
                    }
                }
            }
        )
        scene_def.objects.append(button)

    async def _add_ambient_life(
        self,
        scene_def: SceneDefinition,
        location_data: Dict[str, Any]
    ) -> None:
        """Add ambient life elements to the scene.
        
        Args:
            scene_def: Scene definition to modify
            location_data: Location data
        """
        ambient = location_data.get("ambient", {})
        
        # Add particle systems
        for particle_type in ambient.get("particles", []):
            if particle_type == "dust":
                scene_def.post_processing.append({
                    "type": "particles",
                    "system": "dust",
                    "count": 1000,
                    "size": 0.02,
                    "color": 0xcccccc,
                    "opacity": 0.3
                })

    async def _add_environment_effects(
        self,
        scene_def: SceneDefinition,
        location_data: Dict[str, Any]
    ) -> None:
        """Add environment effects to the scene.
        
        Args:
            scene_def: Scene definition to modify
            location_data: Location data
        """
        # Add fog based on location type
        location_type = location_data.get("type", "")
        if location_type == "dungeon":
            scene_def.environment["fog"] = {
                "type": "exponential",
                "color": 0x222222,
                "density": 0.05
            }
        elif location_type == "cave":
            scene_def.environment["fog"] = {
                "type": "exponential",
                "color": 0x111111,
                "density": 0.08
            }
        
        # Add volumetric lighting if torches are present
        has_torches = any(
            dec.get("type") == "torch"
            for dec in location_data.get("decorations", [])
        )
        if has_torches:
            scene_def.post_processing.append({
                "type": "volumetricLight",
                "density": 0.05,
                "decay": 0.95,
                "weight": 0.5
            })
        
        # Add ambient particles based on location data
        ambient = location_data.get("ambient", {})
        for particle_type in ambient.get("particles", []):
            if particle_type == "dust":
                scene_def.post_processing.append({
                    "type": "particles",
                    "system": "dust",
                    "count": 1000,
                    "size": 0.02,
                    "color": 0xcccccc,
                    "opacity": 0.3,
                    "velocity": {"x": 0, "y": -0.01, "z": 0}
                })
            elif particle_type == "embers":
                scene_def.post_processing.append({
                    "type": "particles",
                    "system": "embers",
                    "count": 50,
                    "size": 0.05,
                    "color": 0xff4400,
                    "opacity": 0.6,
                    "velocity": {"x": 0, "y": 0.05, "z": 0},
                    "lifetime": {"min": 1, "max": 3}
                })
        
        # Add environmental sounds
        for sound in ambient.get("sounds", []):
            scene_def.environment["sounds"] = scene_def.environment.get("sounds", [])
            scene_def.environment["sounds"].append({
                "type": sound,
                "volume": 0.5,
                "loop": True,
                "spatial": True
            })

    async def _get_model_id(self, object_type: str, style: Optional[str] = None) -> UUID:
        """Get appropriate model ID from asset manager.
        
        Args:
            object_type: Type of object
            style: Optional style specification
            
        Returns:
            UUID: Model asset ID
        """
        # TODO: Implement actual asset manager integration
        return UUID('00000000-0000-0000-0000-000000000000')

    async def _add_terrain_cracks(
        self,
        scene_def: SceneDefinition,
        size: Dict[str, float]
    ) -> None:
        """Add crack details to terrain.
        
        Args:
            scene_def: Scene definition to modify
            size: Size specifications
        """
        # Get crack texture
        crack_texture_id = await self._get_texture_id("terrain_cracks")
        
        # Create decal material
        crack_material = {
            "type": "MeshStandardMaterial",
            "color": 0x505050,
            "roughness": 1.0,
            "metalness": 0.0,
            "opacity": 0.8,
            "transparent": True,
            "map": crack_texture_id,
            "normalMap": await self._get_texture_id("terrain_cracks_normal"),
            "roughnessMap": await self._get_texture_id("terrain_cracks_roughness")
        }
        
        # Generate random crack positions
        num_cracks = int((size.get("width", 50) * size.get("length", 50)) / 25)  # One crack per 25 square units
        for i in range(num_cracks):
            # Random position within bounds
            pos_x = random.uniform(-size.get("width", 50)/2, size.get("width", 50)/2)
            pos_z = random.uniform(-size.get("length", 50)/2, size.get("length", 50)/2)
            
            # Random rotation and scale
            rotation_y = random.uniform(0, 2 * pi)
            scale_factor = random.uniform(0.8, 1.5)
            
            # Create decal object
            crack = ObjectDefinition(
                name=f"crack_decal_{i}",
                geometry={
                    "type": "PlaneGeometry",
                    "parameters": [2 * scale_factor, 2 * scale_factor]  # Base size 2x2 units
                },
                material=crack_material,
                position=Vector3(x=pos_x, y=0.01, z=pos_z),  # Slightly above ground
                rotation=Vector3(x=-pi/2, y=rotation_y, z=0),
                scale=Vector3(x=1, y=1, z=1),
                receive_shadows=True,
                render_order=1  # Ensure decals render after ground
            )
            scene_def.objects.append(crack)

    async def _add_terrain_moss(
        self,
        scene_def: SceneDefinition,
        size: Dict[str, float]
    ) -> None:
        """Add moss details to terrain.
        
        Args:
            scene_def: Scene definition to modify
            size: Size specifications
        """
        # Get moss textures
        moss_texture_id = await self._get_texture_id("terrain_moss")
        moss_normal_id = await self._get_texture_id("terrain_moss_normal")
        
        # Create instanced moss patches
        moss_geometry = {
            "type": "InstancedMesh",
            "base_geometry": {
                "type": "PlaneGeometry",
                "parameters": [1, 1, 1, 1]  # 1x1 unit patch
            },
            "instance_count": 100  # Number of moss patches
        }
        
        moss_material = {
            "type": "MeshStandardMaterial",
            "color": 0x2d4f1e,  # Dark green
            "roughness": 1.0,
            "metalness": 0.0,
            "map": moss_texture_id,
            "normalMap": moss_normal_id,
            "transparent": True,
            "alphaTest": 0.5
        }
        
        # Create instanced moss object
        moss_patches = ObjectDefinition(
            name="moss_patches",
            geometry=moss_geometry,
            material=moss_material,
            position=Vector3(x=0, y=0.02, z=0),  # Slightly above ground
            rotation=Vector3(x=-pi/2, y=0, z=0),
            scale=Vector3(x=1, y=1, z=1),
            receive_shadows=True,
            instance_data={
                "positions": self._generate_moss_positions(size),
                "scales": self._generate_moss_scales(100),
                "rotations": self._generate_moss_rotations(100)
            }
        )
        scene_def.objects.append(moss_patches)

    def _generate_moss_positions(self, size: Dict[str, float]) -> List[Dict[str, float]]:
        """Generate random positions for moss patches using Poisson disk sampling.
        
        Args:
            size: Size specifications
            
        Returns:
            List[Dict[str, float]]: List of position vectors
        """
        width = size.get("width", 50)
        length = size.get("length", 50)
        
        # Poisson disk sampling parameters
        radius = 2.0  # Minimum distance between points
        k = 30  # Number of attempts to place each point
        grid_cell_size = radius / sqrt(2)
        
        # Initialize grid
        grid_width = int(width / grid_cell_size) + 1
        grid_length = int(length / grid_cell_size) + 1
        grid = np.full((grid_width, grid_length), -1, dtype=int)
        
        points: List[Tuple[float, float]] = []
        active: List[Tuple[float, float]] = []
        
        # Add first point
        x = random.uniform(-width/2, width/2)
        z = random.uniform(-length/2, length/2)
        points.append((x, z))
        active.append((x, z))
        grid_x = int((x + width/2) / grid_cell_size)
        grid_z = int((z + length/2) / grid_cell_size)
        grid[grid_x, grid_z] = 0
        
        def get_grid_point(x: float, z: float) -> Tuple[int, int]:
            """Convert world coordinates to grid coordinates."""
            gx = int((x + width/2) / grid_cell_size)
            gz = int((z + length/2) / grid_cell_size)
            return (
                min(max(gx, 0), grid_width - 1),
                min(max(gz, 0), grid_length - 1)
            )
        
        def is_valid_point(x: float, z: float) -> bool:
            """Check if point is valid (within bounds and far enough from others)."""
            if x < -width/2 or x > width/2 or z < -length/2 or z > length/2:
                return False
                
            gx, gz = get_grid_point(x, z)
            
            # Check nearby grid cells
            cell_range = int(radius / grid_cell_size) + 1
            for i in range(-cell_range, cell_range + 1):
                for j in range(-cell_range, cell_range + 1):
                    test_gx = gx + i
                    test_gz = gz + j
                    
                    if (0 <= test_gx < grid_width and 
                        0 <= test_gz < grid_length and 
                        grid[test_gx, test_gz] != -1):
                        
                        point_idx = grid[test_gx, test_gz]
                        px, pz = points[point_idx]
                        if sqrt((x - px)**2 + (z - pz)**2) < radius:
                            return False
            
            return True
        
        # Generate points
        while active and len(points) < 100:  # Limit to 100 moss patches
            idx = random.randint(0, len(active) - 1)
            px, pz = active[idx]
            
            found_valid = False
            for _ in range(k):
                # Generate random point in annulus
                theta = random.uniform(0, 2 * pi)
                r = random.uniform(radius, 2 * radius)
                x = px + r * cos(theta)
                z = pz + r * sin(theta)
                
                if is_valid_point(x, z):
                    points.append((x, z))
                    active.append((x, z))
                    gx, gz = get_grid_point(x, z)
                    grid[gx, gz] = len(points) - 1
                    found_valid = True
                    break
            
            if not found_valid:
                active.pop(idx)
        
        # Convert points to position dictionaries
        return [{"x": x, "y": 0, "z": z} for x, z in points]

    def _generate_moss_scales(self, count: int) -> List[Dict[str, float]]:
        """Generate random scales for moss patches.
        
        Args:
            count: Number of scales to generate
            
        Returns:
            List[Dict[str, float]]: List of scale vectors
        """
        scales = []
        for _ in range(count):
            scale = random.uniform(0.5, 1.5)
            scales.append({"x": scale, "y": scale, "z": scale})
        return scales

    def _generate_moss_rotations(self, count: int) -> List[Dict[str, float]]:
        """Generate random rotations for moss patches.
        
        Args:
            count: Number of rotations to generate
            
        Returns:
            List[Dict[str, float]]: List of rotation vectors
        """
        rotations = []
        for _ in range(count):
            rotation = random.uniform(0, 2 * pi)
            rotations.append({"x": 0, "y": rotation, "z": 0})
        return rotations

    async def _add_walls(
        self,
        scene_def: SceneDefinition,
        positions: List[List[float]],
        style: Optional[str]
    ) -> None:
        """Add walls to the scene.
        
        Args:
            scene_def: Scene definition to modify
            positions: Wall segment positions
            style: Architectural style
        """
        for i in range(0, len(positions) - 1):
            start = positions[i]
            end = positions[i + 1]
            
            # Calculate wall dimensions and position
            length = ((end[0] - start[0])**2 + (end[1] - start[1])**2)**0.5
            angle = atan2(end[1] - start[1], end[0] - start[0])
            center_x = (start[0] + end[0]) / 2
            center_z = (start[1] + end[1]) / 2
            
            wall = ObjectDefinition(
                name=f"wall_{i}",
                geometry={
                    "type": "BoxGeometry",
                    "parameters": [length, 4, 0.5]  # length, height, thickness
                },
                material={
                    "type": "MeshStandardMaterial",
                    "color": 0x808080,
                    "roughness": 0.9,
                    "metalness": 0.1
                },
                position=Vector3(x=center_x, y=2, z=center_z),
                rotation=Vector3(x=0, y=angle, z=0),
                scale=Vector3(x=1, y=1, z=1),
                cast_shadows=True,
                receive_shadows=True
            )
            scene_def.objects.append(wall)

    async def _add_pillars(
        self,
        scene_def: SceneDefinition,
        positions: List[List[float]],
        style: Optional[str]
    ) -> None:
        """Add pillars to the scene.
        
        Args:
            scene_def: Scene definition to modify
            positions: Pillar positions
            style: Architectural style
        """
        for i, pos in enumerate(positions):
            pillar = ObjectDefinition(
                name=f"pillar_{i}",
                geometry={
                    "type": "CylinderGeometry",
                    "parameters": [0.4, 0.4, 4, 8]  # radiusTop, radiusBottom, height, segments
                },
                material={
                    "type": "MeshStandardMaterial",
                    "color": 0x808080,
                    "roughness": 0.7,
                    "metalness": 0.2
                },
                position=Vector3(x=pos[0], y=2, z=pos[1]),
                rotation=Vector3(x=0, y=0, z=0),
                scale=Vector3(x=1, y=1, z=1),
                cast_shadows=True,
                receive_shadows=True
            )
            scene_def.objects.append(pillar)
    
    def _apply_quality_settings(
        self,
        scene_def: SceneDefinition,
        quality_settings: Dict[str, Any]
    ) -> None:
        """Apply quality settings to scene definition.
        
        Args:
            scene_def: Scene definition to modify
            quality_settings: Quality settings to apply
        """
        # Apply shadow settings
        for light in scene_def.lights:
            if light.type in ["directional", "spot"]:
                light.cast_shadows = quality_settings.get("shadows_enabled", True)
                light.shadow_map_size = quality_settings.get("shadow_map_size", 1024)
        
        # Apply post-processing
        scene_def.post_processing = self._get_post_processing(quality_settings)
    
    def _get_post_processing(self, quality_settings: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get post-processing effects based on quality settings.
        
        Args:
            quality_settings: Quality settings
            
        Returns:
            List[Dict[str, Any]]: Post-processing effects configuration
        """
        effects = []
        
        if quality_settings.get("ssao_enabled", False):
            effects.append({
                "type": "ssao",
                "radius": quality_settings.get("ssao_radius", 4),
                "intensity": quality_settings.get("ssao_intensity", 1.5)
            })
            
        if quality_settings.get("bloom_enabled", False):
            effects.append({
                "type": "bloom",
                "intensity": quality_settings.get("bloom_intensity", 1.0),
                "threshold": quality_settings.get("bloom_threshold", 0.85)
            })
            
        return effects
    
    def _get_required_assets(self, scene_def: SceneDefinition) -> List[UUID]:
        """Get list of required asset IDs for the scene.
        
        Args:
            scene_def: Scene definition
            
        Returns:
            List[UUID]: List of required asset IDs
        """
        asset_ids = set()
        
        # Collect model assets
        for obj in scene_def.objects:
            if obj.model_id:
                asset_ids.add(obj.model_id)
                
        # Collect material assets
        for obj in scene_def.objects:
            if obj.material_id:
                asset_ids.add(obj.material_id)
                
        # Collect environment assets
        if scene_def.environment and scene_def.environment.get("map_id"):
            asset_ids.add(scene_def.environment["map_id"])
            
        return list(asset_ids)
    
    async def _get_texture_id(self, texture_type: str) -> UUID:
        """Get texture ID from asset manager.
        
        Args:
            texture_type: Type of texture to retrieve
            
        Returns:
            UUID: Texture asset ID
            
        Raises:
            ValueError: If texture not found
        """
        try:
            # Query asset manager for texture by type
            texture: Optional[Texture] = await self.asset_manager.get_texture(texture_type)
            if not texture:
                # Try fallback textures
                fallback_map = {
                    "terrain_cracks": "generic_cracks",
                    "terrain_cracks_normal": "generic_normal",
                    "terrain_cracks_roughness": "generic_roughness",
                    "terrain_moss": "generic_moss",
                    "terrain_moss_normal": "generic_normal"
                }
                fallback_type = fallback_map.get(texture_type)
                if fallback_type:
                    texture = await self.asset_manager.get_texture(fallback_type)
            
            if not texture:
                raise ValueError(f"No texture found for type: {texture_type}")
                
            return texture.id
            
        except Exception as e:
            logger.error(f"Failed to get texture {texture_type}: {str(e)}")
            # Return placeholder texture ID for development
            return UUID('00000000-0000-0000-0000-000000000000') 