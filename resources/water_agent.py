"""
Water Agent for propagating guideline updates across the dependency graph.

This module implements the Water elemental agent responsible for:
1. Coordinating the propagation of validated guideline updates
2. Generating rich contextual information for affected downstream agents
3. Managing the pre-validation and ordered propagation process
4. Verifying the successful application of updates across the system

The Water agent complements the Earth agent's validation by ensuring that
approved changes flow correctly through the dependency graph, maintaining
system consistency during evolution.
"""

import asyncio
import json
import logging
import uuid
from typing import Dict, List, Any, Optional, Set, Tuple, Literal
from dataclasses import dataclass, field, asdict
from datetime import datetime
from collections import defaultdict

from resources import (
    ResourceType, 
    ResourceEventTypes, 
    EventQueue, 
    StateManager, 
    AgentContextManager, 
    CacheManager, 
    MetricsManager,
    ErrorHandler,
    MemoryMonitor
)
from agent import Agent, AgentInterface
from dependency import DependencyInterface, DependencyValidator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define output types for the Water agent
PropagationPhase = Literal["ANALYSIS", "CONTEXT_GENERATION", "ADAPTATION_GUIDANCE"]

@dataclass
class PropagationContext:
    """Detailed context for a propagated update."""
    origin_agent_id: str
    target_agent_id: str
    update_id: str
    validation_result: Dict[str, Any]
    specific_changes: List[Dict[str, Any]]
    interface_impacts: List[Dict[str, Any]]
    behavioral_impacts: List[Dict[str, Any]]
    required_adaptations: List[Dict[str, Any]]
    rich_context: Optional[Dict[str, Any]] = None
    
@dataclass
class PropagationRequest:
    """Request for guideline propagation."""
    request_id: str
    origin_agent_id: str
    validated_update: Dict[str, Any]
    validation_result: Dict[str, Any]
    timestamp: datetime
    impact_score: float = 0.0
    affected_agents: List[str] = field(default_factory=list)
    
@dataclass
class PropagationResult:
    """Results of a completed propagation."""
    request_id: str
    success: bool
    propagation_map: Dict[str, Dict[str, Any]]
    failures: List[Dict[str, Any]]
    start_time: datetime
    end_time: datetime
    metrics: Dict[str, Any]

