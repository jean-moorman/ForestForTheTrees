#!/usr/bin/env python3
"""
Test the full GUI scenario to verify the qasync_wait_for fix.
"""

import asyncio
import sys
import logging
import time
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from PyQt6.QtCore import QTimer, pyqtSignal
import qasync
from qasync import asyncSlot

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

# Import components
from resources.events.loop_management import EventLoopManager
from resources.events.qasync_utils import get_qasync_compatible_loop, qasync_wait_for


class MockOrchestrator:
    """Mock orchestrator that reproduces realistic behavior."""
    
    def __init__(self):
        self.step_count = 0
        
    async def start_phase_one(self, prompt: str) -> str:
        """Mock start_phase_one."""
        operation_id = f"phase_one_test_{int(time.time())}"
        logger.info(f"Started Phase One workflow with operation_id: {operation_id}")
        return operation_id
    
    async def get_step_status(self, operation_id: str):
        """Mock get_step_status."""
        logger.info(f"Step {self.step_count + 1}/6: ready - {self.step_count * 20:.1f}% complete")
        return {
            "current_step": "ready" if self.step_count == 0 else f"step_{self.step_count}",
            "progress_percentage": self.step_count * 20.0
        }
    
    async def execute_next_step(self, operation_id: str):
        """Mock execute_next_step."""
        logger.info(f"Executing step {self.step_count + 1}...")
        
        # Simulate agent processing with realistic delays using qasync-compatible sleep
        from resources.events.qasync_utils import qasync_sleep
        await qasync_sleep(0.5)  # Simulate real agent work
        
        self.step_count += 1
        
        if self.step_count >= 3:  # Complete after 3 steps
            return {
                "status": "completed",
                "step_result": {"final": "completed"}
            }
        else:
            return {
                "status": "step_completed",
                "step_result": {"step": f"step_{self.step_count}_done"}
            }


