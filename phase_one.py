import asyncio
import json
from typing import Callable, Dict, List, Any, Optional, Protocol
from dataclasses import dataclass, field
from datetime import datetime
import logging
from enum import Enum

from resources import ResourceType, ResourceEventTypes, EventQueue, StateManager, AgentContextManager, CacheManager, MetricsManager, ErrorHandler
from resources.monitoring import (
    CircuitBreaker, CircuitState, CircuitOpenError, CircuitBreakerConfig, MemoryThresholds,
    MemoryMonitor, HealthStatus, HealthTracker, SystemMonitor,
    SystemMonitorConfig
)
from interface import AgentInterface, AgentState

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DevelopmentState(Enum):
    INITIALIZING = "initializing" 
    ANALYZING = "analyzing"
    DESIGNING = "designing"
    VALIDATING = "validating"
    REFINING = "refining"
    ERROR = "error"
    COMPLETE = "complete"

@dataclass
class MonitoringFeedback:
    """Structure to process monitoring feedback from Phase Zero"""
    flag_raised: bool = False
    flag_type: Optional[str] = None
    recommendations: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MonitoringFeedback':
        """Create from monitoring result dictionary"""
        return cls(
            flag_raised=data.get('flag_raised', False),
            flag_type=data.get('flag_type'),
            recommendations=data.get('recommendations', []),
            timestamp=datetime.now()
        )

@dataclass
class AnalysisFeedback:
    """Structure to process deep analysis feedback from Phase Zero"""
    soil_analysis: Dict[str, Any] = field(default_factory=dict)
    microbial_analysis: Dict[str, Any] = field(default_factory=dict)
    root_system_analysis: Dict[str, Any] = field(default_factory=dict)
    mycelial_analysis: Dict[str, Any] = field(default_factory=dict)
    insect_analysis: Dict[str, Any] = field(default_factory=dict)
    bird_analysis: Dict[str, Any] = field(default_factory=dict)
    pollinator_analysis: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalysisFeedback':
        """Create from deep analysis dictionary"""
        return cls(
            soil_analysis=data.get('soil', {}),
            microbial_analysis=data.get('microbial', {}),
            root_system_analysis=data.get('root_system', {}),
            mycelial_analysis=data.get('mycelial', {}),
            insect_analysis=data.get('insect', {}),
            bird_analysis=data.get('bird', {}),
            pollinator_analysis=data.get('pollinator', {})
        )
    
    def get_critical_gaps(self) -> List[Dict[str, Any]]:
        """Extract all critical gaps from analysis feedback"""
        gaps = []
        
        # Extract gaps from soil analysis
        if 'critical_requirement_gaps' in self.soil_analysis:
            for category, items in self.soil_analysis['critical_requirement_gaps'].items():
                for item in items:
                    gaps.append({
                        'source': 'soil',
                        'category': category,
                        'details': item
                    })
        
        # Extract gaps from root system analysis
        if 'critical_data_flow_gaps' in self.root_system_analysis:
            for category, items in self.root_system_analysis['critical_data_flow_gaps'].items():
                for item in items:
                    gaps.append({
                        'source': 'root_system',
                        'category': category,
                        'details': item
                    })
                    
        # Extract gaps from insect analysis
        if 'critical_structure_gaps' in self.insect_analysis:
            for category, items in self.insect_analysis['critical_structure_gaps'].items():
                for item in items:
                    gaps.append({
                        'source': 'insect',
                        'category': category,
                        'details': item
                    })
        
        return gaps
    
    def get_critical_conflicts(self) -> List[Dict[str, Any]]:
        """Extract all critical conflicts from analysis feedback"""
        conflicts = []
        
        # Process for each relevant agent
        for source, data in [
            ('microbial', self.microbial_analysis),
            ('mycelial', self.mycelial_analysis),
            ('bird', self.bird_analysis)
        ]:
            if 'critical_guideline_conflicts' in data:
                for category, items in data['critical_guideline_conflicts'].items():
                    for item in items:
                        conflicts.append({
                            'source': source,
                            'category': category,
                            'details': item
                        })
        
        return conflicts
    
    def get_optimization_opportunities(self) -> List[Dict[str, Any]]:
        """Extract optimization opportunities from pollinator analysis"""
        opportunities = []
        
        if 'component_optimization_opportunities' in self.pollinator_analysis:
            for category, items in self.pollinator_analysis['component_optimization_opportunities'].items():
                for item in items:
                    opportunities.append({
                        'source': 'pollinator',
                        'category': category,
                        'details': item
                    })
        
        return opportunities

@dataclass
class EvolutionFeedback:
    """Structure to process evolution synthesis feedback from Phase Zero"""
    key_patterns: List[Dict[str, Any]] = field(default_factory=list)
    adaptations: List[Dict[str, Any]] = field(default_factory=list)
    priorities: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EvolutionFeedback':
        """Create from evolution synthesis dictionary"""
        strategic_adaptations = data.get('strategic_adaptations', {})
        return cls(
            key_patterns=strategic_adaptations.get('key_patterns', []),
            adaptations=strategic_adaptations.get('adaptations', []),
            priorities=strategic_adaptations.get('priorities', {})
        )
    
@dataclass
class RefinementContext:
    iteration: int
    agent_id: str
    original_output: Dict[str, Any]
    refined_output: Dict[str, Any]
    refinement_guidance: Dict[str, Any]
    timestamp: datetime = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "iteration": self.iteration,
            "agent_id": self.agent_id,
            "original_output": self.original_output,
            "refined_output": self.refined_output,
            "refinement_guidance": self.refinement_guidance,
            "timestamp": self.timestamp.isoformat()
        }

class PhaseZeroInterface(Protocol):
    async def process_system_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        pass

@dataclass
class CircuitBreakerDefinition:
    """Configuration for a circuit breaker."""
    name: str
    failure_threshold: int = 3
    recovery_timeout: int = 30
    failure_window: int = 120

@dataclass
class AgentPromptConfig:
    """Configuration for agent prompt paths."""
    system_prompt_base_path: str
    reflection_prompt_name: str
    refinement_prompt_name: str
    initial_prompt_name: str

class ReflectiveAgent(AgentInterface):
    """Enhanced base class for reflective agents with proper resource management."""
    
    def __init__(
        self, 
        agent_id: str, 
        event_queue: EventQueue,
        state_manager: StateManager,
        context_manager: AgentContextManager,
        cache_manager: CacheManager,
        metrics_manager: MetricsManager,
        error_handler: ErrorHandler,
        memory_monitor: MemoryMonitor,
        prompt_config: AgentPromptConfig,
        circuit_breakers: List[CircuitBreakerDefinition] = None,
        health_tracker: HealthTracker = None
    ):
        super().__init__(agent_id, event_queue, state_manager, context_manager, cache_manager, metrics_manager, error_handler, memory_monitor)
        self._development_state = DevelopmentState.INITIALIZING
        self._prompt_config = prompt_config
        
        # Monitoring integrations
        self._health_tracker = health_tracker
        self._memory_monitor = memory_monitor
        
        # Circuit breaker registry
        self._circuit_breakers = {}
        
        # Always create a processing circuit breaker
        self._create_circuit_breaker("processing")
        
        # Create additional circuit breakers if provided
        if circuit_breakers:
            for cb_def in circuit_breakers:
                self._create_circuit_breaker(
                    cb_def.name, 
                    failure_threshold=cb_def.failure_threshold,
                    recovery_timeout=cb_def.recovery_timeout,
                    failure_window=cb_def.failure_window
                )
        
        # Mapping between development states and agent states
        self._state_mapping = {
            DevelopmentState.INITIALIZING: AgentState.READY,
            DevelopmentState.ANALYZING: AgentState.PROCESSING,
            DevelopmentState.DESIGNING: AgentState.PROCESSING,
            DevelopmentState.VALIDATING: AgentState.VALIDATING,
            DevelopmentState.REFINING: AgentState.PROCESSING,
            DevelopmentState.ERROR: AgentState.ERROR,
            DevelopmentState.COMPLETE: AgentState.COMPLETE
        }

        # Initial health report (deferred to async initialization)
        asyncio.create_task(self._ensure_initialized_and_report_health())
    
    async def _ensure_initialized_and_report_health(self):
        """Ensure initialization and report health"""
        await self.ensure_initialized()
        self._report_agent_health()

    def _create_circuit_breaker(
        self, 
        name: str, 
        failure_threshold: int = 3,
        recovery_timeout: int = 30,
        failure_window: int = 120
    ) -> CircuitBreaker:
        """Create and register a circuit breaker."""
        circuit_id = f"{self.interface_id}_{name}"
        
        self._circuit_breakers[name] = CircuitBreaker(
            circuit_id,
            self._event_queue,
            config=CircuitBreakerConfig(
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout,
                failure_window=failure_window
            )
        )
        
        return self._circuit_breakers[name]
    
    def get_circuit_breaker(self, name: str) -> CircuitBreaker:
        """Get a circuit breaker by name."""
        if name not in self._circuit_breakers:
            # Create default if doesn't exist
            return self._create_circuit_breaker(name)
        return self._circuit_breakers[name]
    
    # Health reporting methods
    
    def _report_agent_health(self, custom_status: str = None, description: str = None, metadata: Dict[str, Any] = None):
        """Report agent health status to health tracker."""
        if not self._health_tracker:
            return
            
        # Map development state to health status if not provided
        state_health_mapping = {
            DevelopmentState.INITIALIZING: "HEALTHY",
            DevelopmentState.ANALYZING: "HEALTHY",
            DevelopmentState.DESIGNING: "HEALTHY",
            DevelopmentState.VALIDATING: "HEALTHY",
            DevelopmentState.REFINING: "DEGRADED",
            DevelopmentState.ERROR: "CRITICAL",
            DevelopmentState.COMPLETE: "HEALTHY"
        }
        
        status = custom_status or state_health_mapping.get(self._development_state, "UNKNOWN")
        desc = description or f"Agent {self.interface_id} in state {self._development_state.value}"
        
        # Merge metadata
        meta = {"development_state": self._development_state.value}
        if metadata:
            meta.update(metadata)
        
        # Create health status object
        health_status = HealthStatus(
            status=status,
            source=f"agent_{self.interface_id}",
            description=desc,
            metadata=meta
        )
        
        # Update health tracker asynchronously
        return self._health_tracker.update_health(
            f"agent_{self.interface_id}", 
            health_status
        )
    
    # Memory tracking methods
    
    async def track_string_memory(self, resource_id: str, string_value: str) -> None:
        """Track memory usage of a string resource."""
        if self._memory_monitor:
            size_mb = len(string_value) / (1024 * 1024)  # Rough estimation
            await self.track_memory_usage(resource_id, size_mb)
    
    async def track_dict_memory(self, resource_id: str, dict_value: Dict[str, Any]) -> None:
        """Track memory usage of a dictionary resource."""
        if self._memory_monitor:
            size_mb = len(json.dumps(dict_value)) / (1024 * 1024)  # Rough estimation
            await self.track_memory_usage(resource_id, size_mb)
    
    # Reflection and validation methods
    
    async def standard_reflect(
        self, 
        output: Dict[str, Any],
        circuit_name: str = "processing",
        prompt_path: str = None,
        prompt_name: str = None
    ) -> Dict[str, Any]:
        """Standardized reflection with monitoring."""
        # Ensure initialization
        await self.ensure_initialized()
        
        # Set state and report health
        self.development_state = DevelopmentState.VALIDATING
        
        # Track memory usage of the output
        await self.track_dict_memory("reflection_input", output)
        
        # Use configured paths or overrides
        _prompt_path = prompt_path or self._prompt_config.system_prompt_base_path
        _prompt_name = prompt_name or self._prompt_config.reflection_prompt_name
        
        try:
            # Use circuit breaker for reflection
            return await self.get_circuit_breaker(circuit_name).execute(
                lambda: self.process_with_validation(
                    conversation=f"Reflect on output with a critical eye for fundamental errors and / or faulty assumptions: {output}",
                    system_prompt_info=(_prompt_path, _prompt_name)
                )
            )
        except CircuitOpenError:
            logger.warning(f"Reflection circuit open for agent {self.interface_id}, reflection rejected")
            
            # Report critical health status
            await self._report_agent_health(
                custom_status="CRITICAL",
                description=f"Reflection rejected due to circuit breaker open",
                metadata={
                    "state": "VALIDATING",
                    "circuit": "open"
                }
            )
            
            return {
                "error": "Reflection rejected due to circuit breaker open",
                "status": "failure",
                "agent_id": self.interface_id,
                "timestamp": datetime.now().isoformat(),
                "reflection_results": {
                    "validation_status": {
                        "passed": False
                    }
                }
            }
    
    async def standard_refine(
        self, 
        output: Dict[str, Any], 
        refinement_guidance: Dict[str, Any],
        circuit_name: str = "processing",
        prompt_path: str = None,
        prompt_name: str = None
    ) -> Dict[str, Any]:
        """Standardized refinement with monitoring."""
        # Ensure initialization
        await self.ensure_initialized()

        # Set state and report health
        self.development_state = DevelopmentState.REFINING
        
        # Track memory usage
        combined_size_mb = (len(json.dumps(output)) + len(json.dumps(refinement_guidance))) / (1024 * 1024)
        await self.track_memory_usage("refinement_data", combined_size_mb)
        
        # Use configured paths or overrides
        _prompt_path = prompt_path or self._prompt_config.system_prompt_base_path
        _prompt_name = prompt_name or self._prompt_config.refinement_prompt_name
        
        try:
            # Use circuit breaker for refinement
            refinement_result = await self.get_circuit_breaker(circuit_name).execute(
                lambda: self.process_with_validation(
                    conversation=f"""Refine output based on:
                    Original output: {output}
                    Refinement guidance: {refinement_guidance}""",
                    system_prompt_info=(_prompt_path, _prompt_name)
                )
            )
            
            # Update health status based on refinement result
            if self._health_tracker:
                status = "HEALTHY" if refinement_result.get("status") == "success" else "DEGRADED"
                await self._report_agent_health(
                    custom_status=status,
                    description="Refinement completed",
                    metadata={
                        "state": "COMPLETE" if status == "HEALTHY" else "REFINING",
                        "refinement_status": refinement_result.get("status", "unknown")
                    }
                )
            
            return refinement_result
            
        except CircuitOpenError:
            logger.warning(f"Refinement circuit open for agent {self.interface_id}, refinement rejected")
            
            # Report critical health status
            await self._report_agent_health(
                custom_status="CRITICAL",
                description=f"Refinement rejected due to circuit breaker open",
                metadata={
                    "state": "REFINING",
                    "circuit": "open"
                }
            )
            
            return {
                "error": "Refinement rejected due to circuit breaker open",
                "status": "failure",
                "agent_id": self.interface_id,
                "timestamp": datetime.now().isoformat()
            }
    
    async def track_memory_usage(self, resource_id: str, size_mb: float) -> None:
        """Track memory usage of agent resources."""
        if self._memory_monitor:
            await self._memory_monitor.track_resource(
                f"agent:{self.interface_id}:{resource_id}",
                size_mb,
                f"agent_{self.interface_id}"
            )
            
    async def add_refinement_iteration(
        self,
        context: RefinementContext
    ) -> None:
        """Record refinement iteration with proper persistence."""
        # Store in state manager
        await self._state_manager.set_state(
            f"agent:{self.interface_id}:refinement:{context.iteration}",
            context.to_dict(),
            ResourceType.STATE
        )
        
        # Update refinement history in context
        agent_context = await self._context_manager.get_context(
            f"agent_context:{self.interface_id}"
        )
        if agent_context:
            refinement_history = agent_context.refinement_history or []
            refinement_history.append(context.to_dict())
            await self._context_manager.store_context(
                f"agent_context:{self.interface_id}",
                agent_context
            )
            
    async def get_refinement_history(self) -> List[Dict[str, Any]]:
        """Get refinement history from context manager."""
        agent_context = await self._context_manager.get_context(
            f"agent_context:{self.interface_id}"
        )
        if agent_context:
            return agent_context.refinement_history or []
        return []

