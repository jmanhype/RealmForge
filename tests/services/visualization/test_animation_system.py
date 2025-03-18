"""Tests for the animation system."""

from typing import Any, Dict, List, Optional
import pytest
from uuid import UUID

if True:  # TYPE_CHECKING
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture

from ...models.visualization import Vector3
from ..services.visualization.animation_system import (
    AnimationSystem,
    AnimationType,
    KeyframeData,
    AnimationState,
    AnimationSequence,
    AnimationChain
)

@pytest.fixture
def keyframe_data() -> List[KeyframeData]:
    """Create test keyframe data."""
    return [
        KeyframeData(
            time=0,
            position=Vector3(x=0, y=0, z=0),
            rotation=Vector3(x=0, y=0, z=0),
            scale=Vector3(x=1, y=1, z=1),
            opacity=1.0,
            color=0xffffff,
            easing="linear"
        ),
        KeyframeData(
            time=1,
            position=Vector3(x=1, y=2, z=3),
            rotation=Vector3(x=0, y=1.5708, z=0),
            scale=Vector3(x=2, y=2, z=2),
            opacity=0.5,
            color=0xff0000,
            easing="easeInOut"
        )
    ]

@pytest.fixture
def animation_state() -> AnimationState:
    """Create test animation state."""
    return AnimationState(
        name="test_state",
        duration=1.0,
        keyframes=[],
        transitions={
            "next_state": {
                "duration": 0.5,
                "easing": "linear"
            }
        },
        conditions={
            "is_active": True,
            "health": ">50"
        }
    )

@pytest.fixture
def animation_sequence() -> AnimationSequence:
    """Create test animation sequence."""
    return AnimationSequence(
        name="test_sequence",
        animations=[
            {
                "name": "first",
                "duration": 0.5,
                "keyframes": []
            },
            {
                "name": "second",
                "duration": 0.5,
                "keyframes": []
            }
        ],
        loop=False,
        transition_time=0.1,
        events={
            "onStart": "startEvent",
            "onComplete": "completeEvent"
        }
    )

@pytest.fixture
def animation_chain() -> AnimationChain:
    """Create test animation chain."""
    return AnimationChain(
        name="test_chain",
        stages=[
            {
                "name": "stage1",
                "animations": ["anim1", "anim2"],
                "conditions": {"trigger1": True}
            },
            {
                "name": "stage2",
                "animations": ["anim3"],
                "conditions": {"trigger2": True}
            }
        ],
        parallel=False,
        events={
            "onStageComplete": "stageEvent",
            "onChainComplete": "chainEvent"
        }
    )

