"""
Validation module for phase two component guidelines.
"""
import logging
import asyncio
from typing import Dict, Any, List, Protocol, Optional, Tuple
from datetime import datetime

from resources import EventQueue, StateManager, MetricsManager, ResourceType, ResourceEventTypes
from resources.monitoring import MemoryMonitor, SystemMonitor
from resources.base import AsyncTimeoutManager
from interface import AgentInterface
from resources.earth_agent import EarthAgent
from resources.water_agent import WaterAgent

# We'll define our own ComponentValidationState enum
from enum import Enum
class ComponentValidationState(Enum):
    """Enum defining the possible states of component validation."""
    NOT_STARTED = "not_started"
    DESCRIPTION_VALIDATING = "description_validating"
    DESCRIPTION_REVISING = "description_revising"
    REQUIREMENTS_VALIDATING = "requirements_validating"
    REQUIREMENTS_REVISING = "requirements_revising"
    DATA_FLOW_VALIDATING = "data_flow_validating"
    DATA_FLOW_REVISING = "data_flow_revising"
    FEATURES_VALIDATING = "features_validating"
    FEATURES_REVISING = "features_revising"
    ARBITRATION = "arbitration"
    COMPLETED = "completed"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PhaseZeroInterface(Protocol):
    """Interface for interacting with Phase Zero agents"""
    async def process_system_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        pass
        
