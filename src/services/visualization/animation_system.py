"""Animation system for scene generation."""

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import logging

from ...models.visualization import Vector3, Color

logger = logging.getLogger(__name__)

class AnimationType(Enum):
    """Types of animations available in the system."""
    KEYFRAME = "keyframe"
    PROCEDURAL = "procedural"
    PHYSICS = "physics"
    PARTICLE = "particle"
    STATE = "state"
    SEQUENCE = "sequence"
    CHAIN = "chain"

@dataclass
class KeyframeData:
    """Data for keyframe animations."""
    time: float
    position: Optional[Vector3] = None
    rotation: Optional[Vector3] = None
    scale: Optional[Vector3] = None
    opacity: Optional[float] = None
    color: Optional[Color] = None
    easing: str = "linear"

@dataclass
class AnimationState:
    """State data for state-based animations."""
    name: str
    duration: float
    keyframes: List[KeyframeData]
    transitions: Dict[str, Dict[str, Any]]
    conditions: Optional[Dict[str, Any]] = None

@dataclass
class AnimationSequence:
    """Represents a sequence of animations that play in order."""
    name: str
    animations: List[Union[AnimationState, 'AnimationSequence']]
    loop: bool = False
    transition_time: float = 0.0
    events: Optional[Dict[str, Any]] = None

@dataclass
class AnimationChain:
    """Represents a chain of animations with dependencies."""
    name: str
    stages: List[Dict[str, Any]]  # Each stage has animations and conditions
    parallel: bool = False  # Whether stages can run in parallel if conditions met
    events: Optional[Dict[str, Any]] = None

