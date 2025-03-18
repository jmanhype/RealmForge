"""Tests for the resource management system."""

from typing import Any, Dict, List, Optional
from pathlib import Path
import pytest
import json
import time
from unittest.mock import AsyncMock

if True:  # TYPE_CHECKING
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture

from ...models.resources import ResourceType, CachePolicy, ResourceMetadata
from ..services.resources.resource_manager import ResourceManager

@pytest.fixture
def resource_dir(tmp_path: Path) -> Path:
    """Create a temporary directory for test resources."""
    resource_dir = tmp_path / "resources"
    resource_dir.mkdir()
    return resource_dir

@pytest.fixture
def mock_resource_data() -> bytes:
    """Create mock resource data."""
    return b"mock resource data" * 1000  # 16KB of mock data

@pytest.fixture
def mock_resource_metadata() -> Dict[str, Any]:
    """Create mock resource metadata."""
    return {
        "id": "test_resource",
        "type": ResourceType.BINARY,
        "size": 16000,
        "cache_policy": {
            "type": CachePolicy.LRU,
            "max_age": 3600,
            "priority": 1
        },
        "compression": "gzip",
        "checksum": "abc123",
        "tags": ["test", "mock"]
    }

class TestResourceManager:
    """Test suite for ResourceManager class."""
    
    async def test_resource_loading(
        self,
        resource_dir: Path,
        mock_resource_data: bytes,
        mock_resource_metadata: Dict[str, Any]
    ) -> None:
        """Test basic resource loading functionality."""
        manager = ResourceManager(resource_dir)
        
        # Create resource file
        resource_path = resource_dir / "test_resource.bin"
        with open(resource_path, "wb") as f:
            f.write(mock_resource_data)
        
        # Write metadata
        metadata_path = resource_dir / "metadata/test_resource.json"
        metadata_path.parent.mkdir(exist_ok=True)
        with open(metadata_path, "w") as f:
            json.dump(mock_resource_metadata, f)
        
        # Load resource
        resource = await manager.load_resource("test_resource")
        
        # Verify resource loading
        assert resource is not None
        assert resource.id == "test_resource"
        assert resource.type == ResourceType.BINARY
        assert len(resource.data) == 16000
        assert resource.metadata.cache_policy.type == CachePolicy.LRU
    
    async def test_caching_behavior(
        self,
        resource_dir: Path,
        mock_resource_data: bytes,
        mock_resource_metadata: Dict[str, Any],
        mocker: MockerFixture
    ) -> None:
        """Test resource caching behavior."""
        manager = ResourceManager(resource_dir)
        
        # Create resource
        resource_path = resource_dir / "test_resource.bin"
        with open(resource_path, "wb") as f:
            f.write(mock_resource_data)
        
        # Write metadata
        metadata_path = resource_dir / "metadata/test_resource.json"
        metadata_path.parent.mkdir(exist_ok=True)
        with open(metadata_path, "w") as f:
            json.dump(mock_resource_metadata, f)
        
        # Mock _load_from_disk method
        mock_load = mocker.patch.object(manager, '_load_from_disk')
        mock_load.return_value = mock_resource_data
        
        # Load resource multiple times
        resource1 = await manager.load_resource("test_resource")
        resource2 = await manager.load_resource("test_resource")
        
        # Verify caching
        assert resource1 is resource2
        mock_load.assert_called_once()
    
    async def test_cache_eviction(
        self,
        resource_dir: Path,
        mock_resource_metadata: Dict[str, Any]
    ) -> None:
        """Test cache eviction policies."""
        # Create manager with small cache size
        manager = ResourceManager(resource_dir, max_cache_size_mb=1)
        
        # Create multiple resources
        for i in range(3):
            # Create 500KB resource
            resource_data = b"0" * (500 * 1024)
            resource_path = resource_dir / f"resource_{i}.bin"
            with open(resource_path, "wb") as f:
                f.write(resource_data)
            
            # Create metadata
            metadata = mock_resource_metadata.copy()
            metadata["id"] = f"resource_{i}"
            metadata["size"] = len(resource_data)
            
            metadata_path = resource_dir / f"metadata/resource_{i}.json"
            metadata_path.parent.mkdir(exist_ok=True)
            with open(metadata_path, "w") as f:
                json.dump(metadata, f)
        
        # Load resources to trigger eviction
        for i in range(3):
            await manager.load_resource(f"resource_{i}")
        
        # Verify cache size
        assert manager.current_cache_size <= 1024 * 1024  # 1MB
        assert len(manager.cache) <= 2  # Only 2 resources should fit
    
    async def test_cache_policy_handling(
        self,
        resource_dir: Path,
        mock_resource_data: bytes,
        mock_resource_metadata: Dict[str, Any]
    ) -> None:
        """Test different cache policy behaviors."""
        manager = ResourceManager(resource_dir)
        
        # Create resources with different policies
        policies = [
            ("lru_resource", CachePolicy.LRU, 1),
            ("ttl_resource", CachePolicy.TTL, 2),
            ("priority_resource", CachePolicy.PRIORITY, 3)
        ]
        
        for resource_id, policy_type, priority in policies:
            # Create resource
            resource_path = resource_dir / f"{resource_id}.bin"
            with open(resource_path, "wb") as f:
                f.write(mock_resource_data)
            
            # Create metadata with specific policy
            metadata = mock_resource_metadata.copy()
            metadata["id"] = resource_id
            metadata["cache_policy"] = {
                "type": policy_type,
                "max_age": 1,  # 1 second TTL
                "priority": priority
            }
            
            metadata_path = resource_dir / f"metadata/{resource_id}.json"
            metadata_path.parent.mkdir(exist_ok=True)
            with open(metadata_path, "w") as f:
                json.dump(metadata, f)
        
        # Test TTL policy
        ttl_resource = await manager.load_resource("ttl_resource")
        assert ttl_resource is not None
        
        # Wait for TTL expiration
        time.sleep(1.1)
        
        # Resource should be reloaded
        ttl_resource_2 = await manager.load_resource("ttl_resource")
        assert ttl_resource is not ttl_resource_2
    
    async def test_compression_handling(
        self,
        resource_dir: Path,
        mock_resource_data: bytes,
        mock_resource_metadata: Dict[str, Any]
    ) -> None:
        """Test compression handling in resource loading."""
        manager = ResourceManager(resource_dir)
        
        # Create compressed resource
        import gzip
        compressed_data = gzip.compress(mock_resource_data)
        resource_path = resource_dir / "compressed_resource.bin.gz"
        with open(resource_path, "wb") as f:
            f.write(compressed_data)
        
        # Create metadata
        metadata = mock_resource_metadata.copy()
        metadata["id"] = "compressed_resource"
        metadata["compression"] = "gzip"
        metadata["original_size"] = len(mock_resource_data)
        metadata["compressed_size"] = len(compressed_data)
        
        metadata_path = resource_dir / "metadata/compressed_resource.json"
        metadata_path.parent.mkdir(exist_ok=True)
        with open(metadata_path, "w") as f:
            json.dump(metadata, f)
        
        # Load resource
        resource = await manager.load_resource("compressed_resource")
        
        # Verify decompression
        assert resource is not None
        assert len(resource.data) == len(mock_resource_data)
        assert resource.data == mock_resource_data
    
    async def test_async_loading(
        self,
        resource_dir: Path,
        mock_resource_data: bytes,
        mock_resource_metadata: Dict[str, Any]
    ) -> None:
        """Test asynchronous resource loading."""
        manager = ResourceManager(resource_dir)
        
        # Create multiple resources
        resource_ids = ["async1", "async2", "async3"]
        for resource_id in resource_ids:
            # Create resource
            resource_path = resource_dir / f"{resource_id}.bin"
            with open(resource_path, "wb") as f:
                f.write(mock_resource_data)
            
            # Create metadata
            metadata = mock_resource_metadata.copy()
            metadata["id"] = resource_id
            
            metadata_path = resource_dir / f"metadata/{resource_id}.json"
            metadata_path.parent.mkdir(exist_ok=True)
            with open(metadata_path, "w") as f:
                json.dump(metadata, f)
        
        # Load resources concurrently
        tasks = [manager.load_resource(rid) for rid in resource_ids]
        resources = await asyncio.gather(*tasks)
        
        # Verify concurrent loading
        assert len(resources) == len(resource_ids)
        assert all(r is not None for r in resources)
    
    async def test_error_handling(
        self,
        resource_dir: Path,
        caplog: LogCaptureFixture
    ) -> None:
        """Test error handling in resource management."""
        manager = ResourceManager(resource_dir)
        
        # Test loading nonexistent resource
        resource = await manager.load_resource("nonexistent")
        assert resource is None
        assert any("Resource not found" in record.message
                  for record in caplog.records)
        
        # Test loading corrupted resource
        # Create corrupted resource file
        resource_path = resource_dir / "corrupted.bin"
        with open(resource_path, "wb") as f:
            f.write(b"corrupted data")
        
        # Create metadata with wrong checksum
        metadata = {
            "id": "corrupted",
            "type": ResourceType.BINARY,
            "checksum": "wrong_checksum",
            "size": 100
        }
        metadata_path = resource_dir / "metadata/corrupted.json"
        metadata_path.parent.mkdir(exist_ok=True)
        with open(metadata_path, "w") as f:
            json.dump(metadata, f)
        
        # Load corrupted resource
        resource = await manager.load_resource("corrupted")
        assert resource is None
        assert any("Checksum verification failed" in record.message
                  for record in caplog.records)
    
    async def test_memory_management(
        self,
        resource_dir: Path,
        mock_resource_metadata: Dict[str, Any]
    ) -> None:
        """Test memory management in resource loading."""
        # Create manager with memory limit
        manager = ResourceManager(
            resource_dir,
            max_memory_mb=10,
            max_cache_size_mb=5
        )
        
        # Create large resources
        for i in range(3):
            # Create 4MB resource
            resource_data = b"0" * (4 * 1024 * 1024)
            resource_path = resource_dir / f"large_resource_{i}.bin"
            with open(resource_path, "wb") as f:
                f.write(resource_data)
            
            # Create metadata
            metadata = mock_resource_metadata.copy()
            metadata["id"] = f"large_resource_{i}"
            metadata["size"] = len(resource_data)
            
            metadata_path = resource_dir / f"metadata/large_resource_{i}.json"
            metadata_path.parent.mkdir(exist_ok=True)
            with open(metadata_path, "w") as f:
                json.dump(metadata, f)
        
        # Load resources
        resources = []
        for i in range(3):
            resource = await manager.load_resource(f"large_resource_{i}")
            if resource is not None:
                resources.append(resource)
        
        # Verify memory constraints
        assert manager.current_memory_usage <= 10 * 1024 * 1024  # 10MB
        assert manager.current_cache_size <= 5 * 1024 * 1024  # 5MB
        assert len(resources) <= 2  # Only 2 4MB resources should fit in memory 