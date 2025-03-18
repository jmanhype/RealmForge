"""Models for Three.js scene generation and management."""

from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field


class Vector3(BaseModel):
    """3D vector representation."""
    
    x: float = Field(default=0.0, description="X coordinate")
    y: float = Field(default=0.0, description="Y coordinate")
    z: float = Field(default=0.0, description="Z coordinate")


class CameraDefinition(BaseModel):
    """Camera configuration for Three.js scenes."""
    
    id: str = Field(..., description="Unique camera identifier")
    name: str = Field(..., description="Display name for the camera")
    type: str = Field(..., description="Camera type (e.g. PerspectiveCamera, OrthographicCamera)")
    position: Vector3 = Field(default_factory=Vector3, description="Camera position")
    lookAt: Vector3 = Field(default_factory=Vector3, description="Point camera is looking at")
    fov: float = Field(default=75, description="Field of view in degrees")
    near: float = Field(default=0.1, description="Near clipping plane")
    far: float = Field(default=1000, description="Far clipping plane")


class LightDefinition(BaseModel):
    """Light source configuration for Three.js scenes."""
    
    id: str = Field(..., description="Unique light identifier")
    name: str = Field(..., description="Display name for the light")
    type: str = Field(..., description="Light type (e.g. AmbientLight, DirectionalLight)")
    color: str = Field(default="#ffffff", description="Light color in hex format")
    intensity: float = Field(default=1.0, description="Light intensity")
    position: Optional[Vector3] = Field(None, description="Light position (if applicable)")
    castShadow: bool = Field(default=False, description="Whether light casts shadows")


class EnvironmentDefinition(BaseModel):
    """Environment configuration for Three.js scenes."""
    
    backgroundColor: str = Field(default="#000000", description="Scene background color")
    fog: Optional[Dict[str, Any]] = Field(None, description="Fog configuration")
    skybox: Optional[Dict[str, Any]] = Field(None, description="Skybox configuration")
    ground: Optional[Dict[str, Any]] = Field(None, description="Ground plane configuration")


class SceneDefinition(BaseModel):
    """Complete scene configuration for Three.js."""
    
    scene_id: str = Field(..., description="Unique scene identifier")
    player_id: str = Field(..., description="ID of player viewing the scene")
    location_id: str = Field(..., description="ID of location being rendered")
    camera: CameraDefinition = Field(..., description="Scene camera configuration")
    lights: List[LightDefinition] = Field(default_factory=list, description="Scene lighting setup")
    environment: EnvironmentDefinition = Field(
        default_factory=EnvironmentDefinition,
        description="Scene environment configuration"
    )
    renderer_settings: Dict[str, Any] = Field(
        default_factory=dict,
        description="Three.js renderer settings"
    )


class SceneRequest(BaseModel):
    """Request for scene generation."""
    
    player_id: str = Field(..., description="ID of player requesting the scene")
    location_id: str = Field(..., description="ID of location to render")
    quality_level: str = Field(default="medium", description="Rendering quality level")
    include_assets: bool = Field(default=False, description="Whether to include asset URLs")
    renderer_settings: Dict[str, Any] = Field(
        default_factory=dict,
        description="Custom renderer settings"
    )


class SceneResponse(BaseModel):
    """Response containing generated scene data."""
    
    request_id: str = Field(..., description="Unique request identifier")
    scene_id: Optional[str] = Field(None, description="Generated scene identifier")
    scene_definition: Optional[SceneDefinition] = Field(
        None,
        description="Complete scene configuration"
    )
    asset_urls: Dict[str, str] = Field(
        default_factory=dict,
        description="URLs for scene assets"
    )
    status: str = Field(..., description="Response status (generated, error)")
    error: Optional[str] = Field(None, description="Error message if status is error")


class Color(BaseModel):
    """Color representation for Three.js.
    
    Can be specified as a hex string or RGB values.
    """
    
    hex: Optional[str] = Field(None, description="Hex color string (e.g., '#ff0000')")
    r: Optional[float] = Field(None, description="Red component (0-1)")
    g: Optional[float] = Field(None, description="Green component (0-1)")
    b: Optional[float] = Field(None, description="Blue component (0-1)")


class MaterialDefinition(BaseModel):
    """Definition of a material for Three.js objects.
    
    Includes properties like color, texture, shininess, etc.
    """
    
    id: str = Field(..., description="Unique identifier for the material")
    type: str = Field(
        "MeshStandardMaterial", 
        description="Type of Three.js material"
    )
    color: Union[str, Color] = Field("#ffffff", description="Material color")
    metalness: float = Field(0.0, description="Metalness factor (0-1)")
    roughness: float = Field(0.5, description="Roughness factor (0-1)")
    emissive: Optional[Union[str, Color]] = Field(None, description="Emissive color")
    emissiveIntensity: Optional[float] = Field(None, description="Emissive intensity")
    map: Optional[str] = Field(None, description="Diffuse texture URL")
    normalMap: Optional[str] = Field(None, description="Normal map texture URL")
    roughnessMap: Optional[str] = Field(None, description="Roughness map texture URL")
    metalnessMap: Optional[str] = Field(None, description="Metalness map texture URL")
    aoMap: Optional[str] = Field(None, description="Ambient occlusion map URL")
    alphaTest: Optional[float] = Field(None, description="Alpha test value (0-1)")
    transparent: Optional[bool] = Field(None, description="Whether material is transparent")
    wireframe: Optional[bool] = Field(None, description="Whether to render as wireframe")
    side: Optional[str] = Field(None, description="Which side to render (FrontSide, BackSide, DoubleSide)")


