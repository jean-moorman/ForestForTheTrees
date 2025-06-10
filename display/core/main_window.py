"""
Main application window for the Forest Display monitoring system.
"""
import asyncio
import logging
import traceback
import weakref
from datetime import datetime
from typing import Dict, Any, Optional

import qasync
from qasync import asyncSlot

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QLabel, 
    QApplication, QMessageBox
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QTimer

from resources.events import EventQueue
from resources.monitoring import SystemMonitor, CircuitBreaker
from interfaces import AgentState
from ..utils.styles import get_application_stylesheet
from ..utils.event_handlers import EventHandlerMixin
from ..utils.data_processing import DataProcessor
from ..monitoring import SystemMetricsPanel, SystemMetrics, CircuitBreakerPanel, AgentMetricsPanel
from ..visualization import TimelineWidget
from ..visualization.alerts import AlertLevel
from ..content import PhaseContentArea, PromptInterface
from .async_manager import AsyncHelper

logger = logging.getLogger(__name__)


class ForestDisplay(QMainWindow, EventHandlerMixin):
    """Main application window for forest monitoring system."""

    error_signal = pyqtSignal(str, dict)

    def __init__(self, event_queue: EventQueue, orchestrator, system_monitor: SystemMonitor):
        """Initialize the main window."""
        QMainWindow.__init__(self)
        EventHandlerMixin.__init__(self)
        
        self.event_queue = event_queue
        self.orchestrator = orchestrator
        self.system_monitor = system_monitor
        self.system_metrics = SystemMetrics(self)
        self.async_helper = AsyncHelper(self)
        self._timers = []  # Registry for all timers
        
        self._setup_window()
        self._init_ui()
        self._connect_signals()

        # Defer monitoring initialization to avoid reentrancy with prompt processing
        QTimer.singleShot(100, self._deferred_init_monitoring)

    def _deferred_init_monitoring(self):
        """Initialize monitoring after a short delay to avoid reentrancy."""
        try:
            loop = self._get_qasync_compatible_loop()
            if loop and not loop.is_closed():
                loop.create_task(self._init_monitoring())
        except Exception as e:
            logger.error(f"Error in deferred monitoring init: {e}")
    
    def _get_qasync_compatible_loop(self) -> asyncio.AbstractEventLoop:
        """Get event loop with qasync compatibility."""
        from resources.events.loop_management import EventLoopManager
        
        # Strategy 1: Try to get running loop (works in most qasync contexts)
        try:
            current_loop = asyncio.get_running_loop()
            logger.debug(f"Found running loop via asyncio: {id(current_loop)}")
            return current_loop
        except RuntimeError:
            pass
        
        # Strategy 2: Use EventLoopManager primary loop (qasync-aware)
        primary_loop = EventLoopManager.get_primary_loop()
        if primary_loop and not primary_loop.is_closed():
            logger.debug(f"Using EventLoopManager primary loop: {id(primary_loop)}")
            # Ensure this loop is set as the current event loop for the thread
            try:
                asyncio.set_event_loop(primary_loop)
            except Exception as e:
                logger.debug(f"Could not set primary loop as current: {e}")
            return primary_loop
        
        # Strategy 3: Get thread's default event loop
        try:
            thread_loop = asyncio.get_event_loop()
            logger.debug(f"Using thread event loop: {id(thread_loop)}")
            return thread_loop
        except RuntimeError:
            pass
        
        # Strategy 4: Last resort - create new loop
        logger.warning("No event loop found, creating new one")
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        EventLoopManager.set_primary_loop(new_loop)
        return new_loop

    def _create_timer(self, interval, callback):
        """Create and track a QTimer."""
        timer = QTimer()
        timer.timeout.connect(callback)
        timer.start(interval)
        self._timers.append(timer)
        return timer
    
    def _cleanup_timers(self):
        """Stop all timers in registry."""
        for timer in self._timers:
            timer.stop()
        
        # Also find and stop any timers in child widgets
        for timer in self.findChildren(QTimer):
            timer.stop()
            
    @asyncSlot()
    async def setup_async(self):
        """Setup async components"""
        # Start monitoring systems
        await self.system_monitor.memory_monitor.start()
        await self.system_monitor.start()
        
        # GUI system circuit breaker removed - not needed for UI operations

    def _setup_window(self) -> None:
        """Configure window properties."""
        self.setWindowTitle("Forest For The Trees - System Monitor")
        self.setMinimumSize(QSize(1200, 800))
        self.setStyleSheet(get_application_stylesheet())

    async def _init_monitoring(self) -> None:
        """Initialize monitoring systems."""
        self._pending_updates = set()
        await self.setup_event_subscriptions(self.event_queue)
        self._setup_update_timer()

    def _setup_update_timer(self) -> None:
        """Set up timer for periodic UI updates."""
        self._update_timer = QTimer()
        self._update_timer.timeout.connect(self._process_pending_updates)
        self._update_timer.start(1000)  # Update every second
        
    def _process_pending_updates(self) -> None:
        """Process any pending UI updates."""
        try:
            updates = self._pending_updates.copy()
            self._pending_updates.clear()
            
            for update_type, update_id in updates:
                if update_type == 'agent_state':
                    self._update_agent_display(update_id)
                elif update_type == 'metric':
                    self._update_metrics_display(update_id)
            
            # Update circuit panel periodically regardless of specific events
            if hasattr(self, 'circuit_panel'):
                self.circuit_panel.update_circuits()
                    
        except Exception as e:
            self._handle_error(
                "Failed to process updates",
                {'error': str(e), 'source': 'update_processor'}
            )
            
    def _update_agent_display(self, agent_id: str) -> None:
        """Update display for specific agent."""
        if agent_id in self.phase_content.agent_widgets:
            widget = self.phase_content.agent_widgets[agent_id]
            current_state = self.timeline.agent_states[agent_id].states[-1].state
            widget.update_output({}, current_state)  # Update with actual output as needed
            
    def _update_metrics_display(self, metric_id: str) -> None:
        """Update metrics display based on metric type."""
        try:
            # Call the appropriate update method based on metric type
            if metric_id == 'system_health':
                self.metrics_panel.update_health_status()
            elif metric_id == 'error_rate':
                self.metrics_panel.update_error_metrics()
            elif metric_id == 'memory_usage':
                self.metrics_panel.update_memory_metrics()
            else:
                # If unsure which metric changed, update all
                self.metrics_panel.update_all()
                
            # Update agent metrics if an agent is selected
            if hasattr(self, 'agent_metrics') and self.timeline.selected_agent:
                self.agent_metrics.update_metrics(self.timeline.selected_agent[1])
        except Exception as e:
            logger.error(f"Error updating metrics: {e}")
            self._handle_error(
                "Failed to update metrics",
                {'error': str(e), 'source': 'metrics_updater'}
            )

    def _init_ui(self) -> None:
        """Initialize user interface."""
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        self._create_header(layout)
        self._create_prompt_interface(layout)
        self._create_timeline(layout)
        self._create_content_area(layout)

    def _connect_signals(self) -> None:
        """Connect signal handlers."""
        self.error_signal.connect(self._handle_error)
        # Connect prompt submission to the non-coroutine handler
        self.prompt_interface.prompt_submitted.connect(self._handle_prompt_submission)

    def _handle_prompt_submission(self, prompt: str) -> None:
        """Non-coroutine handler for prompt submission that launches async processing."""
        try:
            # Disable the interface immediately
            self.prompt_interface.setEnabled(False)
            
            # Get the proper qasync loop from EventLoopManager
            from resources.events.loop_management import EventLoopManager
            loop = EventLoopManager.get_primary_loop()
            
            if loop and not loop.is_closed():
                # Create task in the qasync loop context
                task = loop.create_task(self._process_prompt_async(prompt))
                task.add_done_callback(self._handle_prompt_task_done)
                logger.debug(f"Created prompt processing task in qasync loop {id(loop)}")
            else:
                # Fallback to current thread's loop
                try:
                    loop = asyncio.get_event_loop()
                    if loop and not loop.is_closed():
                        task = loop.create_task(self._process_prompt_async(prompt))
                        task.add_done_callback(self._handle_prompt_task_done)
                        logger.warning(f"Using fallback loop {id(loop)} for prompt processing")
                    else:
                        raise RuntimeError("No event loop available")
                except Exception as fallback_error:
                    logger.error(f"No event loop available for prompt processing: {fallback_error}")
                    self.prompt_interface.reset()
                    return
            
        except Exception as e:
            logger.error(f"Failed to submit prompt: {str(e)}", exc_info=True)
            self.error_signal.emit(
                f"Failed to submit prompt: {str(e)}",
                {'error': str(e), 'source': 'prompt_submission'}
            )
            self.prompt_interface.reset()

    def _handle_prompt_task_done(self, task: asyncio.Task) -> None:
        """Handle completion of prompt processing task."""
        try:
            if task.exception():
                # Handle task exception
                error = task.exception()
                logger.error(f"Prompt processing task failed: {error}", exc_info=True)
                self.error_signal.emit(
                    f"Prompt processing failed: {str(error)}",
                    {'error': str(error), 'source': 'prompt_task'}
                )
            else:
                # Handle successful result
                result = task.result()
                self._handle_prompt_result(result)
        except Exception as e:
            logger.error(f"Error handling prompt task completion: {e}", exc_info=True)
        finally:
            # Always re-enable the prompt interface
            self.prompt_interface.reset()

    async def _process_prompt_async(self, prompt: str) -> Dict[str, Any]:
        """Asynchronous prompt processing wrapper for GUI using step-by-step execution."""
        # Ensure GUI async operations use qasync loop context
        import threading
        from resources.events.loop_management import EventLoopManager
        
        if threading.current_thread() is not threading.main_thread():
            raise RuntimeError("GUI operations must run in main thread")
        
        # Get the loop using a robust qasync-aware method
        from resources.events.qasync_utils import get_qasync_compatible_loop, qasync_wait_for
        current_loop = get_qasync_compatible_loop()
        logger.info(f"Using event loop {id(current_loop)} for prompt processing")
        
        try:
            if not prompt.strip():
                raise ValueError("Empty prompt submitted")
                
            logger.info(f"Processing prompt step-by-step: {prompt} [Loop: {id(current_loop)}]")
            
            # Start Phase One workflow and get operation ID
            operation_id = await self.orchestrator.start_phase_one(prompt)
            logger.info(f"Started Phase One workflow with operation_id: {operation_id}")
            
            # Track progress and execute steps one by one
            step_results = {}
            total_steps = ["garden_planner", "earth_agent_validation", "environmental_analysis", 
                          "root_system_architect", "tree_placement_planner", "foundation_refinement"]
            
            for step_num in range(len(total_steps)):
                # Get current status
                status = await self.orchestrator.get_step_status(operation_id)
                logger.info(f"Step {step_num + 1}/{len(total_steps)}: {status.get('current_step', 'unknown')} - {status.get('progress_percentage', 0):.1f}% complete")
                
                # Execute next step with timeout protection using qasync-compatible approach
                try:
                    # Use the consistent loop we already obtained
                    step_coro = self.orchestrator.execute_next_step(operation_id)
                    step_task = current_loop.create_task(step_coro)
                    
                    # Use qasync-compatible wait_for
                    step_result = await qasync_wait_for(step_task, timeout=120.0)
                    
                    if step_result.get("status") == "error":
                        raise ValueError(f"Step failed: {step_result.get('message', 'Unknown error')}")
                    
                    if step_result.get("status") == "completed":
                        # Workflow completed
                        final_status = await self.orchestrator.get_step_status(operation_id)
                        step_results = final_status.get("step_results", {})
                        break
                    
                    # Store step result
                    executed_step = step_result.get("step_executed")
                    if executed_step:
                        step_results[executed_step] = step_result.get("step_result", {})
                        
                except (asyncio.TimeoutError, TimeoutError):
                    raise ValueError(f"Step {step_num + 1} timed out after 2 minutes. This may indicate network issues or complex processing.")
            
            # Format result for compatibility with existing GUI expectations
            result = {
                "status": "success",
                "operation_id": operation_id,
                "phase_one_outputs": step_results,
                "message": f"Phase One completed successfully via step-by-step execution",
                "steps_executed": list(step_results.keys())
            }
            
            logger.info(f"Step-by-step prompt processing completed: {len(step_results)} steps executed")
            return result
            
        except Exception as e:
            logger.error(f"Step-by-step prompt processing failed: {str(e)}", exc_info=True)
            raise

    def _handle_prompt_result(self, result: Optional[Dict[str, Any]]) -> None:
        """Handle the completion of async prompt processing with improved error handling."""
        try:
            # Validate result exists
            if result is None:
                raise ValueError("Prompt processing returned no result")
                
            # Validate result structure before updating UI
            if not isinstance(result, dict):
                raise TypeError(f"Expected dict result, got {type(result)}")
                
            status = result.get('status')
            if status != "success":
                raise ValueError(f"Prompt processing failed with status: {status}")
                
            outputs = result.get('phase_one_outputs')
            if not isinstance(outputs, dict):
                raise TypeError(f"Expected dict outputs, got {type(outputs)}")
                
            # Update UI with validated result
            for agent_id, output in outputs.items():
                if agent_id in self.phase_content.agent_widgets:
                    widget = self.phase_content.agent_widgets[agent_id]
                    if widget is not None:
                        widget.update_output(
                            output or {},  # Ensure we pass a dict even if output is None
                            AgentState.READY
                        )
                        
        except Exception as e:
            error_msg = f"Failed to process prompt result: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.error_signal.emit(
                error_msg,
                {
                    'error': str(e),
                    'source': 'prompt_handler',
                    'result': result  # Include result in error context
                }
            )

    def _handle_monitoring_status(self, event_type: str, data: Dict[str, Any]) -> None:
        """Handle periodic monitoring status updates."""
        try:
            # Update memory monitoring in metrics panel
            if 'memory_monitor' in data and hasattr(self, 'metrics_panel'):
                self.metrics_panel.update_memory_metrics()
                
            # Update circuit breakers in circuit panel
            if 'circuit_breakers' in data and hasattr(self, 'circuit_panel'):
                self.circuit_panel.update_circuits()
                
            # Update agent count in header
            agent_count = len(data.get('circuit_breakers', {}))
            self.agent_count.setText(f"Active Circuits: {agent_count}")
            
        except Exception as e:
            logger.error(f"Error handling monitoring status: {e}")
            # Don't show UI error for this routine update

    def _handle_system_error(self, event_type: str, data: Dict[str, Any]) -> None:
        """Handle system-level errors."""
        try:
            error = data.get('error', 'Unknown error')
            component = data.get('component', 'system')
            
            logger.error(f"System error from {component}: {error}")
            
            # Add to alert widget
            if hasattr(self, 'metrics_panel'):
                self.metrics_panel.alert_widget.add_alert(
                    AlertLevel.ERROR,
                    f"System error in {component}: {error}"
                )
                
            # Update system status
            self.system_status.setText(f"System: Error")
            self.system_status.setStyleSheet("color: #D0021B")
            
        except Exception as e:
            logger.error(f"Error handling system error: {e}")
            self._handle_error(
                "Failed to handle system error event",
                {'error': str(e), 'source': 'error_handler', 'event_data': data}
            )

    def _handle_health_change(self, event_type: str, data: Dict[str, Any]) -> None:
        """Handle system health change events."""
        try:
            component = data.get('component', '')
            status = data.get('status', 'UNKNOWN')
            
            # Circuit breaker events
            if component.startswith('circuit_breaker_'):
                # Update circuit panel if it exists
                if hasattr(self, 'circuit_panel'):
                    self.circuit_panel.handle_circuit_state_change(component, data)
                    
                # Add to pending updates to refresh metrics
                self._pending_updates.add(('metric', 'error_rate'))
                    
            # System memory health events
            elif component == 'system_memory':
                # Update memory usage display
                if hasattr(self, 'metrics_panel'):
                    self.metrics_panel.update_memory_metrics()
                    
                # Add alert based on status
                if status == "CRITICAL":
                    self._show_memory_alert(data)
                    
            # Overall system health
            elif component == 'system':
                # Update health status in metrics panel
                if hasattr(self, 'metrics_panel'):
                    self.metrics_panel.update_health_status()
                    
                # Update system status indicator in header
                self.system_status.setText(f"System: {status}")
                self.system_status.setStyleSheet(self._get_system_status_color(status))
                
            # Update pending metrics to refresh displays
            self._pending_updates.add(('metric', component))
                
        except Exception as e:
            logger.error(f"Error handling health change: {e}")
            self._handle_error(
                "Failed to handle health change event",
                {'error': str(e), 'source': 'health_handler', 'event_data': data}
            )
            
    def _get_system_status_color(self, status: str) -> str:
        """Get color for system status display."""
        return {
            "HEALTHY": "color: #7ED321",
            "DEGRADED": "color: #F5A623",
            "UNHEALTHY": "color: #D0021B",
            "CRITICAL": "color: #B00020",
            "ERROR": "color: #D0021B"
        }.get(status, "color: #808080")  # Default to gray
        
    def _show_memory_alert(self, data: Dict[str, Any]) -> None:
        """Show memory alert notification."""
        usage_percentage = data.get('metadata', {}).get('usage_percentage', 0) * 100
        self.metrics_panel.alert_widget.add_alert(
            AlertLevel.CRITICAL,
            f"Memory usage critical: {usage_percentage:.1f}% of available memory used"
        )

    def _handle_resource_alert(self, event_type: str, data: Dict[str, Any]) -> None:
        """Handle resource alert events."""
        try:
            alert_type = data.get('alert_type', '')
            level = data.get('level', 'WARNING')
            
            # Map alert level to UI alert level
            alert_level_map = {
                'WARNING': AlertLevel.WARNING,
                'ERROR': AlertLevel.ERROR,
                'CRITICAL': AlertLevel.CRITICAL
            }
            alert_level = alert_level_map.get(level, AlertLevel.WARNING)
            
            if alert_type == 'memory':
                # Handle memory alerts
                percent = data.get('percent', 0)
                total_mb = data.get('total_mb', 0)
                
                # Add alert to metrics panel
                if hasattr(self, 'metrics_panel'):
                    self.metrics_panel.alert_widget.add_alert(
                        alert_level,
                        f"Memory alert: {percent:.1f}% used ({total_mb:.1f} MB)"
                    )
                    
                # Update memory metrics
                self._pending_updates.add(('metric', 'memory_usage'))
                    
            elif alert_type == 'circuit_breaker':
                # Handle circuit breaker alerts
                circuit_name = data.get('circuit_name', 'unknown')
                message = data.get('message', 'Circuit breaker alert')
                
                # Add alert to circuit panel
                if hasattr(self, 'circuit_panel'):
                    self.circuit_panel.alert_widget.add_alert(
                        alert_level,
                        f"Circuit {circuit_name}: {message}"
                    )
                    
                # Update circuit display
                self._pending_updates.add(('metric', f'circuit_{circuit_name}'))
                    
        except Exception as e:
            logger.error(f"Error handling resource alert: {e}")
            self._handle_error(
                "Failed to handle resource alert",
                {'error': str(e), 'source': 'alert_handler', 'event_data': data}
            )

    def _create_header(self, layout: QVBoxLayout) -> None:
        """Create the application header."""
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(8, 8, 8, 8)
        
        # Title
        title = QLabel("Forest For The Trees - System Monitor")
        title.setProperty("heading", True)
        header_layout.addWidget(title)
        
        # System status indicators
        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        
        self.system_status = QLabel("System: Healthy")
        self.system_status.setStyleSheet("color: #7ED321")
        status_layout.addWidget(self.system_status)
        
        self.agent_count = QLabel("Active Agents: 0")
        status_layout.addWidget(self.agent_count)
        
        header_layout.addWidget(status_widget)
        header_layout.setStretch(0, 2)
        header_layout.setStretch(1, 1)
        
        layout.addWidget(header)

    def _create_prompt_interface(self, layout: QVBoxLayout) -> None:
        """Create the prompt input interface."""
        self.prompt_interface = PromptInterface()
        layout.addWidget(self.prompt_interface)

    def _create_timeline(self, layout: QVBoxLayout) -> None:
        """Create the timeline visualization."""
        self.timeline = TimelineWidget()
        self.timeline.agent_selected.connect(self._handle_agent_selection)
        layout.addWidget(self.timeline)

    def _create_content_area(self, layout: QVBoxLayout) -> None:
        """Create the main content area with metrics and phase content."""
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Metrics
        metrics_container = QWidget()
        metrics_layout = QVBoxLayout(metrics_container)
        
        self.metrics_panel = SystemMetricsPanel(self.system_monitor)
        self.system_metrics.metric_panel = self.metrics_panel
        self.circuit_panel = CircuitBreakerPanel(self.system_monitor)
        self.agent_metrics = AgentMetricsPanel(self.system_monitor)
        
        metrics_layout.addWidget(self.metrics_panel)
        metrics_layout.addWidget(self.circuit_panel)
        metrics_layout.addWidget(self.agent_metrics)
        splitter.addWidget(metrics_container)
        
        # Right panel - Phase content
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.phase_zero_content = PhaseContentArea("Phase Zero")
        self.phase_one_content = PhaseContentArea("Phase One")
        
        content_splitter.addWidget(self.phase_zero_content)
        content_splitter.addWidget(self.phase_one_content)
        splitter.addWidget(content_splitter)
        
        # Set up a unified phase content interface for backward compatibility
        self.phase_content = self.phase_one_content  # Default to phase one
        
        # Set stretch factors
        splitter.setStretchFactor(0, 1)  # Metrics panel
        splitter.setStretchFactor(1, 2)  # Content area
        
        layout.addWidget(splitter)

    def _handle_agent_selection(self, phase: str, agent_id: str) -> None:
        """Handle agent selection from timeline."""
        try:
            self.timeline.selected_agent = (phase, agent_id)
            # Use AsyncHelper for potentially long-running metric updates
            self.async_helper.run_coroutine(
                self._update_agent_metrics(agent_id),
                callback=self._handle_metrics_update
            )
        except Exception as e:
            self._handle_error(
                "Failed to handle agent selection",
                {'error': str(e), 'source': 'agent_selection_handler'}
            )

    async def _update_agent_metrics(self, agent_id: str) -> Dict[str, Any]:
        """Asynchronously update agent metrics."""
        # Use the orchestrator interface to get agent metrics
        return await self.orchestrator.get_agent_metrics(agent_id)

    def _handle_metrics_update(self, metrics: Dict[str, Any]) -> None:
        """Handle the result of async metrics update."""
        try:
            # Extract agent_id from metrics or use the currently selected agent
            agent_id = metrics.get('agent_id') or (
                self.timeline.selected_agent[1] if self.timeline.selected_agent else None
            )
            if agent_id:
                self.agent_metrics.update_metrics(agent_id)
        except Exception as e:
            self._handle_error(
                "Failed to update metrics display",
                {'error': str(e), 'source': 'metrics_handler'}
            )

    def _handle_error(self, error_msg: str, error_data: Dict[str, Any]) -> None:
        """
        Handle application errors.
        
        Args:
            error_msg: Primary error message
            error_data: Additional error context
        """
        try:
            # Remove potentially problematic check that might suppress errors
            detailed_error = DataProcessor.format_error_message(error_msg, error_data)
            
            # Always log the full error context
            logger.error(detailed_error, extra={
                'error_data': error_data,
                'stack_trace': traceback.format_stack()
            })
            
            # Update UI to show error state
            self.system_status.setText("System: Error Detected")
            self.system_status.setStyleSheet("color: #D0021B")
            
            # Show error in metrics panel
            if hasattr(self, 'metrics_panel'):
                self.metrics_panel.alert_widget.add_alert(
                    AlertLevel.ERROR,
                    detailed_error
                )
            
            # Show dialog for user feedback
            self._show_error_dialog(detailed_error)

        except Exception as handler_error:
            # If error handling itself fails, show critical error
            logger.critical(f"Error handler failed: {handler_error}", exc_info=True)
            QMessageBox.critical(
                self,
                "Critical Error",
                f"Error handling failed: {handler_error}\nOriginal error: {error_msg}"
            )

    def _show_error_dialog(self, message: str) -> None:
        """Display error dialog to user."""
        QMessageBox.critical(self, "Error", message)

    def closeEvent(self, event):
        """Handle application shutdown with simple cleanup."""
        try:
            # Stop all timers immediately
            self._cleanup_timers()
            
            # Stop async helper without complex cleanup
            if hasattr(self, 'async_helper'):
                self.async_helper.stop_all()
            
            # Accept the close event immediately to avoid loop conflicts
            event.accept()
            logger.info("ForestDisplay closed with simple cleanup")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            event.accept()  # Still close even if cleanup fails

