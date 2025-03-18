"""Service for world generation and management in Realm Forge."""

import json
import logging
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

import aiohttp
from loguru import logger

from ..models.world import (
    WorldLocation,
    WorldContext,
    WorldRequest,
    WorldResponse
)
from ..config.settings import Settings

class WorldService:
    """Service for generating and managing game world content.
    
    This service handles world generation, location management, and environment
    creation. It uses templates and procedural generation to create dynamic
    game worlds that adapt to player actions and game state.
    """
    
    def __init__(self, settings: Settings):
        """Initialize the world service.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        self.location_templates: Dict[str, Any] = {}
        self.environment_templates: Dict[str, Any] = {}
        self.active_locations: Dict[str, WorldLocation] = {}
        self.load_templates()
        
    def load_templates(self) -> None:
        """Load location and environment templates from files."""
        try:
            templates_dir = Path(self.settings.aflow.templates_dir)
            
            # Load location templates
            location_path = templates_dir / "locations.json"
            if location_path.exists():
                with open(location_path) as f:
                    self.location_templates = json.load(f)
            
            # Load environment templates
            environment_path = templates_dir / "environments.json"
            if environment_path.exists():
                with open(environment_path) as f:
                    self.environment_templates = json.load(f)
                    
        except Exception as e:
            logger.error(f"Failed to load world templates: {e}")
            # Initialize with empty templates if loading fails
            self.location_templates = {}
            self.environment_templates = {}
    
    async def generate_location(
        self,
        context: WorldContext,
        location_type: str,
        near_location_id: Optional[str] = None,
        options: Dict[str, Any] = None
    ) -> WorldLocation:
        """Generate a new location based on context and type.
        
        Args:
            context: Current world context
            location_type: Type of location to generate
            near_location_id: Optional ID of nearby location
            options: Additional options for location generation
            
        Returns:
            Generated location
        """
        try:
            # Get relevant template
            template = self.location_templates.get(location_type, {})
            options = options or {}
            
            # Generate location ID
            location_id = str(uuid.uuid4())
            
            # Calculate coordinates
            coordinates = self._calculate_coordinates(near_location_id)
            
            # Generate location name
            name = template.get("name_template", "").format(
                **context.dict(),
                **options
            )
            
            # Generate description
            description = template.get("description_template", "").format(
                **context.dict(),
                **options
            )
            
            # Create location
            location = WorldLocation(
                location_id=location_id,
                name=name,
                description=description,
                type=location_type,
                coordinates=coordinates,
                connected_locations=[near_location_id] if near_location_id else [],
                resources=self._generate_resources(template, context),
                points_of_interest=self._generate_points_of_interest(template, context),
                npcs=[],  # NPCs will be added later
                quests=[],  # Quests will be added later
                metadata=options
            )
            
            # Store active location
            self.active_locations[location_id] = location
            
            return location
            
        except Exception as e:
            logger.error(f"Failed to generate location: {e}")
            # Return a default location on error
            return WorldLocation(
                location_id=str(uuid.uuid4()),
                name="Error Location",
                description="Failed to generate location",
                type="error",
                coordinates=(0.0, 0.0, 0.0)
            )
    
    def _calculate_coordinates(
        self,
        near_location_id: Optional[str]
    ) -> Tuple[float, float, float]:
        """Calculate coordinates for a new location.
        
        Args:
            near_location_id: Optional ID of nearby location
            
        Returns:
            Tuple of (x, y, z) coordinates
        """
        if near_location_id and near_location_id in self.active_locations:
            # Place near existing location
            near_loc = self.active_locations[near_location_id]
            x, y, z = near_loc.coordinates
            # Add some random offset
            import random
            x += random.uniform(-100, 100)
            y += random.uniform(-100, 100)
            z += random.uniform(-10, 10)
            return (x, y, z)
        else:
            # Generate new coordinates
            import random
            x = random.uniform(-1000, 1000)
            y = random.uniform(-1000, 1000)
            z = random.uniform(-100, 100)
            return (x, y, z)
    
    def _generate_resources(
        self,
        template: Dict[str, Any],
        context: WorldContext
    ) -> Dict[str, int]:
        """Generate resources for a location.
        
        Args:
            template: Location template
            context: Current world context
            
        Returns:
            Dictionary of resource types and quantities
        """
        try:
            resources = {}
            
            # Get base resources from template
            base_resources = template.get("resources", {})
            
            # Adjust based on context
            for resource, base_amount in base_resources.items():
                # Apply random variation
                import random
                variation = random.uniform(0.8, 1.2)
                
                # Apply context modifiers
                context_modifier = context.world_state.get(
                    f"resource_modifier_{resource}",
                    1.0
                )
                
                # Calculate final amount
                amount = int(base_amount * variation * context_modifier)
                if amount > 0:
                    resources[resource] = amount
            
            return resources
            
        except Exception as e:
            logger.error(f"Failed to generate resources: {e}")
            return {}
    
    def _generate_points_of_interest(
        self,
        template: Dict[str, Any],
        context: WorldContext
    ) -> List[Dict[str, Any]]:
        """Generate points of interest for a location.
        
        Args:
            template: Location template
            context: Current world context
            
        Returns:
            List of points of interest
        """
        try:
            points = []
            
            # Get base POIs from template
            base_pois = template.get("points_of_interest", [])
            
            # Generate each POI
            for base_poi in base_pois:
                # Check requirements
                requirements = base_poi.get("requirements", {})
                if not self._check_requirements(requirements, context):
                    continue
                
                # Generate POI
                poi = {
                    "id": str(uuid.uuid4()),
                    "name": base_poi.get("name", ""),
                    "type": base_poi.get("type", ""),
                    "description": base_poi.get("description", ""),
                    "coordinates": self._calculate_coordinates(None),
                    "metadata": base_poi.get("metadata", {})
                }
                points.append(poi)
            
            return points
            
        except Exception as e:
            logger.error(f"Failed to generate points of interest: {e}")
            return []
    
    def _check_requirements(
        self,
        requirements: Dict[str, Any],
        context: WorldContext
    ) -> bool:
        """Check if requirements are met in the given context.
        
        Args:
            requirements: Dictionary of requirements
            context: Current world context
            
        Returns:
            True if requirements are met, False otherwise
        """
        try:
            for key, value in requirements.items():
                if key.startswith("player_level"):
                    if context.player_level < value:
                        return False
                elif key.startswith("world_state."):
                    state_key = key.split(".", 1)[1]
                    if context.world_state.get(state_key) != value:
                        return False
            return True
            
        except Exception as e:
            logger.error(f"Failed to check requirements: {e}")
            return False
    
    async def process_world_request(
        self,
        request: WorldRequest
    ) -> WorldResponse:
        """Process a world generation request.
        
        Args:
            request: The world generation request
            
        Returns:
            Response containing generated world content
        """
        try:
            # Generate request ID
            request_id = str(uuid.uuid4())
            
            # Initialize response
            response = WorldResponse(
                request_id=request_id,
                player_id=request.player_id,
                locations=[],
                updated_context=request.context,
                three_js_data={},
                cost=0.0
            )
            
            # Generate location if requested
            if request.location_type:
                location = await self.generate_location(
                    request.context,
                    request.location_type,
                    request.near_location_id,
                    request.world_options
                )
                response.locations.append(location)
                
                # Update context
                self._update_context(response)
                
                # Generate Three.js data
                response.three_js_data = self._generate_three_js_data(response)
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to process world request: {e}")
            # Return empty response on error
            return WorldResponse(
                request_id=str(uuid.uuid4()),
                player_id=request.player_id,
                locations=[],
                updated_context=request.context,
                three_js_data={},
                cost=0.0
            )
    
    def _update_context(self, response: WorldResponse) -> None:
        """Update world context based on generated content.
        
        Args:
            response: The world response to update context for
        """
        try:
            context = response.updated_context
            
            # Update existing locations
            for location in response.locations:
                context.existing_locations[location.location_id] = location
                
                # Update world state based on location
                for resource, amount in location.resources.items():
                    current = context.world_state.get(f"total_{resource}", 0)
                    context.world_state[f"total_{resource}"] = current + amount
            
        except Exception as e:
            logger.error(f"Failed to update world context: {e}")
    
    def _generate_three_js_data(self, response: WorldResponse) -> Dict[str, Any]:
        """Generate Three.js compatible data for rendering.
        
        Args:
            response: The world response to generate data for
            
        Returns:
            Dictionary of Three.js scene data
        """
        try:
            three_js_data = {
                "scenes": [],
                "cameras": [],
                "lights": [],
                "objects": []
            }
            
            # Generate scene data for each location
            for location in response.locations:
                # Add scene
                scene = {
                    "id": f"scene_{location.location_id}",
                    "type": "scene",
                    "background": self._get_environment_background(location.type)
                }
                three_js_data["scenes"].append(scene)
                
                # Add camera
                camera = {
                    "id": f"camera_{location.location_id}",
                    "type": "perspective",
                    "position": [0, 5, 10],
                    "target": [0, 0, 0]
                }
                three_js_data["cameras"].append(camera)
                
                # Add lights
                lights = self._generate_location_lights(location)
                three_js_data["lights"].extend(lights)
                
                # Add objects
                objects = self._generate_location_objects(location)
                three_js_data["objects"].extend(objects)
            
            return three_js_data
            
        except Exception as e:
            logger.error(f"Failed to generate Three.js data: {e}")
            return {}
    
    def _get_environment_background(self, location_type: str) -> Dict[str, Any]:
        """Get environment background data for a location type.
        
        Args:
            location_type: Type of location
            
        Returns:
            Dictionary of background data
        """
        try:
            # Get environment template
            template = self.environment_templates.get(location_type, {})
            
            return {
                "type": template.get("background_type", "color"),
                "value": template.get("background_value", "#000000"),
                "intensity": template.get("background_intensity", 1.0)
            }
            
        except Exception as e:
            logger.error(f"Failed to get environment background: {e}")
            return {
                "type": "color",
                "value": "#000000",
                "intensity": 1.0
            }
    
    def _generate_location_lights(
        self,
        location: WorldLocation
    ) -> List[Dict[str, Any]]:
        """Generate lights for a location.
        
        Args:
            location: The location to generate lights for
            
        Returns:
            List of light data
        """
        try:
            lights = []
            
            # Get environment template
            template = self.environment_templates.get(location.type, {})
            
            # Add ambient light
            ambient = {
                "id": f"ambient_{location.location_id}",
                "type": "ambient",
                "color": template.get("ambient_color", "#ffffff"),
                "intensity": template.get("ambient_intensity", 0.5)
            }
            lights.append(ambient)
            
            # Add directional light
            directional = {
                "id": f"directional_{location.location_id}",
                "type": "directional",
                "color": template.get("directional_color", "#ffffff"),
                "intensity": template.get("directional_intensity", 1.0),
                "position": [5, 10, 5],
                "target": [0, 0, 0]
            }
            lights.append(directional)
            
            return lights
            
        except Exception as e:
            logger.error(f"Failed to generate location lights: {e}")
            return []
    
    def _generate_location_objects(
        self,
        location: WorldLocation
    ) -> List[Dict[str, Any]]:
        """Generate objects for a location.
        
        Args:
            location: The location to generate objects for
            
        Returns:
            List of object data
        """
        try:
            objects = []
            
            # Add ground plane
            ground = {
                "id": f"ground_{location.location_id}",
                "type": "plane",
                "width": 1000,
                "height": 1000,
                "position": [0, 0, 0],
                "rotation": [-90, 0, 0],
                "material": {
                    "type": "standard",
                    "color": "#808080",
                    "roughness": 0.8
                }
            }
            objects.append(ground)
            
            # Add points of interest
            for poi in location.points_of_interest:
                obj = {
                    "id": f"poi_{poi['id']}",
                    "type": "marker",
                    "position": list(poi.get("coordinates", (0, 0, 0))),
                    "scale": [1, 1, 1],
                    "material": {
                        "type": "standard",
                        "color": "#ffff00",
                        "emissive": "#ffff00",
                        "emissiveIntensity": 0.5
                    }
                }
                objects.append(obj)
            
            return objects
            
        except Exception as e:
            logger.error(f"Failed to generate location objects: {e}")
            return [] 