class WaterAgent(AgentInterface):
    """
    Water Agent for coordinating update propagation across the dependency graph.
    
    This agent is responsible for facilitating the propagation of validated
    guideline updates throughout the system, ensuring coherent evolution of
    the software architecture.
    
    As an LLM-powered agent, it provides rich contextual information explaining
    the "why" and "how" behind changes, enabling downstream agents to understand
    both technical and conceptual implications of the updates they receive.
    """
    
    def __init__(
        self,
        agent_id: str = "water_agent",
        event_queue: Optional[EventQueue] = None,
        state_manager: Optional[StateManager] = None,
        context_manager: Optional[AgentContextManager] = None,
        cache_manager: Optional[CacheManager] = None,
        metrics_manager: Optional[MetricsManager] = None,
        error_handler: Optional[ErrorHandler] = None,
        memory_monitor: Optional[MemoryMonitor] = None,
        earth_agent = None,
        model: str = "claude-3-7-sonnet-20250219",
        max_iterations: int = 3,
        max_propagation_attempts: int = 3
    ):
        # Initialize base resources if not provided
        if not event_queue:
            event_queue = EventQueue()
            asyncio.create_task(event_queue.start())
        
        if not state_manager:
            state_manager = StateManager(event_queue)
        
        if not context_manager:
            context_manager = AgentContextManager(event_queue)
            
        if not cache_manager:
            cache_manager = CacheManager(event_queue)
            
        if not metrics_manager:
            metrics_manager = MetricsManager(event_queue)
            
        if not error_handler:
            error_handler = ErrorHandler(event_queue)
            
        if not memory_monitor:
            memory_monitor = MemoryMonitor(event_queue)
        
        # Initialize base Agent class with resources
        super().__init__(
            agent_id,
            event_queue,
            state_manager,
            context_manager,
            cache_manager,
            metrics_manager,
            error_handler,
            memory_monitor,
            model=model
        )
        
        # Link to Earth agent for validation results
        self._earth_agent = earth_agent
        
        # Configuration
        self.max_propagation_attempts = max_propagation_attempts
        self.max_iterations = max_iterations
        self.propagation_history = {}
        self.revision_attempts = {}
        
        # Initialize dependency validator for dependency analysis
        self.dependency_validator = DependencyValidator(state_manager)
        
        # Register with system
        self._register_agent()
        
    def _register_agent(self):
        """Register the agent with the system resources."""
        logger.info(f"Registering Water agent ({self.agent_id}) with system resources")
        
        # Register agent state with state manager
        asyncio.create_task(self._state_manager.set_state(
            f"agent:{self.agent_id}:state",
            {
                "type": "water_agent",
                "status": "initialized",
                "timestamp": datetime.now().isoformat()
            },
            resource_type=ResourceType.STATE
        ))
        
        # Register event listeners
        self._event_queue.subscribe(
            "earth_agent:validation_complete", 
            self._handle_validation_complete
        )
        
        self._event_queue.subscribe(
            "agent:update_request",
            self._handle_update_request
        )
        
        # Log successful registration
        logger.info(f"Water agent ({self.agent_id}) successfully registered")
    
    async def _handle_validation_complete(self, event_data: Dict[str, Any]):
        """Handle validation complete events from Earth agent."""
        logger.info(f"Received validation complete event: {event_data}")
        
        # Check if validation was successful
        validation_result = event_data.get("validation_result", {})
        validation_category = validation_result.get("validation_category", "REJECTED")
        
        if validation_category in ["APPROVED", "CORRECTED"]:
            # Validated update ready for propagation
            logger.info(f"Validated update ready for propagation: {validation_category}")
            
            # Extract data
            operation_id = event_data.get("operation_id", "unknown")
            agent_id = event_data.get("agent_id", "unknown")
            update_data = event_data.get("updated_guideline", {})
            
            # Trigger propagation if auto-propagate is enabled
            auto_propagate = event_data.get("auto_propagate", True)
            if auto_propagate:
                await self.coordinate_propagation(
                    origin_agent_id=agent_id,
                    validated_update=update_data,
                    validation_result=validation_result
                )
    
    async def _handle_update_request(self, event_data: Dict[str, Any]):
        """Handle direct update request events."""
        logger.info(f"Received update request event: {event_data}")
        
        # Extract data
        origin_agent_id = event_data.get("origin_agent_id", "unknown")
        validated_update = event_data.get("validated_update", {})
        validation_result = event_data.get("validation_result", {})
        
        # Trigger propagation
        await self.coordinate_propagation(
            origin_agent_id=origin_agent_id,
            validated_update=validated_update,
            validation_result=validation_result
        )
    
    async def map_affected_agents(
        self,
        origin_agent_id: str,
        validated_update: Dict[str, Any]
    ) -> List[str]:
        """Map all agents affected by this update based on dependency analysis."""
        logger.info(f"Mapping agents affected by update from {origin_agent_id}")
        
        # First level is direct dependencies
        affected = set()
        direct_dependencies = await self._get_direct_dependencies(origin_agent_id)
        affected.update(direct_dependencies)
        
        # Perform transitive closure to find all affected agents
        for dep in direct_dependencies:
            transitive_deps = await self._get_transitive_dependencies(dep)
            affected.update(transitive_deps)
            
        # Filter based on actual update content
        filtered_affected = await self._filter_affected_by_relevance(
            list(affected), 
            origin_agent_id,
            validated_update
        )
        
        logger.info(f"Identified {len(filtered_affected)} affected agents: {filtered_affected}")
        return filtered_affected
    
    async def _get_direct_dependencies(self, agent_id: str) -> List[str]:
        """Get direct dependencies of an agent."""
        # This would be implemented using the DependencyInterface
        # For now, we'll use a simple mapping based on the structure
        dependency_chain = {
            "garden_planner": ["environmental_analysis", "root_system", "tree_placement"],
            "environmental_analysis": ["root_system", "tree_placement"],
            "root_system": ["tree_placement"],
            "tree_placement": []
        }
        
        return dependency_chain.get(agent_id, [])
    
    async def _get_transitive_dependencies(self, agent_id: str) -> List[str]:
        """Get transitive dependencies of an agent."""
        # This is a placeholder implementation
        # In a real implementation, this would traverse the dependency graph
        return []
    
    async def _filter_affected_by_relevance(
        self,
        affected_agents: List[str],
        origin_agent_id: str,
        validated_update: Dict[str, Any]
    ) -> List[str]:
        """Filter affected agents based on relevance to the specific update."""
        # Use LLM to analyze relevance based on update content
        propagation_analysis = await self._analyze_propagation(
            origin_agent_id,
            affected_agents,
            validated_update
        )
        
        # Extract affected agents from analysis results
        relevant_agents = []
        if "propagation_analysis" in propagation_analysis:
            affected_agents_analysis = propagation_analysis["propagation_analysis"].get("affected_agents", [])
            for agent in affected_agents_analysis:
                agent_id = agent.get("agent_id")
                if agent_id:
                    relevant_agents.append(agent_id)
        
        # If LLM analysis failed, fall back to original list
        if not relevant_agents:
            return affected_agents
            
        return relevant_agents
    
    async def _analyze_propagation(
        self,
        origin_agent_id: str,
        affected_agents: List[str],
        validated_update: Dict[str, Any],
        operation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Use LLM to analyze the propagation of an update through the dependency graph.
        
        This provides intelligent analysis of how the update should propagate,
        identifying affected agents, determining propagation order, and
        classifying the nature and impact of the update.
        """
        # Generate operation ID if not provided
        if not operation_id:
            operation_id = f"propagation_{datetime.now().isoformat()}_{origin_agent_id}"
            
        # Prepare propagation analysis context
        analysis_context = {
            "origin_agent_id": origin_agent_id,
            "potentially_affected_agents": affected_agents,
            "validated_update": validated_update,
            "dependency_structure": await self._get_dependency_structure(),
            "timestamp": datetime.now().isoformat()
        }
        
        # Convert to JSON for conversation
        conversation = json.dumps(analysis_context, indent=2)
        
        # Get response from LLM using Water Agent's propagation analysis prompt
        result = await self.process_with_validation(
            conversation=conversation,
            system_prompt_info=("FFTT_system_prompts/core_agents/water_agent/propagation_analysis_prompt", "propagation_analysis_prompt"),
            current_phase="propagation_analysis",
            operation_id=operation_id
        )
        
        # Apply reflection and revision process if needed
        if "propagation_analysis" in result:
            result = await self._reflect_and_revise(
                result,
                PropagationPhase.ANALYSIS,
                analysis_context,
                operation_id
            )
        
        return result
    
    async def _get_dependency_structure(self) -> Dict[str, Any]:
        """Get the overall dependency structure of the system."""
        # This would be implemented using the DependencyInterface
        # For now, we'll use a simple structure
        return {
            "agent_dependencies": {
                "garden_planner": ["environmental_analysis", "root_system", "tree_placement"],
                "environmental_analysis": ["root_system", "tree_placement"],
                "root_system": ["tree_placement"],
                "tree_placement": []
            },
            "hierarchy": {
                "top_level": ["garden_planner"],
                "middle_level": ["environmental_analysis", "root_system"],
                "bottom_level": ["tree_placement"]
            }
        }
    
    async def generate_agent_specific_context(
        self,
        origin_agent_id: str,
        target_agent_id: str,
        validated_update: Dict[str, Any],
        validation_result: Dict[str, Any],
        operation_id: Optional[str] = None
    ) -> PropagationContext:
        """
        Generate detailed context for a specific agent using LLM.
        
        This provides rich contextual information explaining the 'why' and 'how'
        behind changes, enabling the target agent to understand both technical 
        and conceptual implications of the update.
        """
        logger.info(f"Generating context for agent {target_agent_id} from update from {origin_agent_id}")
        
        # Generate operation ID if not provided
        if not operation_id:
            operation_id = f"context_{datetime.now().isoformat()}_{target_agent_id}"
        
        # Extract key components from the update (basic extraction)
        update_components = await self._extract_update_components(validated_update)
        
        # Analyze target agent's guidelines (basic extraction)
        target_guideline = await self._get_agent_guideline(target_agent_id)
        
        # Get basic impacts (placeholder implementation)
        interface_impacts = await self._analyze_interface_impacts(
            update_components, 
            target_guideline
        )
        
        behavioral_impacts = await self._analyze_behavioral_impacts(
            update_components, 
            target_guideline
        )
        
        # Determine required adaptations (placeholder implementation)
        required_adaptations = await self._determine_required_adaptations(
            interface_impacts,
            behavioral_impacts,
            target_guideline
        )
        
        # Generate update ID if not present
        update_id = validated_update.get("update_id", f"update_{uuid.uuid4().hex[:8]}")
        
        # Compile basic context
        basic_context = PropagationContext(
            origin_agent_id=origin_agent_id,
            target_agent_id=target_agent_id,
            update_id=update_id,
            validation_result=validation_result,
            specific_changes=update_components,
            interface_impacts=interface_impacts,
            behavioral_impacts=behavioral_impacts,
            required_adaptations=required_adaptations
        )
        
        # Generate rich context using LLM
        rich_context = await self._generate_rich_context(
            origin_agent_id,
            target_agent_id,
            validated_update,
            validation_result,
            basic_context,
            target_guideline,
            operation_id
        )
        
        # Update context with rich information
        if rich_context:
            basic_context.rich_context = rich_context
        
        return basic_context
    
    async def _generate_rich_context(
        self,
        origin_agent_id: str,
        target_agent_id: str,
        validated_update: Dict[str, Any],
        validation_result: Dict[str, Any],
        basic_context: PropagationContext,
        target_guideline: Dict[str, Any],
        operation_id: str
    ) -> Dict[str, Any]:
        """
        Generate rich contextual information using LLM to explain impacts and adaptations.
        
        This is the core function that leverages LLM capabilities to provide detailed
        context about why changes are happening and how they affect the target agent.
        """
        # Prepare context generation input
        context_input = {
            "origin_agent_id": origin_agent_id,
            "target_agent_id": target_agent_id,
            "update": validated_update,
            "validation_result": validation_result,
            "target_guideline": target_guideline,
            "basic_analysis": {
                "specific_changes": basic_context.specific_changes,
                "interface_impacts": basic_context.interface_impacts,
                "behavioral_impacts": basic_context.behavioral_impacts,
                "required_adaptations": basic_context.required_adaptations
            },
            "agent_roles": await self._get_agent_roles(),
            "timestamp": datetime.now().isoformat()
        }
        
        # Convert to JSON for conversation
        conversation = json.dumps(context_input, indent=2)
        
        # Get response from LLM using Water Agent's context generation prompt
        result = await self.process_with_validation(
            conversation=conversation,
            system_prompt_info=("FFTT_system_prompts/core_agents/water_agent/context_generation_prompt", "context_generation_prompt"),
            current_phase="context_generation",
            operation_id=operation_id
        )
        
        # Apply reflection and revision process if needed
        if "update_context" in result:
            result = await self._reflect_and_revise(
                result,
                PropagationPhase.CONTEXT_GENERATION,
                context_input,
                operation_id
            )
        
        return result
    
    async def _get_agent_roles(self) -> Dict[str, str]:
        """Get descriptions of agent roles in the system."""
        # This would be implemented using the AgentRegistry or similar
        # For now, we'll use a placeholder mapping
        return {
            "garden_planner": "High-level planning and coordination of garden components",
            "environmental_analysis": "Analysis of environmental conditions and constraints",
            "root_system": "Design and implementation of underlying root systems",
            "tree_placement": "Spatial arrangement and configuration of trees"
        }
    
    async def _extract_update_components(self, validated_update: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract the key components from an update."""
        # This is a basic implementation for component extraction
        components = []
        
        # Check for component updates
        if "ordered_components" in validated_update:
            for component in validated_update["ordered_components"]:
                components.append({
                    "type": "component",
                    "name": component.get("name", "unknown"),
                    "changed": True
                })
                
        # Check for feature updates
        if "features" in validated_update:
            for feature in validated_update["features"]:
                components.append({
                    "type": "feature",
                    "id": feature.get("id", "unknown"),
                    "changed": True
                })
                
        # Check for functionality updates
        if "functionalities" in validated_update:
            for func in validated_update["functionalities"]:
                components.append({
                    "type": "functionality",
                    "id": func.get("id", "unknown"),
                    "changed": True
                })
                
        return components
    
    async def _get_agent_guideline(self, agent_id: str) -> Dict[str, Any]:
        """Get the current guideline for an agent."""
        # Try to get from state manager
        guideline = await self._state_manager.get_state(f"agent:{agent_id}:guideline")
        
        if guideline:
            return guideline
        
        # Return empty placeholder if not found
        return {
            "agent_id": agent_id,
            "guideline": {}
        }
    
    async def _analyze_interface_impacts(
        self,
        update_components: List[Dict[str, Any]],
        target_guideline: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Analyze impacts on interfaces. (Basic implementation)"""
        return [{
            "type": "interface_impact",
            "severity": "medium",
            "description": "Interface may need to be updated"
        }]
    
    async def _analyze_behavioral_impacts(
        self,
        update_components: List[Dict[str, Any]],
        target_guideline: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Analyze impacts on behavior. (Basic implementation)"""
        return [{
            "type": "behavioral_impact",
            "severity": "low",
            "description": "Minor behavior adjustments may be needed"
        }]
    
    async def _determine_required_adaptations(
        self,
        interface_impacts: List[Dict[str, Any]],
        behavioral_impacts: List[Dict[str, Any]],
        target_guideline: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Determine required adaptations based on impacts. (Basic implementation)"""
        adaptations = []
        
        # Check for interface impacts
        for impact in interface_impacts:
            if impact.get("severity") in ["medium", "high"]:
                adaptations.append({
                    "type": "interface_adaptation",
                    "description": "Update interface to accommodate changes"
                })
                
        # Check for behavioral impacts
        for impact in behavioral_impacts:
            if impact.get("severity") in ["medium", "high"]:
                adaptations.append({
                    "type": "behavioral_adaptation",
                    "description": "Adjust behavior to align with upstream changes"
                })
                
        return adaptations
    
    async def _generate_adaptation_guidance(
        self,
        origin_agent_id: str,
        target_agent_id: str,
        propagation_context: PropagationContext,
        target_guideline: Dict[str, Any],
        operation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate detailed adaptation guidance using LLM.
        
        This provides specific, actionable guidance on how the target agent
        should adapt to the changes, with tailored recommendations for
        implementation and integration.
        """
        # Generate operation ID if not provided
        if not operation_id:
            operation_id = f"adaptation_{datetime.now().isoformat()}_{target_agent_id}"
            
        # Prepare adaptation guidance input
        adaptation_input = {
            "origin_agent_id": origin_agent_id,
            "target_agent_id": target_agent_id,
            "propagation_context": asdict(propagation_context),
            "target_guideline": target_guideline,
            "agent_role": (await self._get_agent_roles()).get(target_agent_id, "Unknown role"),
            "timestamp": datetime.now().isoformat()
        }
        
        # Convert to JSON for conversation
        conversation = json.dumps(adaptation_input, indent=2)
        
        # Get response from LLM using Water Agent's adaptation guidance prompt
        result = await self.process_with_validation(
            conversation=conversation,
            system_prompt_info=("FFTT_system_prompts/core_agents/water_agent/adaptation_guidance_prompt", "adaptation_guidance_prompt"),
            current_phase="adaptation_guidance",
            operation_id=operation_id
        )
        
        # Apply reflection and revision process if needed
        if "adaptation_guidance" in result:
            result = await self._reflect_and_revise(
                result,
                PropagationPhase.ADAPTATION_GUIDANCE,
                adaptation_input,
                operation_id
            )
        
        return result
    
    async def _reflect_and_revise(
        self,
        output_result: Dict[str, Any],
        phase: PropagationPhase,
        input_context: Dict[str, Any],
        operation_id: str
    ) -> Dict[str, Any]:
        """
        Apply reflection and revision process to improve output quality.
        
        Similar to Earth Agent's reflection/revision process, this implements
        a feedback loop to enhance the quality of Water Agent outputs.
        """
        # Initialize tracking for this operation
        if operation_id not in self.revision_attempts:
            self.revision_attempts[operation_id] = 0
            
        current_result = output_result
        reflection_prompt_info = ("FFTT_system_prompts/core_agents/water_agent/reflection_prompt", "reflection_prompt")
        revision_prompt_info = ("FFTT_system_prompts/core_agents/water_agent/revision_prompt", "revision_prompt")
        
        # Continue reflection/revision until max iterations reached
        while self.revision_attempts[operation_id] < self.max_iterations:
            try:
                # Increment revision attempt counter
                self.revision_attempts[operation_id] += 1
                current_attempt = self.revision_attempts[operation_id]
                
                logger.info(f"Starting reflection/revision iteration {current_attempt}/{self.max_iterations} for {operation_id}")
                
                # Prepare reflection context
                reflection_context = {
                    "input_context": input_context,
                    "output_result": current_result,
                    "phase": phase,
                    "iteration": current_attempt,
                    "timestamp": datetime.now().isoformat()
                }
                
                # Process reflection
                reflection_result = await self.process_with_validation(
                    conversation=json.dumps(reflection_context, indent=2),
                    system_prompt_info=reflection_prompt_info,
                    current_phase=f"{phase.lower()}_reflection",
                    operation_id=f"{operation_id}_reflection_{current_attempt}"
                )
                
                # Check if reflection indicates no significant issues
                critical_improvements = reflection_result.get("reflection_results", {}).get("critical_improvements", [])
                decision_quality = reflection_result.get("reflection_results", {}).get("overall_assessment", {}).get("decision_quality_score", 0)
                
                # If decision quality is high (>7) and no critical improvements, stop revision
                if decision_quality >= 7 and len(critical_improvements) == 0:
                    logger.info(f"Reflection indicates high quality decision ({decision_quality}/10) with no critical improvements needed. Stopping revision.")
                    break
                
                # Prepare revision context
                revision_context = {
                    "input_context": input_context,
                    "output_result": current_result,
                    "reflection_result": reflection_result,
                    "phase": phase,
                    "iteration": current_attempt,
                    "timestamp": datetime.now().isoformat()
                }
                
                # Process revision
                revision_result = await self.process_with_validation(
                    conversation=json.dumps(revision_context, indent=2),
                    system_prompt_info=revision_prompt_info,
                    current_phase=f"{phase.lower()}_revision",
                    operation_id=f"{operation_id}_revision_{current_attempt}"
                )
                
                # Update current result from revised validation
                if "revision_results" in revision_result and "revised_validation" in revision_result["revision_results"]:
                    current_result = revision_result["revision_results"]["revised_validation"]
                    
                    # Log revision outcome
                    confidence = revision_result.get("revision_results", {}).get("revision_summary", {}).get("confidence", {})
                    decision_changes = revision_result.get("revision_results", {}).get("revision_summary", {}).get("decision_changes", {})
                    
                    logger.info(f"Completed revision {current_attempt} with confidence score {confidence.get('score', 0)}/10")
                    
                    # If confidence is high (>8) and minimal changes, stop revision
                    if confidence.get("score", 0) >= 8 and not decision_changes.get("significant_content_changes", False):
                        logger.info(f"Revision indicates high confidence ({confidence.get('score', 0)}/10) with minimal changes. Stopping revision.")
                        break
                else:
                    # If revision fails to produce a revised validation, stop the process
                    logger.warning(f"Revision process failed to produce a revised validation in iteration {current_attempt}")
                    break
                
                # Track revision in state
                await self._state_manager.set_state(
                    f"water_agent:{operation_id}:revision:{current_attempt}",
                    {
                        "reflection": reflection_result,
                        "revision": revision_result,
                        "timestamp": datetime.now().isoformat()
                    },
                    resource_type=ResourceType.STATE
                )
                
                # Record metrics
                await self._metrics_manager.record_metric(
                    "water_agent:revision_completed",
                    1.0,
                    metadata={
                        "operation_id": operation_id,
                        "attempt": current_attempt,
                        "phase": phase,
                        "decision_quality": decision_quality,
                        "confidence": confidence.get("score", 0) if confidence else 0
                    }
                )
                
            except Exception as e:
                logger.error(f"Error in reflection/revision iteration {current_attempt}: {str(e)}")
                # Continue with current result despite error
                break
        
        # Return the final result after all iterations
        return current_result
    
    async def calculate_impact_score(
        self,
        validated_update: Dict[str, Any],
        affected_agents: List[str],
        propagation_analysis: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        Calculate the impact score of an update based on various factors.
        
        If propagation_analysis is provided, extract impact score from LLM analysis.
        Otherwise, use the basic heuristic calculation.
        """
        # If propagation analysis is available, use LLM-generated impact score
        if propagation_analysis and "propagation_analysis" in propagation_analysis:
            impact_assessment = propagation_analysis["propagation_analysis"].get("impact_assessment", {})
            overall_score = impact_assessment.get("overall_score")
            if overall_score is not None:
                logger.info(f"Using LLM-generated impact score: {overall_score}")
                return float(overall_score)
        
        # Fall back to basic heuristic calculation
        logger.info(f"Calculating impact score for update affecting {len(affected_agents)} agents")
        
        # Base score starts at 1.0
        score = 1.0
        
        # Factor 1: Number of affected agents
        score *= (1.0 + (len(affected_agents) / 10))
        
        # Factor 2: Interface changes (would require deeper inspection)
        if await self._has_interface_changes(validated_update):
            score *= 1.5
        
        # Factor 3: Position in dependency chain
        dependency_depth = await self._calculate_max_dependency_depth(affected_agents)
        score *= (1.0 + (dependency_depth / 5))
        
        # Factor 4: Fundamental component changes
        if await self._affects_core_components(validated_update):
            score *= 2.0
            
        logger.info(f"Impact score calculated: {score}")
        return score
    
    async def _has_interface_changes(self, validated_update: Dict[str, Any]) -> bool:
        """Check if an update contains interface changes."""
        # This is a placeholder implementation
        return True
    
    async def _calculate_max_dependency_depth(self, affected_agents: List[str]) -> int:
        """Calculate the maximum dependency depth of affected agents."""
        # This is a placeholder implementation
        return 1
    
    async def _affects_core_components(self, validated_update: Dict[str, Any]) -> bool:
        """Check if an update affects core components."""
        # This is a placeholder implementation
        return False
    
    async def _sort_by_dependency_order(
        self, 
        agents: List[str],
        propagation_analysis: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        Sort agents by their dependency order.
        
        If propagation_analysis is provided, use LLM-determined propagation order.
        Otherwise, fall back to basic topological sort.
        """
        # If propagation analysis is available, use LLM-generated propagation order
        if propagation_analysis and "propagation_analysis" in propagation_analysis:
            propagation_order = propagation_analysis["propagation_analysis"].get("propagation_order", [])
            if propagation_order:
                # Filter to only include agents in the original list
                filtered_order = [a for a in propagation_order if a in agents]
                # Add any missing agents at the end
                for agent in agents:
                    if agent not in filtered_order:
                        filtered_order.append(agent)
                return filtered_order
        
        # Fall back to basic dependency chain ordering
        # This is a placeholder implementation that assumes a linear dependency chain
        dependency_chain = {
            "garden_planner": 0,
            "environmental_analysis": 1,
            "root_system": 2,
            "tree_placement": 3
        }
        
        return sorted(agents, key=lambda a: dependency_chain.get(a, 999))
    
    async def coordinate_propagation(
        self,
        origin_agent_id: str,
        validated_update: Dict[str, Any],
        validation_result: Dict[str, Any]
    ) -> PropagationResult:
        """
        Coordinate the entire propagation process using LLM-powered analysis.
        
        This is the main entry point for propagating updates through the system.
        It performs propagation analysis, generates detailed context for each
        affected agent, and coordinates the update application in the proper order.
        """
        logger.info(f"Coordinating propagation for update from {origin_agent_id}")
        
        # Create propagation request
        request_id = f"prop_req_{uuid.uuid4().hex[:8]}"
        request = PropagationRequest(
            request_id=request_id,
            origin_agent_id=origin_agent_id,
            validated_update=validated_update,
            validation_result=validation_result,
            timestamp=datetime.now()
        )
        
        # Register propagation attempt
        await self._state_manager.set_state(
            f"water_agent:propagation:{request_id}",
            asdict(request),
            resource_type=ResourceType.STATE
        )
        
        # Use LLM to analyze propagation
        propagation_analysis = await self._analyze_propagation(
            origin_agent_id, 
            [], # Empty list because we want the LLM to identify affected agents
            validated_update,
            operation_id=f"analysis_{request_id}"
        )
        
        # Map affected agents based on propagation analysis
        affected_agents = await self.map_affected_agents(
            origin_agent_id, 
            validated_update
        )
        request.affected_agents = affected_agents
        
        # If no affected agents, return early
        if not affected_agents:
            logger.info(f"No affected agents found for update from {origin_agent_id}")
            
            result = PropagationResult(
                request_id=request_id,
                success=True,
                propagation_map={},
                failures=[],
                start_time=request.timestamp,
                end_time=datetime.now(),
                metrics={
                    "propagation_time_ms": (datetime.now() - request.timestamp).total_seconds() * 1000,
                    "affected_count": 0,
                    "success_count": 0,
                    "failure_count": 0
                }
            )
            
            # Record result
            await self._state_manager.set_state(
                f"water_agent:result:{request_id}",
                asdict(result),
                resource_type=ResourceType.STATE
            )
            
            return result
        
        # Calculate impact score using propagation analysis
        request.impact_score = await self.calculate_impact_score(
            validated_update,
            affected_agents,
            propagation_analysis
        )
        
        # Generate LLM-based rich context for each affected agent
        contexts = {}
        for agent_id in affected_agents:
            # Get basic context
            target_guideline = await self._get_agent_guideline(agent_id)
            
            # Generate rich context with LLM
            context = await self.generate_agent_specific_context(
                origin_agent_id,
                agent_id,
                validated_update,
                validation_result,
                operation_id=f"context_{request_id}_{agent_id}"
            )
            
            # Generate adaptation guidance with LLM
            adaptation_guidance = await self._generate_adaptation_guidance(
                origin_agent_id,
                agent_id,
                context,
                target_guideline,
                operation_id=f"adaptation_{request_id}_{agent_id}"
            )
            
            # Store context and guidance for this agent
            contexts[agent_id] = {
                "propagation_context": context,
                "adaptation_guidance": adaptation_guidance
            }
        
        # Execute pre-validation phase
        ready_signals = await self.collect_readiness_signals(
            affected_agents,
            contexts
        )
        
        # Check if all agents are ready
        if all(signal.get("ready", False) for signal in ready_signals.values()):
            # Execute ordered propagation based on LLM-determined order
            return await self.execute_ordered_propagation(
                request,
                contexts,
                ready_signals,
                propagation_analysis
            )
        else:
            # Handle rejection
            return await self.handle_propagation_rejection(
                request,
                contexts,
                ready_signals
            )
    
    async def collect_readiness_signals(
        self,
        affected_agents: List[str],
        contexts: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """Collect readiness signals from all affected agents."""
        logger.info(f"Collecting readiness signals from {len(affected_agents)} affected agents")
        
        readiness_signals = {}
        
        # Process in dependency order
        ordered_agents = await self._sort_by_dependency_order(affected_agents)
        
        for agent_id in ordered_agents:
            agent_context = contexts[agent_id]
            
            # Request pre-validation from agent
            try:
                signal = await self._request_agent_readiness(
                    agent_id,
                    agent_context
                )
                
                readiness_signals[agent_id] = {
                    "ready": signal.get("ready", False),
                    "concerns": signal.get("concerns", []),
                    "adaptations_needed": signal.get("adaptations_needed", []),
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error getting readiness from {agent_id}: {e}")
                readiness_signals[agent_id] = {
                    "ready": False,
                    "concerns": [{"type": "system_error", "description": str(e)}],
                    "timestamp": datetime.now().isoformat()
                }
        
        # Record readiness signals
        await self._state_manager.set_state(
            f"water_agent:readiness:{uuid.uuid4().hex[:8]}",
            readiness_signals,
            resource_type=ResourceType.STATE
        )
        
        logger.info(f"Readiness signals collected: {sum(1 for s in readiness_signals.values() if s.get('ready', False))}/{len(affected_agents)} ready")
        return readiness_signals
    
    async def _request_agent_readiness(
        self,
        agent_id: str,
        agent_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Request readiness signal from an agent."""
        logger.info(f"Requesting readiness from agent {agent_id}")
        
        # This is a placeholder implementation
        # In a real implementation, this would call the agent's
        # checkUpdateReadiness method
        
        # For now, simulate a positive response
        return {
            "ready": True,
            "concerns": [],
            "adaptations_needed": [],
            "timestamp": datetime.now().isoformat()
        }
    
    async def execute_ordered_propagation(
        self,
        request: PropagationRequest,
        contexts: Dict[str, Dict[str, Any]],
        ready_signals: Dict[str, Dict[str, Any]],
        propagation_analysis: Optional[Dict[str, Any]] = None
    ) -> PropagationResult:
        """Execute propagation in correct dependency order."""
        logger.info(f"Executing ordered propagation for {len(request.affected_agents)} agents")
        
        start_time = datetime.now()
        propagation_map = {}
        failures = []
        
        # Sort agents by dependency order, using LLM-determined order if available
        ordered_agents = await self._sort_by_dependency_order(
            request.affected_agents,
            propagation_analysis
        )
        
        # Apply updates in order
        for agent_id in ordered_agents:
            agent_context = contexts[agent_id]
            
            try:
                # Apply update to this agent
                result = await self._apply_update_to_agent(
                    agent_id,
                    agent_context,
                    request.validated_update
                )
                
                propagation_map[agent_id] = {
                    "success": result.get("success", False),
                    "timestamp": datetime.now().isoformat(),
                    "details": result
                }
                
                # If propagation failed, record failure
                if not result.get("success", False):
                    failures.append({
                        "agent_id": agent_id,
                        "reason": result.get("reason", "Unknown failure"),
                        "timestamp": datetime.now().isoformat()
                    })
                    # No need to break - continue with remaining agents
                    
            except Exception as e:
                logger.error(f"Error propagating to {agent_id}: {e}")
                failures.append({
                    "agent_id": agent_id,
                    "reason": str(e),
                    "timestamp": datetime.now().isoformat()
                })
        
        # Calculate success based on critical failures
        success = len(failures) == 0
        
        # Compile result
        result = PropagationResult(
            request_id=request.request_id,
            success=success,
            propagation_map=propagation_map,
            failures=failures,
            start_time=start_time,
            end_time=datetime.now(),
            metrics={
                "propagation_time_ms": (datetime.now() - start_time).total_seconds() * 1000,
                "affected_count": len(request.affected_agents),
                "success_count": sum(1 for r in propagation_map.values() if r.get("success", False)),
                "failure_count": len(failures)
            }
        )
        
        # Record result
        await self._state_manager.set_state(
            f"water_agent:result:{request.request_id}",
            asdict(result),
            resource_type=ResourceType.STATE
        )
        
        # Emit completion event
        await self._event_queue.emit_event(
            "water_agent:propagation_complete",
            {
                "request_id": request.request_id,
                "success": success,
                "affected_count": len(request.affected_agents),
                "failure_count": len(failures)
            }
        )
        
        logger.info(f"Propagation completed: success={success}, affected={len(request.affected_agents)}, failures={len(failures)}")
        return result
    
    async def _apply_update_to_agent(
        self,
        agent_id: str,
        agent_context: Dict[str, Any],
        validated_update: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply the update to a specific agent."""
        logger.info(f"Applying update to agent {agent_id}")
        
        # Get agent interface from registry
        agent_interface = await self._get_agent_interface(agent_id)
        
        if not agent_interface:
            logger.warning(f"Agent interface not found: {agent_id}")
            return {
                "success": False,
                "reason": f"Agent interface not found: {agent_id}"
            }
        
        try:
            # Extract relevant context for this agent
            propagation_context = agent_context.get("propagation_context")
            adaptation_guidance = agent_context.get("adaptation_guidance")
            
            # Request the agent to apply the update with rich context
            update_result = await agent_interface.apply_guideline_update(
                origin_agent_id=propagation_context.origin_agent_id,
                propagation_context=asdict(propagation_context),
                adaptation_guidance=adaptation_guidance,
                update_data=validated_update
            )
            
            # Verify the update succeeded
            if update_result.get("success", False):
                # Verify the updated guideline
                verification = await self._verify_agent_update(
                    agent_id,
                    propagation_context,
                    validated_update,
                    update_result
                )
                
                if verification.get("verified", False):
                    return {
                        "success": True,
                        "agent_id": agent_id,
                        "timestamp": datetime.now().isoformat(),
                        "verification": verification
                    }
                else:
                    return {
                        "success": False,
                        "agent_id": agent_id,
                        "reason": "Update verification failed",
                        "verification_errors": verification.get("errors", []),
                        "timestamp": datetime.now().isoformat()
                    }
            else:
                return {
                    "success": False,
                    "agent_id": agent_id,
                    "reason": update_result.get("reason", "Unknown error"),
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error applying update to {agent_id}: {e}")
            
            return {
                "success": False,
                "agent_id": agent_id,
                "reason": f"Exception: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    async def _get_agent_interface(self, agent_id: str):
        """Get an agent's interface."""
        # This is a placeholder implementation
        # In a real implementation, this would retrieve the agent interface
        # from the registry or interface system
        
        # For now, simulate a mock interface
        return MockAgentInterface(agent_id, self._state_manager)
    
    async def _verify_agent_update(
        self,
        agent_id: str,
        context: PropagationContext,
        validated_update: Dict[str, Any],
        update_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Verify that an agent's update was applied correctly."""
        logger.info(f"Verifying update for agent {agent_id}")
        
        # Check if the agent has verification capability
        agent_interface = await self._get_agent_interface(agent_id)
        
        if hasattr(agent_interface, "verify_guideline_update"):
            # Use agent's built-in verification
            verification = await agent_interface.verify_guideline_update(
                update_id=context.update_id
            )
            
            return verification
        else:
            # Perform basic verification
            try:
                # Get updated guideline
                updated_guideline = await self._get_agent_guideline(agent_id)
                
                # Check for required adaptations
                all_adaptations_applied = await self._check_adaptations_applied(
                    updated_guideline,
                    context.required_adaptations
                )
                
                if all_adaptations_applied:
                    return {
                        "verified": True,
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    return {
                        "verified": False,
                        "errors": ["Required adaptations not fully applied"],
                        "timestamp": datetime.now().isoformat()
                    }
                    
            except Exception as e:
                logger.error(f"Error verifying update for {agent_id}: {e}")
                
                return {
                    "verified": False,
                    "errors": [f"Verification error: {str(e)}"],
                    "timestamp": datetime.now().isoformat()
                }
    
    async def _check_adaptations_applied(
        self,
        updated_guideline: Dict[str, Any],
        required_adaptations: List[Dict[str, Any]]
    ) -> bool:
        """Check if all required adaptations have been applied."""
        # This is a placeholder implementation
        # In a real implementation, this would check the updated guideline
        # against the required adaptations
        return True
    
    async def handle_propagation_rejection(
        self,
        request: PropagationRequest,
        contexts: Dict[str, Dict[str, Any]],
        ready_signals: Dict[str, Dict[str, Any]]
    ) -> PropagationResult:
        """Handle the case where some agents reject the propagation."""
        logger.info(f"Handling propagation rejection for request {request.request_id}")
        
        start_time = datetime.now()
        
        # Identify agents that rejected the update
        rejecting_agents = {
            agent_id: signal
            for agent_id, signal in ready_signals.items()
            if not signal.get("ready", False)
        }
        
        # Record rejection details
        rejection_details = []
        for agent_id, signal in rejecting_agents.items():
            rejection_details.append({
                "agent_id": agent_id,
                "concerns": signal.get("concerns", []),
                "timestamp": signal.get("timestamp", datetime.now().isoformat())
            })
        
        # Create result with failures
        result = PropagationResult(
            request_id=request.request_id,
            success=False,
            propagation_map={},  # No propagation happened
            failures=rejection_details,
            start_time=start_time,
            end_time=datetime.now(),
            metrics={
                "propagation_time_ms": 0,  # No actual propagation
                "affected_count": len(request.affected_agents),
                "success_count": 0,
                "failure_count": len(rejection_details),
                "rejection_phase": "pre_validation"
            }
        )
        
        # Record result
        await self._state_manager.set_state(
            f"water_agent:rejection:{request.request_id}",
            asdict(result),
            resource_type=ResourceType.STATE
        )
        
        # Emit rejection event
        await self._event_queue.emit_event(
            "water_agent:propagation_rejected",
            {
                "request_id": request.request_id,
                "rejection_count": len(rejection_details),
                "affected_count": len(request.affected_agents)
            }
        )
        
        logger.info(f"Propagation rejected: {len(rejection_details)}/{len(request.affected_agents)} agents rejected")
        return result

# Mock class for testing
class MockAgentInterface:
    """Mock agent interface for testing."""
    
    def __init__(self, agent_id, state_manager):
        self.agent_id = agent_id
        self._state_manager = state_manager
    
    async def apply_guideline_update(
        self,
        origin_agent_id: str,
        propagation_context: Dict[str, Any],
        adaptation_guidance: Dict[str, Any],
        update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply a guideline update."""
        logger.info(f"[MOCK] Applying update from {origin_agent_id} to {self.agent_id}")
        
        update_id = propagation_context.get("update_id", "unknown")
        
        # Store the update and guidance
        await self._state_manager.set_state(
            f"agent:{self.agent_id}:guideline_update:{update_id}",
            {
                "origin_agent_id": origin_agent_id,
                "update_data": update_data,
                "propagation_context": propagation_context,
                "adaptation_guidance": adaptation_guidance,
                "timestamp": datetime.now().isoformat(),
                "status": "applied"
            }
        )
        
        return {
            "success": True,
            "agent_id": self.agent_id,
            "update_id": update_id,
            "timestamp": datetime.now().isoformat()
        }
    
    async def verify_guideline_update(self, update_id: str) -> Dict[str, Any]:
        """Verify a guideline update."""
        logger.info(f"[MOCK] Verifying update {update_id} for {self.agent_id}")
        
        # Get the update info
        update_info = await self._state_manager.get_state(
            f"agent:{self.agent_id}:guideline_update:{update_id}"
        )
        
        if not update_info:
            return {
                "verified": False,
                "errors": [f"Update {update_id} not found"],
                "timestamp": datetime.now().isoformat()
            }
        
        return {
            "verified": True,
            "agent_id": self.agent_id,
            "update_id": update_id,
            "timestamp": datetime.now().isoformat()
        }