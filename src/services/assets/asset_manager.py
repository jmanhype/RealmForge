"""Asset manager for handling asset operations."""

import os
from typing import Dict, List, Optional, Union, Type, TypeVar, Any
from pathlib import Path
import json
import logging
from uuid import UUID
import shutil
import hashlib
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

from .asset_types import (
    Asset,
    Model3D,
    Texture,
    Material,
    Animation,
    Template,
    AssetMetadata
)

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=Asset)

class AssetManager:
    """Manager for handling asset operations.
    
    This class provides functionality for:
    - Asset loading and caching
    - Asset metadata management
    - Asset optimization and processing
    - Template management
    - Asset dependency resolution
    """
    
    def __init__(
        self,
        base_path: Union[str, Path],
        cache_path: Union[str, Path],
        max_cache_size_mb: int = 1024,
        max_workers: int = 4
    ) -> None:
        """Initialize the asset manager.
        
        Args:
            base_path: Base path for asset storage
            cache_path: Path for asset cache
            max_cache_size_mb: Maximum cache size in megabytes
            max_workers: Maximum number of worker threads
        """
        self.base_path = Path(base_path)
        self.cache_path = Path(cache_path)
        self.max_cache_size = max_cache_size_mb * 1024 * 1024  # Convert to bytes
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # Create directories if they don't exist
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.cache_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize asset registry
        self._asset_registry: Dict[UUID, Asset] = {}
        self._load_asset_registry()
        
        # Initialize cache tracking
        self._cache_size = 0
        self._update_cache_size()
    
    def _load_asset_registry(self) -> None:
        """Load the asset registry from disk."""
        registry_path = self.base_path / "asset_registry.json"
        if registry_path.exists():
            try:
                with open(registry_path, 'r') as f:
                    registry_data = json.load(f)
                for asset_data in registry_data:
                    asset = Asset.parse_obj(asset_data)
                    self._asset_registry[asset.id] = asset
                logger.info(f"Loaded {len(self._asset_registry)} assets from registry")
            except Exception as e:
                logger.error(f"Failed to load asset registry: {str(e)}")
    
    def _save_asset_registry(self) -> None:
        """Save the asset registry to disk."""
        registry_path = self.base_path / "asset_registry.json"
        try:
            registry_data = [asset.dict() for asset in self._asset_registry.values()]
            with open(registry_path, 'w') as f:
                json.dump(registry_data, f, indent=2)
            logger.info("Asset registry saved successfully")
        except Exception as e:
            logger.error(f"Failed to save asset registry: {str(e)}")
    
    def _update_cache_size(self) -> None:
        """Update the current cache size calculation."""
        total_size = 0
        for item in self.cache_path.glob('**/*'):
            if item.is_file():
                total_size += item.stat().st_size
        self._cache_size = total_size
    
    def _generate_cache_key(self, asset: Asset) -> str:
        """Generate a cache key for an asset.
        
        Args:
            asset: The asset to generate a cache key for
            
        Returns:
            str: The generated cache key
        """
        key_components = [
            str(asset.id),
            asset.name,
            str(asset.path),
            str(asset.metadata.updated_at)
        ]
        return hashlib.sha256('|'.join(key_components).encode()).hexdigest()
    
    async def load_asset(
        self,
        asset_id: UUID,
        asset_type: Type[T] = Asset
    ) -> Optional[T]:
        """Load an asset by its ID.
        
        Args:
            asset_id: The ID of the asset to load
            asset_type: The expected asset type
            
        Returns:
            Optional[T]: The loaded asset or None if not found
        """
        if asset_id not in self._asset_registry:
            logger.warning(f"Asset {asset_id} not found in registry")
            return None
            
        asset = self._asset_registry[asset_id]
        if not isinstance(asset, asset_type):
            logger.error(f"Asset {asset_id} is not of type {asset_type.__name__}")
            return None
            
        return asset
    
    async def save_asset(self, asset: Asset) -> bool:
        """Save an asset to the registry.
        
        Args:
            asset: The asset to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self._asset_registry[asset.id] = asset
            self._save_asset_registry()
            return True
        except Exception as e:
            logger.error(f"Failed to save asset {asset.id}: {str(e)}")
            return False
    
    async def delete_asset(self, asset_id: UUID) -> bool:
        """Delete an asset from the registry.
        
        Args:
            asset_id: The ID of the asset to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        if asset_id not in self._asset_registry:
            return False
            
        try:
            asset = self._asset_registry[asset_id]
            if asset.path.exists():
                asset.path.unlink()
            if asset.cache_key:
                cache_path = self.cache_path / asset.cache_key
                if cache_path.exists():
                    cache_path.unlink()
            del self._asset_registry[asset_id]
            self._save_asset_registry()
            self._update_cache_size()
            return True
        except Exception as e:
            logger.error(f"Failed to delete asset {asset_id}: {str(e)}")
            return False
    
    @lru_cache(maxsize=1000)
    async def get_asset_metadata(self, asset_id: UUID) -> Optional[AssetMetadata]:
        """Get metadata for an asset.
        
        Args:
            asset_id: The ID of the asset
            
        Returns:
            Optional[AssetMetadata]: The asset metadata or None if not found
        """
        asset = await self.load_asset(asset_id)
        return asset.metadata if asset else None
    
    async def optimize_asset(self, asset: Asset) -> Optional[Asset]:
        """Optimize an asset for better performance.
        
        Args:
            asset: The asset to optimize
            
        Returns:
            Optional[Asset]: The optimized asset or None if optimization failed
        """
        try:
            if isinstance(asset, Model3D):
                return await self._optimize_model(asset)
            elif isinstance(asset, Texture):
                return await self._optimize_texture(asset)
            else:
                logger.warning(f"No optimization available for asset type {type(asset).__name__}")
                return asset
        except Exception as e:
            logger.error(f"Failed to optimize asset {asset.id}: {str(e)}")
            return None
    
    async def _optimize_model(self, model: Model3D) -> Model3D:
        """Optimize a 3D model asset.
        
        Args:
            model: The model to optimize
            
        Returns:
            Model3D: The optimized model
        """
        # TODO: Implement model optimization (LOD generation, mesh simplification, etc.)
        return model
    
    async def _optimize_texture(self, texture: Texture) -> Texture:
        """Optimize a texture asset.
        
        Args:
            texture: The texture to optimize
            
        Returns:
            Texture: The optimized texture
        """
        # TODO: Implement texture optimization (compression, mipmap generation, etc.)
        return texture
    
    async def get_template(self, template_type: str) -> Optional[Template]:
        """Get a template by its type.
        
        Args:
            template_type: The type of template to retrieve
            
        Returns:
            Optional[Template]: The template or None if not found
        """
        for asset in self._asset_registry.values():
            if isinstance(asset, Template) and asset.template_type == template_type:
                return asset
        return None
    
    async def clear_cache(self) -> None:
        """Clear the asset cache."""
        try:
            shutil.rmtree(self.cache_path)
            self.cache_path.mkdir(parents=True, exist_ok=True)
            self._cache_size = 0
            logger.info("Asset cache cleared successfully")
        except Exception as e:
            logger.error(f"Failed to clear asset cache: {str(e)}")
    
    def __del__(self) -> None:
        """Clean up resources on deletion."""
        self.executor.shutdown(wait=True) 