class GeometryDefinition(BaseModel):
    """Definition of a geometry for Three.js objects.
    
    Can be a primitive or a reference to a loaded model.
    """
    
    id: str = Field(..., description="Unique identifier for the geometry")
    type: str = Field(..., description="Type of geometry (BoxGeometry, SphereGeometry, etc.)")
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Parameters for geometry creation"
    )


class ObjectDefinition(BaseModel):
    """Definition of an object in the Three.js scene.
    
    Includes geometry, material, position, rotation, etc.
    """
    
    id: str = Field(..., description="Unique identifier for the object")
    name: str = Field(..., description="Descriptive name for the object")
    type: str = Field("Mesh", description="Type of Three.js object")
    geometry: str = Field(..., description="ID of the geometry to use")
    material: str = Field(..., description="ID of the material to use")
    position: Vector3 = Field(default_factory=Vector3, description="Position in 3D space")
    rotation: Vector3 = Field(default_factory=Vector3, description="Rotation in radians")
    scale: Vector3 = Field(default_factory=Vector3, description="Scale factors")
    castShadow: bool = Field(False, description="Whether object casts shadows")
    receiveShadow: bool = Field(False, description="Whether object receives shadows")
    visible: bool = Field(True, description="Whether object is visible")
    interactive: bool = Field(False, description="Whether object is interactive")
    userData: Dict[str, Any] = Field(
        default_factory=dict,
        description="Custom data associated with the object"
    )


class ModelDefinition(BaseModel):
    """Definition of a 3D model to load in the Three.js scene.
    
    Includes URL, position, scale, etc.
    """
    
    id: str = Field(..., description="Unique identifier for the model")
    name: str = Field(..., description="Descriptive name for the model")
    url: str = Field(..., description="URL to the model file")
    format: str = Field("gltf", description="Format of the model file")
    position: Vector3 = Field(default_factory=Vector3, description="Position in 3D space")
    rotation: Vector3 = Field(default_factory=Vector3, description="Rotation in radians")
    scale: Vector3 = Field(default_factory=lambda: Vector3(x=1.0, y=1.0, z=1.0), description="Scale factors")
    castShadow: bool = Field(True, description="Whether model casts shadows")
    receiveShadow: bool = Field(True, description="Whether model receives shadows")
    animations: Optional[List[str]] = Field(None, description="List of animation names")
    defaultAnimation: Optional[str] = Field(None, description="Default animation to play")
    interactive: bool = Field(False, description="Whether model is interactive")
    userData: Dict[str, Any] = Field(
        default_factory=dict,
        description="Custom data associated with the model"
    )


class PostProcessingEffect(BaseModel):
    """Definition of a post-processing effect for the Three.js scene.
    
    Includes effect type and parameters.
    """
    
    id: str = Field(..., description="Unique identifier for the effect")
    type: str = Field(..., description="Type of effect (Bloom, SSAO, etc.)")
    enabled: bool = Field(True, description="Whether the effect is enabled")
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Parameters for the effect"
    )


class SceneTemplateRequest(BaseModel):
    """Request for a Three.js scene template.
    
    This model is used to request a template scene based on
    a specific environment type or theme.
    """
    
    template_type: str = Field(..., description="Type of template (forest, cave, town, etc.)")
    template_parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Parameters for template customization"
    )
    quality_level: str = Field(
        default="medium", 
        description="Quality level for the scene (low, medium, high, ultra)"
    )


class SceneTemplateResponse(BaseModel):
    """Response containing a Three.js scene template.
    
    Includes the template scene definition, JavaScript code, and metadata.
    """
    
    template_type: str = Field(..., description="Type of template")
    template_parameters: Dict[str, Any] = Field(default_factory=dict, description="Applied template parameters")
    scene_definition: SceneDefinition = Field(..., description="Template scene definition")
    js_code: str = Field(..., description="Generated JavaScript code for the template")
    assets: Dict[str, str] = Field(default_factory=dict, description="Map of asset IDs to URLs")
    usage_instructions: str = Field(..., description="Instructions for using the template")
    customization_points: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Points where the template can be customized"
    )


class CharacterRequest(BaseModel):
    """Request for character model generation."""
    
    character_id: str = Field(..., description="ID of the character")
    character_type: str = Field(..., description="Type of character (player, npc, enemy)")
    character_class: Optional[str] = Field(None, description="Character class (warrior, mage, etc.)")
    description: str = Field(..., description="Text description of the character")
    height: float = Field(default=1.8, description="Character height in meters")
    build: str = Field(default="average", description="Character build (thin, average, muscular, etc.)")
    quality_level: str = Field(default="medium", description="Model quality level")
    include_animations: bool = Field(default=True, description="Whether to include animations")
    custom_settings: Dict[str, Any] = Field(
        default_factory=dict,
        description="Custom settings for character generation"
    )


class CharacterResponse(BaseModel):
    """Response containing generated character model data."""
    
    request_id: str = Field(..., description="Unique request identifier")
    character_id: str = Field(..., description="ID of the character")
    model_definition: Dict[str, Any] = Field(..., description="Character model definition")
    material_definitions: Dict[str, Any] = Field(
        default_factory=dict,
        description="Material definitions for character model"
    )
    animation_urls: Dict[str, str] = Field(
        default_factory=dict,
        description="URLs for character animations"
    )
    model_url: str = Field(..., description="URL to the generated model file")
    thumbnail_url: Optional[str] = Field(None, description="URL to character thumbnail image")
    status: str = Field(..., description="Response status (generated, error)")
    error: Optional[str] = Field(None, description="Error message if status is error") 