class TestMainWindow(QMainWindow):
    """Test main window that reproduces the failing scenario."""
    
    error_signal = pyqtSignal(str, dict)
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test qasync_wait_for Fix")
        self.setGeometry(100, 100, 500, 300)
        
        # Create orchestrator
        self.orchestrator = MockOrchestrator()
        
        # Create UI
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        self.button = QPushButton("Test Prompt Processing (This was failing!)")
        self.button.clicked.connect(self._handle_prompt_submission)
        layout.addWidget(self.button)
        
        self.status_label = QPushButton("Status: Ready")
        self.status_label.setEnabled(False)
        layout.addWidget(self.status_label)
        
        # Connect error signal
        self.error_signal.connect(self._handle_error)
        
        # Auto-close timer
        self.close_timer = QTimer()
        self.close_timer.timeout.connect(self._auto_close)
        self.close_timer.setSingleShot(True)
        self.close_timer.start(15000)  # Close after 15 seconds
        
        logger.info("TestMainWindow initialized")
    
    def _handle_prompt_submission(self):
        """Handle prompt submission - reproduces the failing pattern."""
        try:
            logger.info("=== Button clicked - starting prompt processing ===")
            self.button.setEnabled(False)
            self.status_label.setText("Status: Processing...")
            
            # Get loop using the same pattern as main_window.py
            from resources.events.qasync_utils import get_qasync_compatible_loop
            loop = get_qasync_compatible_loop()
            
            if loop and not loop.is_closed():
                # Create task in the qasync loop context (same as main_window.py line 194)
                task = loop.create_task(self._process_prompt_async("test prompt"))
                task.add_done_callback(self._handle_prompt_task_done)
                logger.info(f"Created prompt processing task in qasync loop {id(loop)}")
            else:
                raise RuntimeError("No event loop available")
            
        except Exception as e:
            logger.error(f"Failed to submit prompt: {e}", exc_info=True)
            self.error_signal.emit(f"Failed to submit prompt: {e}", {'error': str(e)})
            self._reset_ui()
    
    async def _process_prompt_async(self, prompt: str):
        """Reproduce the exact _process_prompt_async logic that was failing."""
        logger.info(f"=== _process_prompt_async started: {prompt} ===")
        
        # Get loop using robust method (main_window.py lines 289-291)
        current_loop = get_qasync_compatible_loop()
        logger.info(f"Using event loop {id(current_loop)} for prompt processing")
        
        try:
            if not prompt.strip():
                raise ValueError("Empty prompt submitted")
                
            # Start Phase One workflow (lines 287-289)
            operation_id = await self.orchestrator.start_phase_one(prompt)
            
            # Track progress and execute steps (lines 292-329)
            step_results = {}
            total_steps = ["step_1", "step_2", "step_3"]
            
            for step_num in range(len(total_steps)):
                # Get current status (lines 297-299)
                status = await self.orchestrator.get_step_status(operation_id)
                
                # Execute next step - THE CRITICAL FAILING POINT (lines 301-320)
                try:
                    # Use the consistent loop we already obtained (lines 315-317)
                    step_coro = self.orchestrator.execute_next_step(operation_id)
                    step_task = current_loop.create_task(step_coro)
                    
                    # Use qasync-compatible wait_for (line 320) - THIS WAS FAILING BEFORE
                    logger.info(f"About to call qasync_wait_for for step {step_num + 1}...")
                    step_result = await qasync_wait_for(step_task, timeout=10.0)  # Shorter timeout for testing
                    logger.info(f"✅ Step {step_num + 1} qasync_wait_for completed!")
                    
                    if step_result.get("status") == "error":
                        raise ValueError(f"Step failed: {step_result.get('message', 'Unknown error')}")
                    
                    if step_result.get("status") == "completed":
                        logger.info("✅ Workflow completed successfully!")
                        break
                    
                    # Store step result
                    step_results[f"step_{step_num + 1}"] = step_result.get("step_result", {})
                        
                except Exception as e:
                    logger.error(f"❌ Step {step_num + 1} failed: {e}")
                    raise
            
            # Format result (lines 330-340)
            result = {
                "status": "success",
                "operation_id": operation_id,
                "phase_one_outputs": step_results,
                "message": "Phase One completed successfully",
                "steps_executed": list(step_results.keys())
            }
            
            logger.info("=== Prompt processing completed successfully! ===")
            return result
            
        except Exception as e:
            logger.error(f"❌ Prompt processing failed: {e}", exc_info=True)
            raise
    
    def _handle_prompt_task_done(self, task):
        """Handle prompt task completion."""
        try:
            if task.exception():
                error = task.exception()
                logger.error(f"❌ Prompt processing task failed: {error}")
                self.error_signal.emit(f"Processing failed: {error}", {'error': str(error)})
            else:
                result = task.result()
                logger.info(f"✅ Prompt processing completed: {result}")
                self.status_label.setText("Status: ✅ SUCCESS! qasync_wait_for fix works!")
        except Exception as e:
            logger.error(f"Error handling task completion: {e}")
        finally:
            self._reset_ui()
    
    def _handle_error(self, message: str, data: dict):
        """Handle error signal."""
        logger.error(f"GUI Error: {message}")
        self.status_label.setText(f"Status: ❌ ERROR - {message}")
        self._reset_ui()
    
    def _reset_ui(self):
        """Reset UI state."""
        self.button.setEnabled(True)
    
    def _auto_close(self):
        """Auto-close the window."""
        logger.info("Auto-closing test window")
        self.close()


def main():
    """Main function."""
    app = QApplication.instance() or QApplication(sys.argv)
    
    # Create qasync loop exactly like run_phase_one.py
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    logger.info(f"Created qasync event loop: {id(loop)}")
    
    # Register with EventLoopManager exactly like run_phase_one.py
    result = EventLoopManager.set_primary_loop(loop)
    logger.info(f"Registered main event loop with EventLoopManager: {result}")
    
    # Create and show window
    window = TestMainWindow()
    window.show()
    
    logger.info("Starting GUI test application...")
    logger.info("Click the button to test prompt processing with qasync_wait_for fix!")
    
    with loop:
        try:
            return app.exec()
        except Exception as e:
            logger.error(f"Application error: {e}")
            return 1


if __name__ == "__main__":
    exit_code = main()
    logger.info(f"Test completed with exit code: {exit_code}")
    sys.exit(exit_code)