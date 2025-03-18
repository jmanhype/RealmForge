"""Tests for the asset management system."""

from typing import Any, Dict, List, Optional
from pathlib import Path
import pytest
import json
import shutil

if True:  # TYPE_CHECKING
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture

from ...models.assets import AssetMetadata, AssetType, QualityPreset
from ..services.assets.asset_manager import AssetManager

@pytest.fixture
def asset_dir(tmp_path: Path) -> Path:
    """Create a temporary directory structure for test assets."""
    asset_dir = tmp_path / "assets"
    
    # Create directory structure
    dirs = [
        "models/characters",
        "models/environment",
        "textures/materials",
        "textures/terrain",
        "animations/characters",
        "animations/objects",
        "audio/effects",
        "audio/music"
    ]
    
    for dir_path in dirs:
        (asset_dir / dir_path).mkdir(parents=True)
    
    return asset_dir

@pytest.fixture
def mock_model_file(asset_dir: Path) -> Path:
    """Create a mock 3D model file."""
    model_path = asset_dir / "models/characters/test_character.glb"
    model_path.write_bytes(b"mock glb data")
    return model_path

@pytest.fixture
def mock_texture_file(asset_dir: Path) -> Path:
    """Create a mock texture file."""
    texture_path = asset_dir / "textures/materials/test_texture.png"
    texture_path.write_bytes(b"mock png data")
    return texture_path

@pytest.fixture
def mock_metadata(asset_dir: Path) -> Dict[str, Any]:
    """Create mock asset metadata."""
    return {
        "id": "test_character",
        "type": AssetType.MODEL,
        "path": "models/characters/test_character.glb",
        "dependencies": [
            "textures/materials/test_texture.png"
        ],
        "quality_variants": {
            "high": {
                "format": "glb",
                "resolution": "high",
                "compression": "none"
            },
            "medium": {
                "format": "glb",
                "resolution": "medium",
                "compression": "draco"
            },
            "low": {
                "format": "gltf",
                "resolution": "low",
                "compression": "draco"
            }
        },
        "tags": ["character", "humanoid"],
        "properties": {
            "vertex_count": 10000,
            "material_count": 2
        }
    }

@pytest.fixture
def quality_preset() -> QualityPreset:
    """Create a quality preset configuration."""
    return QualityPreset(
        name="medium",
        model_quality="medium",
        texture_resolution="1024",
        texture_compression="dxt",
        shadow_quality="medium",
        particle_quality="medium"
    )

