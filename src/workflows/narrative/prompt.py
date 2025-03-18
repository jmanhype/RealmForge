"""Prompts for the narrative generation workflow."""

NARRATIVE_ANALYSIS_PROMPT = """
Analyze the following player context and choices to generate a cohesive narrative element.

PLAYER CONTEXT:
{player_context}

RECENT PLAYER CHOICE:
{player_choice}

NARRATIVE TYPE:
{narrative_type}

TASK:
Carefully analyze the player's context, history, and recent choices. Consider their character, past decisions, relationships, and the current game state.

Your analysis should include:
1. Key themes from the player's history
2. Important relationships and how they've evolved
3. Narrative threads that can be continued or developed
4. Potential consequences of the player's recent choices
5. Opportunities for character development

Provide a detailed analysis that will serve as the foundation for generating a compelling narrative element.
"""

NARRATIVE_GENERATION_PROMPT = """
Based on the player context and analysis, generate a compelling narrative element.

PLAYER CONTEXT:
{player_context}

NARRATIVE ANALYSIS:
{narrative_analysis}

NARRATIVE TYPE:
{narrative_type}

TASK:
Create a narrative element that feels like a natural progression of the player's story. The narrative should be:

1. Consistent with the player's previous choices and character development
2. Emotionally engaging and meaningful
3. Offering interesting choices with consequences
4. Tailored to the player's apparent preferences and play style
5. Appropriate for the current game state and location

Generate a detailed narrative element that includes:
- Main narrative text (what happens)
- Key NPCs involved
- Emotional tone and themes
- Player choices that make sense in this context (at least 3 distinct options)
- Potential consequences for each choice (hidden from player)

Be creative while maintaining consistency with the established world and character.
"""

NARRATIVE_REVIEW_PROMPT = """
Review the following narrative element for quality, coherence, and consistency.

PLAYER CONTEXT:
{player_context}

GENERATED NARRATIVE:
{generated_narrative}

TASK:
Evaluate the narrative element on the following criteria:

1. Consistency: Does it align with the player's history, character, and world state?
2. Engagement: Is it emotionally engaging and interesting?
3. Choice Quality: Do the player choices feel meaningful and distinct?
4. Consequences: Are the potential consequences logical and varied?
5. Personalization: Is it well-tailored to this specific player?

Provide specific feedback on strengths and weaknesses, with clear suggestions for improvement if needed.
"""

NARRATIVE_REVISION_PROMPT = """
Revise the narrative element based on the review feedback.

ORIGINAL NARRATIVE:
{original_narrative}

REVIEW FEEDBACK:
{review_feedback}

TASK:
Improve the narrative element by addressing the feedback. Focus on:

1. Fixing any inconsistencies with player history or world state
2. Enhancing emotional engagement and interest
3. Improving the quality and distinctiveness of player choices
4. Refining consequences to be more logical and varied
5. Better tailoring the narrative to this specific player

Provide the revised narrative element while maintaining the original structure.
"""

NARRATIVE_FORMAT_PROMPT = """
Format the narrative element for integration with the game engine.

NARRATIVE ELEMENT:
{narrative_element}

TASK:
Format the narrative element into a structured JSON-compatible format that includes:

1. Main narrative text divided into appropriate segments
2. Character dialogue clearly attributed to speakers
3. Player choices formatted as selectable options
4. Relevant metadata for the game engine (emotional tone, themes, etc.)
5. Any special presentation instructions (music cues, visual effects, etc.)

Ensure the formatting is consistent with the structure required by the response models.
""" 