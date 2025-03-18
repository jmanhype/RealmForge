"""Asset type definitions for the asset management system."""

from typing import Dict, List, Optional, Union, Literal
from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from pathlib import Path
from datetime import datetime

class AssetMetadata(BaseModel):
    """Metadata for an asset."""
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    tags: List[str] = Field(default_factory=list)
    category: str
    format: str
    size_bytes: int = 0
    dimensions: Optional[Dict[str, int]] = None
    custom_properties: Dict[str, Union[str, int, float, bool]] = Field(default_factory=dict)

class Asset(BaseModel):
    """Base class for all assets."""
    
    id: UUID = Field(default_factory=uuid4)
    name: str
    path: Path
    metadata: AssetMetadata
    cache_key: Optional[str] = None
    is_template: bool = False
    dependencies: List[UUID] = Field(default_factory=list)

class Model3D(Asset):
    """3D model asset."""
    
    model_format: Literal["gltf", "glb", "obj", "fbx"] = "gltf"
    has_animations: bool = False
    has_materials: bool = False
    vertex_count: Optional[int] = None
    triangle_count: Optional[int] = None
    bone_count: Optional[int] = None
    lod_levels: List[Dict[str, Union[str, int]]] = Field(default_factory=list)

class Texture(Asset):
    """Texture asset."""
    
    texture_type: Literal["diffuse", "normal", "roughness", "metallic", "ambient_occlusion", "emissive"] = "diffuse"
    resolution: Dict[str, int]
    channels: int
    has_mipmaps: bool = True
    compression: Optional[str] = None
    srgb: bool = True

class Material(Asset):
    """Material asset."""
    
    shader_type: str = "standard"
    textures: Dict[str, UUID] = Field(default_factory=dict)
    properties: Dict[str, Union[float, List[float]]] = Field(default_factory=dict)
    render_queue: int = 2000
    is_transparent: bool = False

class Animation(Asset):
    """Animation asset."""
    
    duration: float
    fps: int
    keyframe_count: int
    affected_bones: List[str] = Field(default_factory=list)
    loop: bool = False
    transition_duration: float = 0.0
    events: List[Dict[str, Union[str, float]]] = Field(default_factory=list)

class Template(Asset):
    """Scene template asset."""
    
    template_type: str
    scene_structure: Dict[str, Any]
    placeholders: List[Dict[str, str]] = Field(default_factory=list)
    default_lighting: Dict[str, Any] = Field(default_factory=dict)
    environment_settings: Dict[str, Any] = Field(default_factory=dict)
    optimization_hints: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True 