class TestAssetManager:
    """Test suite for AssetManager class."""
    
    async def test_asset_loading(
        self,
        asset_dir: Path,
        mock_model_file: Path,
        mock_metadata: Dict[str, Any]
    ) -> None:
        """Test basic asset loading functionality."""
        # Create asset manager
        manager = AssetManager(asset_dir)
        
        # Write metadata
        metadata_path = asset_dir / "metadata/test_character.json"
        metadata_path.parent.mkdir(exist_ok=True)
        with open(metadata_path, "w") as f:
            json.dump(mock_metadata, f)
        
        # Load asset
        asset = await manager.load_asset("test_character")
        
        # Verify asset loading
        assert asset is not None
        assert asset.id == "test_character"
        assert asset.type == AssetType.MODEL
        assert asset.path == mock_metadata["path"]
        assert len(asset.dependencies) == 1
    
    async def test_asset_caching(
        self,
        asset_dir: Path,
        mock_model_file: Path,
        mock_metadata: Dict[str, Any],
        mocker: MockerFixture
    ) -> None:
        """Test asset caching system."""
        manager = AssetManager(asset_dir)
        
        # Write metadata
        metadata_path = asset_dir / "metadata/test_character.json"
        metadata_path.parent.mkdir(exist_ok=True)
        with open(metadata_path, "w") as f:
            json.dump(mock_metadata, f)
        
        # Mock load_file method to track calls
        mock_load = mocker.patch.object(manager, '_load_file')
        mock_load.return_value = b"mock data"
        
        # Load asset twice
        asset1 = await manager.load_asset("test_character")
        asset2 = await manager.load_asset("test_character")
        
        # Verify caching
        assert asset1 is asset2  # Same object reference
        mock_load.assert_called_once()  # Load called only once
    
    async def test_quality_variant_loading(
        self,
        asset_dir: Path,
        mock_metadata: Dict[str, Any],
        quality_preset: QualityPreset
    ) -> None:
        """Test loading assets with different quality variants."""
        manager = AssetManager(asset_dir)
        
        # Create quality variants
        variants = ["high", "medium", "low"]
        for variant in variants:
            variant_path = asset_dir / f"models/characters/test_character_{variant}.glb"
            variant_path.write_bytes(f"mock {variant} data".encode())
        
        # Write metadata
        metadata_path = asset_dir / "metadata/test_character.json"
        metadata_path.parent.mkdir(exist_ok=True)
        with open(metadata_path, "w") as f:
            json.dump(mock_metadata, f)
        
        # Set quality preset
        manager.set_quality_preset(quality_preset)
        
        # Load asset
        asset = await manager.load_asset("test_character")
        
        # Verify correct variant loaded
        assert asset.quality_variant == "medium"
        assert "_medium.glb" in str(asset.file_path)
    
    async def test_dependency_resolution(
        self,
        asset_dir: Path,
        mock_model_file: Path,
        mock_texture_file: Path,
        mock_metadata: Dict[str, Any]
    ) -> None:
        """Test asset dependency resolution."""
        manager = AssetManager(asset_dir)
        
        # Write metadata
        metadata_path = asset_dir / "metadata/test_character.json"
        metadata_path.parent.mkdir(exist_ok=True)
        with open(metadata_path, "w") as f:
            json.dump(mock_metadata, f)
        
        # Write texture metadata
        texture_metadata = {
            "id": "test_texture",
            "type": AssetType.TEXTURE,
            "path": "textures/materials/test_texture.png",
            "dependencies": []
        }
        texture_metadata_path = asset_dir / "metadata/test_texture.json"
        with open(texture_metadata_path, "w") as f:
            json.dump(texture_metadata, f)
        
        # Load asset with dependencies
        asset = await manager.load_asset("test_character", load_dependencies=True)
        
        # Verify dependencies loaded
        assert len(asset.loaded_dependencies) == 1
        assert "test_texture" in asset.loaded_dependencies
    
    async def test_asset_optimization(
        self,
        asset_dir: Path,
        mock_model_file: Path,
        mock_metadata: Dict[str, Any]
    ) -> None:
        """Test asset optimization processes."""
        manager = AssetManager(asset_dir)
        
        # Write metadata
        metadata_path = asset_dir / "metadata/test_character.json"
        metadata_path.parent.mkdir(exist_ok=True)
        with open(metadata_path, "w") as f:
            json.dump(mock_metadata, f)
        
        # Create optimization settings
        optimization_settings = {
            "compress_textures": True,
            "generate_mips": True,
            "optimize_geometry": True
        }
        
        # Load and optimize asset
        asset = await manager.load_asset(
            "test_character",
            optimize=True,
            optimization_settings=optimization_settings
        )
        
        # Verify optimization
        assert asset.is_optimized
        assert hasattr(asset, "optimization_info")
    
    async def test_asset_unloading(
        self,
        asset_dir: Path,
        mock_model_file: Path,
        mock_metadata: Dict[str, Any]
    ) -> None:
        """Test asset unloading functionality."""
        manager = AssetManager(asset_dir)
        
        # Write metadata
        metadata_path = asset_dir / "metadata/test_character.json"
        metadata_path.parent.mkdir(exist_ok=True)
        with open(metadata_path, "w") as f:
            json.dump(mock_metadata, f)
        
        # Load and then unload asset
        asset = await manager.load_asset("test_character")
        assert "test_character" in manager.loaded_assets
        
        await manager.unload_asset("test_character")
        assert "test_character" not in manager.loaded_assets
    
    async def test_bulk_loading(
        self,
        asset_dir: Path,
        mock_metadata: Dict[str, Any]
    ) -> None:
        """Test bulk asset loading functionality."""
        manager = AssetManager(asset_dir)
        
        # Create multiple test assets
        asset_ids = ["asset1", "asset2", "asset3"]
        for asset_id in asset_ids:
            # Create asset file
            asset_path = asset_dir / f"models/environment/{asset_id}.glb"
            asset_path.write_bytes(f"mock {asset_id} data".encode())
            
            # Create metadata
            metadata = mock_metadata.copy()
            metadata["id"] = asset_id
            metadata["path"] = f"models/environment/{asset_id}.glb"
            
            metadata_path = asset_dir / f"metadata/{asset_id}.json"
            metadata_path.parent.mkdir(exist_ok=True)
            with open(metadata_path, "w") as f:
                json.dump(metadata, f)
        
        # Bulk load assets
        assets = await manager.bulk_load_assets(asset_ids)
        
        # Verify bulk loading
        assert len(assets) == len(asset_ids)
        for asset_id in asset_ids:
            assert asset_id in manager.loaded_assets
    
    async def test_error_handling(
        self,
        asset_dir: Path,
        caplog: LogCaptureFixture
    ) -> None:
        """Test error handling in asset management."""
        manager = AssetManager(asset_dir)
        
        # Test loading nonexistent asset
        asset = await manager.load_asset("nonexistent")
        assert asset is None
        assert any("Asset not found" in record.message
                  for record in caplog.records)
        
        # Test loading invalid metadata
        metadata_path = asset_dir / "metadata/invalid.json"
        metadata_path.parent.mkdir(exist_ok=True)
        with open(metadata_path, "w") as f:
            f.write("invalid json")
        
        asset = await manager.load_asset("invalid")
        assert asset is None
        assert any("Failed to parse metadata" in record.message
                  for record in caplog.records)
    
    async def test_memory_management(
        self,
        asset_dir: Path,
        mock_metadata: Dict[str, Any]
    ) -> None:
        """Test memory management functionality."""
        manager = AssetManager(asset_dir, max_memory_mb=10)
        
        # Create large test assets
        for i in range(5):
            # Create asset file (2MB each)
            asset_path = asset_dir / f"models/environment/large_asset_{i}.glb"
            asset_path.write_bytes(b"0" * (2 * 1024 * 1024))
            
            # Create metadata
            metadata = mock_metadata.copy()
            metadata["id"] = f"large_asset_{i}"
            metadata["path"] = f"models/environment/large_asset_{i}.glb"
            
            metadata_path = asset_dir / f"metadata/large_asset_{i}.json"
            metadata_path.parent.mkdir(exist_ok=True)
            with open(metadata_path, "w") as f:
                json.dump(metadata, f)
        
        # Load assets until memory limit
        for i in range(5):
            await manager.load_asset(f"large_asset_{i}")
        
        # Verify memory management
        assert manager.current_memory_usage <= 10
        assert len(manager.loaded_assets) <= 5  # Some assets may be unloaded 