"""Dependencies for FastAPI application."""

from typing import Dict, Any
from functools import lru_cache

from ..services.narrative import NarrativeService
from ..services.world import WorldService
from ..services.npc import NPCService
from ..services.difficulty import DifficultyService
from ..services.optimizer import WorkflowOptimizer, OptimizerService
from ..services.visualization import VisualizationService
from ..config.settings import Settings, get_settings


@lru_cache()
def get_narrative_service() -> NarrativeService:
    """Get cached narrative service instance.
    
    Returns:
        NarrativeService: Cached service instance
    """
    settings = get_settings()
    return NarrativeService(settings)


@lru_cache()
def get_world_service() -> WorldService:
    """Get cached world service instance.
    
    Returns:
        WorldService: Cached service instance
    """
    settings = get_settings()
    return WorldService(settings)


@lru_cache()
def get_npc_service() -> NPCService:
    """Get cached NPC service instance.
    
    Returns:
        NPCService: Cached service instance
    """
    settings = get_settings()
    return NPCService(settings)


@lru_cache()
def get_difficulty_service() -> DifficultyService:
    """Get cached difficulty service instance.
    
    Returns:
        DifficultyService: Cached service instance
    """
    settings = get_settings()
    return DifficultyService(settings)


@lru_cache()
def get_workflow_optimizer() -> WorkflowOptimizer:
    """Get cached workflow optimizer instance.
    
    Returns:
        WorkflowOptimizer: Cached optimizer instance
    """
    settings = get_settings()
    return WorkflowOptimizer.create(settings)


@lru_cache()
def get_optimizer_service() -> OptimizerService:
    """Get cached optimizer service instance.
    
    Returns:
        OptimizerService: Cached service instance
    """
    settings = get_settings()
    return OptimizerService(settings)


@lru_cache()
def get_visualization_service() -> VisualizationService:
    """Get cached visualization service instance.
    
    Returns:
        VisualizationService: Cached service instance
    """
    settings = get_settings()
    return VisualizationService(settings) 