class TestAnimationSystem:
    """Test suite for AnimationSystem class."""
    
    async def test_create_sequence(
        self,
        animation_sequence: AnimationSequence
    ) -> None:
        """Test creating an animation sequence."""
        system = AnimationSystem()
        
        # Create sequence
        system.create_sequence(
            name=animation_sequence.name,
            animations=animation_sequence.animations,
            loop=animation_sequence.loop,
            transition_time=animation_sequence.transition_time,
            events=animation_sequence.events
        )
        
        # Verify sequence creation
        sequence = system.get_sequence(animation_sequence.name)
        assert sequence is not None
        assert sequence.name == animation_sequence.name
        assert len(sequence.animations) == 2
        assert sequence.loop is False
        assert sequence.transition_time == 0.1
        assert sequence.events["onStart"] == "startEvent"
        assert sequence.events["onComplete"] == "completeEvent"
    
    async def test_create_chain(
        self,
        animation_chain: AnimationChain
    ) -> None:
        """Test creating an animation chain."""
        system = AnimationSystem()
        
        # Create chain
        system.create_chain(
            name=animation_chain.name,
            stages=animation_chain.stages,
            parallel=animation_chain.parallel,
            events=animation_chain.events
        )
        
        # Verify chain creation
        chain = system.get_chain(animation_chain.name)
        assert chain is not None
        assert chain.name == animation_chain.name
        assert len(chain.stages) == 2
        assert chain.parallel is False
        assert chain.events["onStageComplete"] == "stageEvent"
        assert chain.events["onChainComplete"] == "chainEvent"
    
    async def test_sequence_code_generation(
        self,
        animation_sequence: AnimationSequence,
        keyframe_data: List[KeyframeData]
    ) -> None:
        """Test generating Three.js code for sequences."""
        system = AnimationSystem()
        
        # Add keyframes to sequence animations
        animation_sequence.animations[0]["keyframes"] = keyframe_data
        animation_sequence.animations[1]["keyframes"] = keyframe_data
        
        # Create sequence
        system.create_sequence(
            name=animation_sequence.name,
            animations=animation_sequence.animations,
            loop=animation_sequence.loop,
            transition_time=animation_sequence.transition_time,
            events=animation_sequence.events
        )
        
        # Generate code
        code = system.generate_threejs_code(
            animation_type=AnimationType.SEQUENCE,
            name=animation_sequence.name,
            target_object="testObject"
        )
        
        # Verify code generation
        assert "const testObject_test_sequence" in code
        assert "AnimationMixer" in code
        assert "KeyframeTrack" in code
        assert "AnimationClip" in code
        assert "first" in code
        assert "second" in code
        assert "linear" in code
        assert "easeInOut" in code
    
    async def test_chain_code_generation(
        self,
        animation_chain: AnimationChain,
        keyframe_data: List[KeyframeData]
    ) -> None:
        """Test generating Three.js code for chains."""
        system = AnimationSystem()
        
        # Create animations for chain
        animations = {
            "anim1": {"duration": 0.5, "keyframes": keyframe_data},
            "anim2": {"duration": 0.5, "keyframes": keyframe_data},
            "anim3": {"duration": 0.5, "keyframes": keyframe_data}
        }
        
        # Create chain
        system.create_chain(
            name=animation_chain.name,
            stages=animation_chain.stages,
            parallel=animation_chain.parallel,
            events=animation_chain.events
        )
        
        # Generate code
        code = system.generate_threejs_code(
            animation_type=AnimationType.CHAIN,
            name=animation_chain.name,
            target_object="testObject",
            animations=animations
        )
        
        # Verify code generation
        assert "const testObject_test_chain" in code
        assert "AnimationMixer" in code
        assert "KeyframeTrack" in code
        assert "AnimationClip" in code
        assert "stage1" in code
        assert "stage2" in code
        assert "trigger1" in code
        assert "trigger2" in code
    
    async def test_parallel_chain_execution(
        self,
        animation_chain: AnimationChain,
        keyframe_data: List[KeyframeData]
    ) -> None:
        """Test parallel execution of chain animations."""
        system = AnimationSystem()
        
        # Enable parallel execution
        animation_chain.parallel = True
        
        # Create animations for chain
        animations = {
            "anim1": {"duration": 0.5, "keyframes": keyframe_data},
            "anim2": {"duration": 0.5, "keyframes": keyframe_data},
            "anim3": {"duration": 0.5, "keyframes": keyframe_data}
        }
        
        # Create chain
        system.create_chain(
            name=animation_chain.name,
            stages=animation_chain.stages,
            parallel=animation_chain.parallel,
            events=animation_chain.events
        )
        
        # Generate code
        code = system.generate_threejs_code(
            animation_type=AnimationType.CHAIN,
            name=animation_chain.name,
            target_object="testObject",
            animations=animations
        )
        
        # Verify parallel execution code
        assert "Promise.all" in code
        assert "playAnimationsInParallel" in code
    
    async def test_sequence_event_handling(
        self,
        animation_sequence: AnimationSequence
    ) -> None:
        """Test event handling in sequences."""
        system = AnimationSystem()
        
        # Create sequence
        system.create_sequence(
            name=animation_sequence.name,
            animations=animation_sequence.animations,
            loop=animation_sequence.loop,
            transition_time=animation_sequence.transition_time,
            events=animation_sequence.events
        )
        
        # Generate code
        code = system.generate_threejs_code(
            animation_type=AnimationType.SEQUENCE,
            name=animation_sequence.name,
            target_object="testObject"
        )
        
        # Verify event handling code
        assert "addEventListener" in code
        assert "startEvent" in code
        assert "completeEvent" in code
        assert "dispatchEvent" in code
    
    async def test_chain_event_handling(
        self,
        animation_chain: AnimationChain
    ) -> None:
        """Test event handling in chains."""
        system = AnimationSystem()
        
        # Create chain
        system.create_chain(
            name=animation_chain.name,
            stages=animation_chain.stages,
            parallel=animation_chain.parallel,
            events=animation_chain.events
        )
        
        # Generate code
        code = system.generate_threejs_code(
            animation_type=AnimationType.CHAIN,
            name=animation_chain.name,
            target_object="testObject"
        )
        
        # Verify event handling code
        assert "addEventListener" in code
        assert "stageEvent" in code
        assert "chainEvent" in code
        assert "dispatchEvent" in code
    
    async def test_error_handling(
        self,
        caplog: LogCaptureFixture
    ) -> None:
        """Test error handling in animation system."""
        system = AnimationSystem()
        
        # Test nonexistent sequence
        code = system.generate_threejs_code(
            animation_type=AnimationType.SEQUENCE,
            name="nonexistent",
            target_object="testObject"
        )
        
        # Verify error logging
        assert any("Animation sequence not found" in record.message
                  for record in caplog.records)
        assert code == ""  # Empty string returned on error
        
        # Test nonexistent chain
        code = system.generate_threejs_code(
            animation_type=AnimationType.CHAIN,
            name="nonexistent",
            target_object="testObject"
        )
        
        # Verify error logging
        assert any("Animation chain not found" in record.message
                  for record in caplog.records)
        assert code == ""  # Empty string returned on error 