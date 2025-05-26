"""
Garden Planner validation coordinator for Earth Agent validation.

This module coordinates the validation process between the Garden Planner Agent
and Earth Agent, managing the feedback loop for refinement.
"""
import logging
import asyncio
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime

from resources import EventQueue, StateManager
from interfaces.agent.interface import AgentInterface
from phase_one.models.enums import DevelopmentState
from phase_one.models.refinement import RefinementContext

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GardenPlannerValidator:
    """
    Coordinates the validation process between Garden Planner and Earth Agent.
    
    Manages the feedback loop where:
    1. Garden Planner generates initial task analysis
    2. Earth Agent validates the analysis against user request
    3. If issues are found, Earth Agent provides feedback for refinement
    4. Garden Planner refines its output based on feedback
    5. Process repeats until validation passes or max iterations reached
    
    This validator ensures Garden Planner output meets quality standards before
    proceeding to the next Phase One agent (Environmental Analysis).
    """
    
    def __init__(
        self,
        garden_planner_agent: AgentInterface,
        earth_agent: AgentInterface,
        event_queue: EventQueue,
        state_manager: StateManager,
        max_refinement_cycles: int = 3,
        validation_timeout: float = 60.0
    ):
        """
        Initialize the Garden Planner validator.
        
        Args:
            garden_planner_agent: The Garden Planner agent
            earth_agent: The Earth Agent for validation
            event_queue: Event queue for publishing/subscribing to events
            state_manager: State manager for persistent state
            max_refinement_cycles: Maximum number of refinement cycles
            validation_timeout: Timeout for validation process in seconds
        """
        self.garden_planner_agent = garden_planner_agent
        self.earth_agent = earth_agent
        self.event_queue = event_queue
        self.state_manager = state_manager
        self.max_refinement_cycles = max_refinement_cycles
        self.validation_timeout = validation_timeout
        
        # Tracking for validation cycles
        self.current_cycle = 0
        self.validation_history = []
        
    async def validate_initial_task_analysis(
        self,
        user_request: str,
        initial_analysis: Dict[str, Any],
        operation_id: Optional[str] = None
    ) -> Tuple[bool, Dict[str, Any], List[Dict[str, Any]]]:
        """
        Validate the initial task analysis from Garden Planner against user request.
        
        Args:
            user_request: The original user request
            initial_analysis: The initial Garden Planner output
            operation_id: Optional identifier for this validation
            
        Returns:
            Tuple containing:
            - Boolean indicating if validation passed
            - Final Garden Planner output (original or refined)
            - List of validation history entries
        """
        # Reset validation tracking
        self.current_cycle = 0
        self.validation_history = []
        
        # Generate operation ID if not provided
        if not operation_id:
            operation_id = f"phase_one_validation_{datetime.now().isoformat()}"
        
        # Store initial analysis
        current_analysis = initial_analysis
        
        # Initialize validation tracking in state
        await self.state_manager.set_state(
            f"garden_planner_validation:{operation_id}",
            {
                "status": "in_progress",
                "current_cycle": 0,
                "start_time": datetime.now().isoformat(),
                "user_request": user_request
            },
            "STATE"
        )
        
        # Emit validation start event
        await self.event_queue.emit(
            "garden_planner_validation_started",
            {
                "operation_id": operation_id,
                "timestamp": datetime.now().isoformat(),
                "user_request_snippet": user_request[:100] + "..." if len(user_request) > 100 else user_request
            }
        )
        
        logger.info(f"Starting Garden Planner validation for operation {operation_id}")
        
        try:
            # Reset Earth Agent validation cycle counter
            await self.earth_agent.reset_validation_cycle_counter()
            
            # Process validation with timeout
            async with asyncio.timeout(self.validation_timeout):
                return await self._process_validation_cycles(
                    user_request,
                    current_analysis,
                    operation_id
                )
                
        except asyncio.TimeoutError:
            logger.error(f"Validation timeout exceeded for operation {operation_id}")
            
            # Update validation state
            await self.state_manager.set_state(
                f"garden_planner_validation:{operation_id}",
                {
                    "status": "timeout",
                    "current_cycle": self.current_cycle,
                    "end_time": datetime.now().isoformat(),
                    "error": "Validation timeout exceeded"
                },
                ResourceType="STATE"
            )
            
            # Emit validation timeout event
            await self.event_queue.emit(
                "garden_planner_validation_timeout",
                {
                    "operation_id": operation_id,
                    "cycles_completed": self.current_cycle,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            # Return the current analysis with timeout status
            return False, current_analysis, self.validation_history
            
        except Exception as e:
            logger.error(f"Validation error for operation {operation_id}: {str(e)}")
            
            # Update validation state
            await self.state_manager.set_state(
                f"garden_planner_validation:{operation_id}",
                {
                    "status": "error",
                    "current_cycle": self.current_cycle,
                    "end_time": datetime.now().isoformat(),
                    "error": str(e)
                },
                ResourceType="STATE"
            )
            
            # Emit validation error event
            await self.event_queue.emit(
                "garden_planner_validation_error",
                {
                    "operation_id": operation_id,
                    "error": str(e),
                    "cycles_completed": self.current_cycle,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            # Return the current analysis with error status
            return False, current_analysis, self.validation_history
    
    async def _process_validation_cycles(
        self,
        user_request: str,
        initial_analysis: Dict[str, Any],
        operation_id: str
    ) -> Tuple[bool, Dict[str, Any], List[Dict[str, Any]]]:
        """
        Process validation cycles until validation passes or max cycles reached.
        
        Args:
            user_request: The original user request
            initial_analysis: The initial Garden Planner output
            operation_id: Identifier for this validation
            
        Returns:
            Tuple containing:
            - Boolean indicating if validation passed
            - Final Garden Planner output (original or refined)
            - List of validation history entries
        """
        current_analysis = initial_analysis
        
        # Process validation cycles
        while self.current_cycle < self.max_refinement_cycles:
            # Increment cycle counter
            self.current_cycle += 1
            await self.earth_agent.increment_validation_cycle()
            
            logger.info(f"Starting validation cycle {self.current_cycle}/{self.max_refinement_cycles}")
            
            # Update validation state
            await self.state_manager.set_state(
                f"garden_planner_validation:{operation_id}",
                {
                    "status": "processing",
                    "current_cycle": self.current_cycle,
                    "cycle_start_time": datetime.now().isoformat()
                },
                ResourceType="STATE"
            )
            
            # Validate current analysis with Earth Agent
            validation_id = f"{operation_id}_cycle_{self.current_cycle}"
            validation_result = await self.earth_agent.validate_garden_planner_output(
                user_request,
                current_analysis,
                validation_id
            )
            
            # Track validation history
            self.validation_history.append({
                "cycle": self.current_cycle,
                "validation_id": validation_id,
                "timestamp": datetime.now().isoformat(),
                "validation_category": validation_result.get("validation_result", {}).get("validation_category", "UNKNOWN"),
                "issue_count": len(validation_result.get("architectural_issues", []))
            })
            
            # Update validation state with result
            await self.state_manager.set_state(
                f"garden_planner_validation:{operation_id}:cycle:{self.current_cycle}",
                {
                    "validation_result": validation_result,
                    "timestamp": datetime.now().isoformat()
                },
                ResourceType="STATE"
            )
            
            # Check validation category
            validation_category = validation_result.get("validation_result", {}).get("validation_category", "UNKNOWN")
            
            # If validation is APPROVED or we've reached max cycles, stop validation
            if validation_category == "APPROVED" or self.current_cycle >= self.max_refinement_cycles:
                is_valid = validation_category == "APPROVED"
                
                # For CORRECTED category, use the corrected output
                if validation_category == "CORRECTED" and "corrected_update" in validation_result:
                    current_analysis = validation_result["corrected_update"]
                    is_valid = True
                
                # Finalize validation
                await self._finalize_validation(operation_id, is_valid, validation_category)
                
                # Return final status and analysis
                return is_valid, current_analysis, self.validation_history
            
            # For REJECTED, refine with Garden Planner
            if validation_category == "REJECTED":
                # Prepare refinement guidance
                refinement_guidance = self._create_refinement_guidance(validation_result)
                
                # Process refinement with Garden Planner
                refined_analysis = await self._refine_garden_planner_output(
                    current_analysis,
                    refinement_guidance,
                    operation_id
                )
                
                # Update current analysis for next cycle
                current_analysis = refined_analysis
                
                # Continue to next validation cycle
                continue
            
            # Unexpected validation category
            logger.warning(f"Unexpected validation category: {validation_category}")
            await self._finalize_validation(operation_id, False, validation_category)
            return False, current_analysis, self.validation_history
        
        # Max cycles reached without approval
        logger.warning(f"Max validation cycles ({self.max_refinement_cycles}) reached without approval")
        await self._finalize_validation(operation_id, False, "MAX_CYCLES_REACHED")
        return False, current_analysis, self.validation_history
    
    async def _refine_garden_planner_output(
        self,
        current_analysis: Dict[str, Any],
        refinement_guidance: Dict[str, Any],
        operation_id: str
    ) -> Dict[str, Any]:
        """
        Refine Garden Planner output based on Earth Agent feedback.
        
        Args:
            current_analysis: Current Garden Planner analysis
            refinement_guidance: Refinement guidance from Earth Agent
            operation_id: Identifier for this validation
            
        Returns:
            Refined Garden Planner output
        """
        try:
            # Create refinement context for Garden Planner
            refinement_context = RefinementContext(
                original_output=current_analysis,
                refinement_guidance=refinement_guidance,
                iteration=self.current_cycle,
                timestamp=datetime.now().isoformat()
            )
            
            # Add refinement context to validation state
            await self.state_manager.set_state(
                f"garden_planner_validation:{operation_id}:refinement:{self.current_cycle}",
                refinement_context.to_dict(),
                ResourceType="STATE"
            )
            
            # Reset Garden Planner state to start fresh
            self.garden_planner_agent.development_state = DevelopmentState.REFINING
            
            # Process refinement with Garden Planner
            refined_output = await self.garden_planner_agent.refine(
                current_analysis,
                refinement_guidance
            )
            
            # Add refinement result to validation state
            await self.state_manager.set_state(
                f"garden_planner_validation:{operation_id}:refinement_result:{self.current_cycle}",
                {
                    "refined_output": refined_output,
                    "timestamp": datetime.now().isoformat()
                },
                ResourceType="STATE"
            )
            
            return refined_output
            
        except Exception as e:
            logger.error(f"Error refining Garden Planner output: {str(e)}")
            
            # If refinement fails, return the original analysis
            return current_analysis
    
    def _create_refinement_guidance(self, validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create refinement guidance from Earth Agent validation result.
        
        Args:
            validation_result: Earth Agent validation result
            
        Returns:
            Refinement guidance for Garden Planner
        """
        # Extract relevant information from validation result
        validation_category = validation_result.get("validation_result", {}).get("validation_category", "UNKNOWN")
        explanation = validation_result.get("validation_result", {}).get("explanation", "")
        issues = validation_result.get("architectural_issues", [])
        
        # Group issues by severity
        issues_by_severity = {
            "CRITICAL": [],
            "HIGH": [],
            "MEDIUM": [],
            "LOW": []
        }
        
        for issue in issues:
            severity = issue.get("severity", "UNKNOWN")
            if severity in issues_by_severity:
                issues_by_severity[severity].append(issue)
        
        # Create refinement guidance
        return {
            "validation_category": validation_category,
            "explanation": explanation,
            "total_issues": len(issues),
            "critical_count": len(issues_by_severity["CRITICAL"]),
            "high_count": len(issues_by_severity["HIGH"]),
            "medium_count": len(issues_by_severity["MEDIUM"]),
            "low_count": len(issues_by_severity["LOW"]),
            "issues_by_severity": {
                "critical": issues_by_severity["CRITICAL"],
                "high": issues_by_severity["HIGH"],
                "medium": issues_by_severity["MEDIUM"],
                "low": issues_by_severity["LOW"]
            },
            "focus_areas": self._extract_focus_areas(issues_by_severity),
            "revision_cycle": self.current_cycle,
            "timestamp": datetime.now().isoformat()
        }
    
    def _extract_focus_areas(self, issues_by_severity: Dict[str, List[Dict[str, Any]]]) -> List[str]:
        """
        Extract focus areas from issues grouped by severity.
        
        Args:
            issues_by_severity: Issues grouped by severity
            
        Returns:
            List of focus areas for refinement
        """
        focus_areas = set()
        
        # Prioritize CRITICAL and HIGH issues for focus areas
        for severity in ["CRITICAL", "HIGH"]:
            for issue in issues_by_severity[severity]:
                # Add affected areas to focus areas
                affected_areas = issue.get("affected_areas", [])
                focus_areas.update(affected_areas)
                
                # Add issue type to focus areas
                issue_type = issue.get("issue_type", "")
                if issue_type:
                    focus_areas.add(issue_type)
        
        # If no CRITICAL or HIGH issues, check MEDIUM issues
        if not focus_areas and issues_by_severity["MEDIUM"]:
            for issue in issues_by_severity["MEDIUM"]:
                affected_areas = issue.get("affected_areas", [])
                focus_areas.update(affected_areas)
        
        return list(focus_areas)
    
    async def _finalize_validation(self, operation_id: str, is_valid: bool, validation_category: str):
        """
        Finalize validation process and update state.
        
        Args:
            operation_id: Identifier for this validation
            is_valid: Boolean indicating if validation passed
            validation_category: Validation category from Earth Agent
        """
        # Update validation state
        await self.state_manager.set_state(
            f"garden_planner_validation:{operation_id}",
            {
                "status": "completed",
                "is_valid": is_valid,
                "validation_category": validation_category,
                "cycles_completed": self.current_cycle,
                "end_time": datetime.now().isoformat()
            },
            ResourceType="STATE"
        )
        
        # Emit validation completed event
        await self.event_queue.emit(
            "garden_planner_validation_completed",
            {
                "operation_id": operation_id,
                "is_valid": is_valid,
                "validation_category": validation_category,
                "cycles_completed": self.current_cycle,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        logger.info(f"Garden Planner validation completed for operation {operation_id}")
        logger.info(f"Validation result: {is_valid}, Category: {validation_category}, Cycles: {self.current_cycle}")
        
    async def get_validation_status(self, operation_id: str) -> Dict[str, Any]:
        """
        Get current validation status for an operation.
        
        Args:
            operation_id: Identifier for the validation
            
        Returns:
            Validation status information
        """
        # Get validation state
        validation_state = await self.state_manager.get_state(
            f"garden_planner_validation:{operation_id}",
            ResourceType="STATE"
        )
        
        # If no state found, return unknown status
        if not validation_state:
            return {
                "status": "unknown",
                "operation_id": operation_id,
                "timestamp": datetime.now().isoformat()
            }
        
        # Get validation history
        history = []
        for cycle in range(1, validation_state.get("cycles_completed", 0) + 1):
            cycle_state = await self.state_manager.get_state(
                f"garden_planner_validation:{operation_id}:cycle:{cycle}",
                ResourceType="STATE"
            )
            
            if cycle_state:
                validation_result = cycle_state.get("validation_result", {})
                history.append({
                    "cycle": cycle,
                    "timestamp": cycle_state.get("timestamp", ""),
                    "validation_category": validation_result.get("validation_result", {}).get("validation_category", "UNKNOWN"),
                    "issue_count": len(validation_result.get("architectural_issues", []))
                })
        
        # Return comprehensive status
        return {
            "status": validation_state.get("status", "unknown"),
            "is_valid": validation_state.get("is_valid", False),
            "validation_category": validation_state.get("validation_category", "UNKNOWN"),
            "cycles_completed": validation_state.get("cycles_completed", 0),
            "start_time": validation_state.get("start_time", ""),
            "end_time": validation_state.get("end_time", ""),
            "error": validation_state.get("error", None),
            "history": history,
            "operation_id": operation_id,
            "timestamp": datetime.now().isoformat()
        }