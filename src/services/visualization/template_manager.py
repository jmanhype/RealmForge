"""Template management system for scene generation."""

from typing import Dict, List, Optional, Any
from pathlib import Path
import json
import logging
from dataclasses import dataclass
from uuid import UUID

from ...models.visualization import (
    SceneDefinition,
    ObjectDefinition,
    Vector3
)

logger = logging.getLogger(__name__)

@dataclass
class SceneTemplate:
    """Template for scene generation."""
    name: str
    base_template: Optional[str] = None  # For template inheritance
    objects: Optional[List[Dict[str, Any]]] = None
    lights: Optional[List[Dict[str, Any]]] = None
    camera: Optional[Dict[str, Any]] = None
    environment: Optional[Dict[str, Any]] = None
    animations: Optional[List[Dict[str, Any]]] = None
    patterns: Optional[List[Dict[str, Any]]] = None
    variables: Optional[Dict[str, Any]] = None

class TemplateManager:
    """Manages scene templates and patterns."""
    
    def __init__(self, template_path: Path) -> None:
        """Initialize the template manager.
        
        Args:
            template_path: Path to template directory
        """
        self.template_path = Path(template_path)
        self.templates: Dict[str, SceneTemplate] = {}
        self.patterns: Dict[str, Dict[str, Any]] = {}
        self._load_templates()
        self._load_patterns()
    
    def _load_templates(self) -> None:
        """Load all scene templates from the template directory."""
        try:
            template_files = self.template_path.glob("*.json")
            for template_file in template_files:
                with open(template_file, 'r') as f:
                    template_data = json.load(f)
                    template = SceneTemplate(**template_data)
                    self.templates[template.name] = template
            logger.info(f"Loaded {len(self.templates)} scene templates")
        except Exception as e:
            logger.error(f"Failed to load scene templates: {str(e)}")
    
    def _load_patterns(self) -> None:
        """Load animation and object patterns."""
        pattern_path = self.template_path / "patterns"
        try:
            pattern_files = pattern_path.glob("*.json")
            for pattern_file in pattern_files:
                with open(pattern_file, 'r') as f:
                    pattern_data = json.load(f)
                    pattern_type = pattern_file.stem
                    self.patterns[pattern_type] = pattern_data
            logger.info(f"Loaded {len(self.patterns)} patterns")
        except Exception as e:
            logger.error(f"Failed to load patterns: {str(e)}")
    
    def get_template(self, name: str) -> Optional[SceneTemplate]:
        """Get a scene template by name.
        
        Args:
            name: Template name
            
        Returns:
            Optional[SceneTemplate]: The template if found
        """
        template = self.templates.get(name)
        if template and template.base_template:
            # Handle template inheritance
            base = self.get_template(template.base_template)
            if base:
                return self._merge_templates(base, template)
        return template
    
    def _merge_templates(
        self,
        base: SceneTemplate,
        override: SceneTemplate
    ) -> SceneTemplate:
        """Merge two templates, with override taking precedence.
        
        Args:
            base: Base template
            override: Override template
            
        Returns:
            SceneTemplate: Merged template
        """
        merged = SceneTemplate(
            name=override.name,
            base_template=override.base_template,
            objects=override.objects or base.objects,
            lights=override.lights or base.lights,
            camera=override.camera or base.camera,
            environment=override.environment or base.environment,
            animations=override.animations or base.animations,
            patterns=override.patterns or base.patterns,
            variables={**(base.variables or {}), **(override.variables or {})}
        )
        return merged
    
    def apply_pattern(
        self,
        scene_def: SceneDefinition,
        pattern_name: str,
        parameters: Dict[str, Any]
    ) -> None:
        """Apply a pattern to a scene definition.
        
        Args:
            scene_def: Scene definition to modify
            pattern_name: Name of the pattern to apply
            parameters: Pattern parameters
        """
        pattern = self.patterns.get(pattern_name)
        if not pattern:
            logger.warning(f"Pattern not found: {pattern_name}")
            return
            
        try:
            if pattern["type"] == "object_group":
                self._apply_object_pattern(scene_def, pattern, parameters)
            elif pattern["type"] == "animation_sequence":
                self._apply_animation_pattern(scene_def, pattern, parameters)
        except Exception as e:
            logger.error(f"Failed to apply pattern {pattern_name}: {str(e)}")
    
    def _apply_object_pattern(
        self,
        scene_def: SceneDefinition,
        pattern: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> None:
        """Apply an object pattern to the scene.
        
        Args:
            scene_def: Scene definition to modify
            pattern: Pattern definition
            parameters: Pattern parameters
        """
        objects = pattern.get("objects", [])
        transform = parameters.get("transform", {})
        
        for obj in objects:
            # Apply parameter substitutions
            obj_def = self._substitute_parameters(obj, parameters)
            
            # Apply transform
            if transform:
                obj_def = self._apply_transform(obj_def, transform)
            
            scene_def.objects.append(ObjectDefinition(**obj_def))
    
    def _apply_animation_pattern(
        self,
        scene_def: SceneDefinition,
        pattern: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> None:
        """Apply an animation pattern to the scene.
        
        Args:
            scene_def: Scene definition to modify
            pattern: Pattern definition
            parameters: Pattern parameters
        """
        animations = pattern.get("animations", [])
        target_objects = parameters.get("targets", [])
        
        for target in target_objects:
            obj = next(
                (o for o in scene_def.objects if o.name == target),
                None
            )
            if not obj:
                continue
                
            # Apply animations to object
            if not hasattr(obj, "animations"):
                obj.animations = []
            
            for anim in animations:
                processed_anim = self._substitute_parameters(anim, parameters)
                obj.animations.append(processed_anim)
    
    def _substitute_parameters(
        self,
        data: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Substitute parameters in a data structure.
        
        Args:
            data: Data structure to process
            parameters: Parameter values
            
        Returns:
            Dict[str, Any]: Processed data structure
        """
        result = {}
        for key, value in data.items():
            if isinstance(value, str) and value.startswith("$"):
                param_name = value[1:]
                result[key] = parameters.get(param_name, value)
            elif isinstance(value, dict):
                result[key] = self._substitute_parameters(value, parameters)
            elif isinstance(value, list):
                result[key] = [
                    self._substitute_parameters(item, parameters)
                    if isinstance(item, dict)
                    else item
                    for item in value
                ]
            else:
                result[key] = value
        return result
    
    def _apply_transform(
        self,
        obj_def: Dict[str, Any],
        transform: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply a transform to an object definition.
        
        Args:
            obj_def: Object definition
            transform: Transform parameters
            
        Returns:
            Dict[str, Any]: Transformed object definition
        """
        if "position" in transform:
            pos = obj_def.get("position", {"x": 0, "y": 0, "z": 0})
            obj_def["position"] = {
                "x": pos["x"] + transform["position"].get("x", 0),
                "y": pos["y"] + transform["position"].get("y", 0),
                "z": pos["z"] + transform["position"].get("z", 0)
            }
        
        if "rotation" in transform:
            rot = obj_def.get("rotation", {"x": 0, "y": 0, "z": 0})
            obj_def["rotation"] = {
                "x": rot["x"] + transform["rotation"].get("x", 0),
                "y": rot["y"] + transform["rotation"].get("y", 0),
                "z": rot["z"] + transform["rotation"].get("z", 0)
            }
        
        if "scale" in transform:
            scale = obj_def.get("scale", {"x": 1, "y": 1, "z": 1})
            obj_def["scale"] = {
                "x": scale["x"] * transform["scale"].get("x", 1),
                "y": scale["y"] * transform["scale"].get("y", 1),
                "z": scale["z"] * transform["scale"].get("z", 1)
            }
        
        return obj_def 