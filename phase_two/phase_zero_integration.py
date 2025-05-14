"""
Integration module for Phase Zero contractors with Phase Two component guideline agents.

This module maps Phase Zero contractor agents to the appropriate component guideline agent
in Phase Two, ensuring consistent application of the FFTT conceptual framework.
"""
import logging
from typing import Dict, List, Any, Optional, Callable, Tuple, Awaitable
from datetime import datetime

from resources import (
    EventQueue, StateManager, MetricsManager, ResourceType, ResourceEventTypes
)
from resources.monitoring import MemoryMonitor, SystemMonitor, HealthStatus
from interface import AgentInterface

# Import agent mapping from Phase Zero
from FFTT_system_prompts.phase_zero.agent_mapping import (
    PHASE_1_TO_PHASE_2_MAPPING, 
    AGENT_PURPOSES
)

logger = logging.getLogger(__name__)

# Define agent types for component-level analysis
COMPONENT_AGENT_TYPES = {
    # Description Analysis Group
    "component_sun_agent": ("description", "critical_issues"),
    "component_shade_agent": ("description", "critical_gaps"),
    "component_wind_agent": ("description", "critical_conflicts"),
    
    # Requirement Analysis Group
    "component_soil_agent": ("requirements", "critical_gaps"),
    "component_microbial_agent": ("requirements", "critical_conflicts"),
    "component_rain_agent": ("requirements", "critical_issues"),
    "component_fertilizer_agent": ("requirements", "optimization"),
    
    # Data Flow Analysis Group
    "component_root_agent": ("data_flow", "critical_gaps"),
    "component_mycelial_agent": ("data_flow", "critical_conflicts"),
    "component_worm_agent": ("data_flow", "critical_issues"),
    
    # Structural Analysis Group
    "component_insect_agent": ("features", "critical_gaps"),
    "component_bird_agent": ("features", "critical_conflicts"),
    "component_tree_agent": ("features", "critical_issues"),
    "component_pollinator_agent": ("features", "optimization"),
    
    # Synthesis
    "component_evolution_agent": ("synthesis", "system_adaptations")
}

