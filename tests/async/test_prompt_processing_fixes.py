#!/usr/bin/env python3
"""
Test the end-to-end prompt processing fix.
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
from phase_one.runners.gui.app import PhaseOneApp
from display.core.main_window import ForestDisplay


class MockOrchestrator:
    """Mock orchestrator with realistic async operations."""
    
    def __init__(self):
        self.step_count = 0
    
    async def start_phase_one(self, prompt: str) -> str:
        """Mock start_phase_one."""
        logger.info(f"MockOrchestrator.start_phase_one: {prompt}")
        await asyncio.sleep(0.1)  # Simulate work
        return "test_operation_456"
    
    async def get_step_status(self, operation_id: str):
        """Mock get_step_status."""
        logger.info(f"MockOrchestrator.get_step_status: {operation_id}")
        await asyncio.sleep(0.05)  # Simulate work
        return {
            "current_step": f"step_{self.step_count}",
            "progress_percentage": self.step_count * 25
        }
    
    async def execute_next_step(self, operation_id: str):
        """Mock execute_next_step with realistic behavior."""
        logger.info(f"MockOrchestrator.execute_next_step: {operation_id}")
        
        # Simulate the complex async operations that happen in real agents
        await asyncio.sleep(0.2)
        
        self.step_count += 1
        
        if self.step_count >= 4:
            return {
                "status": "completed",
                "step_result": {"final_output": "test_completed"}
            }
        else:
            return {
                "status": "step_completed", 
                "step_result": {"step_output": f"step_{self.step_count}_done"}
            }
    
    async def get_agent_metrics(self, agent_id: str):
        """Mock get_agent_metrics."""
        await asyncio.sleep(0.05)
        return {"agent_id": agent_id, "status": "active"}


async def test_prompt_processing():
    """Test the full prompt processing chain with our fixes."""
    logger.info("=== Testing end-to-end prompt processing ===")
    
    try:
        # Create PhaseOneApp
        logger.info("Creating PhaseOneApp...")
        app = PhaseOneApp()
        await app.setup_async()
        logger.info("✅ PhaseOneApp setup completed")
        
        # Replace orchestrator with mock to avoid complexity
        mock_orchestrator = MockOrchestrator()
        
        # Create main window with mock orchestrator
        logger.info("Creating ForestDisplay with mock orchestrator...")
        main_window = ForestDisplay(
            app.event_queue, 
            mock_orchestrator, 
            app.system_monitor
        )
        logger.info("✅ ForestDisplay created")
        
        # Test the prompt processing method directly
        logger.info("Testing prompt processing...")
        result = await main_window._process_prompt_async("test prompt for qasync fix")
        logger.info(f"✅ Prompt processing completed: {result}")
        
        # Verify the result structure
        if isinstance(result, dict) and result.get("status") == "success":
            logger.info("✅ Prompt processing returned expected success result")
            return True
        else:
            logger.error(f"❌ Prompt processing returned unexpected result: {result}")
            return False
        
    except Exception as e:
        logger.error(f"❌ Prompt processing test failed: {e}", exc_info=True)
        return False


def main():
    """Main function."""
    try:
        # Create Qt application
        app = QApplication.instance() or QApplication(sys.argv)
        logger.info("QApplication created")
        
        # Create qasync loop
        loop = qasync.QEventLoop(app)
        asyncio.set_event_loop(loop)
        logger.info(f"Created qasync event loop: {id(loop)}")
        
        # Register with EventLoopManager
        result = EventLoopManager.set_primary_loop(loop)
        logger.info(f"Registered main event loop with EventLoopManager: {result}")
        
        # Run the test
        logger.info("Starting prompt processing test...")
        
        with loop:
            try:
                test_result = loop.run_until_complete(
                    asyncio.wait_for(test_prompt_processing(), timeout=30.0)
                )
                
                if test_result:
                    logger.info("🎉 End-to-end prompt processing test passed!")
                    return 0
                else:
                    logger.error("💥 End-to-end prompt processing test failed!")
                    return 1
                    
            except asyncio.TimeoutError:
                logger.error("💥 Test timed out - prompt processing is hanging")
                return 1
            except Exception as e:
                logger.error(f"💥 Test execution failed: {e}", exc_info=True)
                return 1
        
    except Exception as e:
        logger.error(f"Setup error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = main()
    logger.info(f"Test completed with exit code: {exit_code}")
    sys.exit(exit_code)