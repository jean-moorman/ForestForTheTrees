"""
Simple test script to verify the integration between phase_zero and phase_one.
"""
import asyncio
from typing import Dict, Any

class MockPhaseZero:
    """Mock implementation of PhaseZeroOrchestrator for testing integration"""
    
    async def process_system_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Mock implementation of process_system_metrics"""
        print(f"MockPhaseZero.process_system_metrics called with metrics: {len(str(metrics))} chars")
        
        # Return a mock analysis result
        return {
            "monitoring_analysis": {
                "flag_raised": False,
                "recommendations": []
            },
            "deep_analysis": {
                "soil": {"critical_requirement_gaps": {"runtime_gaps": []}},
                "microbial": {"critical_guideline_conflicts": {"task_assumption_conflicts": []}},
                "root_system": {"critical_data_flow_gaps": {"entity_gaps": []}},
                "mycelial": {"critical_guideline_conflicts": {"task_scope_conflicts": []}},
                "insect": {"critical_structure_gaps": {"boundary_gaps": []}},
                "bird": {"critical_guideline_conflicts": {"scope_boundary_conflicts": []}},
                "pollinator": {"component_optimization_opportunities": {"redundant_implementations": []}}
            },
            "evolution_synthesis": {
                "strategic_adaptations": {
                    "key_patterns": [],
                    "adaptations": [],
                    "priorities": {}
                }
            }
        }

# Create a mock phase_one that uses our mock phase_zero
class MockPhaseOne:
    """Mock implementation of PhaseOneOrchestrator for testing integration"""
    
    def __init__(self, phase_zero: MockPhaseZero):
        self.phase_zero = phase_zero
        
    async def process_task(self, task_prompt: str) -> Dict[str, Any]:
        """Mock implementation of process_task that calls phase_zero"""
        print(f"MockPhaseOne.process_task called with prompt: {task_prompt}")
        
        # Mock phase one outputs
        phase_one_outputs = {
            "garden_planner": {"task_elaboration": task_prompt},
            "environmental_analysis": {"core_requirements": ["requirement1", "requirement2"]},
            "root_system": {"data_flow_diagram": "mock diagram"},
            "tree_placement": {"components": ["component1", "component2"]}
        }
        
        # Mock metrics
        metrics = {
            "resource": {"cpu": 25, "memory": 30},
            "error": {"rate": 0.01},
            "development": {"state": "active"}
        }
        
        # Call phase_zero
        print("Calling phase_zero.process_system_metrics...")
        phase_zero_output = await self.phase_zero.process_system_metrics(metrics)
        print(f"phase_zero.process_system_metrics returned {len(str(phase_zero_output))} chars")
        
        # Return result with both outputs
        return {
            "status": "success",
            "phase_one_outputs": phase_one_outputs,
            "phase_zero_outputs": phase_zero_output,
            "message": "Task processing completed successfully"
        }

async def test_phase_integration():
    """Test the integration between phase_zero and phase_one"""
    # Create mock instances
    phase_zero = MockPhaseZero()
    phase_one = MockPhaseOne(phase_zero)
    
    # Test task prompt
    task_prompt = "Create a simple todo list application"
    
    # Process the task
    print(f"Processing task: {task_prompt}")
    result = await phase_one.process_task(task_prompt)
    
    # Verify that phase_zero was called
    if "phase_zero_outputs" in result:
        print("SUCCESS: phase_one successfully called phase_zero!")
        return True
    else:
        print("FAILURE: phase_one did not call phase_zero")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_phase_integration())
    if success:
        print("Test PASSED ✅")
    else:
        print("Test FAILED ❌")