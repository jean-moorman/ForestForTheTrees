"""
Technical validation module for phase one development.
"""
import logging
from typing import Dict, Any, List
from datetime import datetime

from resources import EventQueue, StateManager
from dependency import DependencyValidator
from interface import AgentInterface
from phase_one.models.enums import PhaseValidationState

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TechnicalDependencyValidator:
    """
    Manages the technical validation process during phase one development.
    
    This validator focuses specifically on technical correctness and consistency
    of data flow and structural component architecture. It's used during the
    development process to ensure architectural elements are technically sound
    before proceeding to end-of-phase refinement.
    
    Handles:
    1. Data flow technical validation (cycles, missing elements, duplicates)
    2. Structural breakdown technical validation (dependencies, relationships)
    3. Cross-consistency technical validation (data flow matches structure)
    4. Technical analysis to determine which specific element requires correction
    
    Unlike the PhaseOneValidator which performs holistic quality assessment,
    this validator focuses solely on technical correctness and consistency.
    """
    
    def __init__(
        self, 
        resource_manager: StateManager,
        event_queue: EventQueue, 
        root_system_agent: AgentInterface,
        tree_placement_agent: AgentInterface,
        technical_validator_agent: AgentInterface
    ):
        self.resource_manager = resource_manager
        self.event_queue = event_queue
        self.root_system_agent = root_system_agent
        self.tree_placement_agent = tree_placement_agent
        self.technical_validator_agent = technical_validator_agent
        
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
            "phase_one_technical_validation_state_changed",
            {
                "old_state": old_state.value,
                "new_state": state.value,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        logger.info(f"Phase One technical validation state changed: {old_state.value} -> {state.value}")
        
    async def register_data_flow(self, data_flow: Dict[str, Any]) -> bool:
        """
        Register and validate data flow from Root System Architect.
        
        Returns True if validation passes, False otherwise.
        """
        logger.info("Registering data flow for technical validation")
        await self.set_validation_state(PhaseValidationState.DATA_FLOW_VALIDATING)
        
        # Store data flow
        self._data_flow = data_flow
        
        # Validate data flow
        is_valid, errors = await self.dependency_validator.validate_data_flow(data_flow)
        
        if not is_valid:
            self._last_validation_errors = errors
            await self.set_validation_state(PhaseValidationState.DATA_FLOW_REVISING)
            # Errors will be handled by revision process
            logger.warning(f"Data flow technical validation failed with {len(errors)} errors")
            return False
        
        logger.info("Data flow technical validation successful")
        return True
        
    async def register_structural_breakdown(self, structure: Dict[str, Any]) -> bool:
        """
        Register and validate structural breakdown from Tree Placement Planner.
        
        Returns True if validation passes, False otherwise.
        """
        logger.info("Registering structural breakdown for technical validation")
        await self.set_validation_state(PhaseValidationState.STRUCTURAL_VALIDATING)
        
        # Store structural breakdown
        self._structural_breakdown = structure
        
        # Validate structural breakdown
        is_valid, errors = await self.dependency_validator.validate_structural_breakdown(structure)
        
        if not is_valid:
            self._last_validation_errors = errors
            await self.set_validation_state(PhaseValidationState.STRUCTURAL_REVISING)
            # Errors will be handled by revision process
            logger.warning(f"Structural breakdown technical validation failed with {len(errors)} errors")
            return False
        
        logger.info("Structural breakdown technical validation successful")
        
        # Proceed to cross-validation
        await self.set_validation_state(PhaseValidationState.CROSS_VALIDATING)
        is_consistent, cross_errors = await self.dependency_validator.validate_cross_consistency()
        
        if not is_consistent:
            self._last_validation_errors = cross_errors
            await self.set_validation_state(PhaseValidationState.TECHNICAL_VALIDATION)
            # Errors will be handled by technical analysis process
            logger.warning(f"Cross-consistency technical validation failed with {len(cross_errors)} errors")
            return False
            
        logger.info("Cross-consistency technical validation successful")
        await self.set_validation_state(PhaseValidationState.COMPLETED)
        return True
    
    async def revise_data_flow(self) -> Dict[str, Any]:
        """
        Send feedback to Root System Architect to revise the data flow.
        
        Returns the revised data flow.
        """
        if self.validation_state != PhaseValidationState.DATA_FLOW_REVISING:
            logger.error(f"Cannot revise data flow in technical validation state {self.validation_state}")
            return self._data_flow
            
        logger.info("Preparing technical feedback for Root System Architect")
        
        # Prepare feedback for data flow agent
        feedback = await self.dependency_validator.prepare_agent_feedback(
            "data_flow_agent", 
            self._last_validation_errors
        )
        
        # Get refined data flow from root system agent
        logger.info("Sending technical feedback to Root System Architect for revision")
        
        # Use core_data_flow_revision_prompt
        revision_response = await self.root_system_agent.process_with_validation(
            conversation=f"Revise the data flow structure based on technical validation feedback: {feedback}",
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
                logger.info("Revised data flow technical validation successful")
                return revised_data_flow
            else:
                self._last_validation_errors = errors
                await self.set_validation_state(PhaseValidationState.DATA_FLOW_REVISING)
                logger.warning(f"Revised data flow technical validation failed with {len(errors)} errors")
        
        return self._data_flow
    
    async def revise_structural_breakdown(self) -> Dict[str, Any]:
        """
        Send feedback to Tree Placement Planner to revise the structural breakdown.
        
        Returns the revised structural breakdown.
        """
        if self.validation_state != PhaseValidationState.STRUCTURAL_REVISING:
            logger.error(f"Cannot revise structural breakdown in technical validation state {self.validation_state}")
            return self._structural_breakdown
            
        logger.info("Preparing technical feedback for Tree Placement Planner")
        
        # Prepare feedback for structural agent
        feedback = await self.dependency_validator.prepare_agent_feedback(
            "structural_agent", 
            self._last_validation_errors
        )
        
        # Get refined structural breakdown from tree placement agent
        logger.info("Sending technical feedback to Tree Placement Planner for revision")
        
        # Use structural_component_revision_prompt
        revision_response = await self.tree_placement_agent.process_with_validation(
            conversation=f"Revise the structural breakdown based on technical validation feedback: {feedback}",
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
                logger.info("Revised structural breakdown technical validation successful")
                
                # Proceed to cross-validation
                await self.set_validation_state(PhaseValidationState.CROSS_VALIDATING)
                is_consistent, cross_errors = await self.dependency_validator.validate_cross_consistency()
                
                if is_consistent:
                    logger.info("Cross-consistency technical validation successful")
                    await self.set_validation_state(PhaseValidationState.COMPLETED)
                else:
                    self._last_validation_errors = cross_errors
                    await self.set_validation_state(PhaseValidationState.TECHNICAL_VALIDATION)
                    logger.warning(f"Cross-consistency technical validation failed with {len(cross_errors)} errors")
            else:
                self._last_validation_errors = errors
                await self.set_validation_state(PhaseValidationState.STRUCTURAL_REVISING)
                logger.warning(f"Revised structural breakdown technical validation failed with {len(errors)} errors")
        
        return self._structural_breakdown
    
    async def perform_technical_validation(self) -> str:
        """
        Use Technical Validator to determine which architectural element should be revised.
        
        Returns "data_flow_agent" or "structural_agent" based on technical validation analysis.
        """
        if self.validation_state != PhaseValidationState.TECHNICAL_VALIDATION:
            logger.error(f"Cannot perform technical validation in state {self.validation_state}")
            return None
            
        logger.info("Beginning technical dependency validation process")
        
        # First, use our heuristic algorithm to determine responsible agent
        suggested_agent = await self.dependency_validator.determine_responsible_agent(self._last_validation_errors)
        
        # Prepare validation context with technical details
        validation_context = {
            "data_flow": self._data_flow,
            "structural_breakdown": self._structural_breakdown,
            "validation_errors": self._last_validation_errors,
            "technical_suggested_element": "data_flow" if suggested_agent == "data_flow_agent" else "component_structure",
            "timestamp": datetime.now().isoformat()
        }
        
        # Send to technical dependency validator for analysis
        logger.info("Sending to Technical Dependency Validator for cross-consistency analysis")
        
        # Use the technical dependency validation prompt
        validation_response = await self.technical_validator_agent.process_with_validation(
            conversation=f"Analyze the technical cross-consistency issues between data flow and component structure: {validation_context}",
            system_prompt_info=("FFTT_system_prompts/phase_one", "technical_dependency_validation_prompt")
        )
        
        # Process through reflection and revision for higher quality output
        reflection_response = await self.technical_validator_agent.process_with_validation(
            conversation=f"Reflect on the technical validation analysis: {validation_response}",
            system_prompt_info=("FFTT_system_prompts/phase_one", "technical_validation_reflection_prompt")
        )
        
        revision_response = await self.technical_validator_agent.process_with_validation(
            conversation=f"Revise the technical validation analysis based on reflection: {{'validation_analysis': {validation_response}, 'reflection_results': {reflection_response}}}",
            system_prompt_info=("FFTT_system_prompts/phase_one", "technical_validation_revision_prompt")
        )
        
        # Extract validation decision from the revised response
        responsible_agent = None
        if isinstance(revision_response, dict) and "revision_results" in revision_response:
            revised_validation = revision_response.get("revision_results", {}).get("revised_validation", {})
            element_type = revised_validation.get("responsible_element", {}).get("element_type")
            action = revised_validation.get("correction_guidance", {}).get("action")
            
            if element_type == "data_flow" or action == "revise_data_flow":
                responsible_agent = "data_flow_agent"
            elif element_type == "component_structure" or action == "revise_component_structure":
                responsible_agent = "structural_agent"
                
        if not responsible_agent:
            # Fallback to suggested agent if validation analysis failed
            responsible_agent = suggested_agent or "data_flow_agent"
        
        logger.info(f"Technical validation complete: {responsible_agent} should revise their output")
        
        # Set appropriate validation state based on validation result
        if responsible_agent == "data_flow_agent":
            await self.set_validation_state(PhaseValidationState.DATA_FLOW_REVISING)
        else:
            await self.set_validation_state(PhaseValidationState.STRUCTURAL_REVISING)
            
        return responsible_agent
    
    async def get_validation_status(self) -> Dict[str, Any]:
        """Get current technical validation status."""
        summary = await self.dependency_validator.get_validation_summary()
        
        return {
            "state": self.validation_state.value,
            "validation_type": "technical_dependency_validation",
            "data_flow_validated": summary["data_flow_validated"],
            "structural_breakdown_validated": summary["structural_breakdown_validated"],
            "cross_consistency_validated": summary["cross_consistency_validated"],
            "error_count": len(self._last_validation_errors),
            "timestamp": datetime.now().isoformat()
        }
        
    async def execute_validation_workflow(self) -> bool:
        """
        Execute the full technical validation workflow until completion or maximum attempts reached.
        
        Returns True if validation succeeds, False otherwise.
        """
        max_attempts = 5
        current_attempt = 0
        
        while current_attempt < max_attempts:
            current_attempt += 1
            logger.info(f"Starting technical validation workflow - attempt {current_attempt}/{max_attempts}")
            
            # Handle based on current validation state
            if self.validation_state == PhaseValidationState.DATA_FLOW_REVISING:
                await self.revise_data_flow()
            elif self.validation_state == PhaseValidationState.STRUCTURAL_REVISING:
                await self.revise_structural_breakdown()
            elif self.validation_state == PhaseValidationState.TECHNICAL_VALIDATION:
                responsible_agent = await self.perform_technical_validation()
                
                # Execute the appropriate revision based on technical validation result
                if responsible_agent == "data_flow_agent":
                    await self.revise_data_flow()
                else:
                    await self.revise_structural_breakdown()
            
            # Check if validation is complete
            if self.validation_state == PhaseValidationState.COMPLETED:
                logger.info(f"Technical validation workflow completed successfully after {current_attempt} attempts")
                return True
                
        logger.warning(f"Technical validation workflow failed after {max_attempts} attempts")
        return False