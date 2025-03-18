"""Workflow optimization API endpoints for Realm Forge."""

import uuid
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from loguru import logger

from ...config.settings import Settings
from ...services.optimizer import WorkflowOptimizer


router = APIRouter(
    prefix="/optimizer",
    tags=["optimizer"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"}
    }
)


async def get_optimizer_service() -> WorkflowOptimizer:
    """Get the optimizer service.
    
    Returns:
        WorkflowOptimizer: The optimizer service
    """
    settings = Settings.get_settings()
    return WorkflowOptimizer.create(settings)


@router.post("/optimize/{workflow_type}")
async def start_optimization(
    workflow_type: str,
    initial_round: int = 1,
    max_rounds: int = 20,
    validation_rounds: int = 3,
    check_convergence: bool = True,
    optimizer: WorkflowOptimizer = Depends(get_optimizer_service)
) -> Dict[str, Any]:
    """Start a workflow optimization task.
    
    Args:
        workflow_type: Type of workflow to optimize (narrative, world, npc, difficulty)
        initial_round: Starting round number
        max_rounds: Maximum optimization rounds
        validation_rounds: Number of validation runs per round
        check_convergence: Whether to check for convergence
        optimizer: Workflow optimizer service
        
    Returns:
        Dict with task details
    """
    try:
        logger.info(f"Starting optimization for {workflow_type} workflow")
        
        # Validate workflow type
        if workflow_type not in ["narrative", "world", "npc", "difficulty"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid workflow type: {workflow_type}. Must be one of: narrative, world, npc, difficulty"
            )
        
        # Start optimization
        result = await optimizer.start_optimization(
            workflow_type=workflow_type,
            initial_round=initial_round,
            max_rounds=max_rounds,
            validation_rounds=validation_rounds,
            check_convergence=check_convergence
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Optimization start failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start optimization: {str(e)}"
        )


@router.get("/task/{task_id}")
async def get_optimization_status(
    task_id: str,
    optimizer: WorkflowOptimizer = Depends(get_optimizer_service)
) -> Dict[str, Any]:
    """Get the status of an optimization task.
    
    Args:
        task_id: ID of the optimization task
        optimizer: Workflow optimizer service
        
    Returns:
        Dict with task status
    """
    try:
        logger.info(f"Getting status for optimization task {task_id}")
        
        # Get task status
        result = await optimizer.get_task_status(task_id)
        
        if result.get("status") == "not_found":
            raise HTTPException(
                status_code=404,
                detail=f"Task {task_id} not found"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get task status: {str(e)}"
        )


@router.get("/tasks")
async def get_all_tasks(
    optimizer: WorkflowOptimizer = Depends(get_optimizer_service)
) -> List[Dict[str, Any]]:
    """Get information about all optimization tasks.
    
    Args:
        optimizer: Workflow optimizer service
        
    Returns:
        List of task information
    """
    try:
        logger.info("Getting all optimization tasks")
        
        # Get all tasks
        result = await optimizer.get_all_tasks()
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to get all tasks: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get all tasks: {str(e)}"
        )


@router.get("/best_round/{workflow_type}")
async def get_best_round(
    workflow_type: str,
    optimizer: WorkflowOptimizer = Depends(get_optimizer_service)
) -> Dict[str, Any]:
    """Get the best round for a workflow type.
    
    Args:
        workflow_type: Type of workflow
        optimizer: Workflow optimizer service
        
    Returns:
        Dict with best round information
    """
    try:
        logger.info(f"Getting best round for {workflow_type} workflow")
        
        # Validate workflow type
        if workflow_type not in ["narrative", "world", "npc", "difficulty"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid workflow type: {workflow_type}. Must be one of: narrative, world, npc, difficulty"
            )
        
        # Get best round
        best_round = await optimizer.get_best_round(workflow_type)
        
        return {
            "workflow_type": workflow_type,
            "best_round": best_round
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get best round: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get best round: {str(e)}"
        ) 