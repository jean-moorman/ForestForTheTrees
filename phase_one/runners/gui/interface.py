"""
Phase One GUI Interface

Interface for display to interact with Phase One Orchestrator, providing
synchronous/asynchronous boundaries and step-by-step execution capabilities.
"""

import asyncio
import concurrent.futures
import logging
import threading
import uuid
from datetime import datetime
from typing import Dict, Any


logger = logging.getLogger(__name__)


class PhaseOneInterface:
    """Interface for display to interact with Phase One Orchestrator."""
    
    def __init__(self, phase_one: 'PhaseOneOrchestrator'):
        self.phase_one = phase_one
        self.logger = logging.getLogger(__name__)
        
    def process_task(self, prompt: str) -> Dict[str, Any]:
        """Synchronous wrapper for CLI compatibility - clean sync/async boundary."""
        self.logger.info(f"Processing task (sync wrapper): {prompt}")
        
        # Clean sync wrapper - runs in its own thread with dedicated loop
        import concurrent.futures
        import threading
        
        def run_async_task():
            """Run the async task in a dedicated thread."""
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self.process_task_async(prompt))
            finally:
                loop.close()
        
        # Execute in thread pool to avoid blocking main thread
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_async_task)
            try:
                return future.result(timeout=300)  # 5 minute timeout
            except concurrent.futures.TimeoutError:
                self.logger.error("Phase One processing timed out after 5 minutes")
                return {
                    "status": "error", 
                    "message": "Processing timed out after 5 minutes",
                    "phase_one_outputs": {}
                }
            except Exception as e:
                self.logger.error(f"Error in sync wrapper: {e}", exc_info=True)
                return {
                    "status": "error",
                    "message": str(e), 
                    "phase_one_outputs": {}
                }
    
    async def process_task_async(self, prompt: str) -> Dict[str, Any]:
        """Process task using Phase One orchestrator - async interface for GUI."""
        self.logger.info(f"Processing task async: {prompt}")
        
        try:
            # Directly call the async method without circular dependencies
            result = await self.phase_one.process_task(prompt)
            
            return {
                "status": result.get("status", "unknown"),
                "phase_one_outputs": result,
                "message": f"Processed task through Phase One: {result.get('status', 'unknown')}"
            }
                    
        except Exception as e:
            self.logger.error(f"Error processing task async: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "phase_one_outputs": {}
            }
            
    async def get_agent_metrics(self, agent_id: str) -> Dict[str, Any]:
        """Get metrics for a specific agent."""
        self.logger.info(f"Getting metrics for agent: {agent_id}")
        
        # Import our utility function
        from resources.events.utils import ensure_event_loop, run_async_in_thread
        
        try:
            # Ensure we have an event loop using our utility function
            ensure_event_loop()
            
            try:
                # Delegate to phase_one for agent metrics directly
                return await self.phase_one.get_agent_metrics(agent_id)
            except RuntimeError as e:
                if "no running event loop" in str(e):
                    self.logger.warning(f"No running event loop detected for metrics, using ensure_async_execution: {e}")
                    # Use our special executor for async operations in case of event loop issues
                    return await run_async_in_thread(self.phase_one.get_agent_metrics(agent_id))
                else:
                    # Re-raise other RuntimeErrors
                    raise
            except Exception as e:
                self.logger.error(f"Error getting agent metrics: {e}", exc_info=True)
                return {"status": "error", "message": str(e), "agent_id": agent_id}
        except Exception as e:
            self.logger.error(f"Error in get_agent_metrics: {e}", exc_info=True)
            return {"status": "error", "message": str(e), "agent_id": agent_id}
    
    # ===== STEP-BY-STEP INTERFACE FOR DEBUGGING AND CLARITY =====
    
    async def start_phase_one(self, prompt: str) -> str:
        """
        Start Phase One workflow and return operation ID for tracking.
        
        Args:
            prompt: User prompt to process
            
        Returns:
            operation_id: Unique identifier for this Phase One execution
        """
        import uuid
        from datetime import datetime
        
        # Generate unique operation ID
        operation_id = f"phase_one_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
        
        self.logger.info(f"Starting Phase One workflow with operation_id: {operation_id}")
        
        try:
            # Initialize workflow state
            initial_state = {
                "operation_id": operation_id,
                "prompt": prompt,
                "status": "initialized",
                "current_step": "ready",
                "start_time": datetime.now().isoformat(),
                "steps_completed": [],
                "step_results": {}
            }
            
            # Store initial state
            await self.phase_one._state_manager.set_state(
                f"stepwise_phase_one:{operation_id}",
                initial_state,
                "STATE"
            )
            
            return operation_id
            
        except Exception as e:
            self.logger.error(f"Error starting Phase One: {e}", exc_info=True)
            raise
    
    async def get_step_status(self, operation_id: str) -> Dict[str, Any]:
        """
        Get current status of a Phase One workflow execution.
        
        Args:
            operation_id: The operation ID from start_phase_one()
            
        Returns:
            Dictionary with current status, progress, and results
        """
        try:
            # Get current state
            state_entry = await self.phase_one._state_manager.get_state(
                f"stepwise_phase_one:{operation_id}",
                "STATE"
            )
            
            if not state_entry:
                return {
                    "status": "not_found",
                    "message": f"No workflow found with operation_id: {operation_id}"
                }
            
            # Extract state data from IStateEntry object
            if hasattr(state_entry, 'state'):
                state = state_entry.state
            else:
                # If it's already a dict, use it directly
                state = state_entry
            
            # Calculate progress
            total_steps = ["garden_planner", "earth_agent_validation", "environmental_analysis", 
                          "root_system_architect", "tree_placement_planner", "foundation_refinement"]
            completed_steps = len(state.get("steps_completed", []))
            progress_percentage = (completed_steps / len(total_steps)) * 100
            
            return {
                "operation_id": operation_id,
                "status": state.get("status", "unknown"),
                "current_step": state.get("current_step", "unknown"),
                "progress_percentage": progress_percentage,
                "steps_completed": state.get("steps_completed", []),
                "total_steps": total_steps,
                "start_time": state.get("start_time"),
                "last_updated": state.get("last_updated"),
                "step_results": state.get("step_results", {}),
                "error": state.get("error")
            }
            
        except Exception as e:
            self.logger.error(f"Error getting step status: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "operation_id": operation_id
            }
    
    async def execute_next_step(self, operation_id: str) -> Dict[str, Any]:
        """
        Execute the next step in the Phase One workflow.
        
        Args:
            operation_id: The operation ID from start_phase_one()
            
        Returns:
            Result of the executed step
        """
        try:
            # Get current state
            state_entry = await self.phase_one._state_manager.get_state(
                f"stepwise_phase_one:{operation_id}",
                "STATE"
            )
            
            if not state_entry:
                return {
                    "status": "error",
                    "message": f"No workflow found with operation_id: {operation_id}"
                }
            
            # Extract state data from IStateEntry object
            if hasattr(state_entry, 'state'):
                state = state_entry.state
            else:
                # If it's already a dict, use it directly
                state = state_entry
            
            # Determine next step
            completed_steps = state.get("steps_completed", [])
            current_step = state.get("current_step", "ready")
            
            # Define step sequence
            step_sequence = [
                "garden_planner",
                "earth_agent_validation", 
                "environmental_analysis",
                "root_system_architect",
                "tree_placement_planner",
                "foundation_refinement"
            ]
            
            # Find next step
            if current_step == "ready":
                next_step = step_sequence[0]
            elif current_step == "completed":
                return {
                    "status": "completed",
                    "message": "Phase One workflow completed successfully",
                    "operation_id": operation_id,
                    "final_results": state.get("step_results", {})
                }
            else:
                # Find current step index and get next
                try:
                    current_index = step_sequence.index(current_step)
                    if current_index + 1 >= len(step_sequence):
                        # Mark as completed
                        state["status"] = "completed"
                        state["current_step"] = "completed"
                        state["last_updated"] = datetime.now().isoformat()
                        
                        await self.phase_one._state_manager.set_state(
                            f"stepwise_phase_one:{operation_id}",
                            state,
                            "STATE"
                        )
                        
                        return {
                            "status": "completed",
                            "message": "Phase One workflow completed successfully",
                            "operation_id": operation_id,
                            "final_results": state.get("step_results", {})
                        }
                    
                    next_step = step_sequence[current_index + 1]
                except ValueError:
                    return {
                        "status": "error", 
                        "message": f"Unknown current step: {current_step}",
                        "operation_id": operation_id
                    }
            
            # Execute the next step with step-level retry logic
            self.logger.info(f"Executing step '{next_step}' for operation {operation_id}")
            
            # Configuration for step-level retries (for test compatibility)
            max_step_retries = 2
            step_retry_delays = [5.0, 10.0]
            
            step_result = None
            for step_attempt in range(max_step_retries + 1):
                try:
                    step_result = await self._execute_single_step(
                        next_step, 
                        state.get("prompt", ""), 
                        state.get("step_results", {}),
                        operation_id
                    )
                    
                    # Check if step failed with retryable error
                    if step_result.get("status") == "error":
                        error_message = step_result.get("error", "")
                        
                        # Classify error as retryable or non-retryable
                        non_retryable_patterns = ["required", "missing", "not found", "ValueError"]
                        is_non_retryable = any(pattern in str(error_message) for pattern in non_retryable_patterns)
                        
                        if not is_non_retryable and step_attempt < max_step_retries:
                            # Retryable error and we have retries left
                            self.logger.warning(f"Step {next_step} failed with retryable error, retrying in {step_retry_delays[step_attempt]}s: {error_message}")
                            await asyncio.sleep(step_retry_delays[step_attempt])
                            continue
                        else:
                            # Either non-retryable or out of retries
                            if is_non_retryable:
                                self.logger.error(f"Step {next_step} failed with non-retryable error: {error_message}")
                            else:
                                self.logger.error(f"Step {next_step} failed after {step_attempt + 1} attempts: {error_message}")
                            break
                    else:
                        # Step succeeded
                        if step_attempt > 0:
                            self.logger.info(f"Step {next_step} succeeded after {step_attempt + 1} attempts")
                        break
                        
                except Exception as step_e:
                    # Handle exceptions from _execute_single_step
                    error_message = str(step_e)
                    
                    # Classify error as retryable or non-retryable
                    non_retryable_patterns = ["required", "missing", "not found", "ValueError"]
                    is_non_retryable = any(pattern in error_message for pattern in non_retryable_patterns)
                    
                    if not is_non_retryable and step_attempt < max_step_retries:
                        # Retryable error and we have retries left
                        self.logger.warning(f"Step {next_step} exception retryable, retrying in {step_retry_delays[step_attempt]}s: {error_message}")
                        await asyncio.sleep(step_retry_delays[step_attempt])
                        continue
                    else:
                        # Either non-retryable or out of retries - create error result
                        step_result = {
                            "status": "error",
                            "step_name": next_step,
                            "error": error_message,
                            "message": f"Step failed: {error_message}",
                            "attempts": step_attempt + 1,
                            "non_retryable": is_non_retryable,
                            "timestamp": datetime.now().isoformat()
                        }
                        break
            
            # Update state with step result
            state["current_step"] = next_step
            state["last_updated"] = datetime.now().isoformat()
            state["steps_completed"] = completed_steps + [next_step]
            state["step_results"][next_step] = step_result
            
            if step_result.get("status") == "error":
                state["status"] = "error"
                state["error"] = step_result.get("message", "Unknown error")
            else:
                # Check if this was the final step
                current_step_index = step_sequence.index(next_step)
                if current_step_index + 1 >= len(step_sequence):
                    # This was the final step - mark as completed
                    state["status"] = "completed"
                    state["current_step"] = "completed"
                else:
                    state["status"] = "running"
            
            # Save updated state
            await self.phase_one._state_manager.set_state(
                f"stepwise_phase_one:{operation_id}",
                state,
                "STATE"
            )
            
            return {
                "status": "step_completed",
                "operation_id": operation_id,
                "step_executed": next_step,
                "step_result": step_result,
                "next_step": step_sequence[step_sequence.index(next_step) + 1] if step_sequence.index(next_step) + 1 < len(step_sequence) else "completed"
            }
            
        except KeyboardInterrupt:
            self.logger.warning(f"User interrupted step execution for operation {operation_id}")
            return {
                "status": "error",
                "message": "User interrupted execution",
                "operation_id": operation_id
            }
        except Exception as e:
            # This should only catch unexpected system-level errors
            self.logger.error(f"Unexpected system error in execute_next_step: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"System error: {str(e)}",
                "operation_id": operation_id
            }
    
    async def _execute_single_step(self, step_name: str, prompt: str, previous_results: Dict[str, Any], operation_id: str) -> Dict[str, Any]:
        """
        Execute a single Phase One step with timeout and retry logic.
        
        Args:
            step_name: Name of the step to execute
            prompt: Original user prompt
            previous_results: Results from previous steps
            operation_id: Operation identifier
            
        Returns:
            Result of the single step execution
        """
        
        # Configuration for retry logic
        max_retries = 2
        base_timeout = 180.0  # 3 minutes base timeout
        retry_delays = [5.0, 10.0]  # Increasing delays between retries
        
        for attempt in range(max_retries + 1):
            try:
                step_start_time = datetime.now()
                attempt_log = f" (attempt {attempt + 1}/{max_retries + 1})" if attempt > 0 else ""
                
                # Calculate timeout - increase with retry attempts
                timeout = base_timeout + (attempt * 60.0)  # Add 1 minute per retry
                
                self.logger.info(f"Executing {step_name} for operation {operation_id}{attempt_log} (timeout: {timeout}s)")
                
                # Execute the step with timeout using qasync-compatible utilities
                from resources.events.qasync_utils import qasync_wait_for
                
                try:
                    if step_name == "garden_planner":
                        # Execute Garden Planner
                        result = await qasync_wait_for(
                            self.phase_one.garden_planner_agent.process(prompt),
                            timeout=timeout
                        )
                        
                    elif step_name == "earth_agent_validation":
                        # Execute Earth Agent validation on Garden Planner output
                        garden_output = previous_results.get("garden_planner", {})
                        if not garden_output:
                            raise ValueError("Garden Planner output required for Earth Agent validation")
                        
                        # Use the validation coordinator for Earth Agent validation
                        validation_input = {
                            "user_request": prompt,
                            "garden_planner_output": garden_output,
                            "operation_id": operation_id
                        }
                        result = await qasync_wait_for(
                            self.phase_one.earth_agent.process(validation_input),
                            timeout=timeout
                        )
                        
                    elif step_name == "environmental_analysis":
                        # Execute Environmental Analysis
                        validated_output = previous_results.get("earth_agent_validation", {})
                        if not validated_output:
                            raise ValueError("Earth Agent validation output required for Environmental Analysis")
                        
                        result = await qasync_wait_for(
                            self.phase_one.environmental_analysis_agent.process(validated_output),
                            timeout=timeout
                        )
                        
                    elif step_name == "root_system_architect":
                        # Execute Root System Architect
                        env_output = previous_results.get("environmental_analysis", {})
                        if not env_output:
                            raise ValueError("Environmental Analysis output required for Root System Architect")
                        
                        result = await qasync_wait_for(
                            self.phase_one.root_system_architect_agent.process(env_output),
                            timeout=timeout
                        )
                        
                    elif step_name == "tree_placement_planner":
                        # Execute Tree Placement Planner
                        root_output = previous_results.get("root_system_architect", {})
                        if not root_output:
                            raise ValueError("Root System Architect output required for Tree Placement Planner")
                        
                        result = await qasync_wait_for(
                            self.phase_one.tree_placement_planner_agent.process(root_output),
                            timeout=timeout
                        )
                        
                    elif step_name == "foundation_refinement":
                        # Execute Foundation Refinement with Phase Zero feedback
                        tree_output = previous_results.get("tree_placement_planner", {})
                        if not tree_output:
                            raise ValueError("Tree Placement Planner output required for Foundation Refinement")
                        
                        # Compile all results for refinement analysis
                        compiled_results = {
                            "garden_planner": previous_results.get("garden_planner", {}),
                            "earth_agent_validation": previous_results.get("earth_agent_validation", {}),
                            "environmental_analysis": previous_results.get("environmental_analysis", {}),
                            "root_system_architect": previous_results.get("root_system_architect", {}),
                            "tree_placement_planner": tree_output
                        }
                        
                        result = await qasync_wait_for(
                            self.phase_one.foundation_refinement_agent.process(compiled_results),
                            timeout=timeout
                        )
                        
                    else:
                        raise ValueError(f"Unknown step: {step_name}")
                    
                    # Success - calculate execution time and return
                    execution_time = (datetime.now() - step_start_time).total_seconds()
                    
                    self.logger.info(f"Step {step_name} completed successfully in {execution_time:.2f}s{attempt_log}")
                    
                    return {
                        "status": "success",
                        "step_name": step_name,
                        "execution_time_seconds": execution_time,
                        "result": result,
                        "timestamp": datetime.now().isoformat(),
                        "attempt": attempt + 1,
                        "timeout_used": timeout
                    }
                    
                except asyncio.TimeoutError:
                    execution_time = (datetime.now() - step_start_time).total_seconds()
                    error_msg = f"Step {step_name} timed out after {execution_time:.2f}s (limit: {timeout}s){attempt_log}"
                    self.logger.warning(error_msg)
                    
                    # If this was the last attempt, return timeout error
                    if attempt >= max_retries:
                        return {
                            "status": "error",
                            "step_name": step_name,
                            "execution_time_seconds": execution_time,
                            "error": "timeout",
                            "message": error_msg,
                            "timestamp": datetime.now().isoformat(),
                            "attempts": attempt + 1,
                            "timeout_used": timeout
                        }
                    
                    # Wait before retry
                    await asyncio.sleep(retry_delays[attempt])
                    self.logger.info(f"Retrying {step_name} after {retry_delays[attempt]}s delay...")
                    continue
                    
                except Exception as e:
                    execution_time = (datetime.now() - step_start_time).total_seconds()
                    error_msg = f"Step {step_name} failed: {str(e)}{attempt_log}"
                    self.logger.error(error_msg, exc_info=True)
                    
                    # For certain errors, don't retry (validation errors, missing data)
                    non_retryable_errors = ["required", "missing", "not found", "ValueError"]
                    if any(err in str(e) for err in non_retryable_errors) or attempt >= max_retries:
                        return {
                            "status": "error",
                            "step_name": step_name,
                            "execution_time_seconds": execution_time,
                            "error": str(e),
                            "message": error_msg,
                            "timestamp": datetime.now().isoformat(),
                            "attempts": attempt + 1,
                            "non_retryable": any(err in str(e) for err in non_retryable_errors)
                        }
                    
                    # Wait before retry for retryable errors
                    await asyncio.sleep(retry_delays[attempt])
                    self.logger.info(f"Retrying {step_name} after {retry_delays[attempt]}s delay...")
                    continue
            
            except KeyboardInterrupt:
                # Handle user interruption gracefully
                self.logger.warning(f"User interrupted execution of {step_name}")
                return {
                    "status": "error",
                    "step_name": step_name,
                    "error": "user_interrupted",
                    "message": f"User interrupted execution of {step_name}",
                    "timestamp": datetime.now().isoformat()
                }
            except (SystemExit, MemoryError) as critical_e:
                # Handle critical system errors that shouldn't be retried
                self.logger.error(f"Critical system error in {step_name}: {critical_e}", exc_info=True)
                return {
                    "status": "error",
                    "step_name": step_name,
                    "error": str(critical_e),
                    "message": f"Critical system error: {str(critical_e)}",
                    "timestamp": datetime.now().isoformat()
                }
        
        # This should never be reached due to the continue/return logic above
        return {
            "status": "error",
            "step_name": step_name,
            "error": "max_retries_exceeded",
            "message": f"Step {step_name} failed after {max_retries + 1} attempts",
            "timestamp": datetime.now().isoformat()
        }
    
    async def cleanup_workflow_state(self, operation_id: str) -> bool:
        """
        Remove workflow state for testing/cleanup purposes.
        
        Args:
            operation_id: The operation ID to clean up
            
        Returns:
            True if state was cleaned up, False if not found
        """
        try:
            state_key = f"stepwise_phase_one:{operation_id}"
            
            # Check if state exists
            state_entry = await self.phase_one._state_manager.get_state(state_key, "STATE")
            if not state_entry:
                self.logger.debug(f"No workflow state found for operation_id: {operation_id}")
                return False
            
            # Remove the state
            await self.phase_one._state_manager.delete_state(state_key, "STATE")
            self.logger.info(f"Cleaned up workflow state for operation_id: {operation_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error cleaning up workflow state for {operation_id}: {e}", exc_info=True)
            return False
    
    async def reset_all_workflow_states(self) -> bool:
        """
        Reset all workflow states - for testing only.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get all workflow states
            all_states = await self.phase_one._state_manager.get_all_states()
            
            workflow_keys = []
            for key in all_states:
                if key.startswith("stepwise_phase_one:"):
                    workflow_keys.append(key)
            
            # Delete all workflow states
            for key in workflow_keys:
                await self.phase_one._state_manager.delete_state(key, "STATE")
            
            self.logger.info(f"Reset {len(workflow_keys)} workflow states")
            return True
            
        except Exception as e:
            self.logger.error(f"Error resetting workflow states: {e}", exc_info=True)
            return False
    
    async def verify_clean_state(self) -> bool:
        """
        Verify no workflow states exist - for test verification.
        
        Returns:
            True if no workflow states exist, False otherwise
        """
        try:
            all_states = await self.phase_one._state_manager.get_all_states()
            
            workflow_keys = [key for key in all_states if key.startswith("stepwise_phase_one:")]
            
            if workflow_keys:
                self.logger.warning(f"Found {len(workflow_keys)} workflow states still present: {workflow_keys}")
                return False
                
            self.logger.debug("Verified clean state - no workflow states present")
            return True
            
        except Exception as e:
            self.logger.error(f"Error verifying clean state: {e}", exc_info=True)
            return False