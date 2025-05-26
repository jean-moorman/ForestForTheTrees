"""
Component guideline validation module for handling guideline update requests from subphase 2a agents.

This module implements validation for component guideline agents, supporting self-correction pathways.
"""
import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple, Literal
from datetime import datetime

from resources import (
    EventQueue, 
    StateManager, 
    MetricsManager, 
    ResourceType, 
    ResourceEventTypes
)
from interface import AgentInterface
from phase_one.models.enums import PhaseValidationState, GuidelineUpdateState
from phase_one.validation.refinement_manager import RefinementManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define revision pathways
RevisionPathway = Literal["SELF_CORRECTION"]

class ComponentGuidelineValidator:
    """
    Manages component guideline update requests and validation for subphase 2a agents.
    
    This handler works alongside the standard validators to handle self-correction pathway.
    Earth agent functionality has been modified, and Water agent propagation functionality
    has been removed while keeping coordination functionality intact.
    
    Key features:
    1. Support for self-correction pathway
    2. Tracking and metrics for validation
    """
    
    def __init__(
        self,
        resource_manager: StateManager,
        event_queue: EventQueue,
        refinement_manager: RefinementManager,
        metrics_manager: Optional[MetricsManager] = None
    ):
        self.resource_manager = resource_manager
        self.event_queue = event_queue
        self.refinement_manager = refinement_manager
        self.metrics_manager = metrics_manager or MetricsManager(event_queue)
        
        # Track guideline update requests
        self._guideline_updates = {}
        
        # Track self-correction requests
        self._self_corrections = {}
        
        # Track validation stats
        self._update_stats = {
            "total_requests": 0,
            "approved": 0,
            "corrected": 0,
            "rejected": 0
        }
        
        # Track dual pathway stats
        self._pathway_stats = {
            "SELF_CORRECTION": {
                "total": 0,
                "success": 0,
                "failure": 0
            },
            "GUIDELINE_UPDATE": {
                "total": 0,
                "success": 0,
                "failure": 0
            }
        }
    
    async def process_reflection_outcome(
        self,
        agent_id: str,
        component_id: str,
        output: Dict[str, Any],
        reflection_result: Dict[str, Any],
        revision_pathway: RevisionPathway,
        original_context: Optional[Dict[str, Any]] = None,
        operation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process reflection outcome and route to the appropriate pathway.
        
        This is the main entry point for handling reflection results from
        component guideline agents based on their bifurcation decision.
        
        Args:
            agent_id: ID of the agent that generated the reflection
            component_id: ID of the component being processed
            output: Original agent output
            reflection_result: Reflection analysis output
            revision_pathway: The determined revision pathway (SELF_CORRECTION or GUIDELINE_UPDATE)
            original_context: Optional original context for the agent
            operation_id: Optional operation ID for tracking
            
        Returns:
            Dict containing processing result
        """
        logger.info(f"Processing reflection outcome from {agent_id} for component {component_id} with pathway {revision_pathway}")
        
        # Generate operation ID if not provided
        if not operation_id:
            operation_id = f"reflection_{agent_id}_{component_id}_{datetime.now().isoformat()}"
            
        # Track pathway stats
        self._pathway_stats[revision_pathway]["total"] += 1
        
        # Record metric for the pathway decision
        await self.metrics_manager.record_metric(
            "phase_two:component_guideline:reflection_processed",
            1.0,
            metadata={
                "agent_id": agent_id,
                "component_id": component_id,
                "pathway": revision_pathway,
                "operation_id": operation_id,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # Route based on pathway
        if revision_pathway == "SELF_CORRECTION":
            return await self.handle_agent_self_correction(
                agent_id=agent_id,
                component_id=component_id,
                output=output,
                reflection_result=reflection_result,
                original_context=original_context,
                operation_id=operation_id
            )
        else:  # GUIDELINE_UPDATE
            return await self.handle_guideline_update_request(
                agent_id=agent_id,
                component_id=component_id,
                output=output,
                reflection_result=reflection_result,
                original_context=original_context,
                operation_id=operation_id
            )
    
    async def handle_agent_self_correction(
        self,
        agent_id: str,
        component_id: str,
        output: Dict[str, Any],
        reflection_result: Dict[str, Any],
        original_context: Optional[Dict[str, Any]] = None,
        operation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Handle the self-correction pathway for a component guideline agent.
        
        Args:
            agent_id: ID of the agent
            component_id: ID of the component
            output: Original agent output
            reflection_result: Reflection analysis output
            original_context: Optional original context for the agent
            operation_id: Optional operation ID for tracking
            
        Returns:
            Dict containing processing result
        """
        logger.info(f"Handling self-correction pathway for agent {agent_id} on component {component_id}")
        
        # Generate operation ID if not provided
        if not operation_id:
            operation_id = f"self_correction_{agent_id}_{component_id}_{datetime.now().isoformat()}"
            
        # Create self-correction record
        correction_id = f"component_self_correction:{agent_id}:{operation_id}"
        
        correction_data = {
            "agent_id": agent_id,
            "component_id": component_id,
            "operation_id": operation_id,
            "original_output": output,
            "reflection_result": reflection_result,
            "original_context": original_context,
            "status": "in_progress",
            "timestamp": datetime.now().isoformat(),
            "completion_timestamp": None,
            "success": None,
            "revised_output": None
        }
        
        # Store in state manager
        await self.resource_manager.set_state(
            correction_id,
            correction_data,
            ResourceType.STATE
        )
        
        # Store in memory
        self._self_corrections[correction_id] = correction_data
        
        # Emit event for self-correction start
        await self.event_queue.emit(
            ResourceEventTypes.COMPONENT_GUIDELINE_SELF_CORRECTION_STARTED.value,
            {
                "correction_id": correction_id,
                "agent_id": agent_id,
                "component_id": component_id,
                "operation_id": operation_id,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # Record start metric
        await self.metrics_manager.record_metric(
            "phase_two:component_guideline:self_correction_started",
            1.0,
            metadata={
                "agent_id": agent_id,
                "component_id": component_id,
                "operation_id": operation_id,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # Return the correction data for the agent to handle
        return {
            "correction_id": correction_id,
            "status": "in_progress",
            "pathway": "SELF_CORRECTION",
            "reflection_result": reflection_result,
            "original_output": output,
            "timestamp": datetime.now().isoformat()
        }
    
    async def record_self_correction_result(
        self,
        correction_id: str,
        revised_output: Dict[str, Any],
        success: bool
    ) -> Dict[str, Any]:
        """
        Record the result of a self-correction operation.
        
        Args:
            correction_id: ID of the self-correction operation
            revised_output: The revised output from the agent
            success: Whether the self-correction was successful
            
        Returns:
            Dict containing updated correction data
        """
        # Check if correction exists
        if correction_id not in self._self_corrections:
            # Try to load from state manager
            try:
                state = await self.resource_manager.get_state(correction_id)
                if state and hasattr(state, 'state'):
                    self._self_corrections[correction_id] = state.state
            except Exception as e:
                logger.error(f"Error fetching self-correction record {correction_id}: {str(e)}")
                return {
                    "error": f"Self-correction record {correction_id} not found",
                    "status": "error",
                    "timestamp": datetime.now().isoformat()
                }
        
        # Get correction data
        if correction_id not in self._self_corrections:
            return {
                "error": f"Self-correction record {correction_id} not found",
                "status": "error",
                "timestamp": datetime.now().isoformat()
            }
        
        correction_data = self._self_corrections[correction_id]
        
        # Update correction data
        correction_data["status"] = "completed"
        correction_data["completion_timestamp"] = datetime.now().isoformat()
        correction_data["success"] = success
        correction_data["revised_output"] = revised_output
        
        # Update in state manager
        await self.resource_manager.set_state(
            correction_id,
            correction_data,
            ResourceType.STATE
        )
        
        # Update in memory
        self._self_corrections[correction_id] = correction_data
        
        # Update pathway stats
        if success:
            self._pathway_stats["SELF_CORRECTION"]["success"] += 1
        else:
            self._pathway_stats["SELF_CORRECTION"]["failure"] += 1
        
        # Emit event for self-correction completion
        await self.event_queue.emit(
            ResourceEventTypes.COMPONENT_GUIDELINE_SELF_CORRECTION_COMPLETED.value,
            {
                "correction_id": correction_id,
                "agent_id": correction_data["agent_id"],
                "component_id": correction_data["component_id"],
                "operation_id": correction_data["operation_id"],
                "success": success,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # Record completion metric
        await self.metrics_manager.record_metric(
            "phase_two:component_guideline:self_correction_completed",
            1.0,
            metadata={
                "agent_id": correction_data["agent_id"],
                "component_id": correction_data["component_id"],
                "operation_id": correction_data["operation_id"],
                "success": success,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        return correction_data
    
    async def handle_guideline_update_request(
        self,
        agent_id: str,
        component_id: str,
        output: Dict[str, Any],
        reflection_result: Dict[str, Any],
        original_context: Optional[Dict[str, Any]] = None,
        operation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Handle the guideline update pathway for a component guideline agent.
        
        This function:
        1. Registers the update request
        2. Extracts current and proposed guidelines
        3. Initiates Earth agent validation
        
        Args:
            agent_id: ID of the agent
            component_id: ID of the component
            output: Original agent output
            reflection_result: Reflection analysis output
            original_context: Optional original context for the agent
            operation_id: Optional operation ID for tracking
            
        Returns:
            Dict containing processing result
        """
        logger.info(f"Handling guideline update pathway for agent {agent_id} on component {component_id}")
        
        # Extract current and proposed guidelines from reflection
        current_guideline, proposed_update = await self._extract_guideline_update(
            output, 
            reflection_result,
            original_context
        )
        
        # Ensure component_id is included
        if "component_id" not in current_guideline:
            current_guideline["component_id"] = component_id
        if "component_id" not in proposed_update:
            proposed_update["component_id"] = component_id
        
        # Register the update request
        registration_result = await self.register_guideline_update_request(
            agent_id=agent_id,
            component_id=component_id,
            operation_id=operation_id,
            current_guideline=current_guideline,
            proposed_update=proposed_update,
            reflection_result=reflection_result
        )
        
        # Get the request ID from registration
        request_id = registration_result.get("request_id")
        
        # Start the validation process
        validation_result = await self.validate_guideline_update(request_id)
        
        # Return the result
        return {
            "request_id": request_id,
            "status": validation_result.get("status"),
            "pathway": "GUIDELINE_UPDATE",
            "validation_result": validation_result.get("validation_result"),
            "timestamp": datetime.now().isoformat()
        }
    
    async def _extract_guideline_update(
        self,
        output: Dict[str, Any],
        reflection_result: Dict[str, Any],
        original_context: Optional[Dict[str, Any]] = None
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Extract current guideline and proposed updates from reflection.
        
        Args:
            output: Original agent output
            reflection_result: Reflection analysis  
            original_context: Optional original context
            
        Returns:
            Tuple of (current_guideline, proposed_update)
        """
        # Default current guideline from original context
        current_guideline = {}
        if original_context and isinstance(original_context, dict):
            current_guideline = original_context
        
        # Try to extract current guideline from reflection result
        if "reflection_results" in reflection_result:
            reflection_data = reflection_result["reflection_results"]
            if "current_guideline" in reflection_data:
                current_guideline = reflection_data["current_guideline"]
        
        # Extract proposed update from reflection result
        proposed_update = {}
        if "reflection_results" in reflection_result:
            reflection_data = reflection_result["reflection_results"]
            
            # Direct extraction if available
            if "proposed_guideline_update" in reflection_data:
                proposed_update = reflection_data["proposed_guideline_update"]
            elif "guideline_update_proposal" in reflection_data:
                proposed_update = reflection_data["guideline_update_proposal"]
            else:
                # Fall back to using the output as proposed update
                proposed_update = output
                
                # Try to extract specific updates from reflection analysis
                if "input_quality_assessment" in reflection_data:
                    input_quality = reflection_data["input_quality_assessment"]
                    if "proposed_changes" in input_quality:
                        # Apply changes to current guideline
                        proposed_update = {**current_guideline}  # Create copy
                        for change in input_quality["proposed_changes"]:
                            if "field" in change and "new_value" in change:
                                proposed_update[change["field"]] = change["new_value"]
        
        return current_guideline, proposed_update
        
    async def register_guideline_update_request(
        self,
        agent_id: str,
        component_id: str,
        operation_id: str,
        current_guideline: Dict[str, Any],
        proposed_update: Dict[str, Any],
        reflection_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Register a new component guideline update request from a subphase 2a agent.
        
        Args:
            agent_id: ID of the requesting agent
            component_id: ID of the component being updated
            operation_id: Operation ID for tracking
            current_guideline: Current component guideline state
            proposed_update: Proposed component guideline update
            reflection_result: Agent reflection result
            
        Returns:
            Dict containing registration result
        """
        logger.info(f"Registering component guideline update request from {agent_id} for component {component_id}")
        
        # Generate operation ID if not provided
        if not operation_id:
            operation_id = f"guideline_update_{agent_id}_{component_id}_{datetime.now().isoformat()}"
        
        # Create update request entry
        request_id = f"component_guideline_update:{agent_id}:{operation_id}"
        
        request_data = {
            "agent_id": agent_id,
            "component_id": component_id,
            "operation_id": operation_id,
            "abstraction_tier": "COMPONENT",
            "current_guideline": current_guideline,
            "proposed_update": proposed_update,
            "reflection_result": reflection_result,
            "status": GuidelineUpdateState.PENDING.value,
            "timestamp": datetime.now().isoformat(),
            "validation_result": None,
            "validation_timestamp": None
        }
        
        # Store in state manager
        await self.resource_manager.set_state(
            request_id,
            request_data,
            ResourceType.STATE
        )
        
        # Store in memory
        self._guideline_updates[request_id] = request_data
        
        # Update stats
        self._update_stats["total_requests"] += 1
        
        # Emit event
        await self.event_queue.emit(
            ResourceEventTypes.SUBPHASE_2A_GUIDELINE_UPDATE_REQUESTED.value,
            {
                "request_id": request_id,
                "agent_id": agent_id,
                "component_id": component_id,
                "operation_id": operation_id,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # Record metrics
        await self.metrics_manager.record_metric(
            "phase_two:component_guideline:update:registered",
            1.0,
            metadata={
                "agent_id": agent_id,
                "component_id": component_id,
                "operation_id": operation_id,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        return {
            "request_id": request_id,
            "status": GuidelineUpdateState.PENDING.value,
            "message": "Component guideline update request registered successfully",
            "timestamp": datetime.now().isoformat()
        }
    
    async def validate_guideline_update(self, request_id: str) -> Dict[str, Any]:
        """
        Validate a pending component guideline update request using the Earth agent.
        
        Args:
            request_id: Request ID to validate
            
        Returns:
            Dict containing validation result
        """
        # Check if request exists
        if request_id not in self._guideline_updates:
            logger.error(f"Component guideline update request {request_id} not found")
            return {
                "error": f"Component guideline update request {request_id} not found",
                "status": "error",
                "timestamp": datetime.now().isoformat()
            }
        
        # Get request data
        request = self._guideline_updates[request_id]
        
        # Check if already validated
        if request["status"] != GuidelineUpdateState.PENDING.value:
            logger.warning(f"Component guideline update request {request_id} already validated with status {request['status']}")
            return {
                "warning": f"Component guideline update request {request_id} already validated",
                "status": request["status"],
                "validation_result": request.get("validation_result"),
                "timestamp": datetime.now().isoformat()
            }
        
        # Update status to validating
        await self._update_request_status(request_id, GuidelineUpdateState.VALIDATING)
        
        try:
            # Validate using Earth agent
            validation_start_time = datetime.now()
            
            validation_result = await self.earth_agent.validate_subphase_2a_guideline_update(
                agent_id=request["agent_id"],
                component_id=request["component_id"],
                current_guideline=request["current_guideline"],
                proposed_update=request["proposed_update"],
                operation_id=request["operation_id"],
                reflection_result=request["reflection_result"]
            )
            
            # Calculate duration
            duration = (datetime.now() - validation_start_time).total_seconds()
            
            # Update request with validation result
            validation_category = validation_result.get("validation_result", {}).get("validation_category", "REJECTED")
            is_valid = validation_result.get("validation_result", {}).get("is_valid", False)
            
            # Determine new status based on validation result
            if is_valid:
                if validation_category == "APPROVED":
                    new_status = GuidelineUpdateState.APPROVED
                    self._update_stats["approved"] += 1
                else:  # CORRECTED
                    new_status = GuidelineUpdateState.CORRECTED
                    self._update_stats["corrected"] += 1
            else:
                new_status = GuidelineUpdateState.REJECTED
                self._update_stats["rejected"] += 1
            
            # Update request
            await self._update_request_with_validation(
                request_id, 
                validation_result, 
                new_status
            )
            
            # Record metrics
            await self.metrics_manager.record_metric(
                "phase_two:component_guideline:update:validated",
                duration,
                metadata={
                    "agent_id": request["agent_id"],
                    "component_id": request["component_id"],
                    "operation_id": request["operation_id"],
                    "validation_category": validation_category,
                    "is_valid": is_valid,
                    "status": new_status.value,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            # Emit event
            await self.event_queue.emit(
                ResourceEventTypes.SUBPHASE_2A_GUIDELINE_UPDATE_VALIDATED.value,
                {
                    "request_id": request_id,
                    "agent_id": request["agent_id"],
                    "component_id": request["component_id"],
                    "operation_id": request["operation_id"],
                    "validation_category": validation_category,
                    "is_valid": is_valid,
                    "status": new_status.value,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            # Update pathway stats
            if is_valid:
                self._pathway_stats["GUIDELINE_UPDATE"]["success"] += 1
            else:
                self._pathway_stats["GUIDELINE_UPDATE"]["failure"] += 1
            
            # Automatically process approved updates if needed (water agent propagation removed)
            if is_valid:
                logger.info(f"Skipping propagation for {request_id} as water agent propagation has been removed")
                # No propagation will be performed, but we can still update status to propagated
                await self._update_request_status(request_id, GuidelineUpdateState.PROPAGATED)
            
            return {
                "request_id": request_id,
                "status": new_status.value,
                "validation_result": validation_result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error validating component guideline update request {request_id}: {str(e)}")
            
            # Update status to error
            await self._update_request_status(request_id, GuidelineUpdateState.ERROR)
            
            # Update pathway stats
            self._pathway_stats["GUIDELINE_UPDATE"]["failure"] += 1
            
            return {
                "error": f"Validation error: {str(e)}",
                "status": GuidelineUpdateState.ERROR.value,
                "request_id": request_id,
                "timestamp": datetime.now().isoformat()
            }
    
    async def _update_request_status(self, request_id: str, new_status: GuidelineUpdateState) -> None:
        """Update the status of a component guideline update request."""
        if request_id in self._guideline_updates:
            self._guideline_updates[request_id]["status"] = new_status.value
            self._guideline_updates[request_id]["status_updated_at"] = datetime.now().isoformat()
            
            # Update in state manager
            await self.resource_manager.set_state(
                request_id,
                self._guideline_updates[request_id],
                ResourceType.STATE
            )
    
    async def _update_request_with_validation(
        self, 
        request_id: str, 
        validation_result: Dict[str, Any],
        new_status: GuidelineUpdateState
    ) -> None:
        """Update a request with validation result."""
        if request_id in self._guideline_updates:
            self._guideline_updates[request_id]["validation_result"] = validation_result
            self._guideline_updates[request_id]["validation_timestamp"] = datetime.now().isoformat()
            self._guideline_updates[request_id]["status"] = new_status.value
            self._guideline_updates[request_id]["status_updated_at"] = datetime.now().isoformat()
            
            # Update in state manager
            await self.resource_manager.set_state(
                request_id,
                self._guideline_updates[request_id],
                ResourceType.STATE
            )
    
    async def get_update_request(self, request_id: str) -> Dict[str, Any]:
        """
        Get a component guideline update request by ID.
        
        Args:
            request_id: Request ID
            
        Returns:
            Dict containing request data or error
        """
        if request_id in self._guideline_updates:
            return self._guideline_updates[request_id]
        
        # Try to fetch from state manager
        try:
            state = await self.resource_manager.get_state(request_id)
            if state and hasattr(state, 'state'):
                self._guideline_updates[request_id] = state.state
                return state.state
        except Exception as e:
            logger.error(f"Error fetching component guideline update request {request_id}: {str(e)}")
        
        return {
            "error": f"Component guideline update request {request_id} not found",
            "status": "error",
            "timestamp": datetime.now().isoformat()
        }
    
    async def process_approved_update(self, request_id: str) -> Dict[str, Any]:
        """
        Process an approved component guideline update for propagation.
        
        Note: This is a stub implementation as the Water propagation mechanism has been removed.
        It always returns success without actually propagating anything.
        
        Args:
            request_id: Request ID to process
            
        Returns:
            Dict containing processing result
        """
        # Get request
        request = await self.get_update_request(request_id)
        
        # Check if error
        if "error" in request:
            return request
        
        # Check if approved or corrected
        if request["status"] not in [
            GuidelineUpdateState.APPROVED.value, 
            GuidelineUpdateState.CORRECTED.value
        ]:
            return {
                "error": f"Component guideline update request {request_id} is not approved or corrected",
                "status": request["status"],
                "timestamp": datetime.now().isoformat()
            }
        
        # Update status to propagating
        await self._update_request_status(request_id, GuidelineUpdateState.PROPAGATING)
        
        try:
            # Determine the final guideline update
            validation_result = request["validation_result"]
            validation_category = validation_result.get("validation_result", {}).get("validation_category", "REJECTED")
            
            if validation_category == "APPROVED":
                # Use proposed update directly
                final_update = request["proposed_update"]
            else:  # CORRECTED
                # Use corrected update from Earth
                final_update = validation_result.get("corrected_update", request["proposed_update"])
            
            # Emit event for guideline update propagation
            await self.event_queue.emit(
                ResourceEventTypes.SUBPHASE_2A_GUIDELINE_UPDATE_PROPAGATING.value,
                {
                    "request_id": request_id,
                    "agent_id": request["agent_id"],
                    "component_id": request["component_id"],
                    "operation_id": request["operation_id"],
                    "validation_category": validation_category,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            # Log that propagation is being skipped
            logger.info(f"Skipping water propagation for {request_id} as propagation functionality has been removed")
            
            # Just update status to propagated
            await self._update_request_status(request_id, GuidelineUpdateState.PROPAGATED)
            
            # Record metrics
            await self.metrics_manager.record_metric(
                "phase_two:component_guideline:update:propagated",
                1.0,
                metadata={
                    "agent_id": request["agent_id"],
                    "component_id": request["component_id"],
                    "operation_id": request["operation_id"],
                    "validation_category": validation_category,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            # Emit event for completed propagation (even though it's a stub)
            await self.event_queue.emit(
                ResourceEventTypes.SUBPHASE_2A_GUIDELINE_UPDATE_PROPAGATED.value,
                {
                    "request_id": request_id,
                    "agent_id": request["agent_id"],
                    "component_id": request["component_id"],
                    "operation_id": request["operation_id"],
                    "validation_category": validation_category,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            return {
                "request_id": request_id,
                "status": GuidelineUpdateState.PROPAGATED.value,
                "message": "Component guideline update marked as propagated (stub implementation)",
                "timestamp": datetime.now().isoformat(),
                "final_update": final_update,
                "metadata": {
                    "warning": "Water propagation functionality has been removed. This is a stub implementation."
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing approved component guideline update {request_id}: {str(e)}")
            
            # Update status to error
            await self._update_request_status(request_id, GuidelineUpdateState.ERROR)
            
            return {
                "error": f"Propagation error: {str(e)}",
                "status": GuidelineUpdateState.ERROR.value,
                "request_id": request_id,
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_update_requests_by_component(self, component_id: str) -> List[Dict[str, Any]]:
        """
        Get all component guideline update requests for a specific component.
        
        Args:
            component_id: Component ID
            
        Returns:
            List of request data dictionaries
        """
        results = []
        
        # Filter in-memory requests
        for request_id, request in self._guideline_updates.items():
            if request["component_id"] == component_id:
                results.append(request)
        
        # Try to fetch additional requests from state manager
        try:
            states = await self.resource_manager.get_states_by_prefix(f"component_guideline_update:")
            
            for state_key, state in states.items():
                if hasattr(state, 'state') and state_key not in self._guideline_updates:
                    if state.state.get("component_id") == component_id:
                        self._guideline_updates[state_key] = state.state
                        results.append(state.state)
        except Exception as e:
            logger.error(f"Error fetching component guideline update requests for component {component_id}: {str(e)}")
        
        return results
    
    async def get_update_requests_by_agent(self, agent_id: str) -> List[Dict[str, Any]]:
        """
        Get all component guideline update requests for a specific agent.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            List of request data dictionaries
        """
        results = []
        
        # Filter in-memory requests
        for request_id, request in self._guideline_updates.items():
            if request["agent_id"] == agent_id:
                results.append(request)
        
        # Try to fetch additional requests from state manager
        try:
            states = await self.resource_manager.get_states_by_prefix(f"component_guideline_update:{agent_id}:")
            
            for state_key, state in states.items():
                if hasattr(state, 'state') and state_key not in self._guideline_updates:
                    self._guideline_updates[state_key] = state.state
                    results.append(state.state)
        except Exception as e:
            logger.error(f"Error fetching component guideline update requests for agent {agent_id}: {str(e)}")
        
        return results
    
    async def get_self_corrections_by_component(self, component_id: str) -> List[Dict[str, Any]]:
        """
        Get all self-correction operations for a specific component.
        
        Args:
            component_id: Component ID
            
        Returns:
            List of correction data dictionaries
        """
        results = []
        
        # Filter in-memory corrections
        for correction_id, correction in self._self_corrections.items():
            if correction["component_id"] == component_id:
                results.append(correction)
        
        # Try to fetch additional corrections from state manager
        try:
            states = await self.resource_manager.get_states_by_prefix(f"component_self_correction:")
            
            for state_key, state in states.items():
                if hasattr(state, 'state') and state_key not in self._self_corrections:
                    if state.state.get("component_id") == component_id:
                        self._self_corrections[state_key] = state.state
                        results.append(state.state)
        except Exception as e:
            logger.error(f"Error fetching self-corrections for component {component_id}: {str(e)}")
        
        return results
    
    async def get_update_stats(self) -> Dict[str, Any]:
        """
        Get statistics for component guideline update requests.
        
        Returns:
            Dict containing update statistics
        """
        total = self._update_stats["total_requests"]
        approval_rate = 0.0
        
        if total > 0:
            approval_rate = (self._update_stats["approved"] + self._update_stats["corrected"]) / total
        
        # Calculate pathway success rates
        sc_total = self._pathway_stats["SELF_CORRECTION"]["total"]
        sc_success = self._pathway_stats["SELF_CORRECTION"]["success"]
        sc_success_rate = sc_success / sc_total if sc_total > 0 else 0.0
        
        gu_total = self._pathway_stats["GUIDELINE_UPDATE"]["total"]
        gu_success = self._pathway_stats["GUIDELINE_UPDATE"]["success"]
        gu_success_rate = gu_success / gu_total if gu_total > 0 else 0.0
        
        return {
            "update_stats": {
                "total_requests": total,
                "approved": self._update_stats["approved"],
                "corrected": self._update_stats["corrected"],
                "rejected": self._update_stats["rejected"],
                "approval_rate": approval_rate
            },
            "pathway_stats": {
                "SELF_CORRECTION": {
                    "total": sc_total,
                    "success": sc_success,
                    "failure": self._pathway_stats["SELF_CORRECTION"]["failure"],
                    "success_rate": sc_success_rate
                },
                "GUIDELINE_UPDATE": {
                    "total": gu_total,
                    "success": gu_success,
                    "failure": self._pathway_stats["GUIDELINE_UPDATE"]["failure"],
                    "success_rate": gu_success_rate
                }
            },
            "timestamp": datetime.now().isoformat()
        }