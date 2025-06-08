"""
Hard integration tests for Water Agent coordination functionality.

These tests deliberately avoid mocks and test real coordination workflows
to expose actual system issues and validate genuine functionality.
"""

import pytest
import asyncio
import json
import uuid
from unittest.mock import patch, AsyncMock
from datetime import datetime

from resources.water_agent import WaterAgentCoordinator
from resources.water_agent.context_manager import WaterAgentContextManager
from resources.water_agent.reflective import WaterAgentReflective
from phase_one.validation.coordination import SequentialAgentCoordinator
from interfaces.agent.coordination import CoordinationInterface
from resources.state import StateManager
from resources.base_resource import BaseResource
from interfaces.agent.interface import AgentInterface


# No mock classes needed - we'll use real agents


class HardWaterAgentTests:
    """Hard integration tests that don't mock away complexity."""
    
    @pytest.fixture
    async def real_state_manager(self):
        """Create a real StateManager instance."""
        from resources.events import EventQueue
        from resources.state.models import StateManagerConfig
        
        event_queue = EventQueue()
        config = StateManagerConfig(persistence_type="memory")
        state_manager = StateManager(event_queue=event_queue, config=config)
        await state_manager.initialize()
        yield state_manager
        await state_manager.terminate()
    
    @pytest.fixture
    async def real_agent_infrastructure(self, real_state_manager):
        """Create the full agent infrastructure needed for real agents."""
        from resources import (
            EventQueue, AgentContextManager, CacheManager, 
            MetricsManager, ErrorHandler, MemoryMonitor
        )
        
        # Create shared event queue (reuse from state manager if possible)
        event_queue = EventQueue()
        
        # Create all the resource managers needed
        context_manager = AgentContextManager(event_queue, real_state_manager)
        cache_manager = CacheManager(event_queue, real_state_manager)
        metrics_manager = MetricsManager(event_queue, real_state_manager)
        error_handler = ErrorHandler(event_queue)
        memory_monitor = MemoryMonitor(event_queue)
        
        # Initialize managers that have initialize methods
        await context_manager.initialize()
        await cache_manager.initialize()
        await metrics_manager.initialize()
        # ErrorHandler doesn't have initialize method - it's ready after construction
        await memory_monitor.start()  # MemoryMonitor has start, not initialize
        
        infrastructure = {
            'event_queue': event_queue,
            'state_manager': real_state_manager,
            'context_manager': context_manager,
            'cache_manager': cache_manager,
            'metrics_manager': metrics_manager,
            'error_handler': error_handler,
            'memory_monitor': memory_monitor
        }
        
        yield infrastructure
        
        # Cleanup managers that have terminate methods
        await context_manager.terminate()
        await cache_manager.terminate()
        await metrics_manager.terminate()
        # ErrorHandler doesn't have terminate method
        await memory_monitor.stop()  # MemoryMonitor has stop, not terminate

    @pytest.fixture
    async def real_water_agent_coordinator(self, real_state_manager):
        """Create a real WaterAgentCoordinator."""
        coordinator = WaterAgentCoordinator(
            state_manager=real_state_manager,
            resource_id="test_water_coordinator"
        )
        
        yield coordinator
        await coordinator.terminate()
    
    @pytest.fixture
    async def test_agents(self, real_agent_infrastructure):
        """Create test agents using real AgentInterface instances."""
        infrastructure = real_agent_infrastructure
        
        # Create real AgentInterface instances
        first_agent_interface = AgentInterface(
            agent_id="first_agent",
            **infrastructure
        )
        
        second_agent_interface = AgentInterface(
            agent_id="second_agent", 
            **infrastructure
        )
        
        # Initialize the interfaces using ensure_initialized
        await first_agent_interface.ensure_initialized()
        await second_agent_interface.ensure_initialized()
        
        yield first_agent_interface, second_agent_interface
        
        # Cleanup using cleanup method
        await first_agent_interface.cleanup()
        await second_agent_interface.cleanup()


