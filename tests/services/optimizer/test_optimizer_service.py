"""Tests for the performance optimization and resource management service."""

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

from ....src.services.optimizer import OptimizerService
from ....src.models.optimization import (
    OptimizationSettings,
    ResourceMetrics,
    CacheStrategy,
    PerformanceProfile,
    OptimizationTarget,
    ResourceType,
    CachePolicy
)

@pytest.fixture
def mock_optimization_settings() -> OptimizationSettings:
    """Create mock optimization settings for testing."""
    return OptimizationSettings(
        target_fps=60,
        memory_limit_mb=1024,
        cpu_target_usage=0.7,
        gpu_target_usage=0.8,
        cache_size_mb=256,
        optimization_interval=5.0,  # seconds
        adaptive_quality=True
    )

@pytest.fixture
def mock_resource_metrics() -> ResourceMetrics:
    """Create mock resource usage metrics for testing."""
    return ResourceMetrics(
        fps=55,
        frame_time=16.7,  # ms
        memory_usage_mb=800,
        cpu_usage=0.65,
        gpu_usage=0.75,
        vram_usage_mb=400,
        disk_io_mbps=50,
        network_bandwidth_mbps=10
    )

@pytest.fixture
def mock_performance_profile() -> PerformanceProfile:
    """Create mock performance profile for testing."""
    return PerformanceProfile(
        scene_complexity=0.7,
        entity_count=1000,
        texture_memory_mb=200,
        shader_complexity=0.6,
        particle_count=500,
        shadow_quality=0.8,
        post_processing_level=0.7
    )

@pytest.fixture
async def optimizer_service(
    mock_optimization_settings: OptimizationSettings,
    tmp_path: Path
) -> OptimizerService:
    """Create an OptimizerService instance with mocked dependencies."""
    # Create service instance
    service = OptimizerService(settings=mock_optimization_settings)
    await service.initialize()
    
    return service