class AnimationSystem:
    """System for managing complex animations."""
    
    def __init__(self) -> None:
        """Initialize the animation system."""
        self.sequences: Dict[str, AnimationSequence] = {}
        self.chains: Dict[str, AnimationChain] = {}
    
    def create_sequence(
        self,
        name: str,
        animations: List[Union[AnimationState, AnimationSequence]],
        loop: bool = False,
        transition_time: float = 0.0,
        events: Optional[Dict[str, Any]] = None
    ) -> AnimationSequence:
        """Create a new animation sequence.
        
        Args:
            name: Sequence name
            animations: List of animations in sequence
            loop: Whether to loop the sequence
            transition_time: Time between animations
            events: Event handlers for sequence
            
        Returns:
            AnimationSequence: Created sequence
        """
        sequence = AnimationSequence(
            name=name,
            animations=animations,
            loop=loop,
            transition_time=transition_time,
            events=events
        )
        self.sequences[name] = sequence
        return sequence
    
    def create_chain(
        self,
        name: str,
        stages: List[Dict[str, Any]],
        parallel: bool = False,
        events: Optional[Dict[str, Any]] = None
    ) -> AnimationChain:
        """Create a new animation chain.
        
        Args:
            name: Chain name
            stages: List of animation stages
            parallel: Whether stages can run in parallel
            events: Event handlers for chain
            
        Returns:
            AnimationChain: Created chain
        """
        chain = AnimationChain(
            name=name,
            stages=stages,
            parallel=parallel,
            events=events
        )
        self.chains[name] = chain
        return chain
    
    def get_sequence(self, name: str) -> Optional[AnimationSequence]:
        """Get an animation sequence by name.
        
        Args:
            name: Sequence name
            
        Returns:
            Optional[AnimationSequence]: Found sequence or None
        """
        return self.sequences.get(name)
    
    def get_chain(self, name: str) -> Optional[AnimationChain]:
        """Get an animation chain by name.
        
        Args:
            name: Chain name
            
        Returns:
            Optional[AnimationChain]: Found chain or None
        """
        return self.chains.get(name)
    
    def generate_threejs_code(
        self,
        animation: Union[AnimationSequence, AnimationChain],
        object_name: str
    ) -> str:
        """Generate Three.js animation code.
        
        Args:
            animation: Animation to generate code for
            object_name: Name of target object
            
        Returns:
            str: Generated Three.js code
        """
        if isinstance(animation, AnimationSequence):
            return self._generate_sequence_code(animation, object_name)
        else:
            return self._generate_chain_code(animation, object_name)
    
    def _generate_sequence_code(
        self,
        sequence: AnimationSequence,
        object_name: str
    ) -> str:
        """Generate code for an animation sequence.
        
        Args:
            sequence: Animation sequence
            object_name: Name of target object
            
        Returns:
            str: Generated Three.js code
        """
        code_parts = []
        total_time = 0.0
        
        # Create timeline
        code_parts.append(f"const {sequence.name}Timeline = gsap.timeline({{")
        if sequence.loop:
            code_parts.append("  repeat: -1,")
        code_parts.append("});")
        
        # Add animations to timeline
        for i, anim in enumerate(sequence.animations):
            if isinstance(anim, AnimationState):
                # Add state animation
                for keyframe in anim.keyframes:
                    props = {}
                    if keyframe.position:
                        props["x"] = keyframe.position.x
                        props["y"] = keyframe.position.y
                        props["z"] = keyframe.position.z
                    if keyframe.rotation:
                        props["rotationX"] = keyframe.rotation.x
                        props["rotationY"] = keyframe.rotation.y
                        props["rotationZ"] = keyframe.rotation.z
                    if keyframe.scale:
                        props["scaleX"] = keyframe.scale.x
                        props["scaleY"] = keyframe.scale.y
                        props["scaleZ"] = keyframe.scale.z
                    if keyframe.opacity is not None:
                        props["opacity"] = keyframe.opacity
                    
                    props_str = ", ".join(f'"{k}": {v}' for k, v in props.items())
                    code_parts.append(
                        f"{sequence.name}Timeline.to({object_name}, {{"
                        f"  duration: {keyframe.time},"
                        f"  {props_str},"
                        f"  ease: {keyframe.easing}"
                        f"}}, {total_time});"
                    )
                    total_time += keyframe.time
            else:
                # Add nested sequence
                nested_code = self._generate_sequence_code(anim, object_name)
                code_parts.append(nested_code)
                total_time += sum(
                    k.time for a in anim.animations
                    if isinstance(a, AnimationState)
                    for k in a.keyframes
                )
            
            # Add transition time between animations
            if i < len(sequence.animations) - 1:
                total_time += sequence.transition_time
        
        return "\n".join(code_parts)
    
    def _generate_chain_code(
        self,
        chain: AnimationChain,
        object_name: str
    ) -> str:
        """Generate code for an animation chain.
        
        Args:
            chain: Animation chain
            object_name: Name of target object
            
        Returns:
            str: Generated Three.js code
        """
        code_parts = []
        
        # Create chain controller
        code_parts.append(f"const {chain.name}Controller = {{")
        code_parts.append("  stages: [],")
        code_parts.append("  currentStage: 0,")
        code_parts.append("  parallel: " + str(chain.parallel).lower() + ",")
        code_parts.append("});")
        
        # Add stages
        for i, stage in enumerate(chain.stages):
            stage_name = f"{chain.name}_stage_{i}"
            
            # Create stage timeline
            code_parts.append(f"const {stage_name} = gsap.timeline({{")
            code_parts.append("  paused: true,")
            code_parts.append("});")
            
            # Add animations
            for anim in stage.get("animations", []):
                if isinstance(anim, str):
                    # Reference to existing sequence
                    sequence = self.get_sequence(anim)
                    if sequence:
                        code_parts.append(
                            self._generate_sequence_code(sequence, object_name)
                        )
                else:
                    # Inline animation state
                    state = AnimationState(**anim)
                    for keyframe in state.keyframes:
                        props = {}
                        if keyframe.position:
                            props["x"] = keyframe.position.x
                            props["y"] = keyframe.position.y
                            props["z"] = keyframe.position.z
                        if keyframe.rotation:
                            props["rotationX"] = keyframe.rotation.x
                            props["rotationY"] = keyframe.rotation.y
                            props["rotationZ"] = keyframe.rotation.z
                        if keyframe.scale:
                            props["scaleX"] = keyframe.scale.x
                            props["scaleY"] = keyframe.scale.y
                            props["scaleZ"] = keyframe.scale.z
                        if keyframe.opacity is not None:
                            props["opacity"] = keyframe.opacity
                        
                        props_str = ", ".join(f'"{k}": {v}' for k, v in props.items())
                        code_parts.append(
                            f"{stage_name}.to({object_name}, {{"
                            f"  duration: {keyframe.time},"
                            f"  {props_str},"
                            f"  ease: {keyframe.easing}"
                            f"}});"
                        )
            
            # Add stage to controller
            code_parts.append(f"{chain.name}Controller.stages.push({{")
            code_parts.append(f"  timeline: {stage_name},")
            
            # Add conditions
            if "conditions" in stage:
                conditions_str = ", ".join(
                    f'"{k}": {v}' for k, v in stage["conditions"].items()
                )
                code_parts.append(f"  conditions: {{{conditions_str}}},")
            
            code_parts.append("});")
        
        # Add chain control functions
        code_parts.append(f"function update{chain.name}Chain() {{")
        code_parts.append(f"  const controller = {chain.name}Controller;")
        code_parts.append("  const stage = controller.stages[controller.currentStage];")
        code_parts.append("  ")
        code_parts.append("  if (stage && checkConditions(stage.conditions)) {")
        code_parts.append("    stage.timeline.play();")
        code_parts.append("    if (!controller.parallel) {")
        code_parts.append("      controller.currentStage++;")
        code_parts.append("    }")
        code_parts.append("  }")
        code_parts.append("}")
        
        return "\n".join(code_parts) 