@pytest.mark.asyncio
class TestRealWaterAgentCoordination(HardWaterAgentTests):
    """Test actual coordination workflows without hiding complexity."""
    
    async def test_full_coordination_workflow_no_misunderstandings(
        self, 
        real_water_agent_coordinator,
        test_agents
    ):
        """Test complete coordination workflow when no misunderstandings are detected."""
        first_agent, second_agent = test_agents
        
        first_output = "The system should implement caching for frequently accessed data"
        second_output = "I will add Redis caching to improve performance for repeated queries"
        
        # Run real coordination using the actual coordination interface
        try:
            result = await real_water_agent_coordinator.coordinate_agents(
                first_agent=first_agent,
                first_agent_output=first_output,
                second_agent=second_agent,
                second_agent_output=second_output,
                coordination_context={"coordination_id": "test_coordination_1"}
            )
            
            # Verify we get real results
            assert result is not None
            assert len(result) >= 3  # Should return tuple with outputs and metadata
            
            refined_first, refined_second, metadata = result
            assert isinstance(refined_first, str)
            assert isinstance(refined_second, str) 
            assert isinstance(metadata, dict)
            
        except Exception as e:
            pytest.fail(f"Real coordination workflow failed: {e}")
    
    async def test_coordination_with_actual_misunderstandings(
        self,
        real_water_agent_coordinator, 
        test_agents
    ):
        """Test coordination when misunderstandings are actually detected."""
        first_agent, second_agent = test_agents
        
        # Use conflicting outputs that should trigger misunderstanding detection
        
        first_output = "Use in-memory caching"
        second_output = "Implement persistent storage"
        
        try:
            result = await real_water_agent_coordinator.coordinate_agents(
                first_agent=first_agent,
                first_agent_output=first_output,
                second_agent=second_agent,
                second_agent_output=second_output,
                coordination_context={"coordination_id": "test_coordination_2"}
            )
            
            # Verify coordination attempted to resolve misunderstandings
            assert result is not None
            refined_first, refined_second, metadata = result
            
            # Should have coordination metadata
            assert "coordination_iterations" in metadata or "status" in metadata
            
        except Exception as e:
            pytest.fail(f"Coordination with misunderstandings failed: {e}")
    
    async def test_resource_initialization_stress(self, real_state_manager):
        """Test that resource initialization handles real complexity."""
        coordinators = []
        
        try:
            # Create multiple coordinators simultaneously to test resource management
            for i in range(3):
                coordinator = WaterAgentCoordinator(
                    state_manager=real_state_manager,
                    resource_id=f"stress_test_coordinator_{i}"
                )
                # Let the coordinator create its own agent interface through proper infrastructure
                coordinators.append(coordinator)
            
            # Try to initialize them concurrently
            init_tasks = [coord.initialize() for coord in coordinators]
            await asyncio.gather(*init_tasks, return_exceptions=True)
            
            # Verify they're all working
            for coord in coordinators:
                assert coord.resource_id is not None
                
        except Exception as e:
            pytest.fail(f"Resource initialization stress test failed: {e}")
        finally:
            # Cleanup
            cleanup_tasks = [coord.cleanup() for coord in coordinators]
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)
    
    async def test_context_persistence_across_operations(
        self,
        real_water_agent_coordinator,
        test_agents
    ):
        """Test that coordination context properly persists across operations."""
        first_agent, second_agent = test_agents
        operation_id = f"persistence_test_{uuid.uuid4()}"
        
        # First coordination
        result1 = await real_water_agent_coordinator.coordinate_agents(
            first_agent=first_agent,
            second_agent=second_agent,
            first_agent_output="First operation output",
            second_agent_output="Second operation output", 
            operation_id=operation_id
        )
        
        # Verify context was created and persisted
        context_manager = real_water_agent_coordinator.context_manager
        context = await context_manager.get_coordination_context(operation_id)
        
        if context is None:
            pytest.fail("Coordination context was not persisted")
        
        assert context.first_agent_id == first_agent.agent_id
        assert context.second_agent_id == second_agent.agent_id