class PhaseZeroComponentIntegration:
    """
    Integrates Phase Zero contractor agents with Phase Two component guideline process.
    
    This class maps Phase Zero contractors to component guideline stages and manages
    the aggregation of feedback to incorporate into the component guideline process.
    """
    
    def __init__(
        self,
        event_queue: EventQueue,
        state_manager: StateManager,
        metrics_manager: MetricsManager = None,
        memory_monitor: MemoryMonitor = None,
        system_monitor: SystemMonitor = None
    ):
        """
        Initialize Phase Zero component integration.
        
        Args:
            event_queue: Event queue for communication
            state_manager: State manager for persistence
            metrics_manager: Metrics manager for metrics
            memory_monitor: Memory monitor for memory tracking
            system_monitor: System monitor for system monitoring
        """
        self.event_queue = event_queue
        self.state_manager = state_manager
        self.metrics_manager = metrics_manager
        self.memory_monitor = memory_monitor
        self.system_monitor = system_monitor
        
        # Store agents by type
        self._agents_by_type: Dict[str, Dict[str, AgentInterface]] = {
            "description": {},
            "requirements": {},
            "data_flow": {},
            "features": {},
            "synthesis": {}
        }
        
        # Store component analysis results
        self._component_analysis: Dict[str, Dict[str, Any]] = {}
        
        # Track processing state
        self._active_component_id = None
        
    def register_agent(self, agent_id: str, agent: AgentInterface) -> bool:
        """
        Register a Phase Zero contractor agent for integration.
        
        Args:
            agent_id: ID of the agent to register
            agent: Agent interface for interaction
            
        Returns:
            bool: True if registration succeeded, False otherwise
        """
        # Map from Phase Zero agent ID to component agent ID
        component_agent_id = PHASE_1_TO_PHASE_2_MAPPING.get(agent_id)
        
        if not component_agent_id:
            logger.warning(f"No component mapping found for agent {agent_id}")
            return False
            
        # Get agent type and category
        agent_type_info = COMPONENT_AGENT_TYPES.get(component_agent_id)
        
        if not agent_type_info:
            logger.warning(f"Unknown component agent type for {component_agent_id}")
            return False
            
        agent_type, agent_category = agent_type_info
        
        # Store agent by type
        self._agents_by_type[agent_type][agent_category] = agent
        
        logger.info(f"Registered agent {agent_id} for component {agent_type} - {agent_category}")
        return True
        
    async def analyze_component_description(
        self, 
        component_id: str,
        component_name: str,
        description: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze component description using Phase Zero contractor agents.
        
        Args:
            component_id: ID of the component being analyzed
            component_name: Name of the component being analyzed
            description: Component description to analyze
            
        Returns:
            Dict containing analysis results and feedback
        """
        # Set active component
        self._active_component_id = component_id
        
        # Initialize analysis results
        analysis_results = {
            "component_id": component_id,
            "component_name": component_name,
            "timestamp": datetime.now().isoformat(),
            "description_analysis": {}
        }
        
        # Keep track of metrics
        analysis_counts = {
            "critical_issues": 0,
            "critical_gaps": 0,
            "critical_conflicts": 0,
            "optimization": 0
        }
        
        # Process with each agent type for descriptions
        description_agents = self._agents_by_type["description"]
        
        # Check for critical issues (Sun agent)
        if "critical_issues" in description_agents:
            issues_result = await description_agents["critical_issues"].process_with_validation(
                conversation=f"Analyze component description for critical issues: {description}",
                system_prompt_info=("FFTT_system_prompts/phase_zero/phase_two_contractor", "sun_agent")
            )
            
            # Extract issues
            if "critical_description_issues" in issues_result:
                analysis_results["description_analysis"]["critical_issues"] = issues_result["critical_description_issues"]
                analysis_counts["critical_issues"] = self._count_issues(issues_result["critical_description_issues"])
            
        # Check for critical gaps (Shade agent)
        if "critical_gaps" in description_agents:
            gaps_result = await description_agents["critical_gaps"].process_with_validation(
                conversation=f"Analyze component description for critical gaps: {description}",
                system_prompt_info=("FFTT_system_prompts/phase_zero/phase_two_contractor", "shade_agent")
            )
            
            # Extract gaps
            if "critical_description_gaps" in gaps_result:
                analysis_results["description_analysis"]["critical_gaps"] = gaps_result["critical_description_gaps"]
                analysis_counts["critical_gaps"] = self._count_issues(gaps_result["critical_description_gaps"])
            
        # Check for critical conflicts (Wind agent)
        if "critical_conflicts" in description_agents:
            conflicts_result = await description_agents["critical_conflicts"].process_with_validation(
                conversation=f"Analyze component description for critical conflicts: {description}",
                system_prompt_info=("FFTT_system_prompts/phase_zero/phase_two_contractor", "wind_agent")
            )
            
            # Extract conflicts
            if "critical_description_conflicts" in conflicts_result:
                analysis_results["description_analysis"]["critical_conflicts"] = conflicts_result["critical_description_conflicts"]
                analysis_counts["critical_conflicts"] = self._count_issues(conflicts_result["critical_description_conflicts"])
        
        # Store analysis results
        await self.state_manager.set_state(
            f"component_phase_zero:description_analysis:{component_id}",
            analysis_results,
            ResourceType.STATE
        )
        
        # Cache in memory
        if component_id not in self._component_analysis:
            self._component_analysis[component_id] = {}
        self._component_analysis[component_id]["description"] = analysis_results
        
        # Record metrics
        await self._record_analysis_metrics(
            component_id, 
            "description", 
            analysis_counts
        )
        
        # Generate overall feedback based on analysis
        feedback = self._generate_description_feedback(analysis_results)
        analysis_results["feedback"] = feedback
        
        # Emit analysis event
        await self._emit_analysis_event(
            component_id,
            "description",
            analysis_results,
            analysis_counts
        )
        
        # Reset active component
        self._active_component_id = None
        
        return analysis_results
        
    async def analyze_component_requirements(
        self, 
        component_id: str,
        component_name: str,
        requirements: Dict[str, Any],
        description: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze component requirements using Phase Zero contractor agents.
        
        Args:
            component_id: ID of the component being analyzed
            component_name: Name of the component being analyzed
            requirements: Component requirements to analyze
            description: Optional component description for context
            
        Returns:
            Dict containing analysis results and feedback
        """
        # Set active component
        self._active_component_id = component_id
        
        # Initialize analysis results
        analysis_results = {
            "component_id": component_id,
            "component_name": component_name,
            "timestamp": datetime.now().isoformat(),
            "requirements_analysis": {}
        }
        
        # Keep track of metrics
        analysis_counts = {
            "critical_issues": 0,
            "critical_gaps": 0,
            "critical_conflicts": 0,
            "optimization": 0
        }
        
        # Create context with description if available
        context = {"component_requirements": requirements}
        if description:
            context["component_description"] = description
            
        # Process with each agent type for requirements
        requirements_agents = self._agents_by_type["requirements"]
        
        # Check for critical issues (Rain agent)
        if "critical_issues" in requirements_agents:
            issues_result = await requirements_agents["critical_issues"].process_with_validation(
                conversation=f"Analyze component requirements for critical issues: {context}",
                system_prompt_info=("FFTT_system_prompts/phase_zero/phase_two_contractor", "rain_agent")
            )
            
            # Extract issues
            if "critical_requirement_issues" in issues_result:
                analysis_results["requirements_analysis"]["critical_issues"] = issues_result["critical_requirement_issues"]
                analysis_counts["critical_issues"] = self._count_issues(issues_result["critical_requirement_issues"])
            
        # Check for critical gaps (Soil agent)
        if "critical_gaps" in requirements_agents:
            gaps_result = await requirements_agents["critical_gaps"].process_with_validation(
                conversation=f"Analyze component requirements for critical gaps: {context}",
                system_prompt_info=("FFTT_system_prompts/phase_zero/phase_two_contractor", "soil_agent")
            )
            
            # Extract gaps
            if "critical_requirement_gaps" in gaps_result:
                analysis_results["requirements_analysis"]["critical_gaps"] = gaps_result["critical_requirement_gaps"]
                analysis_counts["critical_gaps"] = self._count_issues(gaps_result["critical_requirement_gaps"])
            
        # Check for critical conflicts (Microbial agent)
        if "critical_conflicts" in requirements_agents:
            conflicts_result = await requirements_agents["critical_conflicts"].process_with_validation(
                conversation=f"Analyze component requirements for critical conflicts: {context}",
                system_prompt_info=("FFTT_system_prompts/phase_zero/phase_two_contractor", "microbial_agent")
            )
            
            # Extract conflicts
            if "critical_requirement_conflicts" in conflicts_result:
                analysis_results["requirements_analysis"]["critical_conflicts"] = conflicts_result["critical_requirement_conflicts"]
                analysis_counts["critical_conflicts"] = self._count_issues(conflicts_result["critical_requirement_conflicts"])
        
        # Check for optimization opportunities (Fertilizer agent)
        if "optimization" in requirements_agents:
            optimization_result = await requirements_agents["optimization"].process_with_validation(
                conversation=f"Analyze component requirements for optimization opportunities: {context}",
                system_prompt_info=("FFTT_system_prompts/phase_zero/phase_two_contractor", "fertilizer_agent")
            )
            
            # Extract optimization opportunities
            if "requirement_optimization_opportunities" in optimization_result:
                analysis_results["requirements_analysis"]["optimization"] = optimization_result["requirement_optimization_opportunities"]
                analysis_counts["optimization"] = self._count_issues(optimization_result["requirement_optimization_opportunities"])
        
        # Store analysis results
        await self.state_manager.set_state(
            f"component_phase_zero:requirements_analysis:{component_id}",
            analysis_results,
            ResourceType.STATE
        )
        
        # Cache in memory
        if component_id not in self._component_analysis:
            self._component_analysis[component_id] = {}
        self._component_analysis[component_id]["requirements"] = analysis_results
        
        # Record metrics
        await self._record_analysis_metrics(
            component_id, 
            "requirements", 
            analysis_counts
        )
        
        # Generate overall feedback based on analysis
        feedback = self._generate_requirements_feedback(analysis_results)
        analysis_results["feedback"] = feedback
        
        # Emit analysis event
        await self._emit_analysis_event(
            component_id,
            "requirements",
            analysis_results,
            analysis_counts
        )
        
        # Reset active component
        self._active_component_id = None
        
        return analysis_results
        
    async def analyze_component_data_flow(
        self, 
        component_id: str,
        component_name: str,
        data_flow: Dict[str, Any],
        requirements: Optional[Dict[str, Any]] = None,
        description: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze component data flow using Phase Zero contractor agents.
        
        Args:
            component_id: ID of the component being analyzed
            component_name: Name of the component being analyzed
            data_flow: Component data flow to analyze
            requirements: Optional component requirements for context
            description: Optional component description for context
            
        Returns:
            Dict containing analysis results and feedback
        """
        # Set active component
        self._active_component_id = component_id
        
        # Initialize analysis results
        analysis_results = {
            "component_id": component_id,
            "component_name": component_name,
            "timestamp": datetime.now().isoformat(),
            "data_flow_analysis": {}
        }
        
        # Keep track of metrics
        analysis_counts = {
            "critical_issues": 0,
            "critical_gaps": 0,
            "critical_conflicts": 0,
            "optimization": 0
        }
        
        # Create context with available information
        context = {"component_data_flow": data_flow}
        if requirements:
            context["component_requirements"] = requirements
        if description:
            context["component_description"] = description
            
        # Process with each agent type for data flow
        data_flow_agents = self._agents_by_type["data_flow"]
        
        # Check for critical issues (Worm agent)
        if "critical_issues" in data_flow_agents:
            issues_result = await data_flow_agents["critical_issues"].process_with_validation(
                conversation=f"Analyze component data flow for critical issues: {context}",
                system_prompt_info=("FFTT_system_prompts/phase_zero/phase_two_contractor", "worm_agent")
            )
            
            # Extract issues
            if "critical_data_flow_issues" in issues_result:
                analysis_results["data_flow_analysis"]["critical_issues"] = issues_result["critical_data_flow_issues"]
                analysis_counts["critical_issues"] = self._count_issues(issues_result["critical_data_flow_issues"])
            
        # Check for critical gaps (Root agent)
        if "critical_gaps" in data_flow_agents:
            gaps_result = await data_flow_agents["critical_gaps"].process_with_validation(
                conversation=f"Analyze component data flow for critical gaps: {context}",
                system_prompt_info=("FFTT_system_prompts/phase_zero/phase_two_contractor", "root_system_agent")
            )
            
            # Extract gaps
            if "critical_data_flow_gaps" in gaps_result:
                analysis_results["data_flow_analysis"]["critical_gaps"] = gaps_result["critical_data_flow_gaps"]
                analysis_counts["critical_gaps"] = self._count_issues(gaps_result["critical_data_flow_gaps"])
            
        # Check for critical conflicts (Mycelial agent)
        if "critical_conflicts" in data_flow_agents:
            conflicts_result = await data_flow_agents["critical_conflicts"].process_with_validation(
                conversation=f"Analyze component data flow for critical conflicts: {context}",
                system_prompt_info=("FFTT_system_prompts/phase_zero/phase_two_contractor", "mycelial_agent")
            )
            
            # Extract conflicts
            if "critical_data_flow_conflicts" in conflicts_result:
                analysis_results["data_flow_analysis"]["critical_conflicts"] = conflicts_result["critical_data_flow_conflicts"]
                analysis_counts["critical_conflicts"] = self._count_issues(conflicts_result["critical_data_flow_conflicts"])
        
        # Store analysis results
        await self.state_manager.set_state(
            f"component_phase_zero:data_flow_analysis:{component_id}",
            analysis_results,
            ResourceType.STATE
        )
        
        # Cache in memory
        if component_id not in self._component_analysis:
            self._component_analysis[component_id] = {}
        self._component_analysis[component_id]["data_flow"] = analysis_results
        
        # Record metrics
        await self._record_analysis_metrics(
            component_id, 
            "data_flow", 
            analysis_counts
        )
        
        # Generate overall feedback based on analysis
        feedback = self._generate_data_flow_feedback(analysis_results)
        analysis_results["feedback"] = feedback
        
        # Emit analysis event
        await self._emit_analysis_event(
            component_id,
            "data_flow",
            analysis_results,
            analysis_counts
        )
        
        # Reset active component
        self._active_component_id = None
        
        return analysis_results
        
    async def analyze_component_features(
        self, 
        component_id: str,
        component_name: str,
        features: Dict[str, Any],
        data_flow: Optional[Dict[str, Any]] = None,
        requirements: Optional[Dict[str, Any]] = None,
        description: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze component features using Phase Zero contractor agents.
        
        Args:
            component_id: ID of the component being analyzed
            component_name: Name of the component being analyzed
            features: Component features to analyze
            data_flow: Optional component data flow for context
            requirements: Optional component requirements for context
            description: Optional component description for context
            
        Returns:
            Dict containing analysis results and feedback
        """
        # Set active component
        self._active_component_id = component_id
        
        # Initialize analysis results
        analysis_results = {
            "component_id": component_id,
            "component_name": component_name,
            "timestamp": datetime.now().isoformat(),
            "features_analysis": {}
        }
        
        # Keep track of metrics
        analysis_counts = {
            "critical_issues": 0,
            "critical_gaps": 0,
            "critical_conflicts": 0,
            "optimization": 0
        }
        
        # Create context with available information
        context = {"component_features": features}
        if data_flow:
            context["component_data_flow"] = data_flow
        if requirements:
            context["component_requirements"] = requirements
        if description:
            context["component_description"] = description
            
        # Process with each agent type for features
        features_agents = self._agents_by_type["features"]
        
        # Check for critical issues (Tree agent)
        if "critical_issues" in features_agents:
            issues_result = await features_agents["critical_issues"].process_with_validation(
                conversation=f"Analyze component features for critical issues: {context}",
                system_prompt_info=("FFTT_system_prompts/phase_zero/phase_two_contractor", "tree_agent")
            )
            
            # Extract issues
            if "critical_features_issues" in issues_result:
                analysis_results["features_analysis"]["critical_issues"] = issues_result["critical_features_issues"]
                analysis_counts["critical_issues"] = self._count_issues(issues_result["critical_features_issues"])
            
        # Check for critical gaps (Insect agent)
        if "critical_gaps" in features_agents:
            gaps_result = await features_agents["critical_gaps"].process_with_validation(
                conversation=f"Analyze component features for critical gaps: {context}",
                system_prompt_info=("FFTT_system_prompts/phase_zero/phase_two_contractor", "insect_agent")
            )
            
            # Extract gaps
            if "critical_features_gaps" in gaps_result:
                analysis_results["features_analysis"]["critical_gaps"] = gaps_result["critical_features_gaps"]
                analysis_counts["critical_gaps"] = self._count_issues(gaps_result["critical_features_gaps"])
            
        # Check for critical conflicts (Bird agent)
        if "critical_conflicts" in features_agents:
            conflicts_result = await features_agents["critical_conflicts"].process_with_validation(
                conversation=f"Analyze component features for critical conflicts: {context}",
                system_prompt_info=("FFTT_system_prompts/phase_zero/phase_two_contractor", "bird_agent")
            )
            
            # Extract conflicts
            if "critical_features_conflicts" in conflicts_result:
                analysis_results["features_analysis"]["critical_conflicts"] = conflicts_result["critical_features_conflicts"]
                analysis_counts["critical_conflicts"] = self._count_issues(conflicts_result["critical_features_conflicts"])
                
        # Check for optimization opportunities (Pollinator agent)
        if "optimization" in features_agents:
            optimization_result = await features_agents["optimization"].process_with_validation(
                conversation=f"Analyze component features for optimization opportunities: {context}",
                system_prompt_info=("FFTT_system_prompts/phase_zero/phase_two_contractor", "pollinator_agent")
            )
            
            # Extract optimization opportunities
            if "features_optimization_opportunities" in optimization_result:
                analysis_results["features_analysis"]["optimization"] = optimization_result["features_optimization_opportunities"]
                analysis_counts["optimization"] = self._count_issues(optimization_result["features_optimization_opportunities"])
        
        # Store analysis results
        await self.state_manager.set_state(
            f"component_phase_zero:features_analysis:{component_id}",
            analysis_results,
            ResourceType.STATE
        )
        
        # Cache in memory
        if component_id not in self._component_analysis:
            self._component_analysis[component_id] = {}
        self._component_analysis[component_id]["features"] = analysis_results
        
        # Record metrics
        await self._record_analysis_metrics(
            component_id, 
            "features", 
            analysis_counts
        )
        
        # Generate overall feedback based on analysis
        feedback = self._generate_features_feedback(analysis_results)
        analysis_results["feedback"] = feedback
        
        # Emit analysis event
        await self._emit_analysis_event(
            component_id,
            "features",
            analysis_results,
            analysis_counts
        )
        
        # Reset active component
        self._active_component_id = None
        
        return analysis_results
        
    async def synthesize_component_analysis(
        self,
        component_id: str,
        component_name: str,
        all_analysis: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Synthesize all component analysis results using the Evolution agent.
        
        Args:
            component_id: ID of the component being analyzed
            component_name: Name of the component being analyzed
            all_analysis: Optional dictionary containing all analysis results
            
        Returns:
            Dict containing synthesis results and suggestions
        """
        # Set active component
        self._active_component_id = component_id
        
        # Retrieve all analysis results if not provided
        if not all_analysis:
            all_analysis = {}
            
            # Get description analysis
            description_analysis = await self.state_manager.get_state(
                f"component_phase_zero:description_analysis:{component_id}"
            )
            if description_analysis:
                all_analysis["description"] = description_analysis
                
            # Get requirements analysis
            requirements_analysis = await self.state_manager.get_state(
                f"component_phase_zero:requirements_analysis:{component_id}"
            )
            if requirements_analysis:
                all_analysis["requirements"] = requirements_analysis
                
            # Get data flow analysis
            data_flow_analysis = await self.state_manager.get_state(
                f"component_phase_zero:data_flow_analysis:{component_id}"
            )
            if data_flow_analysis:
                all_analysis["data_flow"] = data_flow_analysis
                
            # Get features analysis
            features_analysis = await self.state_manager.get_state(
                f"component_phase_zero:features_analysis:{component_id}"
            )
            if features_analysis:
                all_analysis["features"] = features_analysis
                
        # Process with evolution agent
        synthesis_agents = self._agents_by_type["synthesis"]
        synthesis_result = None
        
        if "system_adaptations" in synthesis_agents:
            evolution_agent = synthesis_agents["system_adaptations"]
            
            synthesis_result = await evolution_agent.process_with_validation(
                conversation=f"Synthesize component analysis and determine adaptations: {all_analysis}",
                system_prompt_info=("FFTT_system_prompts/phase_zero/phase_two_contractor", "evolution_agent")
            )
        
        if not synthesis_result:
            synthesis_result = {
                "component_id": component_id,
                "component_name": component_name,
                "timestamp": datetime.now().isoformat(),
                "synthesis": {
                    "status": "no_synthesis_agent_available"
                }
            }
        else:
            # Add metadata
            synthesis_result["component_id"] = component_id
            synthesis_result["component_name"] = component_name
            synthesis_result["timestamp"] = datetime.now().isoformat()
        
        # Store synthesis results
        await self.state_manager.set_state(
            f"component_phase_zero:synthesis:{component_id}",
            synthesis_result,
            ResourceType.STATE
        )
        
        # Cache in memory
        if component_id not in self._component_analysis:
            self._component_analysis[component_id] = {}
        self._component_analysis[component_id]["synthesis"] = synthesis_result
        
        # Record metrics
        await self.metrics_manager.record_metric(
            "component_guideline:synthesis:completed",
            1.0,
            metadata={
                "component_id": component_id,
                "component_name": component_name,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # Emit synthesis event
        await self.event_queue.emit(
            ResourceEventTypes.COMPONENT_PHASE_ZERO_SYNTHESIS_COMPLETE.value,
            {
                "component_id": component_id,
                "component_name": component_name,
                "synthesis_complete": True,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # Reset active component
        self._active_component_id = None
        
        return synthesis_result
        
    async def get_component_analysis(self, component_id: str) -> Dict[str, Any]:
        """
        Get all analysis results for a component.
        
        Args:
            component_id: ID of the component to get analysis for
            
        Returns:
            Dict containing all analysis results
        """
        # Return from memory if available
        if component_id in self._component_analysis:
            return self._component_analysis[component_id]
            
        # Retrieve from state manager
        analysis = {}
        
        # Get description analysis
        description_analysis = await self.state_manager.get_state(
            f"component_phase_zero:description_analysis:{component_id}"
        )
        if description_analysis:
            analysis["description"] = description_analysis
            
        # Get requirements analysis
        requirements_analysis = await self.state_manager.get_state(
            f"component_phase_zero:requirements_analysis:{component_id}"
        )
        if requirements_analysis:
            analysis["requirements"] = requirements_analysis
            
        # Get data flow analysis
        data_flow_analysis = await self.state_manager.get_state(
            f"component_phase_zero:data_flow_analysis:{component_id}"
        )
        if data_flow_analysis:
            analysis["data_flow"] = data_flow_analysis
            
        # Get features analysis
        features_analysis = await self.state_manager.get_state(
            f"component_phase_zero:features_analysis:{component_id}"
        )
        if features_analysis:
            analysis["features"] = features_analysis
            
        # Get synthesis
        synthesis = await self.state_manager.get_state(
            f"component_phase_zero:synthesis:{component_id}"
        )
        if synthesis:
            analysis["synthesis"] = synthesis
            
        # Store in memory for future use
        self._component_analysis[component_id] = analysis
        
        return analysis
    
    def _count_issues(self, issues_dict: Dict[str, Any]) -> int:
        """Count the total number of issues in an analysis result."""
        total = 0
        
        # Handle different formats
        if isinstance(issues_dict, dict):
            for category, issues in issues_dict.items():
                if isinstance(issues, list):
                    total += len(issues)
                    
        elif isinstance(issues_dict, list):
            total = len(issues_dict)
            
        return total
    
    async def _record_analysis_metrics(
        self,
        component_id: str,
        analysis_type: str,
        counts: Dict[str, int]
    ) -> None:
        """Record analysis metrics."""
        if not self.metrics_manager:
            return
            
        # Record overall metric
        await self.metrics_manager.record_metric(
            f"component_guideline:{analysis_type}_analysis:completed",
            1.0,
            metadata={
                "component_id": component_id,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # Record counts for each issue type
        for issue_type, count in counts.items():
            await self.metrics_manager.record_metric(
                f"component_guideline:{analysis_type}_analysis:{issue_type}",
                count,
                metadata={
                    "component_id": component_id,
                    "timestamp": datetime.now().isoformat()
                }
            )
    
    async def _emit_analysis_event(
        self,
        component_id: str,
        analysis_type: str,
        results: Dict[str, Any],
        counts: Dict[str, int]
    ) -> None:
        """Emit an analysis event."""
        # Create event data
        event_data = {
            "component_id": component_id,
            "analysis_type": analysis_type,
            "timestamp": datetime.now().isoformat(),
            "issue_counts": counts,
            "total_issues": sum(counts.values())
        }
        
        # Emit event
        await self.event_queue.emit(
            ResourceEventTypes.COMPONENT_PHASE_ZERO_ANALYSIS_COMPLETE.value,
            event_data
        )
    
    def _generate_description_feedback(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate feedback based on description analysis."""
        feedback = {
            "severity": "low",
            "requires_revision": False,
            "suggestion": "No significant issues detected."
        }
        
        # Extract analysis
        description_analysis = analysis_results.get("description_analysis", {})
        
        # Check for critical issues
        critical_issues = description_analysis.get("critical_issues", {})
        critical_gaps = description_analysis.get("critical_gaps", {})
        critical_conflicts = description_analysis.get("critical_conflicts", {})
        
        # Count total issues
        total_issues = (
            self._count_issues(critical_issues) +
            self._count_issues(critical_gaps) +
            self._count_issues(critical_conflicts)
        )
        
        if total_issues > 0:
            # Determine severity based on issue count
            if total_issues > 5:
                feedback["severity"] = "high"
                feedback["requires_revision"] = True
            elif total_issues > 2:
                feedback["severity"] = "medium"
                feedback["requires_revision"] = True
            
            # Generate suggestion
            suggestion = "Consider revising the component description to address: "
            details = []
            
            if self._count_issues(critical_issues) > 0:
                details.append(f"{self._count_issues(critical_issues)} critical issues")
            if self._count_issues(critical_gaps) > 0:
                details.append(f"{self._count_issues(critical_gaps)} critical gaps")
            if self._count_issues(critical_conflicts) > 0:
                details.append(f"{self._count_issues(critical_conflicts)} critical conflicts")
                
            feedback["suggestion"] = suggestion + ", ".join(details)
        
        return feedback
    
    def _generate_requirements_feedback(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate feedback based on requirements analysis."""
        feedback = {
            "severity": "low",
            "requires_revision": False,
            "suggestion": "No significant issues detected."
        }
        
        # Extract analysis
        requirements_analysis = analysis_results.get("requirements_analysis", {})
        
        # Check for critical issues
        critical_issues = requirements_analysis.get("critical_issues", {})
        critical_gaps = requirements_analysis.get("critical_gaps", {})
        critical_conflicts = requirements_analysis.get("critical_conflicts", {})
        optimization = requirements_analysis.get("optimization", {})
        
        # Count total issues (excluding optimization)
        total_issues = (
            self._count_issues(critical_issues) +
            self._count_issues(critical_gaps) +
            self._count_issues(critical_conflicts)
        )
        
        if total_issues > 0:
            # Determine severity based on issue count
            if total_issues > 5:
                feedback["severity"] = "high"
                feedback["requires_revision"] = True
            elif total_issues > 2:
                feedback["severity"] = "medium"
                feedback["requires_revision"] = True
            
            # Generate suggestion
            suggestion = "Consider revising the component requirements to address: "
            details = []
            
            if self._count_issues(critical_issues) > 0:
                details.append(f"{self._count_issues(critical_issues)} critical issues")
            if self._count_issues(critical_gaps) > 0:
                details.append(f"{self._count_issues(critical_gaps)} critical gaps")
            if self._count_issues(critical_conflicts) > 0:
                details.append(f"{self._count_issues(critical_conflicts)} critical conflicts")
                
            feedback["suggestion"] = suggestion + ", ".join(details)
        
        # Add optimization suggestions if any
        opt_count = self._count_issues(optimization)
        if opt_count > 0:
            if feedback["suggestion"] == "No significant issues detected.":
                feedback["suggestion"] = f"Consider {opt_count} optimization opportunities to improve the requirements."
            else:
                feedback["suggestion"] += f" Also consider {opt_count} optimization opportunities."
        
        return feedback
    
    def _generate_data_flow_feedback(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate feedback based on data flow analysis."""
        feedback = {
            "severity": "low",
            "requires_revision": False,
            "suggestion": "No significant issues detected."
        }
        
        # Extract analysis
        data_flow_analysis = analysis_results.get("data_flow_analysis", {})
        
        # Check for critical issues
        critical_issues = data_flow_analysis.get("critical_issues", {})
        critical_gaps = data_flow_analysis.get("critical_gaps", {})
        critical_conflicts = data_flow_analysis.get("critical_conflicts", {})
        
        # Count total issues
        total_issues = (
            self._count_issues(critical_issues) +
            self._count_issues(critical_gaps) +
            self._count_issues(critical_conflicts)
        )
        
        if total_issues > 0:
            # Determine severity based on issue count
            if total_issues > 5:
                feedback["severity"] = "high"
                feedback["requires_revision"] = True
            elif total_issues > 2:
                feedback["severity"] = "medium"
                feedback["requires_revision"] = True
            
            # Generate suggestion
            suggestion = "Consider revising the component data flow to address: "
            details = []
            
            if self._count_issues(critical_issues) > 0:
                details.append(f"{self._count_issues(critical_issues)} critical issues")
            if self._count_issues(critical_gaps) > 0:
                details.append(f"{self._count_issues(critical_gaps)} critical gaps")
            if self._count_issues(critical_conflicts) > 0:
                details.append(f"{self._count_issues(critical_conflicts)} critical conflicts")
                
            feedback["suggestion"] = suggestion + ", ".join(details)
        
        return feedback
    
    def _generate_features_feedback(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate feedback based on features analysis."""
        feedback = {
            "severity": "low",
            "requires_revision": False,
            "suggestion": "No significant issues detected."
        }
        
        # Extract analysis
        features_analysis = analysis_results.get("features_analysis", {})
        
        # Check for critical issues
        critical_issues = features_analysis.get("critical_issues", {})
        critical_gaps = features_analysis.get("critical_gaps", {})
        critical_conflicts = features_analysis.get("critical_conflicts", {})
        optimization = features_analysis.get("optimization", {})
        
        # Count total issues (excluding optimization)
        total_issues = (
            self._count_issues(critical_issues) +
            self._count_issues(critical_gaps) +
            self._count_issues(critical_conflicts)
        )
        
        if total_issues > 0:
            # Determine severity based on issue count
            if total_issues > 5:
                feedback["severity"] = "high"
                feedback["requires_revision"] = True
            elif total_issues > 2:
                feedback["severity"] = "medium"
                feedback["requires_revision"] = True
            
            # Generate suggestion
            suggestion = "Consider revising the component features to address: "
            details = []
            
            if self._count_issues(critical_issues) > 0:
                details.append(f"{self._count_issues(critical_issues)} critical issues")
            if self._count_issues(critical_gaps) > 0:
                details.append(f"{self._count_issues(critical_gaps)} critical gaps")
            if self._count_issues(critical_conflicts) > 0:
                details.append(f"{self._count_issues(critical_conflicts)} critical conflicts")
                
            feedback["suggestion"] = suggestion + ", ".join(details)
        
        # Add optimization suggestions if any
        opt_count = self._count_issues(optimization)
        if opt_count > 0:
            if feedback["suggestion"] == "No significant issues detected.":
                feedback["suggestion"] = f"Consider {opt_count} optimization opportunities to improve the features."
            else:
                feedback["suggestion"] += f" Also consider {opt_count} optimization opportunities."
        
        return feedback