class TestOptimizerService:
    """Test suite for OptimizerService class."""
    
    async def test_performance_monitoring(
        self,
        optimizer_service: OptimizerService,
        mock_resource_metrics: ResourceMetrics
    ) -> None:
        """Test performance monitoring and metrics collection."""
        # Record metrics
        await optimizer_service.record_metrics(mock_resource_metrics)
        
        # Get performance report
        report = await optimizer_service.get_performance_report()
        
        # Verify report contents
        assert "fps" in report
        assert "frame_time" in report
        assert "memory_usage" in report
        assert report["fps"] == mock_resource_metrics.fps
        assert report["memory_usage"]["current"] == mock_resource_metrics.memory_usage_mb
        
        # Test average metrics
        for _ in range(5):
            await optimizer_service.record_metrics(mock_resource_metrics)
        
        avg_metrics = await optimizer_service.get_average_metrics(
            duration_seconds=1.0
        )
        
        assert abs(avg_metrics.fps - mock_resource_metrics.fps) < 0.1
        assert abs(avg_metrics.cpu_usage - mock_resource_metrics.cpu_usage) < 0.01
    
    async def test_resource_optimization(
        self,
        optimizer_service: OptimizerService,
        mock_resource_metrics: ResourceMetrics,
        mock_performance_profile: PerformanceProfile
    ) -> None:
        """Test resource usage optimization."""
        # Test CPU optimization
        cpu_adjustments = await optimizer_service.optimize_resource_usage(
            resource_type=ResourceType.CPU,
            current_metrics=mock_resource_metrics,
            performance_profile=mock_performance_profile
        )
        
        assert isinstance(cpu_adjustments, dict)
        assert "entity_processing" in cpu_adjustments
        assert "physics_quality" in cpu_adjustments
        
        # Test GPU optimization
        gpu_adjustments = await optimizer_service.optimize_resource_usage(
            resource_type=ResourceType.GPU,
            current_metrics=mock_resource_metrics,
            performance_profile=mock_performance_profile
        )
        
        assert "shader_quality" in gpu_adjustments
        assert "shadow_quality" in gpu_adjustments
        assert all(0 <= v <= 1 for v in gpu_adjustments.values())
        
        # Test memory optimization
        memory_adjustments = await optimizer_service.optimize_resource_usage(
            resource_type=ResourceType.MEMORY,
            current_metrics=mock_resource_metrics,
            performance_profile=mock_performance_profile
        )
        
        assert "texture_quality" in memory_adjustments
        assert "model_detail" in memory_adjustments
    
    async def test_cache_management(
        self,
        optimizer_service: OptimizerService,
        mock_performance_profile: PerformanceProfile
    ) -> None:
        """Test cache management and strategies."""
        # Test cache strategy selection
        strategy = await optimizer_service.select_cache_strategy(
            performance_profile=mock_performance_profile,
            available_memory_mb=512
        )
        
        assert isinstance(strategy, CacheStrategy)
        assert strategy.policy in [CachePolicy.LRU, CachePolicy.MRU]
        assert strategy.size_mb <= 512
        
        # Test cache operations
        await optimizer_service.configure_cache(strategy)
        
        # Add items to cache
        await optimizer_service.cache_resource(
            resource_id="texture_1",
            size_mb=10,
            priority=0.8
        )
        
        await optimizer_service.cache_resource(
            resource_id="model_1",
            size_mb=20,
            priority=0.9
        )
        
        # Verify cache status
        cache_status = await optimizer_service.get_cache_status()
        assert cache_status["used_mb"] == 30
        assert len(cache_status["cached_resources"]) == 2
        
        # Test cache eviction
        large_resource_size = strategy.size_mb
        await optimizer_service.cache_resource(
            resource_id="large_resource",
            size_mb=large_resource_size,
            priority=1.0
        )
        
        updated_status = await optimizer_service.get_cache_status()
        assert "large_resource" in updated_status["cached_resources"]
        assert "texture_1" not in updated_status["cached_resources"]
    
    async def test_quality_adaptation(
        self,
        optimizer_service: OptimizerService,
        mock_resource_metrics: ResourceMetrics,
        mock_performance_profile: PerformanceProfile
    ) -> None:
        """Test adaptive quality adjustments."""
        # Test quality adjustment based on performance
        adjustments = await optimizer_service.adapt_quality(
            current_metrics=mock_resource_metrics,
            performance_profile=mock_performance_profile
        )
        
        assert isinstance(adjustments, dict)
        assert "visual_quality" in adjustments
        assert "performance_impact" in adjustments
        
        # Test quality presets
        preset = await optimizer_service.get_quality_preset(
            target=OptimizationTarget.PERFORMANCE
        )
        
        assert preset["shadow_quality"] < performance_profile.shadow_quality
        assert preset["particle_count"] < performance_profile.particle_count
        
        # Test gradual quality adjustment
        for _ in range(5):
            metrics = ResourceMetrics(
                fps=30,  # Below target
                frame_time=33.3,
                memory_usage_mb=800,
                cpu_usage=0.9,  # High usage
                gpu_usage=0.95,  # High usage
                vram_usage_mb=400,
                disk_io_mbps=50,
                network_bandwidth_mbps=10
            )
            
            await optimizer_service.record_metrics(metrics)
        
        emergency_adjustments = await optimizer_service.get_emergency_adjustments()
        assert emergency_adjustments["quality_reduction"] > 0.2
    
    async def test_optimization_strategies(
        self,
        optimizer_service: OptimizerService,
        mock_resource_metrics: ResourceMetrics,
        mock_performance_profile: PerformanceProfile
    ) -> None:
        """Test different optimization strategies."""
        # Test balanced optimization
        balanced = await optimizer_service.optimize_for_target(
            target=OptimizationTarget.BALANCED,
            current_metrics=mock_resource_metrics,
            performance_profile=mock_performance_profile
        )
        
        assert balanced["quality_adjustments"]["shadow_quality"] == performance_profile.shadow_quality
        assert 0.4 <= balanced["resource_allocation"]["cpu"] <= 0.8
        
        # Test performance optimization
        performance = await optimizer_service.optimize_for_target(
            target=OptimizationTarget.PERFORMANCE,
            current_metrics=mock_resource_metrics,
            performance_profile=mock_performance_profile
        )
        
        assert performance["quality_adjustments"]["shadow_quality"] < balanced["quality_adjustments"]["shadow_quality"]
        assert performance["quality_adjustments"]["particle_count"] < performance_profile.particle_count
        
        # Test quality optimization
        quality = await optimizer_service.optimize_for_target(
            target=OptimizationTarget.QUALITY,
            current_metrics=mock_resource_metrics,
            performance_profile=mock_performance_profile
        )
        
        assert quality["quality_adjustments"]["shadow_quality"] > balanced["quality_adjustments"]["shadow_quality"]
        assert quality["quality_adjustments"]["post_processing_level"] > balanced["quality_adjustments"]["post_processing_level"]
    
    async def test_resource_prediction(
        self,
        optimizer_service: OptimizerService,
        mock_performance_profile: PerformanceProfile
    ) -> None:
        """Test resource usage prediction."""
        # Predict resource usage for scene
        prediction = await optimizer_service.predict_resource_usage(
            performance_profile=mock_performance_profile
        )
        
        assert isinstance(prediction, dict)
        assert all(k in prediction for k in [
            "expected_memory_mb",
            "expected_cpu_usage",
            "expected_gpu_usage",
            "expected_fps"
        ])
        
        # Test prediction accuracy
        measured_metrics = ResourceMetrics(
            fps=58,
            frame_time=17.2,
            memory_usage_mb=prediction["expected_memory_mb"],
            cpu_usage=prediction["expected_cpu_usage"],
            gpu_usage=prediction["expected_gpu_usage"],
            vram_usage_mb=400,
            disk_io_mbps=50,
            network_bandwidth_mbps=10
        )
        
        accuracy = await optimizer_service.evaluate_prediction_accuracy(
            prediction=prediction,
            actual_metrics=measured_metrics
        )
        
        assert accuracy["memory_accuracy"] > 0.8
        assert accuracy["cpu_accuracy"] > 0.8
        assert accuracy["gpu_accuracy"] > 0.8
    
    async def test_error_handling(
        self,
        optimizer_service: OptimizerService,
        mock_resource_metrics: ResourceMetrics,
        caplog: LogCaptureFixture
    ) -> None:
        """Test error handling in optimization processes."""
        # Test invalid resource type
        with pytest.raises(ValueError):
            await optimizer_service.optimize_resource_usage(
                resource_type="invalid_type",
                current_metrics=mock_resource_metrics,
                performance_profile=mock_performance_profile
            )
        
        # Test invalid cache size
        with pytest.raises(ValueError):
            await optimizer_service.configure_cache(
                CacheStrategy(
                    policy=CachePolicy.LRU,
                    size_mb=-100
                )
            )
        
        # Test invalid metrics
        invalid_metrics = ResourceMetrics(
            fps=-30,
            frame_time=-16.7,
            memory_usage_mb=-800,
            cpu_usage=1.5,
            gpu_usage=1.2,
            vram_usage_mb=-400,
            disk_io_mbps=-50,
            network_bandwidth_mbps=-10
        )
        
        with pytest.raises(ValueError):
            await optimizer_service.record_metrics(invalid_metrics)
        
        # Verify error logging
        assert any("Invalid resource type" in record.message
                  for record in caplog.records)
        assert any("Invalid cache configuration" in record.message
                  for record in caplog.records)
        assert any("Invalid metrics values" in record.message
                  for record in caplog.records) 