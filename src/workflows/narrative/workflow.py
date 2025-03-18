"""Narrative generation workflow implementation."""

import json
import uuid
from typing import Dict, Any, Tuple, Optional

from metagpt.provider.llm_provider_registry import create_llm_instance
from metagpt.utils.cost_manager import CostManager
from metagpt.ext.aflow.scripts.operator import Operator

from ..utils import format_context, serialize_for_prompt
from . import prompt


class AnalysisOperator(Operator):
    """Operator for analyzing player context and choices."""
    
    async def __call__(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze player context and choices.
        
        Args:
            input_data: Input data containing player context, choice, and narrative type
            
        Returns:
            Dict containing analysis and updated input data
        """
        player_context = format_context(input_data.get("context", {}))
        player_choice = serialize_for_prompt(input_data.get("player_choice", {}))
        narrative_type = input_data.get("narrative_type", "quest")
        
        instruction = prompt.NARRATIVE_ANALYSIS_PROMPT.format(
            player_context=player_context,
            player_choice=player_choice,
            narrative_type=narrative_type
        )
        
        response = await self.llm.aask(instruction)
        
        return {
            "narrative_analysis": response,
            **input_data
        }


class GenerationOperator(Operator):
    """Operator for generating narrative elements."""
    
    async def __call__(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate narrative elements based on analysis.
        
        Args:
            input_data: Input data containing player context, analysis, and narrative type
            
        Returns:
            Dict containing generated narrative and updated input data
        """
        player_context = format_context(input_data.get("context", {}))
        narrative_analysis = input_data.get("narrative_analysis", "")
        narrative_type = input_data.get("narrative_type", "quest")
        
        instruction = prompt.NARRATIVE_GENERATION_PROMPT.format(
            player_context=player_context,
            narrative_analysis=narrative_analysis,
            narrative_type=narrative_type
        )
        
        response = await self.llm.aask(instruction)
        
        return {
            "generated_narrative": response,
            **input_data
        }


class ReviewOperator(Operator):
    """Operator for reviewing generated narrative."""
    
    async def __call__(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Review generated narrative for quality and consistency.
        
        Args:
            input_data: Input data containing player context and generated narrative
            
        Returns:
            Dict containing review feedback and updated input data
        """
        player_context = format_context(input_data.get("context", {}))
        generated_narrative = input_data.get("generated_narrative", "")
        
        instruction = prompt.NARRATIVE_REVIEW_PROMPT.format(
            player_context=player_context,
            generated_narrative=generated_narrative
        )
        
        response = await self.llm.aask(instruction)
        
        return {
            "review_feedback": response,
            **input_data
        }


class RevisionOperator(Operator):
    """Operator for revising narrative based on review feedback."""
    
    async def __call__(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Revise narrative based on review feedback.
        
        Args:
            input_data: Input data containing original narrative and review feedback
            
        Returns:
            Dict containing revised narrative and updated input data
        """
        original_narrative = input_data.get("generated_narrative", "")
        review_feedback = input_data.get("review_feedback", "")
        
        instruction = prompt.NARRATIVE_REVISION_PROMPT.format(
            original_narrative=original_narrative,
            review_feedback=review_feedback
        )
        
        response = await self.llm.aask(instruction)
        
        return {
            "revised_narrative": response,
            **input_data
        }


class FormatOperator(Operator):
    """Operator for formatting narrative elements for the game engine."""
    
    async def __call__(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format narrative elements for integration with the game engine.
        
        Args:
            input_data: Input data containing narrative element to format
            
        Returns:
            Dict containing formatted narrative and updated input data
        """
        narrative_element = input_data.get("revised_narrative", 
                                          input_data.get("generated_narrative", ""))
        
        instruction = prompt.NARRATIVE_FORMAT_PROMPT.format(
            narrative_element=narrative_element
        )
        
        response = await self.llm.aask(instruction)
        
        try:
            # Try to parse as JSON, if it's already in JSON format
            formatted_narrative = json.loads(response)
        except json.JSONDecodeError:
            # If not valid JSON, keep as string
            formatted_narrative = response
        
        return {
            "formatted_narrative": formatted_narrative,
            **input_data
        }


class NarrativeWorkflow:
    """Narrative generation workflow.
    
    This workflow generates narrative elements based on player context and choices.
    It uses a series of operators to analyze context, generate narrative,
    review for quality, revise based on feedback, and format for the game engine.
    """
    
    def __init__(self, name: str, llm_config: Dict[str, Any], dataset: str = "RPG") -> None:
        """Initialize the narrative workflow.
        
        Args:
            name: Name of the workflow
            llm_config: LLM configuration
            dataset: Dataset type (default: "RPG")
        """
        self.name = name
        self.dataset = dataset
        self.llm = create_llm_instance(llm_config)
        self.llm.cost_manager = CostManager()
        
        # Initialize operators
        self.analysis = AnalysisOperator(self.llm, "analysis")
        self.generation = GenerationOperator(self.llm, "generation")
        self.review = ReviewOperator(self.llm, "review")
        self.revision = RevisionOperator(self.llm, "revision")
        self.format = FormatOperator(self.llm, "format")
    
    async def __call__(self, request_data: Dict[str, Any]) -> Tuple[Dict[str, Any], float]:
        """Execute the narrative generation workflow.
        
        Args:
            request_data: Input data for the workflow
            
        Returns:
            Tuple containing the generated narrative response and the cost
        """
        try:
            # Extract input data
            player_id = request_data.get("player_id", "")
            context = request_data.get("context", {})
            player_choice = request_data.get("player_choice", None)
            narrative_type = request_data.get("narrative_type", "quest")
            
            # Prepare input data
            input_data = {
                "player_id": player_id,
                "context": context,
                "player_choice": player_choice,
                "narrative_type": narrative_type
            }
            
            # Execute workflow steps
            analysis_result = await self.analysis(input_data)
            generation_result = await self.generation(analysis_result)
            review_result = await self.review(generation_result)
            
            # Conditionally revise based on review feedback
            if review_result["review_feedback"].strip().lower() != "no revisions needed":
                revision_result = await self.revision(review_result)
            else:
                revision_result = {
                    "revised_narrative": generation_result["generated_narrative"],
                    **review_result
                }
            
            format_result = await self.format(revision_result)
            
            # Extract the formatted narrative
            formatted_narrative = format_result.get("formatted_narrative", {})
            
            # Generate response
            request_id = str(uuid.uuid4())
            
            # Process the formatted narrative into response structure
            narrative_elements = []
            next_choices = []
            
            if isinstance(formatted_narrative, dict):
                # If formatted as a dictionary
                narrative_text = formatted_narrative.get("narrative_text", "")
                next_choices = formatted_narrative.get("player_choices", [])
                
                # Create narrative element
                element_id = str(uuid.uuid4())
                narrative_elements.append({
                    "element_id": element_id,
                    "element_type": narrative_type,
                    "content": narrative_text,
                    "metadata": {
                        "tone": formatted_narrative.get("tone", ""),
                        "themes": formatted_narrative.get("themes", []),
                        "npc_involved": formatted_narrative.get("npcs", []),
                        "presentation": formatted_narrative.get("presentation", {})
                    }
                })
            else:
                # If still in text format, do basic processing
                element_id = str(uuid.uuid4())
                narrative_elements.append({
                    "element_id": element_id,
                    "element_type": narrative_type,
                    "content": formatted_narrative,
                    "metadata": {}
                })
                
                # Default choices if not provided
                next_choices = [
                    {"choice_id": "1", "text": "Accept", "consequences": {}},
                    {"choice_id": "2", "text": "Decline", "consequences": {}}
                ]
            
            # Create response
            response = {
                "request_id": request_id,
                "player_id": player_id,
                "narrative_elements": narrative_elements,
                "updated_context": context,  # This should be updated in a real implementation
                "next_choices": next_choices,
                "cost": self.llm.cost_manager.total_cost
            }
            
            return response, self.llm.cost_manager.total_cost
        
        except Exception as e:
            # Handle errors
            error_response = {
                "request_id": str(uuid.uuid4()),
                "player_id": request_data.get("player_id", ""),
                "error": str(e),
                "cost": self.llm.cost_manager.total_cost
            }
            
            return error_response, self.llm.cost_manager.total_cost 