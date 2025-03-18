"""Configuration settings for Realm Forge."""

from functools import lru_cache
from typing import Dict, Optional, Any
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class APISettings(BaseModel):
    """API server settings."""
    host: str = Field(default="0.0.0.0", env="API_HOST")
    port: int = Field(default=8001, env="API_PORT")
    workers: int = Field(default=4, env="API_WORKERS")
    debug: bool = Field(default=False, env="DEBUG")

class OpenAISettings(BaseModel):
    """OpenAI API configuration settings."""
    api_key: str = Field(default="", env="OPENAI_API_KEY")
    model_name: str = Field(default="gpt-4-turbo-preview", env="OPENAI_MODEL_NAME")
    temperature: float = Field(default=0.7, env="OPENAI_TEMPERATURE")
    max_tokens: int = Field(default=1000, env="OPENAI_MAX_TOKENS")
    top_p: float = Field(default=1.0, env="OPENAI_TOP_P")
    frequency_penalty: float = Field(default=0.0, env="OPENAI_FREQUENCY_PENALTY")
    presence_penalty: float = Field(default=0.0, env="OPENAI_PRESENCE_PENALTY")

class LLMSettings(BaseModel):
    """LLM configuration settings."""
    narrative_llm: str = Field(default="gpt-4-turbo", env="NARRATIVE_LLM")
    world_llm: str = Field(default="gpt-4o-mini", env="WORLD_LLM")
    npc_llm: str = Field(default="gpt-4o-mini", env="NPC_LLM")
    difficulty_llm: str = Field(default="gpt-4o-mini", env="DIFFICULTY_LLM")
    optimizer_llm: str = Field(default="gpt-4-turbo", env="OPTIMIZER_LLM")

class AFlowSettings(BaseModel):
    """AFLOW configuration settings."""
    optimized_path: str = Field(default="../metagpt/ext/aflow/scripts/optimized", env="AFLOW_OPTIMIZED_PATH")
    narrative_workflow_round: str = Field(default="best", env="NARRATIVE_WORKFLOW_ROUND")
    world_workflow_round: str = Field(default="best", env="WORLD_WORKFLOW_ROUND")
    npc_workflow_round: str = Field(default="best", env="NPC_WORKFLOW_ROUND")
    difficulty_workflow_round: str = Field(default="best", env="DIFFICULTY_WORKFLOW_ROUND")

class OptimizationSettings(BaseModel):
    """Optimization settings."""
    enable_auto_optimization: bool = Field(default=False, env="ENABLE_AUTO_OPTIMIZATION")
    optimization_interval_hours: int = Field(default=24, env="OPTIMIZATION_INTERVAL_HOURS")
    validation_rounds: int = Field(default=3, env="VALIDATION_ROUNDS")

class PerformanceSettings(BaseModel):
    """Performance settings."""
    max_concurrent_requests: int = Field(default=10, env="MAX_CONCURRENT_REQUESTS")
    request_timeout_seconds: int = Field(default=30, env="REQUEST_TIMEOUT_SECONDS")
    cache_expiry_seconds: int = Field(default=3600, env="CACHE_EXPIRY_SECONDS")

class VisualizationSettings(BaseModel):
    """Visualization settings."""
    asset_base_path: str = Field(default="./assets", env="ASSET_BASE_PATH")
    template_path: str = Field(default="./templates", env="TEMPLATE_PATH")
    max_scene_size_mb: int = Field(default=50, env="MAX_SCENE_SIZE_MB")
    enable_ray_tracing: bool = Field(default=False, env="ENABLE_RAY_TRACING")
    default_quality: str = Field(default="medium", env="DEFAULT_QUALITY")

class Settings(BaseSettings):
    """Main settings class."""
    api: APISettings = Field(default_factory=APISettings)
    openai: OpenAISettings = Field(default_factory=OpenAISettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    aflow: AFlowSettings = Field(default_factory=AFlowSettings)
    optimization: OptimizationSettings = Field(default_factory=OptimizationSettings)
    performance: PerformanceSettings = Field(default_factory=PerformanceSettings)
    visualization: VisualizationSettings = Field(default_factory=VisualizationSettings)

    class Config:
        """Pydantic config."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "allow"
        protected_namespaces = ()
        
    @classmethod
    def get_settings(cls) -> "Settings":
        """Get cached settings instance.
        
        Returns:
            Settings: Cached settings instance
        """
        return get_settings()

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance.
    
    Returns:
        Settings: Cached settings instance
    """
    return Settings() 