class GardenPlannerAgent(ReflectiveAgent):
    def __init__(self, agent_id: str, event_queue: EventQueue,
                state_manager: StateManager,
                context_manager: AgentContextManager,
                cache_manager: CacheManager,
                metrics_manager: MetricsManager,
                error_handler: ErrorHandler,
                memory_monitor: MemoryMonitor,
                 health_tracker: HealthTracker = None):
        
        # Define prompt configuration
        prompt_config = AgentPromptConfig(
            system_prompt_base_path="FFTT_system_prompts/phase_one/garden_planner_agent",
            reflection_prompt_name="task_reflection_prompt",
            refinement_prompt_name="task_elaboration_refinement_prompt",
            initial_prompt_name="initial_task_elaboration_prompt"
        )
        
        # Define circuit breakers
        circuit_breakers = [
            CircuitBreakerDefinition(
                name="analysis",
                failure_threshold=3,
                recovery_timeout=30,
                failure_window=120
            )
        ]
        
        # Initialize base class with configuration
        super().__init__(
            agent_id, 
            event_queue, state_manager, context_manager, cache_manager, metrics_manager, error_handler, 
            prompt_config,
            circuit_breakers,
            health_tracker, 
            memory_monitor
        )
        
        # Set initial state
        self.development_state = DevelopmentState.INITIALIZING
        self.validation_history = []
        
        # Register with memory monitor if available
        if self._memory_monitor:
            # Register specific thresholds for this agent
            self._memory_monitor.register_component(
                f"agent_{agent_id}",
                MemoryThresholds(
                    per_resource_max_mb=50,  # Max size of any resource
                    warning_percent=0.5,     # 50% warning threshold
                    critical_percent=0.8     # 80% critical threshold
                )
            )

    async def _process(self, task_prompt: str) -> Dict[str, Any]:
        """Process the task prompt with proper async handling and monitoring."""
        try:
            # Track memory usage of the task prompt
            await self.track_string_memory("task_prompt", task_prompt)
            
            # Process initial analysis with circuit breaker protection
            try:
                initial_analysis = await self.get_circuit_breaker("analysis").execute(
                    lambda: self.process_with_validation(
                        conversation=f"Analyze task requirements: {task_prompt}",
                        system_prompt_info=(self._prompt_config.system_prompt_base_path, 
                                          self._prompt_config.initial_prompt_name)
                    )
                )
            except CircuitOpenError:
                logger.warning(f"Analysis circuit open for agent {self.interface_id}, processing rejected")
                self.development_state = DevelopmentState.ERROR
                return {
                    "error": "Analysis rejected due to circuit breaker open",
                    "status": "failure",
                    "agent_id": self.interface_id,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Use standardized reflection method
            reflection_result = await self.standard_reflect(
                initial_analysis,
                circuit_name="analysis"
            )
            
            # Check validation status from reflection
            if not (await self._get_validation_status(reflection_result)):
                self.development_state = DevelopmentState.REFINING
                return reflection_result
            
            # Report healthy status after successful processing
            await self._report_agent_health(
                custom_status="HEALTHY",
                description="Successfully processed task",
                metadata={
                    "development_state": "COMPLETE",
                    "validation_status": "passed"
                }
            )
            
            return initial_analysis
            
        except Exception as e:
            self.development_state = DevelopmentState.ERROR
            await self._report_agent_health(
                custom_status="CRITICAL",
                description=f"Processing error: {str(e)}",
                metadata={
                    "development_state": "ERROR",
                    "error": str(e)
                }
            )
            raise

    # Now only the specialized methods or overrides remain
    async def reflect(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """Delegate to standardized reflection method."""
        return await self.standard_reflect(output, "analysis")

    async def refine(self, output: Dict[str, Any], refinement_guidance: Dict[str, Any]) -> Dict[str, Any]:
        """Delegate to standardized refinement method."""
        return await self.standard_refine(output, refinement_guidance, "analysis")

    async def _get_validation_status(self, reflection_result: Dict[str, Any]) -> bool:
        """Extract validation status from reflection result."""
        try:
            return reflection_result.get("reflection_results", {}).get("validation_status", {}).get("passed", False)
        except Exception:
            return False
               
class EnvironmentalAnalysisAgent(ReflectiveAgent):
    def __init__(self, agent_id: str, event_queue: EventQueue,
                state_manager: StateManager,
                context_manager: AgentContextManager,
                cache_manager: CacheManager,
                metrics_manager: MetricsManager,
                error_handler: ErrorHandler,
                 memory_monitor: MemoryMonitor,
                 health_tracker: HealthTracker = None):
        
        # Define prompt configuration
        prompt_config = AgentPromptConfig(
            system_prompt_base_path="FFTT_system_prompts/phase_one/environmental_analysis_agent",
            reflection_prompt_name="core_requirements_reflection_prompt",
            refinement_prompt_name="core_requirements_refinement_prompt",
            initial_prompt_name="initial_core_requirements_prompt"
        )
        
        # Define circuit breakers
        circuit_breakers = [
            CircuitBreakerDefinition(
                name="analysis",
                failure_threshold=3,
                recovery_timeout=30,
                failure_window=120
            )
        ]
        
        # Initialize base class with configuration
        super().__init__(
            agent_id, 
            event_queue, state_manager, context_manager, cache_manager, metrics_manager, error_handler, 
            prompt_config,
            circuit_breakers,
            health_tracker, 
            memory_monitor
        )
        
        # Set initial state
        self.development_state = DevelopmentState.INITIALIZING
        
        # Register with memory monitor if available
        if self._memory_monitor:
            self._memory_monitor.register_component(
                f"agent_{agent_id}",
                MemoryThresholds(
                    per_resource_max_mb=70,  # Environment data could be larger
                    warning_percent=0.5,
                    critical_percent=0.8
                )
            )

    async def _process(self, garden_planner_output: Dict[str, Any]) -> Dict[str, Any]:
        """Process garden planner output with monitoring."""
        try:
            # Track memory usage of input data
            await self.track_dict_memory("garden_planner_input", garden_planner_output)
            
            # Update health status to processing
            await self._report_agent_health(
                description="Processing environment analysis",
                metadata={"state": "ANALYZING"}
            )
            
            # Process analysis with circuit breaker protection
            try:
                self.development_state = DevelopmentState.ANALYZING
                
                initial_analysis = await self.get_circuit_breaker("analysis").execute(
                    lambda: self.process_with_validation(
                        conversation=f"Analyze environment based on: {garden_planner_output}",
                        system_prompt_info=(self._prompt_config.system_prompt_base_path, 
                                          self._prompt_config.initial_prompt_name)
                    )
                )
            except CircuitOpenError:
                logger.warning(f"Analysis circuit open for agent {self.interface_id}, processing rejected")
                self.development_state = DevelopmentState.ERROR
                return {
                    "error": "Analysis rejected due to circuit breaker open",
                    "status": "failure",
                    "agent_id": self.interface_id,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Track memory usage of analysis result
            await self.track_dict_memory("analysis_result", initial_analysis)
            
            # Use standardized reflection method
            reflection_result = await self.standard_reflect(
                initial_analysis,
                circuit_name="analysis"
            )
            
            # Check validation status
            if not reflection_result["reflection_results"]["validation_status"]["passed"]:
                self.development_state = DevelopmentState.REFINING
                
                # Report degraded health
                await self._report_agent_health(
                    custom_status="DEGRADED",
                    description="Validation failed, entering refinement",
                    metadata={
                        "state": "REFINING",
                        "validation": "failed"
                    }
                )
                
                return reflection_result
            
            # Set state to complete and report success
            self.development_state = DevelopmentState.COMPLETE
            
            await self._report_agent_health(
                description="Environment analysis completed successfully",
                metadata={"state": "COMPLETE"}
            )
            
            return initial_analysis
            
        except Exception as e:
            self.development_state = DevelopmentState.ERROR
            
            await self._report_agent_health(
                custom_status="CRITICAL",
                description=f"Processing error: {str(e)}",
                metadata={
                    "state": "ERROR",
                    "error": str(e)
                }
            )
            
            raise

    async def reflect(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """Delegate to standardized reflection method."""
        return await self.standard_reflect(output, "analysis")

    async def refine(self, output: Dict[str, Any], refinement_guidance: Dict[str, Any]) -> Dict[str, Any]:
        """Delegate to standardized refinement method."""
        return await self.standard_refine(output, refinement_guidance, "analysis")
     
class RootSystemArchitectAgent(ReflectiveAgent):
    def __init__(self, agent_id: str, event_queue: EventQueue,
                state_manager: StateManager,
                context_manager: AgentContextManager,
                cache_manager: CacheManager,
                metrics_manager: MetricsManager,
                error_handler: ErrorHandler,
                 memory_monitor: MemoryMonitor,
                 health_tracker: HealthTracker = None):
        
        # Define prompt configuration
        prompt_config = AgentPromptConfig(
            system_prompt_base_path="FFTT_system_prompts/phase_one/root_system_architect_agent",
            reflection_prompt_name="core_data_flow_reflection_prompt",
            refinement_prompt_name="core_data_flow_refinement_prompt",
            initial_prompt_name="initial_core_data_flow_prompt"
        )
        
        # Define circuit breakers
        circuit_breakers = [
            CircuitBreakerDefinition(
                name="design",
                failure_threshold=3,
                recovery_timeout=45,   # Longer timeout for complex design work
                failure_window=180     # Consider failures over longer period
            )
        ]
        
        # Initialize base class with configuration
        super().__init__(
            agent_id, 
            event_queue, state_manager, context_manager, cache_manager, metrics_manager, error_handler, 
            prompt_config,
            circuit_breakers,
            health_tracker, 
            memory_monitor
        )
        
        # Set initial state
        self.development_state = DevelopmentState.INITIALIZING
        
        # Register with memory monitor if available
        if self._memory_monitor:
            self._memory_monitor.register_component(
                f"agent_{agent_id}",
                MemoryThresholds(
                    per_resource_max_mb=100,  # Architecture diagrams can be larger
                    warning_percent=0.6,
                    critical_percent=0.85
                )
            )

    async def _process(self, garden_planner_output: Dict[str, Any],
                     environment_analysis_output: Dict[str, Any]) -> Dict[str, Any]:
        """Process architecture design with monitoring."""
        try:
            # Track memory usage of input data
            await self.track_dict_memory("garden_planner_input", garden_planner_output)
            await self.track_dict_memory("environment_analysis_input", environment_analysis_output)
            
            # Calculate total input size for monitoring
            planner_size_mb = len(json.dumps(garden_planner_output)) / (1024 * 1024)
            env_size_mb = len(json.dumps(environment_analysis_output)) / (1024 * 1024)
            await self.track_memory_usage("total_input", planner_size_mb + env_size_mb)
            
            # Update health status to designing
            await self._report_agent_health(
                description="Designing data architecture",
                metadata={
                    "state": "DESIGNING",
                    "input_sources": ["garden_planner", "environment_analysis"]
                }
            )
            
            # Design architecture with circuit breaker protection
            try:
                self.development_state = DevelopmentState.DESIGNING
                
                initial_design = await self.get_circuit_breaker("design").execute(
                    lambda: self.process_with_validation(
                        conversation=f"""Design data architecture based on:
                        Garden planner: {garden_planner_output}
                        Environment analysis: {environment_analysis_output}""",
                        system_prompt_info=(self._prompt_config.system_prompt_base_path, 
                                          self._prompt_config.initial_prompt_name)
                    )
                )
            except CircuitOpenError:
                logger.warning(f"Design circuit open for agent {self.interface_id}, processing rejected")
                self.development_state = DevelopmentState.ERROR
                
                await self._report_agent_health(
                    custom_status="CRITICAL",
                    description="Design rejected due to circuit breaker open",
                    metadata={
                        "state": "ERROR",
                        "circuit": "design_circuit",
                        "circuit_state": "OPEN"
                    }
                )
                
                return {
                    "error": "Design operation rejected due to circuit breaker open",
                    "status": "failure",
                    "agent_id": self.interface_id,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Track memory usage of design result
            await self.track_dict_memory("initial_design", initial_design)
            
            # Use standardized reflection method
            self.development_state = DevelopmentState.VALIDATING
            reflection_result = await self.standard_reflect(
                initial_design,
                circuit_name="design"
            )
            
            # Check validation status
            if not reflection_result["reflection_results"]["validation_status"]["passed"]:
                self.development_state = DevelopmentState.REFINING
                
                await self._report_agent_health(
                    custom_status="DEGRADED",
                    description="Validation failed, design requires refinement",
                    metadata={
                        "state": "REFINING",
                        "validation": "failed"
                    }
                )
                
                return reflection_result
            
            # Set state to complete
            self.development_state = DevelopmentState.COMPLETE
            
            # Record metrics for successful design
            await self._metrics_manager.record_metric(
                f"agent:{self.interface_id}:design_completed",
                1.0,
                metadata={
                    "timestamp": datetime.now().isoformat(),
                    "validation": "passed"
                }
            )
            
            await self._report_agent_health(
                description="Data architecture design completed successfully",
                metadata={"state": "COMPLETE"}
            )
            
            return initial_design
            
        except Exception as e:
            self.development_state = DevelopmentState.ERROR
            
            await self._report_agent_health(
                custom_status="CRITICAL",
                description=f"Design error: {str(e)}",
                metadata={
                    "state": "ERROR",
                    "error": str(e)
                }
            )
            
            # Record error metric
            await self._metrics_manager.record_metric(
                f"agent:{self.interface_id}:design_errors",
                1.0,
                metadata={
                    "timestamp": datetime.now().isoformat(),
                    "error": str(e)
                }
            )
            
            raise

    async def reflect(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """Specialized reflection method that measures performance."""
        reflection_start = datetime.now()
        
        result = await self.standard_reflect(output, "design")
        
        # Track reflection time
        reflection_time = (datetime.now() - reflection_start).total_seconds()
        await self._metrics_manager.record_metric(
            f"agent:{self.interface_id}:reflection_time",
            reflection_time,
            metadata={"success": True}
        )
        
        return result

    async def refine(self, output: Dict[str, Any], refinement_guidance: Dict[str, Any]) -> Dict[str, Any]:
        """Specialized refinement method that measures performance."""
        refinement_start = datetime.now()
        
        result = await self.standard_refine(output, refinement_guidance, "design")
        
        # Track refinement time
        refinement_time = (datetime.now() - refinement_start).total_seconds()
        await self._metrics_manager.record_metric(
            f"agent:{self.interface_id}:refinement_time",
            refinement_time,
            metadata={"success": True}
        )
        
        return result
    
class TreePlacementPlannerAgent(ReflectiveAgent):
    def __init__(self, agent_id: str, event_queue: EventQueue,
                state_manager: StateManager,
                context_manager: AgentContextManager,
                cache_manager: CacheManager,
                metrics_manager: MetricsManager,
                error_handler: ErrorHandler,
                 memory_monitor: MemoryMonitor,
                 health_tracker: HealthTracker = None):
        
        # Define prompt configuration
        prompt_config = AgentPromptConfig(
            system_prompt_base_path="FFTT_system_prompts/phase_one/tree_placement_planner_agent",
            reflection_prompt_name="structural_component_reflection_prompt",
            refinement_prompt_name="structural_component_refinement_prompt",
            initial_prompt_name="initial_structural_components_prompt"
        )
        
        # Define circuit breakers
        circuit_breakers = [
            CircuitBreakerDefinition(
                name="component_design",
                failure_threshold=4,      # More failures allowed for complex component design
                recovery_timeout=40,
                failure_window=180
            )
        ]
        
        # Initialize base class with configuration
        super().__init__(
            agent_id, 
            event_queue, state_manager, context_manager, cache_manager, metrics_manager, error_handler, 
            prompt_config,
            circuit_breakers,
            health_tracker, 
            memory_monitor
        )
        
        # Set initial state
        self.development_state = DevelopmentState.INITIALIZING
        
        # Register with memory monitor if available
        if self._memory_monitor:
            self._memory_monitor.register_component(
                f"agent_{agent_id}",
                MemoryThresholds(
                    per_resource_max_mb=120,  # Component diagrams can be larger
                    warning_percent=0.6,
                    critical_percent=0.85
                )
            )
            
        # Initialize performance tracking
        self._processing_times = []
        self._component_counts = []

    async def _process(self, garden_planner_output: Dict[str, Any],
                      environment_analysis_output: Dict[str, Any],
                      root_system_output: Dict[str, Any]) -> Dict[str, Any]:
        """Process component architecture design with monitoring."""
        processing_start = datetime.now()
        
        try:
            # Track memory usage of input data
            await self.track_dict_memory("garden_planner_input", garden_planner_output)
            await self.track_dict_memory("environment_analysis_input", environment_analysis_output)
            await self.track_dict_memory("root_system_input", root_system_output)
            
            # Calculate total input size for monitoring
            planner_size_mb = len(json.dumps(garden_planner_output)) / (1024 * 1024)
            env_size_mb = len(json.dumps(environment_analysis_output)) / (1024 * 1024)
            root_size_mb = len(json.dumps(root_system_output)) / (1024 * 1024)
            await self.track_memory_usage("total_input", planner_size_mb + env_size_mb + root_size_mb)
            
            # Count expected components from requirements (estimated)
            estimated_components = self._estimate_component_count(
                garden_planner_output, 
                environment_analysis_output
            )
            
            # Update health status to designing
            await self._report_agent_health(
                description="Designing component architecture",
                metadata={
                    "state": "DESIGNING",
                    "input_sources": ["garden_planner", "environment_analysis", "root_system"],
                    "estimated_components": estimated_components
                }
            )
            
            # Design components with circuit breaker protection
            try:
                self.development_state = DevelopmentState.DESIGNING
                
                initial_design = await self.get_circuit_breaker("component_design").execute(
                    lambda: self.process_with_validation(
                        conversation=f"""Design component architecture based on:
                        Garden planner: {garden_planner_output}
                        Environment analysis: {environment_analysis_output}
                        Root system: {root_system_output}""",
                        system_prompt_info=(self._prompt_config.system_prompt_base_path, 
                                          self._prompt_config.initial_prompt_name)
                    )
                )
            except CircuitOpenError:
                logger.warning(f"Component design circuit open for agent {self.interface_id}, processing rejected")
                self.development_state = DevelopmentState.ERROR
                
                await self._report_agent_health(
                    custom_status="CRITICAL",
                    description="Component design rejected due to circuit breaker open",
                    metadata={
                        "state": "ERROR",
                        "circuit": "component_design_circuit",
                        "circuit_state": "OPEN"
                    }
                )
                
                return {
                    "error": "Component design operation rejected due to circuit breaker open",
                    "status": "failure",
                    "agent_id": self.interface_id,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Track memory usage of design result
            await self.track_dict_memory("component_design", initial_design)
            
            # Count actual components in the design
            actual_components = self._count_components(initial_design)
            
            # Store component counts for metrics
            self._component_counts.append(actual_components)
            
            # Record component metrics
            await self._metrics_manager.record_metric(
                f"agent:{self.interface_id}:component_count",
                actual_components,
                metadata={
                    "timestamp": datetime.now().isoformat(),
                    "estimated": estimated_components
                }
            )
            
            # Use standardized reflection method
            self.development_state = DevelopmentState.VALIDATING
            reflection_result = await self.reflect(initial_design)
            
            # Check validation status
            if not reflection_result["reflection_results"]["validation_status"]["passed"]:
                self.development_state = DevelopmentState.REFINING
                
                await self._report_agent_health(
                    custom_status="DEGRADED",
                    description="Validation failed, component design requires refinement",
                    metadata={
                        "state": "REFINING",
                        "validation": "failed",
                        "component_count": actual_components
                    }
                )
                
                return reflection_result
            
            # Set state to complete
            self.development_state = DevelopmentState.COMPLETE
            
            # Calculate processing time
            processing_time = (datetime.now() - processing_start).total_seconds()
            self._processing_times.append(processing_time)
            
            # Record processing time metric
            await self._metrics_manager.record_metric(
                f"agent:{self.interface_id}:processing_time",
                processing_time,
                metadata={
                    "component_count": actual_components,
                    "success": True
                }
            )
            
            # Track average time per component
            if actual_components > 0:
                await self._metrics_manager.record_metric(
                    f"agent:{self.interface_id}:time_per_component",
                    processing_time / actual_components,
                    metadata={"timestamp": datetime.now().isoformat()}
                )
            
            await self._report_agent_health(
                description="Component architecture design completed successfully",
                metadata={
                    "state": "COMPLETE",
                    "component_count": actual_components,
                    "processing_time": processing_time
                }
            )
            
            return initial_design
            
        except Exception as e:
            self.development_state = DevelopmentState.ERROR
            
            # Calculate processing time before failure
            processing_time = (datetime.now() - processing_start).total_seconds()
            
            # Record error metrics
            await self._metrics_manager.record_metric(
                f"agent:{self.interface_id}:processing_errors",
                1.0,
                metadata={
                    "error": str(e),
                    "processing_time": processing_time
                }
            )
            
            await self._report_agent_health(
                custom_status="CRITICAL",
                description=f"Component design error: {str(e)}",
                metadata={
                    "state": "ERROR",
                    "error": str(e),
                    "processing_time": processing_time
                }
            )
            
            raise

    async def reflect(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """Specialized reflection method that measures performance."""
        reflection_start = datetime.now()
        
        result = await self.standard_reflect(output, "component_design")
        
        # Calculate reflection time
        reflection_time = (datetime.now() - reflection_start).total_seconds()
        
        # Record reflection time metric
        await self._metrics_manager.record_metric(
            f"agent:{self.interface_id}:reflection_time",
            reflection_time,
            metadata={"success": True}
        )
        
        return result

    async def refine(self, output: Dict[str, Any], refinement_guidance: Dict[str, Any]) -> Dict[str, Any]:
        """Specialized refinement method with component metrics."""
        refinement_start = datetime.now()
        
        refinement_result = await self.standard_refine(
            output, 
            refinement_guidance, 
            "component_design"
        )
        
        # Calculate refinement time
        refinement_time = (datetime.now() - refinement_start).total_seconds()
        
        # Track component counts in refined design
        refined_components = self._count_components(refinement_result)
        
        # Record refinement metrics
        await self._metrics_manager.record_metric(
            f"agent:{self.interface_id}:refinement_time",
            refinement_time,
            metadata={
                "success": True,
                "component_count": refined_components
            }
        )
        
        return refinement_result
    
    # Helper methods specific to TreePlacementPlannerAgent
    def _estimate_component_count(self, garden_planner_output: Dict[str, Any],
                                   environment_analysis_output: Dict[str, Any]) -> int:
        """Estimate number of components based on requirements (helper method)."""
        try:
            # Simple estimation based on requirements length
            requirements_str = json.dumps(garden_planner_output) + json.dumps(environment_analysis_output)
            # Rough estimation: 1 component per 1000 chars of requirements
            estimated = max(3, len(requirements_str) // 1000)
            return estimated
        except Exception:
            # Default estimate if parsing fails
            return 5
    
    def _count_components(self, design_output: Dict[str, Any]) -> int:
        """Count actual components in design output (helper method)."""
        try:
            # Try to extract component count from design output
            components = design_output.get("components", [])
            if isinstance(components, list):
                return len(components)
            
            # Alternative way to count if structure is different
            design_str = json.dumps(design_output)
            component_mentions = design_str.count("component")
            return max(1, component_mentions // 3)  # Rough estimate
        except Exception:
            # Default count if parsing fails
            return 1
              
class GardenFoundationRefinementAgent(ReflectiveAgent):
    def __init__(self, agent_id: str, event_queue: EventQueue,
                state_manager: StateManager,
                context_manager: AgentContextManager,
                cache_manager: CacheManager,
                metrics_manager: MetricsManager,
                error_handler: ErrorHandler,
                 memory_monitor: MemoryMonitor,
                 health_tracker: HealthTracker = None):
        
        # Define prompt configuration
        prompt_config = AgentPromptConfig(
            system_prompt_base_path="FFTT_system_prompts/phase_one/garden_foundation_refinement_agent",
            reflection_prompt_name="task_foundation_reflection_prompt",
            refinement_prompt_name="task_foundation_refinement_prompt",
            initial_prompt_name="task_foundation_refinement_prompt"
        )
        
        # Define circuit breakers
        circuit_breakers = [
            CircuitBreakerDefinition(
                name="refinement",
                failure_threshold=4,
                recovery_timeout=60,
                failure_window=300
            ),
            CircuitBreakerDefinition(
                name="validation",
                failure_threshold=3,
                recovery_timeout=45,
                failure_window=180
            )
        ]
        
        # Initialize base class with configuration
        super().__init__(
            agent_id, 
            event_queue, state_manager, context_manager, cache_manager, metrics_manager, error_handler, 
            prompt_config,
            circuit_breakers,
            health_tracker, 
            memory_monitor
        )
        
        # Set initial state
        self.development_state = DevelopmentState.INITIALIZING
        self.validation_history = []
        
        # Register with memory monitor if available
        if self._memory_monitor:
            self._memory_monitor.register_component(
                f"agent_{agent_id}",
                MemoryThresholds(
                    per_resource_max_mb=200,  # Refinement may need more memory
                    warning_percent=0.7,
                    critical_percent=0.9
                )
            )
            
        # Initialize refinement tracking
        self._refinement_metrics = {
            "critical_failures": 0,
            "issues_identified": 0,
            "successful_refinements": 0,
            "total_processing_time": 0
        }

    async def _process(self, phase_one_outputs: Dict[str, Any],
                      phase_zero_outputs: Dict[str, Any]) -> Dict[str, Any]:
        """Process foundation refinement with monitoring."""
        processing_start = datetime.now()
        
        try:
            # Track memory usage of input data
            await self.track_dict_memory("phase_one_outputs", phase_one_outputs)
            await self.track_dict_memory("phase_zero_outputs", phase_zero_outputs)
            
            # Calculate total input size
            phase_one_size_mb = len(json.dumps(phase_one_outputs)) / (1024 * 1024)
            phase_zero_size_mb = len(json.dumps(phase_zero_outputs)) / (1024 * 1024)
            total_input_size_mb = phase_one_size_mb + phase_zero_size_mb
            await self.track_memory_usage("total_input", total_input_size_mb)
            
            # Log large input warning if needed
            if total_input_size_mb > 50:  # Arbitrary threshold for demonstration
                logger.warning(f"Large input for {self.interface_id}: {total_input_size_mb:.2f} MB")
                
                # Record large input metric
                await self._metrics_manager.record_metric(
                    f"agent:{self.interface_id}:large_input",
                    total_input_size_mb,
                    metadata={"timestamp": datetime.now().isoformat()}
                )
                
                # Report status for large input
                await self._report_agent_health(
                    custom_status="DEGRADED",
                    description=f"Large input detected: {total_input_size_mb:.2f} MB",
                    metadata={
                        "phase_one_size_mb": phase_one_size_mb,
                        "phase_zero_size_mb": phase_zero_size_mb
                    }
                )
            
            # Update health status to analyzing
            await self._report_agent_health(
                description="Analyzing foundation refinement",
                metadata={
                    "state": "ANALYZING",
                    "input_sources": ["phase_one", "phase_zero"]
                }
            )
            
            # Analyze with circuit breaker protection
            try:
                self.development_state = DevelopmentState.ANALYZING
                
                initial_analysis = await self.get_circuit_breaker("refinement").execute(
                    lambda: self.process_with_validation(
                        conversation=f"""Analyze phase one outputs and phase zero feedback:
                        Phase one outputs: {phase_one_outputs}
                        Phase zero outputs: {phase_zero_outputs}""",
                        system_prompt_info=(self._prompt_config.system_prompt_base_path, 
                                          self._prompt_config.initial_prompt_name)
                    )
                )
            except CircuitOpenError:
                logger.warning(f"Refinement circuit open for agent {self.interface_id}, processing rejected")
                self.development_state = DevelopmentState.ERROR
                
                await self._report_agent_health(
                    custom_status="CRITICAL",
                    description="Refinement analysis rejected due to circuit breaker open",
                    metadata={
                        "state": "ERROR",
                        "circuit": "refinement_circuit",
                        "circuit_state": "OPEN"
                    }
                )
                
                return {
                    "error": "Refinement analysis rejected due to circuit breaker open",
                    "status": "failure",
                    "agent_id": self.interface_id,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Track memory usage of analysis result
            await self.track_dict_memory("refinement_analysis", initial_analysis)
            
            # Check for critical failures in the analysis
            if self._has_critical_failure(initial_analysis):
                # Update refinement metrics
                self._refinement_metrics["critical_failures"] += 1
                self._refinement_metrics["issues_identified"] += self._count_issues(initial_analysis)
                
                # Record refinement metrics
                await self._metrics_manager.record_metric(
                    f"agent:{self.interface_id}:critical_failures",
                    1.0,
                    metadata={
                        "timestamp": datetime.now().isoformat(),
                        "total_failures": self._refinement_metrics["critical_failures"]
                    }
                )
                
                # Report degraded health for critical failure
                await self._report_agent_health(
                    custom_status="DEGRADED",
                    description="Critical failures identified in phase one outputs",
                    metadata={
                        "state": "ANALYZING",
                        "critical_failures": True,
                        "failure_count": self._refinement_metrics["critical_failures"],
                        "responsible_agent": self._get_responsible_agent(initial_analysis)
                    }
                )
            
            # Get reflection result with validation circuit breaker protection
            try:
                self.development_state = DevelopmentState.VALIDATING
                reflection_result = await self.reflect(initial_analysis)
            except CircuitOpenError:
                logger.warning(f"Validation circuit open for agent {self.interface_id}, validation rejected")
                
                await self._report_agent_health(
                    custom_status="CRITICAL",
                    description="Validation rejected due to circuit breaker open",
                    metadata={
                        "state": "VALIDATING",
                        "circuit": "validation_circuit",
                        "circuit_state": "OPEN"
                    }
                )
                
                return {
                    "error": "Validation rejected due to circuit breaker open",
                    "status": "failure",
                    "agent_id": self.interface_id,
                    "timestamp": datetime.now().isoformat(),
                    "initial_analysis": initial_analysis
                }
            
            # Check validation status
            if not reflection_result["reflection_results"]["validation_status"]["passed"]:
                self.development_state = DevelopmentState.REFINING
                
                await self._report_agent_health(
                    custom_status="DEGRADED",
                    description="Validation failed, foundation analysis requires refinement",
                    metadata={
                        "state": "REFINING",
                        "validation": "failed"
                    }
                )
                
                return reflection_result
            
            # Set state to complete
            self.development_state = DevelopmentState.COMPLETE
            
            # Calculate processing time and update metrics
            processing_time = (datetime.now() - processing_start).total_seconds()
            self._refinement_metrics["total_processing_time"] += processing_time
            self._refinement_metrics["successful_refinements"] += 1
            
            # Record metrics
            await self._metrics_manager.record_metric(
                f"agent:{self.interface_id}:processing_time",
                processing_time,
                metadata={
                    "success": True,
                    "critical_failures": self._has_critical_failure(initial_analysis)
                }
            )
            
            # Calculate success rate
            total_attempts = (self._refinement_metrics["successful_refinements"] + 
                              self._refinement_metrics["critical_failures"])
            success_rate = self._refinement_metrics["successful_refinements"] / total_attempts if total_attempts > 0 else 1.0
            
            await self._metrics_manager.record_metric(
                f"agent:{self.interface_id}:success_rate",
                success_rate,
                metadata={"total_attempts": total_attempts}
            )
            
            await self._report_agent_health(
                description="Foundation refinement analysis completed successfully",
                metadata={
                    "state": "COMPLETE",
                    "processing_time": processing_time,
                    "critical_failures": self._has_critical_failure(initial_analysis),
                    "success_rate": success_rate
                }
            )
            
            return initial_analysis
            
        except Exception as e:
            self.development_state = DevelopmentState.ERROR
            
            # Calculate processing time before failure
            processing_time = (datetime.now() - processing_start).total_seconds()
            
            # Record error metrics
            await self._metrics_manager.record_metric(
                f"agent:{self.interface_id}:processing_errors",
                1.0,
                metadata={
                    "error": str(e),
                    "processing_time": processing_time
                }
            )
            
            await self._report_agent_health(
                custom_status="CRITICAL",
                description=f"Foundation refinement error: {str(e)}",
                metadata={
                    "state": "ERROR",
                    "error": str(e),
                    "processing_time": processing_time
                }
            )
            
            raise

    async def reflect(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """Specialized reflection with metrics and history tracking."""
        reflection_start = datetime.now()
        
        try:
            result = await self.standard_reflect(output, "validation")
            
            # Calculate reflection time
            reflection_time = (datetime.now() - reflection_start).total_seconds()
            
            # Add to validation history
            self.validation_history.append({
                "timestamp": datetime.now().isoformat(),
                "success": result["reflection_results"]["validation_status"]["passed"],
                "duration": reflection_time
            })
            
            # Record reflection time metric
            await self._metrics_manager.record_metric(
                f"agent:{self.interface_id}:reflection_time",
                reflection_time,
                metadata={"success": True}
            )
            
            return result
        except CircuitOpenError:
            # Calculate reflection time before failure
            reflection_time = (datetime.now() - reflection_start).total_seconds()
            
            # Add to validation history
            self.validation_history.append({
                "timestamp": datetime.now().isoformat(),
                "success": False,
                "duration": reflection_time,
                "error": "circuit_open"
            })
            
            # Re-raise the exception to be handled by caller
            raise

    # Helper methods specific to GardenFoundationRefinementAgent
    def _has_critical_failure(self, analysis: Dict[str, Any]) -> bool:
        """Check if analysis contains critical failures."""
        try:
            return analysis.get("refinement_analysis", {}).get("critical_failure", False)
        except Exception:
            return False
    
    def _get_responsible_agent(self, analysis: Dict[str, Any]) -> str:
        """Get responsible agent for critical failure."""
        try:
            return analysis.get("refinement_analysis", {}).get("root_cause", {}).get("responsible_agent", "unknown")
        except Exception:
            return "unknown"
    
    def _count_issues(self, analysis: Dict[str, Any]) -> int:
        """Count identified issues in analysis."""
        try:
            issues = analysis.get("refinement_analysis", {}).get("issues", [])
            if isinstance(issues, list):
                return len(issues)
            return 1 if self._has_critical_failure(analysis) else 0
        except Exception:
            return 0
         
class PhaseOneOrchestrator:
    def __init__(
        self,
        event_queue: EventQueue,
        state_manager: StateManager,
        context_manager: AgentContextManager,
        cache_manager: CacheManager,
        metrics_manager: MetricsManager,
        error_handler: ErrorHandler,
        phase_zero, #will be phase zero orchestrator but avoiding type correctness for circular dependency reasons
        health_tracker: Optional[HealthTracker] = None,
        memory_monitor: Optional[MemoryMonitor] = None,
        system_monitor: Optional[SystemMonitor] = None
    ):
        # Initialize resource managers
        self._event_queue = event_queue
        self._state_manager = state_manager
        self._context_manager = context_manager
        self._cache_manager = cache_manager
        self._metrics_manager = metrics_manager
        self._error_handler = error_handler

        # Monitoring components
        self._health_tracker = health_tracker
        self._memory_monitor = memory_monitor
        self._system_monitor = system_monitor
        
        # Ensure event queue is started
        asyncio.create_task(self._ensure_event_queue_started())

        # Initialize circuit breaker for orchestration
        self._orchestration_circuit = CircuitBreaker(
            "phase_one_orchestration", 
            event_queue
        )
        
        # Register circuit breaker with system monitor if available
        if self._system_monitor and self._orchestration_circuit:
            asyncio.create_task(
                self._system_monitor.register_circuit_breaker(
                    "phase_one_orchestration", 
                    self._orchestration_circuit
                )
            )

        # Initialize orchestrator state
        self.refinement_attempts = 0
        self.MAX_REFINEMENT_ATTEMPTS = 5
        self.phase_zero = phase_zero
        
        # Initialize agents with shared event queue
        self._initialize_agents()
        
        # Set flag for agent initialization status
        self._agents_initialized = False
        
        # Create task for initialization
        self._init_task = asyncio.create_task(self._init_agents_async())

        # Store initial state
        asyncio.create_task(self._store_initial_state())

        # Report initial health status
        if self._health_tracker:
            asyncio.create_task(
                self._health_tracker.update_health(
                    "phase_one_orchestrator",
                    HealthStatus(
                        status="HEALTHY",
                        source="phase_one_orchestrator",
                        description="Phase one orchestrator initialized",
                        metadata={"refinement_attempts": 0}
                    )
                )
            )

    def _initialize_agents(self) -> None:
        """Initialize all phase one agents with shared event queue and monitoring."""
        self.garden_planner = GardenPlannerAgent(
            "garden_planner", 
            self._event_queue,
            self._state_manager,
            self._context_manager,
            self._cache_manager,
            self._metrics_manager,
            self._error_handler,
            health_tracker=self._health_tracker,
            memory_monitor=self._memory_monitor
        )
        
        self.environmental_analysis = EnvironmentalAnalysisAgent(
            "environmental_analysis", 
            self._event_queue,
            self._state_manager,
            self._context_manager,
            self._cache_manager,
            self._metrics_manager,
            self._error_handler,
            health_tracker=self._health_tracker,
            memory_monitor=self._memory_monitor
        )
        
        self.root_system_architect = RootSystemArchitectAgent(
            "root_system", 
            self._event_queue,
            self._state_manager,
            self._context_manager,
            self._cache_manager,
            self._metrics_manager,
            self._error_handler,
            health_tracker=self._health_tracker,
            memory_monitor=self._memory_monitor
        )
        
        self.tree_placement_planner = TreePlacementPlannerAgent(
            "tree_placement", 
            self._event_queue,
            self._state_manager,
            self._context_manager,
            self._cache_manager,
            self._metrics_manager,
            self._error_handler,
            health_tracker=self._health_tracker,
            memory_monitor=self._memory_monitor
        )
        
        self.foundation_refinement = GardenFoundationRefinementAgent(
            "foundation_refinement", 
            self._event_queue,
            self._state_manager,
            self._context_manager,
            self._cache_manager,
            self._metrics_manager,
            self._error_handler,
            health_tracker=self._health_tracker,
            memory_monitor=self._memory_monitor
        )
        
        # Register agent circuit breakers with system monitor
        if self._system_monitor:
            for agent in [self.garden_planner, self.environmental_analysis, 
                         self.root_system_architect, self.tree_placement_planner,
                         self.foundation_refinement]:
                # Register all circuit breakers for each agent
                for cb_name, cb in agent._circuit_breakers.items():
                    asyncio.create_task(
                        self._system_monitor.register_circuit_breaker(
                            f"{agent.interface_id}_{cb_name}", 
                            cb
                        )
                    )
        
        self.refinement_history = {}

    async def _store_initial_state(self) -> None:
        """Store initial orchestrator state."""
        await self._state_manager.set_state(
            "phase_one:orchestrator",
            {
                "status": "initialized",
                "timestamp": datetime.now().isoformat(),
                "agents": [
                    "garden_planner",
                    "environmental_analysis",
                    "root_system",
                    "tree_placement",
                    "foundation_refinement"
                ],
                "refinement_attempts": 0,
                "max_refinement_attempts": self.MAX_REFINEMENT_ATTEMPTS
            },
            resource_type=ResourceType.STATE
        )

    async def _ensure_event_queue_started(self):
        """Ensure the event queue is started"""
        try:
            if hasattr(self._event_queue, '_running') and not self._event_queue._running:
                logger.info("Starting event queue for orchestrator")
                await self._event_queue.start()
        except Exception as e:
            logger.error(f"Error starting event queue: {str(e)}")
    
    async def _init_agents_async(self):
        """Initialize all agents asynchronously"""
        try:
            # Ensure event queue is started first
            await self._ensure_event_queue_started()
            
            # Initialize each agent
            agents = [
                self.garden_planner,
                self.environmental_analysis,
                self.root_system_architect,
                self.tree_placement_planner,
                self.foundation_refinement
            ]
            
            for agent in agents:
                try:
                    # Ensure agent is initialized
                    await agent.ensure_initialized()
                except Exception as e:
                    logger.error(f"Error initializing agent {agent.interface_id}: {str(e)}")
            
            # Set flag indicating initialization is complete
            self._agents_initialized = True
            logger.info("All agents initialized successfully")
        except Exception as e:
            logger.error(f"Error in agent initialization: {str(e)}")

    async def process_task(self, task_prompt: str,
                         phase_zero_outputs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # Ensure agents are initialized
            if hasattr(self, '_init_task') and not self._agents_initialized:
                try:
                    logger.info("Waiting for agent initialization to complete...")
                    await asyncio.wait_for(self._init_task, timeout=10)
                except asyncio.TimeoutError:
                    logger.warning("Timed out waiting for agent initialization, proceeding anyway")
                except Exception as e:
                    logger.error(f"Error waiting for agent initialization: {str(e)}")

            # Track memory usage for prompt
            if self._memory_monitor:
                prompt_size_mb = len(task_prompt) / (1024 * 1024)  # Rough estimation
                await self._memory_monitor.track_resource(
                    "phase_one:task_prompt",
                    prompt_size_mb,
                    "phase_one_orchestrator"
                )
            
            # Update health status to processing
            if self._health_tracker:
                await self._health_tracker.update_health(
                    "phase_one_orchestrator",
                    HealthStatus(
                        status="HEALTHY",
                        source="phase_one_orchestrator",
                        description="Processing task",
                        metadata={"task_size": len(task_prompt)}
                    )
                )
            
            try:
                # Use circuit breaker to protect the entire processing pipeline
                return await self._orchestration_circuit.execute(
                    lambda: self._process_task_internal(task_prompt, phase_zero_outputs)
                )
            except CircuitOpenError:
                logger.error("Phase one orchestration circuit open, processing rejected")
                
                # Update health status to critical
                if self._health_tracker:
                    await self._health_tracker.update_health(
                        "phase_one_orchestrator",
                        HealthStatus(
                            status="CRITICAL",
                            source="phase_one_orchestrator",
                            description="Processing rejected due to circuit breaker open",
                            metadata={"circuit": "phase_one_orchestration"}
                        )
                    )
                
                return {
                    "status": "error",
                    "error": "Phase one processing rejected due to circuit breaker open",
                    "phase": "phase_one_orchestration"
                }
                
        except Exception as e:
            logger.error(f"Phase one processing failed: {e}")
            
            # Update health status to critical
            if self._health_tracker:
                await self._health_tracker.update_health(
                    "phase_one_orchestrator",
                    HealthStatus(
                        status="CRITICAL",
                        source="phase_one_orchestrator",
                        description=f"Processing failed: {str(e)}",
                        metadata={"error": str(e)}
                    )
                )
            
            return {
                "status": "error",
                "error": str(e),
                "phase": "phase_one_orchestration"
            }
        
    async def _process_task_internal(self, task_prompt: str,
                            phase_zero_outputs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            initial_result = None
            while self.refinement_attempts < self.MAX_REFINEMENT_ATTEMPTS:
                # Execute phase one
                result = await self._execute_phase_one(task_prompt)
                
                if not initial_result:
                    initial_result = result.copy()
                
                if result["status"] != "success":
                    # Update health status to reflect failure
                    if self._health_tracker:
                        await self._health_tracker.update_health(
                            "phase_one_orchestrator",
                            HealthStatus(
                                status="DEGRADED",
                                source="phase_one_orchestrator",
                                description=f"Phase one execution failed: {result.get('error', 'Unknown error')}",
                                metadata={"status": result["status"]}
                            )
                        )
                    return result
                
                # Store phase one outputs using the data interface
                try:
                    phase_one_version = await self._data_interface.store_phase_one_outputs(
                        result["phase_one_outputs"]
                    )
                    logger.info(f"Stored Phase One outputs with version {phase_one_version}")
                except ValueError as e:
                    logger.error(f"Failed to store Phase One outputs: {e}")
                    # Continue anyway, as we have the outputs in memory

                # Run phase zero monitoring if available
                if self.phase_zero:
                    # Gather comprehensive metrics
                    system_metrics = await self._gather_metrics(result["phase_one_outputs"])
                    try:
                        # Process metrics through Phase Zero
                        monitoring_result = await self.phase_zero.process_system_metrics(system_metrics)
                        
                        # Store monitoring results using data interface
                        try:
                            feedback_version = await self._data_interface.store_phase_zero_feedback(
                                monitoring_result, phase_one_version
                            )
                            logger.info(f"Stored Phase Zero feedback with version {feedback_version}")
                        except ValueError as e:
                            logger.error(f"Failed to store Phase Zero feedback: {e}")
                            # Continue anyway as we have the feedback in memory

                        # Analyze Phase Zero output through foundation refinement agent
                        refinement_output = await self.foundation_refinement._process(
                            result["phase_one_outputs"],
                            monitoring_result
                        )
                        
                        # Check for critical failures
                        if refinement_output.get("refinement_analysis", {}).get("critical_failure"):
                            self.refinement_attempts += 1
                            
                            # Log refinement attempt
                            logger.info(f"Starting refinement attempt {self.refinement_attempts}/{self.MAX_REFINEMENT_ATTEMPTS}")
                            
                            # Handle refinement based on phase zero feedback
                            refined_result = await self._handle_refinement({
                                "status": "refinement_needed",
                                "refinement": refinement_output,
                                "phase_one_outputs": result["phase_one_outputs"],
                                "monitoring_result": monitoring_result
                            })
                            
                            if refined_result["status"] == "success":
                                # If refinement was successful, return the result
                                return self._prepare_final_output(True, initial_result, refined_result, monitoring_result)
                            else:
                                return {
                                    "status": "error",
                                    "error": "Refinement attempt failed",
                                    "phase": "phase_one_orchestration",
                                    "initial_outputs": initial_result.get("phase_one_outputs"),
                                    "refinement_history": self._get_complete_refinement_history()
                                }
                        else:
                            # No critical failures detected
                            return self._prepare_final_output(True, initial_result, result, monitoring_result)

                    except Exception as e:
                        logger.error(f"Error processing system metrics through Phase Zero: {e}")
                        return self._prepare_final_output(False, initial_result, result, 
                                                        {"error": f"Phase Zero processing failed: {str(e)}"})

        except Exception as e:
            logger.error(f"Phase one processing failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "phase": "phase_one_orchestration"
            }
        
    async def _gather_metrics(self, phase_one_outputs: Dict[str, Any]) -> Dict[str, Any]:
        """Gather system metrics using metrics manager."""
        try:
            metrics = {
                "resource": {},
                "error": {},
                "development": {},
                "performance": {},
                "health": {},
                "timestamp": datetime.now().isoformat()
            }
            
            # Get metrics for each agent
            agents = {
                "garden_planner": self.garden_planner,
                "environmental_analysis": self.environmental_analysis,
                "root_system": self.root_system_architect,
                "tree_placement": self.tree_placement_planner
            }
            
            for agent_id, agent in agents.items():
                # Development state metrics
                metrics["development"][agent_id] = agent.development_state.value

                # Record development state
                await self._metrics_manager.record_metric(
                    f"agent:{agent_id}:development",
                    agent.development_state.value,
                    metadata={
                        "state": agent.development_state.name,
                        "timestamp": datetime.now().isoformat()
                    }
                )
                
            # Gather memory usage metrics if memory monitor available
            if self._memory_monitor:
                # Get total memory usage for each agent
                for agent_id in agents.keys():
                    resource_size = sum(
                        size for res_id, size in self._memory_monitor._resource_sizes.items()
                        if res_id.startswith(f"agent:{agent_id}:")
                    )
                    metrics["resource"][agent_id] = resource_size
                
                # Get total memory usage for orchestrator
                orchestrator_size = sum(
                    size for res_id, size in self._memory_monitor._resource_sizes.items()
                    if res_id.startswith("phase_one:")
                )
                metrics["resource"]["orchestrator"] = orchestrator_size
            
            # Gather error metrics
            if self._health_tracker:
                for component_id, health in self._health_tracker._component_health.items():
                    if health.status == "CRITICAL" or health.status == "UNHEALTHY":
                        agent_id = component_id.replace("agent_", "")
                        metrics["error"][agent_id] = 1.0
                    elif health.status == "DEGRADED":
                        agent_id = component_id.replace("agent_", "")
                        metrics["error"][agent_id] = 0.5
                    else:
                        agent_id = component_id.replace("agent_", "")
                        metrics["error"][agent_id] = 0.0
            
            # Gather performance metrics 
            for agent_id in agents.keys():
                performance_metrics = await self._metrics_manager.get_metrics(
                    f"agent:{agent_id}:processing_time",
                    limit=5  # Get the 5 most recent
                )
                
                if performance_metrics:
                    metrics["performance"][agent_id] = sum(m["value"] for m in performance_metrics) / len(performance_metrics)
                else:
                    metrics["performance"][agent_id] = 0
            
            # Get system health status
            if self._health_tracker:
                system_health = self._health_tracker.get_system_health()
                metrics["health"]["system"] = system_health.status
                metrics["health"]["description"] = system_health.description
                
                # Count components in each health status
                status_counts = {}
                for health in self._health_tracker._component_health.values():
                    status_counts[health.status] = status_counts.get(health.status, 0) + 1
                
                metrics["health"]["status_counts"] = status_counts
            
            return metrics
                
        except Exception as e:
            logger.error(f"Error gathering metrics: {e}")
            await self._event_queue.emit(
                ResourceEventTypes.ERROR_OCCURRED.value,
                {
                    "error": str(e),
                    "source": "metric_collection",
                    "timestamp": datetime.now().isoformat()
                }
            )
            return {
                "resource": {},
                "error": {},
                "development": {},
                "error_message": str(e)
            }

    async def _handle_refinement(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Handle refinement based on Phase Zero feedback."""
        try:
            # Get refinement analysis from foundation_refinement agent
            refinement_output = result.get("refinement", {})
            refinement_analysis = refinement_output.get("refinement_analysis", {})
            
            # Check if there's a critical failure that needs refinement
            if not refinement_analysis.get("critical_failure", False):
                return {
                    "status": "success",
                    "phase_one_outputs": result["phase_one_outputs"]
                }
            
            # Get responsible agent from refinement analysis
            target_agent_id = refinement_analysis.get("root_cause", {}).get("responsible_agent")
            if not target_agent_id:
                logger.warning("Refinement analysis indicates critical failure but no responsible agent identified")
                return {
                    "status": "error",
                    "error": "No responsible agent identified for refinement",
                    "phase": "refinement"
                }
            
            # Get the agent instance
            target_agent = self._get_agent_by_name(target_agent_id)
            if not target_agent:
                logger.error(f"Invalid target agent {target_agent_id} for refinement")
                return {
                    "status": "error",
                    "error": f"Invalid target agent {target_agent_id} for refinement",
                    "phase": "refinement"
                }
            
            # Log refinement attempt
            logger.info(f"Refinement attempt {self.refinement_attempts} targeting agent {target_agent_id}")
            
            # Record metrics for refinement attempt
            await self._metrics_manager.record_metric(
                f"refinement:attempt",
                1.0,
                metadata={
                    "attempt": self.refinement_attempts,
                    "target_agent": target_agent_id,
                    "root_cause": refinement_analysis.get("root_cause", {})
                }
            )
            
            # Get refinement guidance from analysis
            refinement_guidance = refinement_analysis.get("refinement_action", {})
            
            # Create refinement context
            context = RefinementContext(
                iteration=self.refinement_attempts,
                agent_id=target_agent_id,
                original_output=result["phase_one_outputs"][target_agent_id],
                refined_output=None,
                refinement_guidance=refinement_guidance
            )
            
            # Apply refinement to target agent
            refined_output = await target_agent.refine(
                result["phase_one_outputs"][target_agent_id],
                refinement_guidance
            )
            
            # Update context with refined output
            context.refined_output = refined_output
            
            # Update refinement history
            await target_agent.add_refinement_iteration(context)
            if target_agent_id not in self.refinement_history:
                self.refinement_history[target_agent_id] = []
            self.refinement_history[target_agent_id].append(context)
            
            # Update outputs and re-execute pipeline from this agent forward
            result["phase_one_outputs"][target_agent_id] = refined_output
            return await self._execute_phase_one_from_agent(
                target_agent,
                result["phase_one_outputs"]
            )

        except Exception as e:
            logger.error(f"Refinement failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "phase": "refinement"
            }
        
    def _get_agent_by_name(self, agent_id: str) -> Optional[ReflectiveAgent]:
        """Get agent instance by ID."""
        agent_map = {
            "garden_planner": self.garden_planner,
            "environmental_analysis": self.environmental_analysis,
            "root_system": self.root_system_architect,
            "tree_placement": self.tree_placement_planner
        }
        return agent_map.get(agent_id)
    
    def _check_agent_failure(self, agent: ReflectiveAgent) -> bool:
        """Check if agent is in error state."""
        return agent.development_state == DevelopmentState.ERROR

    def _prepare_final_output(self, success: bool, initial_result: Dict[str, Any], 
                            final_result: Dict[str, Any],
                            feedback_analysis: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Prepare final output with feedback analysis"""
        output = {
            "status": success,
            "initial_outputs": initial_result.get("phase_one_outputs"),
            "final_outputs": final_result.get("phase_one_outputs"),
            "refinement_history": self._get_complete_refinement_history(),
            "refinement_attempts": self.refinement_attempts
        }
        
        # Include feedback analysis if available
        if feedback_analysis:
            output["feedback_analysis"] = feedback_analysis
        else:
            # Try to retrieve the latest feedback from the data interface
            try:
                if hasattr(self, '_data_interface') and self._data_interface is not None:
                    asyncio.create_task(
                        self._retrieve_and_attach_latest_feedback(output)
                    )
            except Exception as e:
                logger.error(f"Error retrieving latest feedback: {e}")
        
        # Include system health if available
        if self._health_tracker:
            output["system_health"] = self._health_tracker.get_system_health().to_dict()
        
        return output

    async def _retrieve_and_attach_latest_feedback(self, output: Dict[str, Any]):
        """Retrieve and attach latest feedback asynchronously."""
        try:
            feedback = await self._data_interface.retrieve_latest_phase_zero_feedback()
            if feedback:
                output["feedback_analysis"] = feedback
        except Exception as e:
            logger.error(f"Error in async feedback retrieval: {e}")
    
    async def _execute_phase_one(self, task_prompt: str) -> Dict[str, Any]:
        """Execute main phase one pipeline with retry logic and monitoring"""
        execution_start_time = datetime.now()
        
        try:
            # Update health status to processing
            if self._health_tracker:
                await self._health_tracker.update_health(
                    "phase_one_pipeline",
                    HealthStatus(
                        status="HEALTHY",
                        source="phase_one_orchestrator",
                        description="Starting phase one execution",
                        metadata={"task_size": len(task_prompt)}
                    )
                )
            
            # Sequential agent processing with retries
            garden_planner_output = await self._execute_with_retry(
                self.garden_planner,
                "garden_planner",
                lambda: self.garden_planner._process(task_prompt)
            )
            
            if self._check_agent_failure(self.garden_planner):
                return self._handle_agent_failure("garden_planner")

            env_analysis_output = await self._execute_with_retry(
                self.environmental_analysis,
                "environmental_analysis",
                lambda: self.environmental_analysis._process(garden_planner_output)
            )
            
            if self._check_agent_failure(self.environmental_analysis):
                return self._handle_agent_failure("environmental_analysis")

            root_system_output = await self._execute_with_retry(
                self.root_system_architect,
                "root_system_architect",
                lambda: self.root_system_architect._process(
                    garden_planner_output,
                    env_analysis_output
                )
            )
            
            if self._check_agent_failure(self.root_system_architect):
                return self._handle_agent_failure("root_system_architect")

            tree_placement_output = await self._execute_with_retry(
                self.tree_placement_planner,
                "tree_placement_planner",
                lambda: self.tree_placement_planner._process(
                    garden_planner_output,
                    env_analysis_output,
                    root_system_output
                )
            )
            
            if self._check_agent_failure(self.tree_placement_planner):
                return self._handle_agent_failure("tree_placement_planner")

            # Collect phase one outputs
            phase_one_outputs = {
                "garden_planner": garden_planner_output,
                "environmental_analysis": env_analysis_output,
                "root_system": root_system_output,
                "tree_placement": tree_placement_output
            }
            
            # Track memory usage of outputs
            if self._memory_monitor:
                outputs_size_mb = len(json.dumps(phase_one_outputs)) / (1024 * 1024)
                await self._memory_monitor.track_resource(
                    "phase_one:outputs",
                    outputs_size_mb,
                    "phase_one_orchestrator"
                )
            
            # Record execution time metric
            execution_time = (datetime.now() - execution_start_time).total_seconds()
            await self._metrics_manager.record_metric(
                "phase_one:execution_time",
                execution_time,
                metadata={"success": True}
            )
            
            # Update health status to successful completion
            if self._health_tracker:
                await self._health_tracker.update_health(
                    "phase_one_pipeline",
                    HealthStatus(
                        status="HEALTHY",
                        source="phase_one_orchestrator",
                        description="Phase one execution completed successfully",
                        metadata={
                            "execution_time": execution_time,
                            "agent_count": 4
                        }
                    )
                )

            return {
                "status": "success",
                "phase_one_outputs": phase_one_outputs,
                "execution_time": execution_time
            }

        except Exception as e:
            logger.error(f"Phase one processing failed: {e}")
            
            # Record execution time metric for failed execution
            execution_time = (datetime.now() - execution_start_time).total_seconds()
            await self._metrics_manager.record_metric(
                "phase_one:execution_time",
                execution_time,
                metadata={"success": False, "error": str(e)}
            )
            
            # Update health status to critical
            if self._health_tracker:
                await self._health_tracker.update_health(
                    "phase_one_pipeline",
                    HealthStatus(
                        status="CRITICAL",
                        source="phase_one_orchestrator",
                        description=f"Phase one execution failed: {str(e)}",
                        metadata={
                            "execution_time": execution_time,
                            "error": str(e)
                        }
                    )
                )
            
            return {
                "status": "error",
                "error": str(e),
                "phase": "phase_one_orchestration",
                "execution_time": execution_time
            }
        
    async def _execute_with_retry(self, agent: ReflectiveAgent, 
                            agent_id: str, 
                            process_func: Callable, 
                            max_retries: int = 3) -> Dict[str, Any]:
        """Execute agent process with retry logic and monitoring."""
        retries = 0
        execution_start_time = datetime.now()
        
        # Update health status for agent execution
        if self._health_tracker:
            await self._health_tracker.update_health(
                f"execution_{agent_id}",
                HealthStatus(
                    status="HEALTHY",
                    source="phase_one_orchestrator",
                    description=f"Starting execution of agent {agent_id}",
                    metadata={"retries": retries, "max_retries": max_retries}
                )
            )
        
        while retries < max_retries:
            try:
                agent.development_state = DevelopmentState.INITIALIZING
                coro = await process_func()
                
                # Add timeout
                try:
                    result = await self.with_timeout(
                        coro, 
                        60, # 60 seconds before timeout
                        f"agent_execution_{agent_id}"
                    )
                    
                    # Record successful execution time
                    execution_time = (datetime.now() - execution_start_time).total_seconds()
                    await self._metrics_manager.record_metric(
                        f"agent:{agent_id}:execution_time",
                        execution_time,
                        metadata={"success": True, "retries": retries}
                    )
                    
                    # Update health status for successful execution
                    if self._health_tracker:
                        await self._health_tracker.update_health(
                            f"execution_{agent_id}",
                            HealthStatus(
                                status="HEALTHY",
                                source="phase_one_orchestrator",
                                description=f"Agent {agent_id} executed successfully",
                                metadata={
                                    "execution_time": execution_time,
                                    "retries": retries
                                }
                            )
                        )
                    
                    if not self._check_agent_failure(agent):
                        return result
                    
                    # If we get here, agent failed but might be retryable
                    retries += 1
                    logger.warning(f"Agent {agent_id} failed, attempt {retries}/{max_retries}")
                    
                    # Update health status for retry
                    if self._health_tracker:
                        await self._health_tracker.update_health(
                            f"execution_{agent_id}",
                            HealthStatus(
                                status="DEGRADED",
                                source="phase_one_orchestrator",
                                description=f"Agent {agent_id} failed, retrying {retries}/{max_retries}",
                                metadata={"retries": retries, "max_retries": max_retries}
                            )
                        )
                    
                    if retries < max_retries:
                        # Wait with exponential backoff before retry
                        await asyncio.sleep(2 ** retries)
                        continue
                        
                except asyncio.TimeoutError:
                    retries += 1
                    logger.warning(f"Agent {agent_id} timed out (attempt {retries}/{max_retries})")
                    
                    # Record timeout metric
                    await self._metrics_manager.record_metric(
                        f"agent:{agent_id}:timeouts",
                        1.0,
                        metadata={"attempt": retries}
                    )
                    
                    # Update health status for timeout
                    if self._health_tracker:
                        await self._health_tracker.update_health(
                            f"execution_{agent_id}",
                            HealthStatus(
                                status="DEGRADED",
                                source="phase_one_orchestrator",
                                description=f"Agent {agent_id} timed out, retrying {retries}/{max_retries}",
                                metadata={"retries": retries, "max_retries": max_retries}
                            )
                        )
                    
                    if retries >= max_retries:
                        agent.development_state = DevelopmentState.ERROR
                        
                        # Update health status for max retries exceeded
                        if self._health_tracker:
                            await self._health_tracker.update_health(
                                f"execution_{agent_id}",
                                HealthStatus(
                                    status="CRITICAL",
                                    source="phase_one_orchestrator",
                                    description=f"Agent {agent_id} timed out, max retries exceeded",
                                    metadata={"retries": retries, "max_retries": max_retries}
                                )
                            )
                        
                        raise
                    continue
                    
            except Exception as e:
                retries += 1
                logger.error(f"Agent {agent_id} error on attempt {retries}/{max_retries}: {str(e)}")
                
                # Record error metric
                await self._metrics_manager.record_metric(
                    f"agent:{agent_id}:errors",
                    1.0,
                    metadata={"attempt": retries, "error": str(e)}
                )
                
                # Update health status for error
                if self._health_tracker:
                    await self._health_tracker.update_health(
                        f"execution_{agent_id}",
                        HealthStatus(
                            status="DEGRADED",
                            source="phase_one_orchestrator",
                            description=f"Agent {agent_id} error: {str(e)}, retrying {retries}/{max_retries}",
                            metadata={"retries": retries, "max_retries": max_retries, "error": str(e)}
                        )
                    )
                
                if retries >= max_retries:
                    agent.development_state = DevelopmentState.ERROR
                    
                    # Update health status for max retries exceeded
                    if self._health_tracker:
                        await self._health_tracker.update_health(
                            f"execution_{agent_id}",
                            HealthStatus(
                                status="CRITICAL",
                                source="phase_one_orchestrator",
                                description=f"Agent {agent_id} error, max retries exceeded",
                                metadata={"retries": retries, "max_retries": max_retries, "error": str(e)}
                            )
                        )
                    
                    raise

        # If we get here, we've exhausted retries
        return self._handle_agent_failure(agent_id)

    def _handle_agent_failure(self, agent_id: str) -> Dict[str, Any]:
        """Create standardized error response for agent failure with monitoring."""
        # Update health status for agent failure
        if self._health_tracker:
            asyncio.create_task(
                self._health_tracker.update_health(
                    f"agent_{agent_id}",
                    HealthStatus(
                        status="CRITICAL",
                        source="phase_one_orchestrator",
                        description=f"Agent {agent_id} failed during execution",
                        metadata={"agent_id": agent_id}
                    )
                )
            )
        
        # Record failure metric
        asyncio.create_task(
            self._metrics_manager.record_metric(
                f"agent:{agent_id}:failures",
                1.0,
                metadata={"timestamp": datetime.now().isoformat()}
            )
        )
        
        return {
            "status": "error",
            "error": f"Agent {agent_id} failed during execution",
            "phase": "phase_one_execution",
            "agent": agent_id
        }

    async def with_timeout(self, coro, timeout_seconds: float, operation_name: str):
        """Execute a coroutine with a timeout and monitoring."""
        try:
            # Update health status for operation start
            if self._health_tracker:
                await self._health_tracker.update_health(
                    f"operation_{operation_name}",
                    HealthStatus(
                        status="HEALTHY",
                        source="phase_one_orchestrator",
                        description=f"Starting operation {operation_name}",
                        metadata={"timeout": timeout_seconds}
                    )
                )
            
            # Start timer
            start_time = datetime.now()
            
            # Execute with timeout
            result = await asyncio.wait_for(coro, timeout=timeout_seconds)
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Record execution time metric
            await self._metrics_manager.record_metric(
                f"operation:{operation_name}:execution_time",
                execution_time,
                metadata={"success": True}
            )
            
            # Update health status for operation completion
            if self._health_tracker:
                await self._health_tracker.update_health(
                    f"operation_{operation_name}",
                    HealthStatus(
                        status="HEALTHY",
                        source="phase_one_orchestrator",
                        description=f"Operation {operation_name} completed",
                        metadata={"execution_time": execution_time}
                    )
                )
            
            return result
            
        except asyncio.TimeoutError:
            logger.error(f"Operation {operation_name} timed out after {timeout_seconds}s")
            
            # Record timeout metric
            await self._metrics_manager.record_metric(
                "operation_timeouts",
                1.0,
                metadata={"operation": operation_name}
            )
            
            # Update health status for operation timeout
            if self._health_tracker:
                await self._health_tracker.update_health(
                    f"operation_{operation_name}",
                    HealthStatus(
                        status="CRITICAL",
                        source="phase_one_orchestrator",
                        description=f"Operation {operation_name} timed out after {timeout_seconds}s",
                        metadata={"timeout": timeout_seconds}
                    )
                )
            
            # Emit timeout event
            await self._event_queue.emit(
                ResourceEventTypes.TIMEOUT_OCCURRED.value,
                {
                    "operation": operation_name,
                    "timeout": timeout_seconds,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            raise

    def _get_complete_refinement_history(self) -> Dict[str, List[Dict[str, Any]]]:
        return {
            agent_id: [r.to_dict() for r in history]
            for agent_id, history in self.refinement_history.items()
        }
    
    async def _execute_phase_one_from_agent(self, start_agent: ReflectiveAgent,
                                       existing_outputs: Dict[str, Any]) -> Dict[str, Any]:
        """Re-execute phase one pipeline starting from a specific agent"""
        try:
            # Define execution sequence
            execution_sequence = {
                "garden_planner": [self.garden_planner, []],
                "environmental_analysis": [self.environmental_analysis, ["garden_planner"]],
                "root_system": [self.root_system_architect, ["garden_planner", "environmental_analysis"]],
                "tree_placement": [self.tree_placement_planner, ["garden_planner", "environmental_analysis", "root_system"]]
            }
            
            # Find start point in sequence
            start_found = False
            outputs = existing_outputs.copy()
            
            # Execute remaining sequence
            for agent_id, (agent, dependencies) in execution_sequence.items():
                if agent == start_agent:
                    start_found = True
                
                if start_found:
                    # Gather required outputs for this agent
                    agent_inputs = [outputs[dep] for dep in dependencies]
                    
                    # Execute agent based on number of dependencies
                    if len(agent_inputs) == 0:
                        agent_output = await agent._process(None)  # Should never happen in current setup
                    elif len(agent_inputs) == 1:
                        agent_output = await agent._process(agent_inputs[0])
                    elif len(agent_inputs) == 2:
                        agent_output = await agent._process(*agent_inputs)
                    else:
                        agent_output = await agent._process(*agent_inputs)
                    
                    if self._check_agent_failure(agent):
                        return self._handle_agent_failure(agent_id)
                    
                    outputs[agent_id] = agent_output
            
            return {
                "status": "success",
                "phase_one_outputs": outputs
            }
            
        except Exception as e:
            logger.error(f"Phase one re-execution failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "phase": "phase_one_reexecution"
            }
        
async def main_with_monitoring():
    """Test the PhaseOneOrchestrator with monitoring integration."""
    # Initialize event queue
    event_queue = EventQueue()

    # Start event queue explicitly
    logger.info("Starting event queue")
    await event_queue.start()

    # Initialize monitoring components
    memory_monitor = MemoryMonitor(event_queue)
    health_tracker = HealthTracker(event_queue)
    system_monitor = SystemMonitor(
        event_queue,
        memory_monitor,
        health_tracker
    )
    
    # Start monitoring
    await memory_monitor.start()
    await system_monitor.start()
    
    mock_state_manager = StateManager(event_queue)
    # Ensure state manager has any needed initialization
    if hasattr(mock_state_manager, 'initialize'):
        await mock_state_manager.initialize()
    
    # Create context manager with explicit initialization
    mock_context_manager = AgentContextManager(event_queue)
    if hasattr(mock_context_manager, 'initialize'):
        await mock_context_manager.initialize()
    
    # Create cache manager with explicit initialization
    mock_cache_manager = CacheManager(event_queue)
    if hasattr(mock_cache_manager, 'initialize'):
        await mock_cache_manager.initialize()
    
    # Create metrics manager with explicit initialization
    mock_metrics_manager = MetricsManager(event_queue)
    if hasattr(mock_metrics_manager, 'initialize'):
        await mock_metrics_manager.initialize()
    
    # Create error handler with explicit initialization
    mock_error_handler = ErrorHandler(event_queue)
    if hasattr(mock_error_handler, 'initialize'):
        await mock_error_handler.initialize()
    
    # Initialize phase zero orchestrator first
    from phase_zero import PhaseZeroOrchestrator
    phase_zero = PhaseZeroOrchestrator(
        event_queue,
        mock_state_manager,
        mock_context_manager,
        mock_cache_manager,
        mock_metrics_manager,
        mock_error_handler,
        health_tracker=health_tracker,
        memory_monitor=memory_monitor,
        system_monitor=system_monitor
    )
    
    # Initialize orchestrator with monitoring and initialized components
    orchestrator = PhaseOneOrchestrator(
        event_queue,
        mock_state_manager,
        mock_context_manager,
        mock_cache_manager,
        mock_metrics_manager,
        mock_error_handler,
        phase_zero=phase_zero,  # Use phase_zero for proper integration
        health_tracker=health_tracker,
        memory_monitor=memory_monitor,
        system_monitor=system_monitor
    )

    # Wait for orchestrator to initialize agents
    try:
        logger.info("Waiting for orchestrator to initialize agents")
        await asyncio.wait_for(orchestrator._init_task, timeout=30)
        logger.info("Orchestrator initialization complete")
    except asyncio.TimeoutError:
        logger.warning("Timed out waiting for orchestrator initialization, proceeding anyway")
    except Exception as e:
        logger.error(f"Error during orchestrator initialization: {str(e)}")

    # Define a simple game development task
    task_prompt = """
    Create a simple 2D platformer game with the following features:
    - A player character that can run and jump
    - Basic platform obstacles
    - Simple coin collection mechanics
    - A scoring system
    Please design the core architecture and systems needed for this game.
    """

    try:
        # Process the task with monitoring
        print("Starting phase one processing...")
        result = await orchestrator.process_task(task_prompt)
        
        # Print results
        print("\nProcessing complete!")
        print(f"Status: {result['status']}")
        
        if result['status'] == 'success':
            print("\nGarden Planner Analysis:")
            print(json.dumps(result['final_outputs']['garden_planner'], indent=2))
            
            # Additional result printing...
        else:
            print(f"Error: {result.get('error')}")
            print(f"Error phase: {result.get('phase')}")
            
            if 'refinement_history' in result:
                print("\nRefinement History:")
                print(json.dumps(result['refinement_history'], indent=2))

    except Exception as e:
        print(f"Test failed with error: {str(e)}")
        raise
    finally:
        # Stop monitoring
        await system_monitor.stop()
        await memory_monitor.stop()
        await event_queue.stop()

if __name__ == "__main__":
    # Run the test with monitoring
    asyncio.run(main_with_monitoring())