@pytest.mark.asyncio  
class TestSequentialAgentCoordinatorReal(HardWaterAgentTests):
    """Test SequentialAgentCoordinator with real Water Agent integration."""
    
    async def test_real_sequential_coordination(self, real_state_manager, test_agents):
        """Test sequential coordination using real components."""
        first_agent, second_agent = test_agents
        
        # Create real sequential coordinator
        seq_coordinator = SequentialAgentCoordinator(
            state_manager=real_state_manager,
            resource_id="real_seq_coordinator"
        )
        
        try:
            await seq_coordinator.initialize()
            
            # Test real coordination handoff
            result = await seq_coordinator.coordinate_agent_handoff(
                first_agent=first_agent,
                second_agent=second_agent,
                first_agent_output="Real output from first agent",
                operation_id="real_sequential_test"
            )
            
            # Verify real coordination occurred
            assert result is not None
            assert len(result) >= 2  # Should return updated outputs
            
        except Exception as e:
            pytest.fail(f"Real sequential coordination failed: {e}")
        finally:
            await seq_coordinator.cleanup()


@pytest.mark.asyncio
class TestWaterAgentReflectiveReal(HardWaterAgentTests):
    """Test WaterAgentReflective without mocking away the complexity."""
    
    async def test_reflective_agent_initialization(self, real_state_manager):
        """Test that WaterAgentReflective can actually be initialized."""
        try:
            # Attempt real initialization with all dependencies
            reflective_agent = WaterAgentReflective(
                agent_id="test_reflective_agent",
                state_manager=real_state_manager,
                # Note: This will likely fail and expose real initialization issues
            )
            
            await reflective_agent.initialize()
            
            # If we get here, the initialization actually worked
            assert reflective_agent.agent_id == "test_reflective_agent"
            
        except Exception as e:
            # Expected to fail - this exposes real initialization issues
            pytest.fail(
                f"WaterAgentReflective initialization failed (expected): {e}\n"
                "This reveals real architectural issues that need fixing."
            )
    
    async def test_detect_misunderstandings_with_reflection(self, real_state_manager):
        """Test misunderstanding detection with real reflection enabled."""
        # This test will expose the real async/resource issues without hiding them behind mocks
        
        try:
            reflective_agent = WaterAgentReflective(
                agent_id="reflection_detector",
                state_manager=real_state_manager,
            )
            
            result = await reflective_agent.detect_misunderstandings(
                first_agent_output="Complex output 1",
                second_agent_output="Complex output 2", 
                use_reflection=True
            )
            
            # Verify reflection actually occurred
            assert "misunderstandings" in result
            
        except Exception as e:
            pytest.fail(
                f"Reflective misunderstanding detection failed: {e}\n"
                "This exposes real issues with the reflection system."
            )


@pytest.mark.asyncio
class TestPromptTemplateIntegration:
    """Test that prompt templates work with real JSON data."""
    
    async def test_resolution_assessment_prompt_formatting(self):
        """Test the RESOLUTION_ASSESSMENT_PROMPT with real data to expose formatting issues."""
        from FFTT_system_prompts.core_agents.water_agent import RESOLUTION_ASSESSMENT_PROMPT
        
        # Real misunderstandings data that would come from the system
        misunderstandings = [
            {
                "id": "real_misunderstanding_1",
                "description": "Agents have different approaches to data validation", 
                "severity": "HIGH",
                "affected_elements": ["validation_logic", "error_handling"]
            }
        ]
        
        # Real Q&A data
        first_agent_qa = "Q1: How do you handle validation?\nA1: I use schema validation"
        second_agent_qa = "Q1: What about error cases?\nA1: I throw exceptions"
        
        try:
            # This should expose the real formatting issues
            formatted_prompt = RESOLUTION_ASSESSMENT_PROMPT.format(
                misunderstandings=json.dumps(misunderstandings, indent=2),
                first_agent_questions_and_responses=first_agent_qa,
                second_agent_questions_and_responses=second_agent_qa,
                current_iteration=1
            )
            
            # If we get here, formatting actually works
            assert "real_misunderstanding_1" in formatted_prompt
            assert "validation_logic" in formatted_prompt
            
        except KeyError as e:
            pytest.fail(
                f"Prompt formatting failed with real data (expected): {e}\n"
                "This exposes the real JSON formatting conflicts in prompt templates."
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])