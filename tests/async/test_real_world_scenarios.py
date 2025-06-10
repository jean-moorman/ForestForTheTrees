#!/usr/bin/env python3
"""
Test the real-world scenario that was failing with the exact error pattern.
"""

import asyncio
import sys
import logging
from unittest.mock import Mock, AsyncMock
from PyQt6.QtWidgets import QApplication
import qasync

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

# Import components
from resources.events.loop_management import EventLoopManager
from resources.events.qasync_utils import get_qasync_compatible_loop, qasync_wait_for


class RealWorldOrchestrator:
    """Mock orchestrator that reproduces the real failure conditions."""
    
    def __init__(self):
        self.step_count = 0
        
    async def start_phase_one(self, prompt: str) -> str:
        """Mock start_phase_one that returns the exact operation ID format."""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        operation_id = f"phase_one_{timestamp}_da8b7e86"
        logger.info(f"Started Phase One workflow with operation_id: {operation_id}")
        return operation_id
    
    async def get_step_status(self, operation_id: str):
        """Mock get_step_status that reproduces the real status."""
        logger.info(f"Step {self.step_count + 1}/6: ready - 0.0% complete")
        return {
            "current_step": "ready",
            "progress_percentage": 0.0
        }
    
    async def execute_next_step(self, operation_id: str):
        """Mock execute_next_step that simulates the real system's async behavior."""
        # This simulates a complex agent operation that might trigger the timeout issue
        logger.info(f"MockOrchestrator.execute_next_step called with: {operation_id}")
        
        # Simulate complex nested async operations like the real agents do
        async def simulate_agent_processing():
            # Simulate what real agents do - multiple async operations
            await asyncio.sleep(0.1)  # Network call simulation
            await asyncio.sleep(0.2)  # LLM processing simulation  
            await asyncio.sleep(0.1)  # Result processing simulation
            return {"agent_output": "processed_result"}
        
        # This is where the real system was failing - in the nested timeout
        result = await simulate_agent_processing()
        
        self.step_count += 1
        return {
            "status": "step_completed",
            "step_result": result
        }


async def test_real_world_prompt_processing():
    """Test the exact prompt processing pattern that was failing."""
    logger.info("=== Testing real-world prompt processing scenario ===")
    
    try:
        # Create the orchestrator
        orchestrator = RealWorldOrchestrator()
        
        # Simulate the exact _process_prompt_async logic from main_window.py
        prompt = "make a simple game"
        
        # Get loop using our robust method (line 289-291 in main_window.py)
        current_loop = get_qasync_compatible_loop()
        logger.info(f"Using event loop {id(current_loop)} for prompt processing")
        
        # Step 1: Start Phase One workflow (lines 287-289)
        operation_id = await orchestrator.start_phase_one(prompt)
        
        # Step 2: Execute steps with the same pattern as the real system (lines 292-329)
        step_results = {}
        total_steps = ["garden_planner", "earth_agent_validation", "environmental_analysis", 
                      "root_system_architect", "tree_placement_planner", "foundation_refinement"]
        
        for step_num in range(1):  # Just test first step to reproduce the error
            # Get current status (lines 297-299)
            status = await orchestrator.get_step_status(operation_id)
            
            # Execute next step - THIS IS WHERE THE REAL SYSTEM WAS FAILING (lines 301-320)
            try:
                # Use the consistent loop we already obtained (lines 315-317)
                step_coro = orchestrator.execute_next_step(operation_id)
                step_task = current_loop.create_task(step_coro)
                
                # Use qasync-compatible wait_for (line 320) - THIS WAS THE FAILURE POINT
                logger.info("About to call qasync_wait_for with 120.0s timeout...")
                step_result = await qasync_wait_for(step_task, timeout=120.0)
                logger.info("✅ qasync_wait_for completed successfully!")
                
                if step_result.get("status") == "error":
                    raise ValueError(f"Step failed: {step_result.get('message', 'Unknown error')}")
                
                # Store step result (lines 324-325)
                executed_step = step_result.get("step_executed", f"step_{step_num}")
                step_results[executed_step] = step_result.get("step_result", {})
                logger.info(f"✅ Step {step_num + 1} completed successfully")
                    
            except Exception as e:
                logger.error(f"❌ Step {step_num + 1} failed: {e}")
                raise
        
        # Format result (lines 330-340)
        result = {
            "status": "success",
            "operation_id": operation_id,
            "phase_one_outputs": step_results,
            "message": f"Phase One completed successfully via step-by-step execution",
            "steps_executed": list(step_results.keys())
        }
        
        logger.info("=== Real-world prompt processing completed successfully! ===")
        return result
        
    except Exception as e:
        logger.error(f"❌ Real-world prompt processing failed: {e}", exc_info=True)
        raise


def main():
    """Main function that reproduces the exact qasync environment."""
    app = QApplication.instance() or QApplication(sys.argv)
    
    # Create qasync loop exactly like run_phase_one.py
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    logger.info(f"Created qasync event loop: {id(loop)}")
    
    # Register with EventLoopManager exactly like run_phase_one.py
    result = EventLoopManager.set_primary_loop(loop)
    logger.info(f"Registered main event loop with EventLoopManager: {result}")
    
    # Run the test
    with loop:
        try:
            test_result = loop.run_until_complete(test_real_world_prompt_processing())
            logger.info(f"🎉 Real-world test passed! Result: {test_result}")
            return 0
        except Exception as e:
            logger.error(f"💥 Real-world test failed: {e}")
            return 1


if __name__ == "__main__":
    exit_code = main()
    logger.info(f"Test completed with exit code: {exit_code}")
    sys.exit(exit_code)