class ComponentValidator:
    """
    Manages the sequential validation process for phase two component guidelines.
    
    Handles:
    1. Component description validation using the Flower Bed Planner Agent
    2. Component requirements validation using the Flower Bed Environment Agent
    3. Component data flow validation using the Flower Root System Agent
    4. Component features validation using the Flower Placement Agent 
    5. Arbitration and coordination when conflicts occur
    6. Integration with Earth and Water elemental agents
    7. Context cleanup and progress tracking during refinement
    """
    
    def __init__(
        self, 
        resource_manager: StateManager,
        event_queue: EventQueue,
        flower_bed_planner_agent: AgentInterface,
        flower_bed_environment_agent: AgentInterface,
        flower_root_system_agent: AgentInterface,
        flower_placement_agent: AgentInterface,
        refinement_agent: AgentInterface,
        earth_agent: Optional[EarthAgent] = None,
        water_agent: Optional[WaterAgent] = None,
        metrics_manager: Optional[MetricsManager] = None,
        memory_monitor: Optional[MemoryMonitor] = None,
        system_monitor: Optional[SystemMonitor] = None,
        timeout_manager: Optional[AsyncTimeoutManager] = None
    ):
        """
        Initialize component validator with required resources and agents.
        
        Args:
            resource_manager: State manager for persistence
            event_queue: Event queue for communication
            flower_bed_planner_agent: Agent for component description
            flower_bed_environment_agent: Agent for component requirements
            flower_root_system_agent: Agent for component data flow
            flower_placement_agent: Agent for component features
            refinement_agent: Agent for arbitration and refinement
            earth_agent: Earth elemental agent for validation
            water_agent: Water elemental agent for propagation
            metrics_manager: Metrics manager
            memory_monitor: Memory monitor
            system_monitor: System monitor
            timeout_manager: Timeout manager
        """
        self.resource_manager = resource_manager
        self.event_queue = event_queue
        self.flower_bed_planner_agent = flower_bed_planner_agent
        self.flower_bed_environment_agent = flower_bed_environment_agent
        self.flower_root_system_agent = flower_root_system_agent
        self.flower_placement_agent = flower_placement_agent
        self.refinement_agent = refinement_agent
        self.earth_agent = earth_agent
        self.water_agent = water_agent
        self.metrics_manager = metrics_manager or MetricsManager(event_queue)
        self.memory_monitor = memory_monitor
        self.system_monitor = system_monitor
        
        # Initialize timeout manager if not provided
        self.timeout_manager = timeout_manager or AsyncTimeoutManager()
        
        # Create refinement manager
        from phase_two.validation.refinement_manager import ComponentRefinementManager
        self.refinement_manager = ComponentRefinementManager(
            event_queue=event_queue,
            state_manager=resource_manager,
            metrics_manager=self.metrics_manager,
            memory_monitor=memory_monitor,
            system_monitor=system_monitor,
            timeout_manager=timeout_manager
        )
        
        # Initialize validation state
        self.validation_state = ComponentValidationState.NOT_STARTED
        self._last_validation_errors = []
        self._active_refinement_context_id = None
        
        # Store component guidelines
        self._component_id = None
        self._component_name = None
        self._component_description = None
        self._component_requirements = None
        self._component_data_flow = None
        self._component_features = None
        
        # Track performance metrics
        self._validation_start_time = None
        self._validation_attempts = 0
        
        # Refinement tracking
        self._arbitration_result = None  # Store arbitration analysis 
        self._root_cause_agent = None  # Original agent ID identified as root cause
        self._refinement_in_progress = False  # Flag to track if refinement is in progress
        
    async def set_validation_state(self, state: ComponentValidationState) -> None:
        """
        Update validation state and emit event.
        
        This method also handles cleanup of obsolete refinement contexts
        when backtracking to an earlier state.
        """
        old_state = self.validation_state
        self.validation_state = state
        
        # Emit state change event using standardized event type and payload
        from resources.events import ResourceEventTypes
        from resources.schemas import ValidationStateChangedPayload
        from dataclasses import asdict
        
        # Create standardized payload
        payload = ValidationStateChangedPayload(
            old_state=old_state.value,
            new_state=state.value,
            source_id="component_validator",
            context_id=self._active_refinement_context_id,
            error_count=len(self._last_validation_errors) if hasattr(self, '_last_validation_errors') else 0,
            responsible_agent=self._root_cause_agent
        )
        
        # Emit with standard event type
        await self.event_queue.emit(
            ResourceEventTypes.COMPONENT_VALIDATION_STATE_CHANGED.value,
            asdict(payload)
        )
        
        logger.info(f"Component validation state changed: {old_state.value} -> {state.value}")
        
        # Record metrics for state transition
        await self.metrics_manager.record_metric(
            "component_guideline:validation:state_change",
            1.0,
            metadata={
                "component_id": self._component_id,
                "old_state": old_state.value,
                "new_state": state.value,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # Check if we're backtracking to an earlier state
        if self._is_backtracking(old_state, state):
            logger.info(f"Backtracking detected from {old_state.value} to {state.value}, cleaning up obsolete contexts")
            
            # Clean up obsolete refinement contexts
            await self.refinement_manager.cleanup_obsolete_contexts(state, self._root_cause_agent)
            
            # Reset active refinement context if needed
            if self._active_refinement_context_id:
                # Only reset if the active context is no longer relevant
                if state in [
                    ComponentValidationState.DESCRIPTION_REVISING, 
                    ComponentValidationState.REQUIREMENTS_REVISING,
                    ComponentValidationState.DATA_FLOW_REVISING,
                    ComponentValidationState.FEATURES_REVISING
                ]:
                    # Keep context if we're targeting the specific revision state
                    pass
                else:
                    self._active_refinement_context_id = None
    
    def _is_backtracking(self, old_state: ComponentValidationState, new_state: ComponentValidationState) -> bool:
        """
        Determine if a state transition represents backtracking.
        
        Args:
            old_state: Previous validation state
            new_state: New validation state
            
        Returns:
            bool: True if backtracking, False otherwise
        """
        # State precedence order 
        state_order = {
            ComponentValidationState.NOT_STARTED: 0,
            ComponentValidationState.DESCRIPTION_VALIDATING: 1,
            ComponentValidationState.DESCRIPTION_REVISING: 2,
            ComponentValidationState.REQUIREMENTS_VALIDATING: 3,
            ComponentValidationState.REQUIREMENTS_REVISING: 4,
            ComponentValidationState.DATA_FLOW_VALIDATING: 5,
            ComponentValidationState.DATA_FLOW_REVISING: 6,
            ComponentValidationState.FEATURES_VALIDATING: 7,
            ComponentValidationState.FEATURES_REVISING: 8,
            ComponentValidationState.ARBITRATION: 9,
            ComponentValidationState.COMPLETED: 10
        }
        
        # Special case: ARBITRATION to any revising state is not backtracking
        # but rather a directed refinement action 
        if (old_state == ComponentValidationState.ARBITRATION and 
            new_state in [
                ComponentValidationState.DESCRIPTION_REVISING,
                ComponentValidationState.REQUIREMENTS_REVISING,
                ComponentValidationState.DATA_FLOW_REVISING,
                ComponentValidationState.FEATURES_REVISING
            ]):
            return False
            
        # Otherwise, check if new state precedes old state
        old_order = state_order.get(old_state, 0)
        new_order = state_order.get(new_state, 0)
        
        return new_order < old_order
        
    async def set_component_info(self, component_id: str, component_name: str) -> None:
        """
        Set component information for validation.
        
        Args:
            component_id: Unique identifier for the component
            component_name: Human-readable name for the component
        """
        self._component_id = component_id
        self._component_name = component_name
        
        # Reset the validation state
        await self.set_validation_state(ComponentValidationState.NOT_STARTED)
        
        # Record component info in state manager
        await self.resource_manager.set_state(
            f"component:validation:{component_id}:info",
            {
                "component_id": component_id,
                "component_name": component_name,
                "validation_state": self.validation_state.value,
                "timestamp": datetime.now().isoformat()
            },
            ResourceType.STATE
        )
        
        # Record metrics
        await self.metrics_manager.record_metric(
            "component_guideline:validation:component_registered",
            1.0,
            metadata={
                "component_id": component_id,
                "component_name": component_name,
                "timestamp": datetime.now().isoformat()
            }
        )
        
    async def validate_component_description(self, description: Dict[str, Any]) -> bool:
        """
        Validate component description using the Flower Bed Planner Agent.
        
        This method also integrates with the Earth agent for additional validation.
        
        Args:
            description: Component description to validate
            
        Returns:
            bool: True if validation passes, False otherwise
        """
        logger.info(f"Validating component description for component {self._component_id}")
        await self.set_validation_state(ComponentValidationState.DESCRIPTION_VALIDATING)
        
        # Store component description
        self._component_description = description
        
        # First, use Earth agent for validation if available
        if self.earth_agent:
            try:
                validation_result = await self.earth_agent.validate_component_description(
                    self._component_id, description
                )
                
                if not validation_result.get("passed", True):
                    self._last_validation_errors = validation_result.get("issues", [])
                    await self.set_validation_state(ComponentValidationState.DESCRIPTION_REVISING)
                    logger.warning(f"Component description validation failed with Earth agent: {len(self._last_validation_errors)} issues")
                    return False
            except Exception as e:
                logger.error(f"Error validating with Earth agent: {str(e)}")
                # Continue with regular validation
        
        # Run standard validation checks
        is_valid, errors = await self._validate_component_description(description)
        
        if not is_valid:
            self._last_validation_errors = errors
            await self.set_validation_state(ComponentValidationState.DESCRIPTION_REVISING)
            logger.warning(f"Component description validation failed with {len(errors)} errors")
            return False
        
        logger.info("Component description validation successful")
        return True
        
    async def _validate_component_description(self, description: Dict[str, Any]) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Perform validation checks on component description.
        
        Args:
            description: Component description to validate
            
        Returns:
            Tuple[bool, List[Dict]]: (is_valid, errors)
        """
        errors = []
        
        # Check if component description has required fields
        required_fields = ["component_description"]
        
        for field in required_fields:
            if field not in description:
                errors.append({
                    "error_type": "missing_field",
                    "field": field,
                    "message": f"Missing required field: {field}"
                })
        
        # Check component description content
        if "component_description" in description:
            comp_desc = description["component_description"]
            
            # Check if it's a dictionary
            if not isinstance(comp_desc, dict):
                errors.append({
                    "error_type": "invalid_format",
                    "field": "component_description",
                    "message": "Component description must be a dictionary"
                })
            else:
                # Check for required fields in component description
                desc_required_fields = ["overview", "purpose", "responsibilities"]
                
                for field in desc_required_fields:
                    if field not in comp_desc:
                        errors.append({
                            "error_type": "missing_field",
                            "field": f"component_description.{field}",
                            "message": f"Missing required field in component description: {field}"
                        })
        
        # Return validation result
        return len(errors) == 0, errors
    
    async def validate_component_requirements(self, requirements: Dict[str, Any]) -> bool:
        """
        Validate component requirements using the Flower Bed Environment Agent.
        
        This method also integrates with the Earth agent for additional validation.
        
        Args:
            requirements: Component requirements to validate
            
        Returns:
            bool: True if validation passes, False otherwise
        """
        logger.info(f"Validating component requirements for component {self._component_id}")
        await self.set_validation_state(ComponentValidationState.REQUIREMENTS_VALIDATING)
        
        # Store component requirements
        self._component_requirements = requirements
        
        # First, use Earth agent for validation if available
        if self.earth_agent and self._component_description:
            try:
                validation_result = await self.earth_agent.validate_component_requirements(
                    self._component_id, requirements, self._component_description
                )
                
                if not validation_result.get("passed", True):
                    self._last_validation_errors = validation_result.get("issues", [])
                    await self.set_validation_state(ComponentValidationState.REQUIREMENTS_REVISING)
                    logger.warning(f"Component requirements validation failed with Earth agent: {len(self._last_validation_errors)} issues")
                    return False
            except Exception as e:
                logger.error(f"Error validating with Earth agent: {str(e)}")
                # Continue with regular validation
        
        # Run standard validation checks
        is_valid, errors = await self._validate_component_requirements(requirements)
        
        if not is_valid:
            self._last_validation_errors = errors
            await self.set_validation_state(ComponentValidationState.REQUIREMENTS_REVISING)
            logger.warning(f"Component requirements validation failed with {len(errors)} errors")
            return False
        
        logger.info("Component requirements validation successful")
        return True
        
    async def _validate_component_requirements(self, requirements: Dict[str, Any]) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Perform validation checks on component requirements.
        
        Args:
            requirements: Component requirements to validate
            
        Returns:
            Tuple[bool, List[Dict]]: (is_valid, errors)
        """
        errors = []
        
        # Check if component requirements has required fields
        required_fields = ["component_requirements"]
        
        for field in required_fields:
            if field not in requirements:
                errors.append({
                    "error_type": "missing_field",
                    "field": field,
                    "message": f"Missing required field: {field}"
                })
        
        # Check component requirements content
        if "component_requirements" in requirements:
            comp_reqs = requirements["component_requirements"]
            
            # Check if it's a dictionary
            if not isinstance(comp_reqs, dict):
                errors.append({
                    "error_type": "invalid_format",
                    "field": "component_requirements",
                    "message": "Component requirements must be a dictionary"
                })
            else:
                # Check for required fields in component requirements
                reqs_required_fields = ["functional_requirements", "non_functional_requirements", "interfaces"]
                
                for field in reqs_required_fields:
                    if field not in comp_reqs:
                        errors.append({
                            "error_type": "missing_field",
                            "field": f"component_requirements.{field}",
                            "message": f"Missing required field in component requirements: {field}"
                        })
        
        # Return validation result
        return len(errors) == 0, errors
    
    async def validate_component_data_flow(self, data_flow: Dict[str, Any]) -> bool:
        """
        Validate component data flow using the Flower Root System Agent.
        
        This method also integrates with the Earth agent for additional validation.
        
        Args:
            data_flow: Component data flow to validate
            
        Returns:
            bool: True if validation passes, False otherwise
        """
        logger.info(f"Validating component data flow for component {self._component_id}")
        await self.set_validation_state(ComponentValidationState.DATA_FLOW_VALIDATING)
        
        # Store component data flow
        self._component_data_flow = data_flow
        
        # First, use Earth agent for validation if available
        if self.earth_agent and self._component_requirements:
            try:
                validation_result = await self.earth_agent.validate_component_data_flow(
                    self._component_id, data_flow, self._component_requirements
                )
                
                if not validation_result.get("passed", True):
                    self._last_validation_errors = validation_result.get("issues", [])
                    await self.set_validation_state(ComponentValidationState.DATA_FLOW_REVISING)
                    logger.warning(f"Component data flow validation failed with Earth agent: {len(self._last_validation_errors)} issues")
                    return False
            except Exception as e:
                logger.error(f"Error validating with Earth agent: {str(e)}")
                # Continue with regular validation
        
        # Run standard validation checks
        is_valid, errors = await self._validate_component_data_flow(data_flow)
        
        if not is_valid:
            self._last_validation_errors = errors
            await self.set_validation_state(ComponentValidationState.DATA_FLOW_REVISING)
            logger.warning(f"Component data flow validation failed with {len(errors)} errors")
            return False
        
        logger.info("Component data flow validation successful")
        return True
        
    async def _validate_component_data_flow(self, data_flow: Dict[str, Any]) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Perform validation checks on component data flow.
        
        Args:
            data_flow: Component data flow to validate
            
        Returns:
            Tuple[bool, List[Dict]]: (is_valid, errors)
        """
        errors = []
        
        # Check if component data flow has required fields
        required_fields = ["component_data_flow"]
        
        for field in required_fields:
            if field not in data_flow:
                errors.append({
                    "error_type": "missing_field",
                    "field": field,
                    "message": f"Missing required field: {field}"
                })
        
        # Check component data flow content
        if "component_data_flow" in data_flow:
            comp_data_flow = data_flow["component_data_flow"]
            
            # Check if it's a dictionary
            if not isinstance(comp_data_flow, dict):
                errors.append({
                    "error_type": "invalid_format",
                    "field": "component_data_flow",
                    "message": "Component data flow must be a dictionary"
                })
            else:
                # Check for required fields in component data flow
                flow_required_fields = ["inputs", "outputs", "internal_transformations"]
                
                for field in flow_required_fields:
                    if field not in comp_data_flow:
                        errors.append({
                            "error_type": "missing_field",
                            "field": f"component_data_flow.{field}",
                            "message": f"Missing required field in component data flow: {field}"
                        })
        
        # Return validation result
        return len(errors) == 0, errors
    
    async def validate_component_features(self, features: Dict[str, Any]) -> bool:
        """
        Validate component features using the Flower Placement Agent.
        
        This method also integrates with the Earth agent for additional validation.
        
        Args:
            features: Component features to validate
            
        Returns:
            bool: True if validation passes, False otherwise
        """
        logger.info(f"Validating component features for component {self._component_id}")
        await self.set_validation_state(ComponentValidationState.FEATURES_VALIDATING)
        
        # Store component features
        self._component_features = features
        
        # First, use Earth agent for validation if available
        if self.earth_agent and self._component_data_flow:
            try:
                validation_result = await self.earth_agent.validate_component_features(
                    self._component_id, features, self._component_data_flow
                )
                
                if not validation_result.get("passed", True):
                    self._last_validation_errors = validation_result.get("issues", [])
                    await self.set_validation_state(ComponentValidationState.FEATURES_REVISING)
                    logger.warning(f"Component features validation failed with Earth agent: {len(self._last_validation_errors)} issues")
                    return False
            except Exception as e:
                logger.error(f"Error validating with Earth agent: {str(e)}")
                # Continue with regular validation
        
        # Run standard validation checks
        is_valid, errors = await self._validate_component_features(features)
        
        if not is_valid:
            self._last_validation_errors = errors
            await self.set_validation_state(ComponentValidationState.FEATURES_REVISING)
            logger.warning(f"Component features validation failed with {len(errors)} errors")
            return False
        
        logger.info("Component features validation successful")
        
        # If we got here, all validations have succeeded
        await self.set_validation_state(ComponentValidationState.COMPLETED)
        return True
        
    async def _validate_component_features(self, features: Dict[str, Any]) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Perform validation checks on component features.
        
        Args:
            features: Component features to validate
            
        Returns:
            Tuple[bool, List[Dict]]: (is_valid, errors)
        """
        errors = []
        
        # Check if features have the required fields
        required_fields = ["features"]
        
        for field in required_fields:
            if field not in features:
                errors.append({
                    "error_type": "missing_field",
                    "field": field,
                    "message": f"Missing required field: {field}"
                })
        
        # Check features content
        if "features" in features:
            feature_list = features["features"]
            
            # Check if it's a list
            if not isinstance(feature_list, list):
                errors.append({
                    "error_type": "invalid_format",
                    "field": "features",
                    "message": "Features must be a list"
                })
            elif len(feature_list) == 0:
                errors.append({
                    "error_type": "empty_list",
                    "field": "features",
                    "message": "No features defined"
                })
            else:
                # Check if feature relationships are defined if multiple features
                if len(feature_list) > 1 and "feature_relationships" not in features:
                    errors.append({
                        "error_type": "missing_field",
                        "field": "feature_relationships",
                        "message": "Feature relationships must be defined when multiple features are present"
                    })
                
                # Check each feature for required fields
                for i, feature in enumerate(feature_list):
                    if not isinstance(feature, dict):
                        errors.append({
                            "error_type": "invalid_format",
                            "field": f"features[{i}]",
                            "message": "Feature must be a dictionary"
                        })
                        continue
                    
                    # Check for required fields in each feature
                    feature_required_fields = ["id", "name", "description"]
                    
                    for field in feature_required_fields:
                        if field not in feature:
                            errors.append({
                                "error_type": "missing_field",
                                "field": f"features[{i}].{field}",
                                "message": f"Missing required field in feature: {field}"
                            })
                
                # Validate feature data flow against component data flow if available
                if self._component_data_flow:
                    from phase_two.utils import validate_feature_data_flow
                    
                    data_flow_valid, data_flow_errors = validate_feature_data_flow(
                        feature_list, 
                        self._component_data_flow
                    )
                    
                    if not data_flow_valid:
                        logger.warning(f"Feature data flow validation found {len(data_flow_errors)} issues")
                        # Add data flow errors to our error list
                        errors.extend(data_flow_errors)
        
        # Return validation result
        return len(errors) == 0, errors
    
    async def revise_component_description(self) -> Dict[str, Any]:
        """
        Send feedback to Flower Bed Planner Agent to revise the component description.
        
        Returns the revised component description.
        """
        if self.validation_state != ComponentValidationState.DESCRIPTION_REVISING:
            logger.error(f"Cannot revise component description in state {self.validation_state}")
            return self._component_description
            
        logger.info("Preparing feedback for Flower Bed Planner Agent")
        
        # Prepare feedback for description agent
        feedback = {
            "component_id": self._component_id,
            "component_name": self._component_name,
            "validation_errors": self._last_validation_errors,
            "current_description": self._component_description
        }
        
        # Create refinement context
        refinement_context = await self.refinement_manager.create_refinement_context(
            component_id=self._component_id,
            validation_state=self.validation_state,
            responsible_agent="flower_bed_planner",
            validation_errors=self._last_validation_errors,
            metadata={
                "component_name": self._component_name
            }
        )
        
        # Store active refinement context ID
        self._active_refinement_context_id = refinement_context.context_id
        
        # Use the three-stage refinement process
        logger.info("Starting three-stage refinement process for component description")
        refinement_result = await self.refinement_manager.three_stage_refinement(
            context_id=refinement_context.context_id,
            agent=self.flower_bed_planner_agent,
            initial_input=feedback,
            refinement_timeout=180.0,  # 3 minutes
            reflection_timeout=120.0,  # 2 minutes
            revision_timeout=150.0,    # 2.5 minutes
            max_iterations=2
        )
        
        # Extract revised description
        revised_description = None
        if isinstance(refinement_result, dict) and "component_description" in refinement_result:
            revised_description = refinement_result
        
        if revised_description:
            # Update stored description
            self._component_description = revised_description
            
            # Validate revised description
            await self.set_validation_state(ComponentValidationState.DESCRIPTION_VALIDATING)
            is_valid, errors = await self._validate_component_description(revised_description)
            
            if is_valid:
                logger.info("Revised component description validation successful")
                self._active_refinement_context_id = None  # Clear active refinement
                return revised_description
            else:
                self._last_validation_errors = errors
                await self.set_validation_state(ComponentValidationState.DESCRIPTION_REVISING)
                logger.warning(f"Revised component description validation failed with {len(errors)} errors")
        
        return self._component_description
    
    async def revise_component_requirements(self) -> Dict[str, Any]:
        """
        Send feedback to Flower Bed Environment Agent to revise the component requirements.
        
        Returns the revised component requirements.
        """
        if self.validation_state != ComponentValidationState.REQUIREMENTS_REVISING:
            logger.error(f"Cannot revise component requirements in state {self.validation_state}")
            return self._component_requirements
            
        logger.info("Preparing feedback for Flower Bed Environment Agent")
        
        # Prepare feedback for requirements agent
        feedback = {
            "component_id": self._component_id,
            "component_name": self._component_name,
            "validation_errors": self._last_validation_errors,
            "current_requirements": self._component_requirements,
            "component_description": self._component_description
        }
        
        # Create refinement context
        refinement_context = await self.refinement_manager.create_refinement_context(
            component_id=self._component_id,
            validation_state=self.validation_state,
            responsible_agent="flower_bed_environment",
            validation_errors=self._last_validation_errors,
            metadata={
                "component_name": self._component_name
            }
        )
        
        # Store active refinement context ID
        self._active_refinement_context_id = refinement_context.context_id
        
        # Use the three-stage refinement process
        logger.info("Starting three-stage refinement process for component requirements")
        refinement_result = await self.refinement_manager.three_stage_refinement(
            context_id=refinement_context.context_id,
            agent=self.flower_bed_environment_agent,
            initial_input=feedback,
            refinement_timeout=180.0,  # 3 minutes
            reflection_timeout=120.0,  # 2 minutes
            revision_timeout=150.0,    # 2.5 minutes
            max_iterations=2
        )
        
        # Extract revised requirements
        revised_requirements = None
        if isinstance(refinement_result, dict) and "component_requirements" in refinement_result:
            revised_requirements = refinement_result
        
        if revised_requirements:
            # Update stored requirements
            self._component_requirements = revised_requirements
            
            # Validate revised requirements
            await self.set_validation_state(ComponentValidationState.REQUIREMENTS_VALIDATING)
            is_valid, errors = await self._validate_component_requirements(revised_requirements)
            
            if is_valid:
                logger.info("Revised component requirements validation successful")
                self._active_refinement_context_id = None  # Clear active refinement
                return revised_requirements
            else:
                self._last_validation_errors = errors
                await self.set_validation_state(ComponentValidationState.REQUIREMENTS_REVISING)
                logger.warning(f"Revised component requirements validation failed with {len(errors)} errors")
        
        return self._component_requirements
    
    async def revise_component_data_flow(self) -> Dict[str, Any]:
        """
        Send feedback to Flower Root System Agent to revise the component data flow.
        
        Returns the revised component data flow.
        """
        if self.validation_state != ComponentValidationState.DATA_FLOW_REVISING:
            logger.error(f"Cannot revise component data flow in state {self.validation_state}")
            return self._component_data_flow
            
        logger.info("Preparing feedback for Flower Root System Agent")
        
        # Prepare feedback for data flow agent
        feedback = {
            "component_id": self._component_id,
            "component_name": self._component_name,
            "validation_errors": self._last_validation_errors,
            "current_data_flow": self._component_data_flow,
            "component_description": self._component_description,
            "component_requirements": self._component_requirements
        }
        
        # Create refinement context
        refinement_context = await self.refinement_manager.create_refinement_context(
            component_id=self._component_id,
            validation_state=self.validation_state,
            responsible_agent="flower_root_system",
            validation_errors=self._last_validation_errors,
            metadata={
                "component_name": self._component_name
            }
        )
        
        # Store active refinement context ID
        self._active_refinement_context_id = refinement_context.context_id
        
        # Use the three-stage refinement process
        logger.info("Starting three-stage refinement process for component data flow")
        refinement_result = await self.refinement_manager.three_stage_refinement(
            context_id=refinement_context.context_id,
            agent=self.flower_root_system_agent,
            initial_input=feedback,
            refinement_timeout=180.0,  # 3 minutes
            reflection_timeout=120.0,  # 2 minutes
            revision_timeout=150.0,    # 2.5 minutes
            max_iterations=2
        )
        
        # Extract revised data flow
        revised_data_flow = None
        if isinstance(refinement_result, dict) and "component_data_flow" in refinement_result:
            revised_data_flow = refinement_result
        
        if revised_data_flow:
            # Update stored data flow
            self._component_data_flow = revised_data_flow
            
            # Validate revised data flow
            await self.set_validation_state(ComponentValidationState.DATA_FLOW_VALIDATING)
            is_valid, errors = await self._validate_component_data_flow(revised_data_flow)
            
            if is_valid:
                logger.info("Revised component data flow validation successful")
                self._active_refinement_context_id = None  # Clear active refinement
                return revised_data_flow
            else:
                self._last_validation_errors = errors
                await self.set_validation_state(ComponentValidationState.DATA_FLOW_REVISING)
                logger.warning(f"Revised component data flow validation failed with {len(errors)} errors")
        
        return self._component_data_flow
    
    async def revise_component_features(self) -> Dict[str, Any]:
        """
        Send feedback to Flower Placement Agent to revise the component features.
        
        Returns the revised component features.
        """
        if self.validation_state != ComponentValidationState.FEATURES_REVISING:
            logger.error(f"Cannot revise component features in state {self.validation_state}")
            return self._component_features
            
        logger.info("Preparing feedback for Flower Placement Agent")
        
        # Prepare feedback for features agent
        feedback = {
            "component_id": self._component_id,
            "component_name": self._component_name,
            "validation_errors": self._last_validation_errors,
            "current_features": self._component_features,
            "component_description": self._component_description,
            "component_requirements": self._component_requirements,
            "component_data_flow": self._component_data_flow
        }
        
        # Create refinement context
        refinement_context = await self.refinement_manager.create_refinement_context(
            component_id=self._component_id,
            validation_state=self.validation_state,
            responsible_agent="flower_placement",
            validation_errors=self._last_validation_errors,
            metadata={
                "component_name": self._component_name
            }
        )
        
        # Store active refinement context ID
        self._active_refinement_context_id = refinement_context.context_id
        
        # Use the three-stage refinement process
        logger.info("Starting three-stage refinement process for component features")
        refinement_result = await self.refinement_manager.three_stage_refinement(
            context_id=refinement_context.context_id,
            agent=self.flower_placement_agent,
            initial_input=feedback,
            refinement_timeout=180.0,  # 3 minutes
            reflection_timeout=120.0,  # 2 minutes
            revision_timeout=150.0,    # 2.5 minutes
            max_iterations=2
        )
        
        # Extract revised features
        revised_features = None
        if isinstance(refinement_result, dict) and "features" in refinement_result:
            revised_features = refinement_result
        
        if revised_features:
            # Update stored features
            self._component_features = revised_features
            
            # Validate revised features
            await self.set_validation_state(ComponentValidationState.FEATURES_VALIDATING)
            is_valid, errors = await self._validate_component_features(revised_features)
            
            if is_valid:
                logger.info("Revised component features validation successful")
                self._active_refinement_context_id = None  # Clear active refinement
                await self.set_validation_state(ComponentValidationState.COMPLETED)
                return revised_features
            else:
                self._last_validation_errors = errors
                await self.set_validation_state(ComponentValidationState.FEATURES_REVISING)
                logger.warning(f"Revised component features validation failed with {len(errors)} errors")
        
        return self._component_features
    
    async def perform_arbitration(self) -> str:
        """
        Use refinement agent to determine which agent should revise their deliverable.
        
        Returns the agent ID that should perform revisions.
        """
        if self.validation_state != ComponentValidationState.ARBITRATION:
            logger.error(f"Cannot perform arbitration in state {self.validation_state}")
            return None
            
        logger.info("Beginning arbitration process for component guidelines")
        
        # Mark the start of validation if not already set
        if not self._validation_start_time:
            self._validation_start_time = datetime.now()
        self._validation_attempts += 1
        
        # Prepare arbitration context for refinement agent
        arbitration_context = {
            "component_id": self._component_id,
            "component_name": self._component_name,
            "component_description": self._component_description,
            "component_requirements": self._component_requirements,
            "component_data_flow": self._component_data_flow,
            "component_features": self._component_features,
            "validation_errors": self._last_validation_errors,
            "timestamp": datetime.now().isoformat(),
            "validation_attempt": self._validation_attempts
        }
        
        # Create refinement context for arbitration
        refinement_context = await self.refinement_manager.create_refinement_context(
            component_id=self._component_id,
            validation_state=self.validation_state,
            responsible_agent="refinement_agent",
            validation_errors=self._last_validation_errors,
            metadata={
                "component_name": self._component_name,
                "validation_attempt": self._validation_attempts
            }
        )
        
        # Store active refinement context ID
        self._active_refinement_context_id = refinement_context.context_id
        
        # Execute arbitration process with timeout
        logger.info("Executing arbitration with refinement agent")
        
        # Use the timeout-tracked version via the refinement manager
        arbitration_result, duration_seconds, success = await self.refinement_manager.run_with_timeout(
            self.refinement_agent.process_with_validation(
                conversation=f"Perform arbitration for component guideline inconsistencies: {arbitration_context}",
                system_prompt_info=("FFTT_system_prompts/phase_two", "component_guideline_arbitration_prompt")
            ),
            240.0,  # 4 minutes timeout for arbitration
            refinement_context.context_id,
            "arbitration"
        )
        
        # Track the arbitration as a refinement iteration
        await self.refinement_manager.track_refinement_iteration(
            context_id=refinement_context.context_id,
            iteration_number=1,
            refinement_type="arbitration",
            input_data=arbitration_context,
            output_data=arbitration_result,
            success=success,
            duration_seconds=duration_seconds,
            metadata={"stage": 1}
        )
        
        # Store the arbitration result for later use
        self._arbitration_result = arbitration_result
        
        # Extract arbitration decision
        responsible_agent = None
        if success and isinstance(arbitration_result, dict) and "arbitration_results" in arbitration_result:
            # Extract responsible agent
            responsible_agent = arbitration_result["arbitration_results"].get("responsible_agent")
            
            # Store original agent identifier for better tracking
            self._root_cause_agent = arbitration_result["arbitration_results"].get("root_cause_agent")
            
            # Get the revision agent based on responsible agent
            agent_mapping = {
                "flower_bed_planner": ComponentValidationState.DESCRIPTION_REVISING,
                "flower_bed_environment": ComponentValidationState.REQUIREMENTS_REVISING,
                "flower_root_system": ComponentValidationState.DATA_FLOW_REVISING,
                "flower_placement": ComponentValidationState.FEATURES_REVISING
            }
            
            # Set appropriate validation state based on arbitration result
            revision_state = agent_mapping.get(responsible_agent)
            if revision_state:
                await self.set_validation_state(revision_state)
            else:
                # Default to description revision if no valid agent is returned
                await self.set_validation_state(ComponentValidationState.DESCRIPTION_REVISING)
                responsible_agent = "flower_bed_planner"
        else:
            # Default to description revision if no valid result is returned
            await self.set_validation_state(ComponentValidationState.DESCRIPTION_REVISING)
            responsible_agent = "flower_bed_planner"
            
        logger.info(f"Arbitration complete: {responsible_agent} should revise their output")
        
        # Clear the active refinement context ID as we're moving to a new state
        self._active_refinement_context_id = None
        
        # Record result metrics
        await self.metrics_manager.record_metric(
            "component_guideline:arbitration:completion",
            1.0,
            metadata={
                "component_id": self._component_id,
                "responsible_agent": responsible_agent,
                "root_cause_agent": self._root_cause_agent,
                "validation_attempt": self._validation_attempts,
                "duration_seconds": (datetime.now() - self._validation_start_time).total_seconds(),
                "timestamp": datetime.now().isoformat()
            }
        )
        
        return responsible_agent
    
    async def get_validation_status(self) -> Dict[str, Any]:
        """Get current validation status."""
        status = {
            "component_id": self._component_id,
            "component_name": self._component_name,
            "state": self.validation_state.value,
            "description_validated": self.validation_state.value not in [
                ComponentValidationState.NOT_STARTED.value,
                ComponentValidationState.DESCRIPTION_VALIDATING.value,
                ComponentValidationState.DESCRIPTION_REVISING.value
            ],
            "requirements_validated": self.validation_state.value not in [
                ComponentValidationState.NOT_STARTED.value,
                ComponentValidationState.DESCRIPTION_VALIDATING.value,
                ComponentValidationState.DESCRIPTION_REVISING.value,
                ComponentValidationState.REQUIREMENTS_VALIDATING.value,
                ComponentValidationState.REQUIREMENTS_REVISING.value
            ],
            "data_flow_validated": self.validation_state.value not in [
                ComponentValidationState.NOT_STARTED.value,
                ComponentValidationState.DESCRIPTION_VALIDATING.value,
                ComponentValidationState.DESCRIPTION_REVISING.value,
                ComponentValidationState.REQUIREMENTS_VALIDATING.value,
                ComponentValidationState.REQUIREMENTS_REVISING.value,
                ComponentValidationState.DATA_FLOW_VALIDATING.value,
                ComponentValidationState.DATA_FLOW_REVISING.value
            ],
            "features_validated": self.validation_state.value == ComponentValidationState.COMPLETED.value,
            "error_count": len(self._last_validation_errors),
            "timestamp": datetime.now().isoformat()
        }
        
        # Add refinement information if available
        if self._active_refinement_context_id:
            status["refinement_active"] = True
            status["refinement_context_id"] = self._active_refinement_context_id
            status["root_cause_agent"] = self._root_cause_agent
        else:
            status["refinement_active"] = False
            
        return status
        
    async def get_complete_guidelines(self) -> Dict[str, Any]:
        """
        Get the complete component guidelines that have passed validation.
        
        Returns None if validation is not complete.
        """
        if self.validation_state != ComponentValidationState.COMPLETED:
            logger.warning(f"Cannot get complete guidelines in state {self.validation_state}")
            return None
            
        # Assemble the complete component guidelines
        complete_guidelines = {
            "component_id": self._component_id,
            "component_name": self._component_name,
            "description": self._component_description.get("component_description", {}),
            "requirements": self._component_requirements.get("component_requirements", {}),
            "data_flow": self._component_data_flow.get("component_data_flow", {}),
            "features": self._component_features.get("features", []),
            "feature_relationships": self._component_features.get("feature_relationships", []),
            "feature_groups": self._component_features.get("feature_groups", []),
            "status": "completed",
            "timestamp": datetime.now().isoformat()
        }
        
        # Use Water agent for propagation if available
        if self.water_agent:
            try:
                await self.water_agent.propagate_guideline_update(
                    f"component_{self._component_id}",
                    complete_guidelines,
                    {}  # Context information would be provided here
                )
            except Exception as e:
                logger.error(f"Error propagating guidelines with Water agent: {str(e)}")
                # Continue without propagation
        
        return complete_guidelines
        
    async def execute_validation_workflow(self, max_attempts: int = 5) -> bool:
        """
        Execute the full validation workflow until completion or maximum attempts reached.
        
        Args:
            max_attempts: Maximum number of validation attempts (default: 5)
            
        Returns:
            bool: True if validation succeeds, False otherwise
        """
        self._validation_start_time = datetime.now()
        self._validation_attempts = 0
        current_attempt = 0
        
        while current_attempt < max_attempts:
            current_attempt += 1
            self._validation_attempts = current_attempt
            
            logger.info(f"Starting component validation workflow - attempt {current_attempt}/{max_attempts}")
            
            # Record attempt metrics
            await self.metrics_manager.record_metric(
                "component_guideline:validation:workflow_attempt",
                current_attempt,
                metadata={
                    "component_id": self._component_id,
                    "state": self.validation_state.value,
                    "max_attempts": max_attempts,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            try:
                # Handle based on current validation state
                if self.validation_state == ComponentValidationState.DESCRIPTION_REVISING:
                    logger.info("Executing component description revision")
                    await self.revise_component_description()
                        
                elif self.validation_state == ComponentValidationState.REQUIREMENTS_REVISING:
                    logger.info("Executing component requirements revision")
                    await self.revise_component_requirements()
                        
                elif self.validation_state == ComponentValidationState.DATA_FLOW_REVISING:
                    logger.info("Executing component data flow revision")
                    await self.revise_component_data_flow()
                        
                elif self.validation_state == ComponentValidationState.FEATURES_REVISING:
                    logger.info("Executing component features revision")
                    await self.revise_component_features()
                        
                elif self.validation_state == ComponentValidationState.ARBITRATION:
                    logger.info("Executing arbitration process")
                    responsible_agent = await self.perform_arbitration()
                    
                    # The perform_arbitration method already sets the appropriate validation state
                    # so we don't need to take any additional action here
                
                # Check if validation is complete
                if self.validation_state == ComponentValidationState.COMPLETED:
                    duration = (datetime.now() - self._validation_start_time).total_seconds()
                    logger.info(f"Validation workflow completed successfully after {current_attempt} attempts ({duration:.1f}s)")
                    
                    # Record success metrics
                    await self.metrics_manager.record_metric(
                        "component_guideline:validation:workflow_success",
                        duration,
                        metadata={
                            "component_id": self._component_id,
                            "attempts": current_attempt,
                            "max_attempts": max_attempts,
                            "timestamp": datetime.now().isoformat()
                        }
                    )
                    
                    return True
            except Exception as e:
                logger.error(f"Error in validation workflow attempt {current_attempt}: {str(e)}")
                
                # Record error metrics
                await self.metrics_manager.record_metric(
                    "component_guideline:validation:workflow_error",
                    1.0,
                    metadata={
                        "component_id": self._component_id,
                        "attempt": current_attempt,
                        "error": str(e),
                        "state": self.validation_state.value,
                        "timestamp": datetime.now().isoformat()
                    }
                )
        
        # If we reach here, we've exhausted all attempts
        duration = (datetime.now() - self._validation_start_time).total_seconds()
        logger.warning(f"Validation workflow failed after {max_attempts} attempts ({duration:.1f}s)")
        
        # Record failure metrics
        await self.metrics_manager.record_metric(
            "component_guideline:validation:workflow_failure",
            duration,
            metadata={
                "component_id": self._component_id,
                "attempts": current_attempt,
                "max_attempts": max_attempts,
                "final_state": self.validation_state.value,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        return False