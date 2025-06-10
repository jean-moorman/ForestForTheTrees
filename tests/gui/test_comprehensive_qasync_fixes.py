#!/usr/bin/env python3
"""
Comprehensive test to validate the qasync event loop fix.
Tests the complete chain: GUI signal -> main_window -> orchestrator -> agents
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

# Import our fixes
from resources.events.loop_management import EventLoopManager
from resources.events.qasync_utils import get_qasync_compatible_loop, qasync_wait_for


class MockOrchestrator:
    """Mock orchestrator that simulates the real system's behavior."""
    
    def __init__(self):
        self.step_counter = 0
        
    async def start_phase_one(self, prompt: str) -> str:
        """Mock start_phase_one."""
        logger.info(f"MockOrchestrator.start_phase_one called with: {prompt}")
        # Test loop detection here
        loop = get_qasync_compatible_loop()
        logger.info(f"MockOrchestrator using loop: {id(loop)}")
        await asyncio.sleep(0.1)  # Simulate work
        return "test_operation_123"
    
    async def get_step_status(self, operation_id: str):
        """Mock get_step_status."""
        logger.info(f"MockOrchestrator.get_step_status called with: {operation_id}")
        # Test loop detection here
        loop = get_qasync_compatible_loop()
        logger.info(f"MockOrchestrator.get_step_status using loop: {id(loop)}")
        await asyncio.sleep(0.05)  # Simulate work
        return {
            "current_step": f"step_{self.step_counter}",
            "progress_percentage": self.step_counter * 20
        }
    
    async def execute_next_step(self, operation_id: str):
        """Mock execute_next_step - this is where the real failure occurs."""
        logger.info(f"MockOrchestrator.execute_next_step called with: {operation_id}")
        
        # This is the critical test - can we detect the loop during nested execution?
        try:
            # Test 1: Direct asyncio.get_running_loop()
            direct_loop = asyncio.get_running_loop()
            logger.info(f"✅ Direct asyncio.get_running_loop() works: {id(direct_loop)}")
        except RuntimeError as e:
            logger.error(f"❌ Direct asyncio.get_running_loop() failed: {e}")
        
        # Test 2: Our robust method
        robust_loop = get_qasync_compatible_loop()
        logger.info(f"✅ Robust get_qasync_compatible_loop() works: {id(robust_loop)}")
        
        # Test 3: Nested task creation (what actually fails in production)
        async def nested_operation():
            # This simulates what agent.process() does internally
            nested_loop = get_qasync_compatible_loop()
            logger.info(f"Nested operation using loop: {id(nested_loop)}")
            await asyncio.sleep(0.1)
            return {"agent_output": f"step_{self.step_counter}_result"}
        
        # Test 4: Using our qasync_wait_for (the fix)
        try:
            result = await qasync_wait_for(nested_operation(), timeout=5.0)
            logger.info(f"✅ qasync_wait_for succeeded: {result}")
        except Exception as e:
            logger.error(f"❌ qasync_wait_for failed: {e}")
            raise
        
        self.step_counter += 1
        
        if self.step_counter >= 3:
            return {"status": "completed", "step_result": result}
        else:
            return {"status": "step_completed", "step_result": result}


class TestMainWindow:
    """Simplified version of main_window that tests the critical path."""
    
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
    
    async def process_prompt_async(self, prompt: str):
        """Simplified version of _process_prompt_async that tests the critical path."""
        logger.info(f"=== TestMainWindow.process_prompt_async: {prompt} ===")
        
        # This mirrors the exact pattern in main_window.py
        from resources.events.qasync_utils import get_qasync_compatible_loop, qasync_wait_for
        current_loop = get_qasync_compatible_loop()
        logger.info(f"Using event loop {id(current_loop)} for prompt processing")
        
        try:
            # Step 1: Start Phase One workflow
            operation_id = await self.orchestrator.start_phase_one(prompt)
            logger.info(f"Started Phase One workflow with operation_id: {operation_id}")
            
            # Step 2: Execute steps with the same pattern as the real system
            step_results = {}
            total_steps = ["step_1", "step_2", "step_3"]
            
            for step_num in range(len(total_steps)):
                # Get current status
                status = await self.orchestrator.get_step_status(operation_id)
                logger.info(f"Step {step_num + 1}/{len(total_steps)}: {status.get('current_step', 'unknown')} - {status.get('progress_percentage', 0):.1f}% complete")
                
                # Execute next step - THIS IS WHERE THE REAL SYSTEM FAILS
                try:
                    # Use the consistent loop we already obtained (same as fixed main_window.py)
                    step_coro = self.orchestrator.execute_next_step(operation_id)
                    step_task = current_loop.create_task(step_coro)
                    
                    # Use qasync-compatible wait_for (the fix)
                    step_result = await qasync_wait_for(step_task, timeout=10.0)
                    
                    if step_result.get("status") == "error":
                        raise ValueError(f"Step failed: {step_result.get('message', 'Unknown error')}")
                    
                    if step_result.get("status") == "completed":
                        logger.info("✅ Workflow completed successfully!")
                        break
                    
                    # Store step result
                    step_results[f"step_{step_num + 1}"] = step_result.get("step_result", {})
                    logger.info(f"✅ Step {step_num + 1} completed successfully")
                        
                except Exception as e:
                    logger.error(f"❌ Step {step_num + 1} failed: {e}")
                    raise
            
            logger.info("=== Prompt processing completed successfully! ===")
            return {
                "status": "success",
                "operation_id": operation_id,
                "phase_one_outputs": step_results,
                "message": "Phase One completed successfully"
            }
            
        except Exception as e:
            logger.error(f"❌ Prompt processing failed: {e}")
            raise


async def test_qasync_compatibility():
    """Test the complete qasync compatibility fix."""
    logger.info("=== Starting comprehensive qasync compatibility test ===")
    
    # Create mock orchestrator
    orchestrator = MockOrchestrator()
    
    # Create test main window
    main_window = TestMainWindow(orchestrator)
    
    # Test the critical path
    try:
        result = await main_window.process_prompt_async("test prompt")
        logger.info(f"✅ Test completed successfully: {result}")
        return True
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False


def main():
    """Main function that sets up qasync environment and runs the test."""
    app = QApplication.instance() or QApplication(sys.argv)
    
    # Create qasync loop (same as run_phase_one.py)
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    logger.info(f"Created qasync event loop: {id(loop)}")
    
    # Register with EventLoopManager (same as run_phase_one.py)
    result = EventLoopManager.set_primary_loop(loop)
    logger.info(f"Registered main event loop with EventLoopManager: {result}")
    
    # Run the test
    with loop:
        try:
            test_result = loop.run_until_complete(test_qasync_compatibility())
            if test_result:
                logger.info("🎉 All tests passed! The qasync fix is working correctly.")
                return 0
            else:
                logger.error("💥 Tests failed! The qasync fix needs more work.")
                return 1
        except Exception as e:
            logger.error(f"💥 Test execution failed: {e}")
            return 1


if __name__ == "__main__":
    sys.exit(main())