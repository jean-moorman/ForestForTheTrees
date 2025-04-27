"""
Validation module for phase one deliverables.
"""
import logging
from typing import Dict, Any, List, Protocol
from datetime import datetime

from resources import EventQueue, StateManager
from dependency import DependencyValidator
from interface import AgentInterface
from phase_one.models.enums import PhaseValidationState

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PhaseZeroInterface(Protocol):
    """Interface for interacting with Phase Zero agents"""
    async def process_system_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        pass
        
class PhaseOneValidator:
    """
    Manages the sequential validation process for phase one deliverables.
    
    Handles:
    1. Data flow validation from Root System Architect
    2. Structural breakdown validation from Tree Placement Planner
    3. Cross-consistency validation between the two
    4. Arbitration via Garden Foundation Refinement Agent when conflicts occur
    """
    
    def __init__(
        self, 
        resource_manager: StateManager,
        event_queue: EventQueue, 
        root_system_agent: AgentInterface,
        tree_placement_agent: AgentInterface,
        foundation_refinement_agent: AgentInterface
    ):
        self.resource_manager = resource_manager
        self.event_queue = event_queue
        self.root_system_agent = root_system_agent
        self.tree_placement_agent = tree_placement_agent
        self.foundation_refinement_agent = foundation_refinement_agent
        
        # Create dependency validator
        self.dependency_validator = DependencyValidator(resource_manager)
        
        # Initialize validation state
        self.validation_state = PhaseValidationState.NOT_STARTED
        self._last_validation_errors = []
        
        # Store deliverables
        self._data_flow = None
        self._structural_breakdown = None
        
    async def set_validation_state(self, state: PhaseValidationState) -> None:
        """Update validation state and emit event."""
        old_state = self.validation_state
        self.validation_state = state
        
        # Emit state change event
        await self.event_queue.emit(
            "phase_one_validation_state_changed",
            {
                "old_state": old_state.value,
                "new_state": state.value,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        logger.info(f"Phase One validation state changed: {old_state.value} -> {state.value}")
        
    async def register_data_flow(self, data_flow: Dict[str, Any]) -> bool:
        """
        Register and validate data flow from Root System Architect.
        
        Returns True if validation passes, False otherwise.
        """
        logger.info("Registering data flow for validation")
        await self.set_validation_state(PhaseValidationState.DATA_FLOW_VALIDATING)
        
        # Store data flow
        self._data_flow = data_flow
        
        # Validate data flow
        is_valid, errors = await self.dependency_validator.validate_data_flow(data_flow)
        
        if not is_valid:
            self._last_validation_errors = errors
            await self.set_validation_state(PhaseValidationState.DATA_FLOW_REVISING)
            # Errors will be handled by revision process
            logger.warning(f"Data flow validation failed with {len(errors)} errors")
            return False
        
        logger.info("Data flow validation successful")
        return True
        
    async def register_structural_breakdown(self, structure: Dict[str, Any]) -> bool:
        """
        Register and validate structural breakdown from Tree Placement Planner.
        
        Returns True if validation passes, False otherwise.
        """
        logger.info("Registering structural breakdown for validation")
        await self.set_validation_state(PhaseValidationState.STRUCTURAL_VALIDATING)
        
        # Store structural breakdown
        self._structural_breakdown = structure
        
        # Validate structural breakdown
        is_valid, errors = await self.dependency_validator.validate_structural_breakdown(structure)
        
        if not is_valid:
            self._last_validation_errors = errors
            await self.set_validation_state(PhaseValidationState.STRUCTURAL_REVISING)
            # Errors will be handled by revision process
            logger.warning(f"Structural breakdown validation failed with {len(errors)} errors")
            return False
        
        logger.info("Structural breakdown validation successful")
        
        # Proceed to cross-validation
        await self.set_validation_state(PhaseValidationState.CROSS_VALIDATING)
        is_consistent, cross_errors = await self.dependency_validator.validate_cross_consistency()
        
        if not is_consistent:
            self._last_validation_errors = cross_errors
            await self.set_validation_state(PhaseValidationState.ARBITRATION)
            # Errors will be handled by arbitration process
            logger.warning(f"Cross-consistency validation failed with {len(cross_errors)} errors")
            return False
            
        logger.info("Cross-consistency validation successful")
        await self.set_validation_state(PhaseValidationState.COMPLETED)
        return True
    
    async def revise_data_flow(self) -> Dict[str, Any]:
        """
        Send feedback to Root System Architect to revise the data flow.
        
        Returns the revised data flow.
        """
        if self.validation_state != PhaseValidationState.DATA_FLOW_REVISING:
            logger.error(f"Cannot revise data flow in state {self.validation_state}")
            return self._data_flow
            
        logger.info("Preparing feedback for Root System Architect")
        
        # Prepare feedback for data flow agent
        feedback = await self.dependency_validator.prepare_agent_feedback(
            "data_flow_agent", 
            self._last_validation_errors
        )
        
        # Get refined data flow from root system agent
        logger.info("Sending feedback to Root System Architect for revision")
        
        # Assume core_data_flow_revision_prompt is used
        revision_response = await self.root_system_agent.process_with_validation(
            conversation=f"Revise the data flow structure based on validation feedback: {feedback}",
            system_prompt_info=("FFTT_system_prompts/phase_one", "core_data_flow_revision_prompt")
        )
        
        # Extract revised data flow
        revised_data_flow = None
        if isinstance(revision_response, dict) and "data_architecture" in revision_response:
            revised_data_flow = revision_response.get("data_architecture")
        
        if revised_data_flow:
            # Update stored data flow
            self._data_flow = revised_data_flow
            
            # Validate revised data flow
            await self.set_validation_state(PhaseValidationState.DATA_FLOW_VALIDATING)
            is_valid, errors = await self.dependency_validator.validate_data_flow(revised_data_flow)
            
            if is_valid:
                logger.info("Revised data flow validation successful")
                return revised_data_flow
            else:
                self._last_validation_errors = errors
                await self.set_validation_state(PhaseValidationState.DATA_FLOW_REVISING)
                logger.warning(f"Revised data flow validation failed with {len(errors)} errors")
        
        return self._data_flow
    
    async def revise_structural_breakdown(self) -> Dict[str, Any]:
        """
        Send feedback to Tree Placement Planner to revise the structural breakdown.
        
        Returns the revised structural breakdown.
        """
        if self.validation_state != PhaseValidationState.STRUCTURAL_REVISING:
            logger.error(f"Cannot revise structural breakdown in state {self.validation_state}")
            return self._structural_breakdown
            
        logger.info("Preparing feedback for Tree Placement Planner")
        
        # Prepare feedback for structural agent
        feedback = await self.dependency_validator.prepare_agent_feedback(
            "structural_agent", 
            self._last_validation_errors
        )
        
        # Get refined structural breakdown from tree placement agent
        logger.info("Sending feedback to Tree Placement Planner for revision")
        
        # Assume structural_component_revision_prompt is used
        revision_response = await self.tree_placement_agent.process_with_validation(
            conversation=f"Revise the structural breakdown based on validation feedback: {feedback}",
            system_prompt_info=("FFTT_system_prompts/phase_one", "structural_component_revision_prompt")
        )
        
        # Extract revised structural breakdown
        revised_structure = None
        if isinstance(revision_response, dict) and "component_architecture" in revision_response:
            revised_structure = revision_response.get("component_architecture")
        
        if revised_structure:
            # Update stored structural breakdown
            self._structural_breakdown = revised_structure
            
            # Validate revised structural breakdown
            await self.set_validation_state(PhaseValidationState.STRUCTURAL_VALIDATING)
            is_valid, errors = await self.dependency_validator.validate_structural_breakdown(revised_structure)
            
            if is_valid:
                logger.info("Revised structural breakdown validation successful")
                
                # Proceed to cross-validation
                await self.set_validation_state(PhaseValidationState.CROSS_VALIDATING)
                is_consistent, cross_errors = await self.dependency_validator.validate_cross_consistency()
                
                if is_consistent:
                    logger.info("Cross-consistency validation successful")
                    await self.set_validation_state(PhaseValidationState.COMPLETED)
                else:
                    self._last_validation_errors = cross_errors
                    await self.set_validation_state(PhaseValidationState.ARBITRATION)
                    logger.warning(f"Cross-consistency validation failed with {len(cross_errors)} errors")
            else:
                self._last_validation_errors = errors
                await self.set_validation_state(PhaseValidationState.STRUCTURAL_REVISING)
                logger.warning(f"Revised structural breakdown validation failed with {len(errors)} errors")
        
        return self._structural_breakdown
    
    async def perform_arbitration(self) -> str:
        """
        Use Foundation Refinement Agent to determine which agent should revise their deliverable.
        
        Returns "data_flow_agent" or "structural_agent" based on arbitration result.
        """
        if self.validation_state != PhaseValidationState.ARBITRATION:
            logger.error(f"Cannot perform arbitration in state {self.validation_state}")
            return None
            
        logger.info("Beginning arbitration process")
        
        # First, use our heuristic algorithm to determine responsible agent
        suggested_agent = await self.dependency_validator.determine_responsible_agent(self._last_validation_errors)
        
        # Prepare arbitration context for refinement agent
        arbitration_context = {
            "data_flow": self._data_flow,
            "structural_breakdown": self._structural_breakdown,
            "validation_errors": self._last_validation_errors,
            "suggested_agent": suggested_agent,
            "timestamp": datetime.now().isoformat()
        }
        
        # Send to foundation refinement agent for arbitration
        logger.info("Sending to Garden Foundation Refinement Agent for arbitration")
        
        # Assume task_foundation_refinement_prompt is used
        refinement_response = await self.foundation_refinement_agent.process_with_validation(
            conversation=f"Determine which agent should revise their output to resolve cross-consistency errors: {arbitration_context}",
            system_prompt_info=("FFTT_system_prompts/phase_one", "task_foundation_refinement_prompt")
        )
        
        # Extract arbitration decision
        responsible_agent = None
        if isinstance(refinement_response, dict) and "refinement_analysis" in refinement_response:
            analysis = refinement_response.get("refinement_analysis", {})
            if "root_cause" in analysis and "responsible_agent" in analysis["root_cause"]:
                agent_mapping = {
                    "root_system_architect": "data_flow_agent",
                    "tree_placement_planner": "structural_agent"
                }
                responsible_agent = agent_mapping.get(analysis["root_cause"]["responsible_agent"])
                
        if not responsible_agent:
            # Fallback to suggested agent if arbitration failed
            responsible_agent = suggested_agent or "data_flow_agent"
        
        logger.info(f"Arbitration complete: {responsible_agent} should revise their output")
        
        # Set appropriate validation state based on arbitration result
        if responsible_agent == "data_flow_agent":
            await self.set_validation_state(PhaseValidationState.DATA_FLOW_REVISING)
        else:
            await self.set_validation_state(PhaseValidationState.STRUCTURAL_REVISING)
            
        return responsible_agent
    
    async def get_validation_status(self) -> Dict[str, Any]:
        """Get current validation status."""
        summary = await self.dependency_validator.get_validation_summary()
        
        return {
            "state": self.validation_state.value,
            "data_flow_validated": summary["data_flow_validated"],
            "structural_breakdown_validated": summary["structural_breakdown_validated"],
            "cross_consistency_validated": summary["cross_consistency_validated"],
            "error_count": len(self._last_validation_errors),
            "timestamp": datetime.now().isoformat()
        }
        
    async def execute_validation_workflow(self) -> bool:
        """
        Execute the full validation workflow until completion or maximum attempts reached.
        
        Returns True if validation succeeds, False otherwise.
        """
        max_attempts = 5
        current_attempt = 0
        
        while current_attempt < max_attempts:
            current_attempt += 1
            logger.info(f"Starting validation workflow - attempt {current_attempt}/{max_attempts}")
            
            # Handle based on current validation state
            if self.validation_state == PhaseValidationState.DATA_FLOW_REVISING:
                await self.revise_data_flow()
            elif self.validation_state == PhaseValidationState.STRUCTURAL_REVISING:
                await self.revise_structural_breakdown()
            elif self.validation_state == PhaseValidationState.ARBITRATION:
                responsible_agent = await self.perform_arbitration()
                
                # Execute the appropriate revision based on arbitration result
                if responsible_agent == "data_flow_agent":
                    await self.revise_data_flow()
                else:
                    await self.revise_structural_breakdown()
            
            # Check if validation is complete
            if self.validation_state == PhaseValidationState.COMPLETED:
                logger.info(f"Validation workflow completed successfully after {current_attempt} attempts")
                return True
                
        logger.warning(f"Validation workflow failed after {max_attempts} attempts")
        return False