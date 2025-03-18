"""Tests for the configuration management system."""

from typing import Any, Dict, List, Optional
from pathlib import Path
import pytest
import json
import os
from unittest.mock import patch

if True:  # TYPE_CHECKING
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture

from ...models.config import ConfigSchema, Environment
from ..services.config.config_manager import ConfigManager

@pytest.fixture
def config_dir(tmp_path: Path) -> Path:
    """Create a temporary directory for test configurations."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir

@pytest.fixture
def mock_config_data() -> Dict[str, Any]:
    """Create mock configuration data."""
    return {
        "app": {
            "name": "RealmForge",
            "version": "1.0.0",
            "debug": False
        },
        "rendering": {
            "resolution": {
                "width": 1920,
                "height": 1080
            },
            "quality": "high",
            "vsync": True,
            "antialiasing": "MSAA4x"
        },
        "assets": {
            "base_path": "/assets",
            "cache_size_mb": 1024,
            "preload": ["textures", "models"]
        },
        "network": {
            "host": "localhost",
            "port": 8080,
            "timeout": 30
        }
    }

@pytest.fixture
def mock_schema() -> Dict[str, Any]:
    """Create mock configuration schema."""
    return {
        "type": "object",
        "required": ["app", "rendering", "assets", "network"],
        "properties": {
            "app": {
                "type": "object",
                "required": ["name", "version"],
                "properties": {
                    "name": {"type": "string"},
                    "version": {"type": "string"},
                    "debug": {"type": "boolean"}
                }
            },
            "rendering": {
                "type": "object",
                "required": ["resolution", "quality"],
                "properties": {
                    "resolution": {
                        "type": "object",
                        "properties": {
                            "width": {"type": "integer", "minimum": 800},
                            "height": {"type": "integer", "minimum": 600}
                        }
                    },
                    "quality": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "ultra"]
                    },
                    "vsync": {"type": "boolean"},
                    "antialiasing": {"type": "string"}
                }
            }
        }
    }

class TestConfigManager:
    """Test suite for ConfigManager class."""
    
    async def test_config_loading(
        self,
        config_dir: Path,
        mock_config_data: Dict[str, Any]
    ) -> None:
        """Test basic configuration loading functionality."""
        # Create config file
        config_path = config_dir / "config.json"
        with open(config_path, "w") as f:
            json.dump(mock_config_data, f)
        
        # Create manager and load config
        manager = ConfigManager(config_dir)
        config = await manager.load_config("config.json")
        
        # Verify config loading
        assert config is not None
        assert config["app"]["name"] == "RealmForge"
        assert config["rendering"]["resolution"]["width"] == 1920
        assert config["assets"]["cache_size_mb"] == 1024
    
    async def test_environment_handling(
        self,
        config_dir: Path,
        mock_config_data: Dict[str, Any],
        monkeypatch: MonkeyPatch
    ) -> None:
        """Test environment-specific configuration handling."""
        # Create base config
        base_config_path = config_dir / "config.json"
        with open(base_config_path, "w") as f:
            json.dump(mock_config_data, f)
        
        # Create environment-specific config
        dev_config = {
            "app": {"debug": True},
            "network": {
                "host": "dev-server",
                "port": 9000
            }
        }
        dev_config_path = config_dir / "config.dev.json"
        with open(dev_config_path, "w") as f:
            json.dump(dev_config, f)
        
        # Set environment
        monkeypatch.setenv("REALM_FORGE_ENV", "dev")
        
        # Load config with environment
        manager = ConfigManager(config_dir)
        config = await manager.load_config("config.json")
        
        # Verify environment overrides
        assert config["app"]["debug"] is True
        assert config["network"]["host"] == "dev-server"
        assert config["network"]["port"] == 9000
        # Base config values should remain
        assert config["app"]["name"] == "RealmForge"
        assert config["rendering"]["quality"] == "high"
    
    async def test_schema_validation(
        self,
        config_dir: Path,
        mock_config_data: Dict[str, Any],
        mock_schema: Dict[str, Any]
    ) -> None:
        """Test configuration schema validation."""
        # Create config file
        config_path = config_dir / "config.json"
        with open(config_path, "w") as f:
            json.dump(mock_config_data, f)
        
        # Create schema file
        schema_path = config_dir / "schema.json"
        with open(schema_path, "w") as f:
            json.dump(mock_schema, f)
        
        # Create manager with schema validation
        manager = ConfigManager(config_dir, schema_path=schema_path)
        
        # Test valid config
        config = await manager.load_config("config.json")
        assert config is not None
        
        # Test invalid config
        invalid_config = mock_config_data.copy()
        invalid_config["rendering"]["resolution"]["width"] = 400  # Below minimum
        
        invalid_path = config_dir / "invalid_config.json"
        with open(invalid_path, "w") as f:
            json.dump(invalid_config, f)
        
        with pytest.raises(ValueError):
            await manager.load_config("invalid_config.json")
    
    async def test_config_caching(
        self,
        config_dir: Path,
        mock_config_data: Dict[str, Any],
        mocker: MockerFixture
    ) -> None:
        """Test configuration caching behavior."""
        # Create config file
        config_path = config_dir / "config.json"
        with open(config_path, "w") as f:
            json.dump(mock_config_data, f)
        
        # Create manager
        manager = ConfigManager(config_dir)
        
        # Mock _load_file method
        mock_load = mocker.patch.object(manager, '_load_file')
        mock_load.return_value = mock_config_data
        
        # Load config multiple times
        config1 = await manager.load_config("config.json")
        config2 = await manager.load_config("config.json")
        
        # Verify caching
        assert config1 is config2
        mock_load.assert_called_once()
    
    async def test_environment_variables(
        self,
        config_dir: Path,
        mock_config_data: Dict[str, Any],
        monkeypatch: MonkeyPatch
    ) -> None:
        """Test environment variable substitution in config."""
        # Create config with variable references
        config_with_vars = mock_config_data.copy()
        config_with_vars["network"]["host"] = "${RF_HOST}"
        config_with_vars["network"]["port"] = "${RF_PORT}"
        
        config_path = config_dir / "config.json"
        with open(config_path, "w") as f:
            json.dump(config_with_vars, f)
        
        # Set environment variables
        monkeypatch.setenv("RF_HOST", "custom-host")
        monkeypatch.setenv("RF_PORT", "8888")
        
        # Load config
        manager = ConfigManager(config_dir)
        config = await manager.load_config("config.json")
        
        # Verify variable substitution
        assert config["network"]["host"] == "custom-host"
        assert config["network"]["port"] == 8888  # Should be converted to int
    
    async def test_config_inheritance(
        self,
        config_dir: Path,
        mock_config_data: Dict[str, Any]
    ) -> None:
        """Test configuration inheritance and merging."""
        # Create base config
        base_config = {
            "app": {"name": "Base"},
            "features": ["basic", "advanced"],
            "settings": {
                "timeout": 30,
                "retries": 3
            }
        }
        base_path = config_dir / "base.json"
        with open(base_path, "w") as f:
            json.dump(base_config, f)
        
        # Create child config
        child_config = {
            "extends": "base.json",
            "app": {"version": "2.0.0"},
            "features": ["premium"],
            "settings": {
                "timeout": 60
            }
        }
        child_path = config_dir / "child.json"
        with open(child_path, "w") as f:
            json.dump(child_config, f)
        
        # Load child config
        manager = ConfigManager(config_dir)
        config = await manager.load_config("child.json")
        
        # Verify inheritance
        assert config["app"]["name"] == "Base"  # From base
        assert config["app"]["version"] == "2.0.0"  # From child
        assert set(config["features"]) == {"basic", "advanced", "premium"}
        assert config["settings"]["timeout"] == 60  # Overridden
        assert config["settings"]["retries"] == 3  # From base
    
    async def test_config_reloading(
        self,
        config_dir: Path,
        mock_config_data: Dict[str, Any]
    ) -> None:
        """Test configuration reloading functionality."""
        # Create initial config
        config_path = config_dir / "config.json"
        with open(config_path, "w") as f:
            json.dump(mock_config_data, f)
        
        # Load initial config
        manager = ConfigManager(config_dir)
        config1 = await manager.load_config("config.json")
        
        # Modify config file
        modified_config = mock_config_data.copy()
        modified_config["app"]["version"] = "2.0.0"
        with open(config_path, "w") as f:
            json.dump(modified_config, f)
        
        # Reload config
        config2 = await manager.reload_config("config.json")
        
        # Verify reload
        assert config2["app"]["version"] == "2.0.0"
        assert config1 is not config2
    
    async def test_error_handling(
        self,
        config_dir: Path,
        caplog: LogCaptureFixture
    ) -> None:
        """Test error handling in configuration management."""
        manager = ConfigManager(config_dir)
        
        # Test loading nonexistent config
        config = await manager.load_config("nonexistent.json")
        assert config is None
        assert any("Configuration file not found" in record.message
                  for record in caplog.records)
        
        # Test loading invalid JSON
        invalid_path = config_dir / "invalid.json"
        with open(invalid_path, "w") as f:
            f.write("invalid json")
        
        config = await manager.load_config("invalid.json")
        assert config is None
        assert any("Failed to parse configuration" in record.message
                  for record in caplog.records)
        
        # Test circular inheritance
        circular1 = {"extends": "circular2.json"}
        circular2 = {"extends": "circular1.json"}
        
        with open(config_dir / "circular1.json", "w") as f:
            json.dump(circular1, f)
        with open(config_dir / "circular2.json", "w") as f:
            json.dump(circular2, f)
        
        with pytest.raises(ValueError) as exc_info:
            await manager.load_config("circular1.json")
        assert "Circular inheritance detected" in str(exc_info.value) 