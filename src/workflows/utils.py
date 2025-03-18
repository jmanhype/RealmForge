"""Utility functions for workflows."""

import json
from typing import Any, Dict, List, Union


def format_context(context: Dict[str, Any]) -> str:
    """Format context data into a string for use in prompts.
    
    Args:
        context: Context data as a dictionary
        
    Returns:
        Formatted context string
    """
    if not context:
        return "No context available."
    
    formatted_sections = []
    
    # Process player character info if available
    if player_char := context.get("player_character", {}):
        player_section = "PLAYER CHARACTER:\n"
        player_section += f"Name: {player_char.get('name', 'Unknown')}\n"
        player_section += f"Class: {player_char.get('class_type', 'Unknown')}\n"
        player_section += f"Level: {player_char.get('level', 1)}\n"
        
        # Format stats if available
        if stats := player_char.get("stats", {}):
            player_section += "Stats:\n"
            for stat, value in stats.items():
                player_section += f"- {stat.capitalize()}: {value}\n"
        
        formatted_sections.append(player_section)
    
    # Process world state if available
    if world_state := context.get("world_state", {}):
        world_section = "WORLD STATE:\n"
        for key, value in world_state.items():
            if isinstance(value, dict):
                world_section += f"{key.capitalize()}:\n"
                for subkey, subvalue in value.items():
                    world_section += f"- {subkey.capitalize()}: {subvalue}\n"
            else:
                world_section += f"{key.capitalize()}: {value}\n"
        
        formatted_sections.append(world_section)
    
    # Process character relationships if available
    if relationships := context.get("character_relationships", {}):
        rel_section = "CHARACTER RELATIONSHIPS:\n"
        for character, value in relationships.items():
            rel_section += f"- {character}: {value}\n"
        
        formatted_sections.append(rel_section)
    
    # Process quest history if available
    if quest_history := context.get("quest_history", []):
        quest_section = "QUEST HISTORY:\n"
        for quest in quest_history:
            quest_section += f"- {quest.get('name', 'Unnamed quest')}: {quest.get('outcome', 'Unknown outcome')}\n"
        
        formatted_sections.append(quest_section)
    
    # Process current location if available
    if current_location := context.get("current_location", {}):
        loc_section = "CURRENT LOCATION:\n"
        loc_section += f"Name: {current_location.get('name', 'Unknown')}\n"
        loc_section += f"Type: {current_location.get('type', 'Unknown')}\n"
        loc_section += f"Description: {current_location.get('description', 'No description')}\n"
        
        formatted_sections.append(loc_section)
    
    # Process active quests if available
    if active_quests := context.get("active_quests", []):
        active_section = "ACTIVE QUESTS:\n"
        for quest in active_quests:
            active_section += f"- {quest.get('name', 'Unnamed quest')}: {quest.get('status', 'Unknown status')}\n"
        
        formatted_sections.append(active_section)
    
    # Combine all sections
    return "\n".join(formatted_sections)


def serialize_for_prompt(data: Union[Dict[str, Any], List[Any], None]) -> str:
    """Serialize data for use in prompts.
    
    Args:
        data: Data to serialize (dict, list, or None)
        
    Returns:
        Serialized data as a string
    """
    if data is None:
        return "None"
    
    try:
        return json.dumps(data, indent=2)
    except (TypeError, ValueError):
        return str(data)


def parse_llm_response(response: str) -> Dict[str, Any]:
    """Parse LLM response into a structured format.
    
    Args:
        response: Raw response from the LLM
        
    Returns:
        Parsed response as a dictionary
    """
    # Try to parse as JSON first
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass
    
    # If not valid JSON, try to extract structured information
    result = {}
    current_section = None
    section_content = []
    
    for line in response.strip().split("\n"):
        line = line.strip()
        
        # Skip empty lines
        if not line:
            continue
        
        # Check if line is a section header
        if line.isupper() or (line.endswith(":") and ":" not in line[:-1]):
            # Save previous section if exists
            if current_section and section_content:
                result[current_section.lower().replace(":", "").strip()] = "\n".join(section_content).strip()
                section_content = []
            
            # Set new section
            current_section = line.replace(":", "").strip()
        else:
            # Add line to current section
            if current_section:
                section_content.append(line)
            else:
                # If no section yet, add to root content
                if "content" not in result:
                    result["content"] = []
                result["content"].append(line)
    
    # Save last section
    if current_section and section_content:
        result[current_section.lower().replace(":", "").strip()] = "\n".join(section_content).strip()
    
    # If we collected content lines without a section, join them
    if "content" in result and isinstance(result["content"], list):
        result["content"] = "\n".join(result["content"]).strip()
    
    return result


def extract_choices(text: str) -> List[Dict[str, Any]]:
    """Extract choices from text.
    
    Args:
        text: Text containing choices
        
    Returns:
        List of choice dictionaries
    """
    choices = []
    choice_markers = ["Option", "Choice", "*", "-", "•"]
    lines = text.split("\n")
    current_choice = None
    
    for line in lines:
        line = line.strip()
        
        # Skip empty lines
        if not line:
            continue
        
        # Check if line starts with a choice marker
        is_choice_line = False
        for marker in choice_markers:
            if line.startswith(marker):
                is_choice_line = True
                
                # Extract choice text and create new choice
                choice_text = line.split(":", 1)[1].strip() if ":" in line else line[len(marker):].strip()
                
                # Save previous choice if exists
                if current_choice:
                    choices.append(current_choice)
                
                # Create new choice
                current_choice = {
                    "choice_id": str(len(choices) + 1),
                    "text": choice_text,
                    "consequences": {}
                }
                break
        
        # If not a choice line and we have a current choice, add as consequence
        if not is_choice_line and current_choice and "(" in line and ")" in line:
            # Extract consequence from line with format "(consequenceType: detail)"
            consequence_part = line.split("(", 1)[1].split(")", 1)[0].strip()
            if ":" in consequence_part:
                cons_type, cons_detail = consequence_part.split(":", 1)
                current_choice["consequences"][cons_type.strip()] = cons_detail.strip()
    
    # Save last choice
    if current_choice:
        choices.append(current_choice)
    
    return choices 