import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

from resources import (
    ResourceType, 
    EventQueue, 
    StateManager, 
    CacheManager, 
    AgentContextManager, 
    MetricsManager, 
    ErrorHandler, 
    MemoryMonitor,
    SystemMonitor
)
from phase_four import PhaseFourInterface

from phase_three.development import ParallelFeatureDevelopment
from phase_three.evolution import (
    NaturalSelectionAgent,
    FeatureReplacementStrategy,
    FeatureImprovementStrategy,
    FeatureCombinationStrategy
)

logger = logging.getLogger(__name__)

class PhaseThreeInterface:
    """Interface for Phase Three operations"""
    
    def __init__(self, 
                 event_queue: EventQueue,
                 state_manager: StateManager,
                 context_manager: AgentContextManager,
                 cache_manager: CacheManager,
                 metrics_manager: MetricsManager,
                 error_handler: ErrorHandler,
                 memory_monitor: Optional[MemoryMonitor] = None,
                 system_monitor: Optional[SystemMonitor] = None):
        """Initialize the Phase Three interface.
        
        Args:
            event_queue: Queue for system events
            state_manager: Manager for application state
            context_manager: Manager for agent context
            cache_manager: Manager for caching results
            metrics_manager: Manager for metrics collection
            error_handler: Handler for error processing
            memory_monitor: Optional monitor for memory usage
            system_monitor: Optional system monitor
        """
        self._event_queue = event_queue
        self._state_manager = state_manager
        self._context_manager = context_manager
        self._cache_manager = cache_manager
        self._metrics_manager = metrics_manager
        self._error_handler = error_handler
        self._memory_monitor = memory_monitor
        self._system_monitor = system_monitor
        
        # Initialize phase four interface
        self._phase_four_interface = PhaseFourInterface(
            event_queue, state_manager, context_manager, cache_manager,
            metrics_manager, error_handler, memory_monitor, system_monitor
        )
        
        # Initialize parallel feature development
        self._feature_development = ParallelFeatureDevelopment(
            event_queue, state_manager, context_manager, cache_manager,
            metrics_manager, error_handler, self._phase_four_interface, memory_monitor
        )
        
        # Initialize natural selection agent
        self._natural_selection_agent = NaturalSelectionAgent(
            event_queue, state_manager, context_manager, cache_manager,
            metrics_manager, error_handler, memory_monitor
        )
        
        # Initialize evolution strategies
        self._replacement_strategy = FeatureReplacementStrategy(
            state_manager, metrics_manager, event_queue
        )
        self._improvement_strategy = FeatureImprovementStrategy(
            state_manager, metrics_manager, event_queue
        )
        self._combination_strategy = FeatureCombinationStrategy(
            state_manager, metrics_manager, event_queue
        )
        
        # Track growth intervals
        self._last_evaluation_time = time.time()
        self._evaluation_interval = 3600  # 1 hour between evaluations
        
        logger.info("Phase Three interface initialized")
    
    async def start_feature_cultivation(self, component_features: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Start feature cultivation for a component.
        
        Args:
            component_features: List of features to cultivate
            
        Returns:
            Dict containing cultivation operation status
        """
        try:
            logger.info(f"Starting feature cultivation for {len(component_features)} features")
            
            # Record cultivation start
            operation_id = f"cultivation_{int(time.time())}"
            await self._metrics_manager.record_metric(
                "phase_three:cultivation:start",
                1.0,
                metadata={
                    "feature_count": len(component_features),
                    "operation_id": operation_id
                }
            )
            
            # Identify independent features for parallel development
            dependency_map = {}
            for feature in component_features:
                feature_id = feature.get("id", f"feature_{int(time.time())}_{len(dependency_map)}")
                dependencies = feature.get("dependencies", [])
                
                # Ensure feature ID is in the feature
                if "id" not in feature:
                    feature["id"] = feature_id
                    
                dependency_map[feature_id] = dependencies
            
            # Start development of non-dependent features first
            started_features = []
            for feature in component_features:
                feature_id = feature.get("id")
                dependencies = dependency_map.get(feature_id, [])
                
                # Check if dependencies have already been started
                if not dependencies or all(dep in started_features for dep in dependencies):
                    # Start feature development
                    await self._feature_development.start_feature_development(feature)
                    started_features.append(feature_id)
            
            # Store cultivation state
            cultivation_state = {
                "operation_id": operation_id,
                "total_features": len(component_features),
                "started_features": started_features,
                "timestamp": datetime.now().isoformat()
            }
            await self._state_manager.set_state(
                f"phase_three:cultivation:{operation_id}",
                cultivation_state,
                ResourceType.STATE
            )
            
            return cultivation_state
            
        except Exception as e:
            logger.error(f"Error starting feature cultivation: {str(e)}", exc_info=True)
            
            await self._metrics_manager.record_metric(
                "phase_three:cultivation:error",
                1.0,
                metadata={"error": str(e)}
            )
            
            return {
                "error": f"Failed to start feature cultivation: {str(e)}"
            }
    
    async def evaluate_feature_evolution(self, component_id: str = None) -> Dict[str, Any]:
        """Evaluate feature performance and make evolution decisions.
        
        Args:
            component_id: Optional component ID to filter features
            
        Returns:
            Dict containing evolution evaluation results
        """
        try:
            # Check if it's time for evaluation
            current_time = time.time()
            if current_time - self._last_evaluation_time < self._evaluation_interval:
                logger.info("Skipping evolution evaluation - minimum interval not reached")
                return {
                    "status": "skipped",
                    "reason": "Minimum interval not reached",
                    "next_evaluation": self._last_evaluation_time + self._evaluation_interval
                }
                
            self._last_evaluation_time = current_time
            operation_id = f"evolution_{int(current_time)}"
                
            logger.info(f"Starting feature evolution evaluation for operation {operation_id}")
            
            # Record evaluation start
            await self._metrics_manager.record_metric(
                "phase_three:evolution:start",
                1.0,
                metadata={"operation_id": operation_id}
            )
            
            # Get all feature statuses
            all_statuses = await self._feature_development.get_all_feature_statuses()
            
            # Filter for completed features
            completed_features = [
                status for status in all_statuses.values() 
                if status.get("state") == "COMPLETED"
            ]
            
            if not completed_features:
                logger.info("No completed features to evaluate")
                return {
                    "operation_id": operation_id,
                    "status": "no_features",
                    "message": "No completed features to evaluate"
                }
            
            # Run natural selection evaluation
            evaluation_result = await self._natural_selection_agent.evaluate_features(
                completed_features,
                operation_id
            )
            
            if "error" in evaluation_result:
                logger.error(f"Evolution evaluation failed: {evaluation_result['error']}")
                return {
                    "operation_id": operation_id,
                    "status": "error",
                    "error": evaluation_result["error"]
                }
            
            # Store evaluation result
            await self._state_manager.set_state(
                f"phase_three:evolution:{operation_id}",
                evaluation_result,
                ResourceType.STATE
            )
            
            # Record evaluation completion
            await self._metrics_manager.record_metric(
                "phase_three:evolution:complete",
                1.0,
                metadata={
                    "operation_id": operation_id,
                    "evaluated_features": len(completed_features)
                }
            )
            
            # Apply evolution decisions
            applied_decisions = await self._apply_evolution_decisions(evaluation_result)
            
            return {
                "operation_id": operation_id,
                "status": "completed",
                "evaluation_result": evaluation_result,
                "applied_decisions": applied_decisions
            }
            
        except Exception as e:
            logger.error(f"Error in feature evolution evaluation: {str(e)}", exc_info=True)
            
            await self._metrics_manager.record_metric(
                "phase_three:evolution:error",
                1.0,
                metadata={"error": str(e)}
            )
            
            return {
                "status": "error",
                "error": f"Feature evolution evaluation failed: {str(e)}"
            }
    
    async def _apply_evolution_decisions(self, evaluation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Apply evolution decisions from natural selection.
        
        Args:
            evaluation_result: Results from natural selection evaluation
            
        Returns:
            Dict containing applied decision results
        """
        decisions = evaluation_result.get("optimization_decisions", [])
        applied = {
            "total_decisions": len(decisions),
            "applied_decisions": 0,
            "actions": []
        }
        
        for decision in decisions:
            feature_id = decision.get("feature_id")
            decision_type = decision.get("decision")
            
            if not feature_id or not decision_type:
                continue
                
            # Handle different decision types
            if decision_type == "replace":
                # Implement feature replacement
                replacement_result = await self._replacement_strategy.apply(
                    feature_id, 
                    decision.get("rationale", ""),
                    evaluation_result,
                    self._feature_development
                )
                
                applied["actions"].append({
                    "feature_id": feature_id,
                    "action": "replaced_feature",
                    "details": decision.get("rationale", ""),
                    "replacement_id": replacement_result.get("replacement_id"),
                    "replacement_method": replacement_result.get("method"),
                    "status": replacement_result.get("status")
                })
                applied["applied_decisions"] += 1
                
            elif decision_type == "improve":
                # Implement feature improvement
                improvement_result = await self._improvement_strategy.apply(
                    feature_id, 
                    decision.get("rationale", ""),
                    evaluation_result,
                    self._phase_four_interface
                )
                
                applied["actions"].append({
                    "feature_id": feature_id,
                    "action": "improved_feature",
                    "details": decision.get("rationale", ""),
                    "status": improvement_result.get("status"),
                    "improvements": improvement_result.get("improvements", [])
                })
                applied["applied_decisions"] += 1
                
            elif decision_type == "combine":
                # Mark for combination - implementation handled separately
                # because it requires coordinating multiple features
                applied["actions"].append({
                    "feature_id": feature_id,
                    "action": "marked_for_combination",
                    "details": decision.get("rationale", "")
                })
                applied["applied_decisions"] += 1
                
            elif decision_type == "keep":
                # No action needed
                pass
        
        # Store applied decisions in state manager
        await self._state_manager.set_state(
            f"phase_three:evolution:applied:{int(time.time())}",
            applied,
            ResourceType.STATE
        )
        
        # If there are features marked for combination, handle them now
        combination_candidates = [action for action in applied["actions"] 
                                if action["action"] == "marked_for_combination"]
        if combination_candidates:
            combination_result = await self._combination_strategy.combine_features(
                combination_candidates,
                evaluation_result,
                self._feature_development
            )
            applied["combination_results"] = combination_result
        
        return applied
    
    async def get_feature_status(self, feature_id: str) -> Dict[str, Any]:
        """Get the current status of a feature.
        
        Args:
            feature_id: ID of the feature to check
            
        Returns:
            Dict containing feature status
        """
        return await self._feature_development.get_feature_status(feature_id)
        
    async def get_component_features(self, component_id: str) -> List[Dict[str, Any]]:
        """Get all features for a component.
        
        Args:
            component_id: ID of the component
            
        Returns:
            List of feature status dicts
        """
        # Get all feature statuses
        all_statuses = await self._feature_development.get_all_feature_statuses()
        
        # Filter for the specified component if available
        if component_id:
            # In a real implementation, this would filter based on component ID
            # For now, we just return all features
            component_features = list(all_statuses.values())
        else:
            component_features = list(all_statuses.values())
            
        return component_features
    
    async def get_cultivation_status(self, operation_id: str) -> Dict[str, Any]:
        """Get the status of a cultivation operation.
        
        Args:
            operation_id: ID of the cultivation operation
            
        Returns:
            Dict containing cultivation status
        """
        cultivation_state = await self._state_manager.get_state(f"phase_three:cultivation:{operation_id}")
        
        if not cultivation_state:
            return {"error": f"Cultivation operation {operation_id} not found"}
            
        # Get current status of all started features
        started_features = cultivation_state.get("started_features", [])
        feature_statuses = {}
        
        for feature_id in started_features:
            feature_statuses[feature_id] = await self._feature_development.get_feature_status(feature_id)
            
        # Count features in each state
        state_counts = {}
        for status in feature_statuses.values():
            state = status.get("state", "UNKNOWN")
            state_counts[state] = state_counts.get(state, 0) + 1
            
        # Calculate overall completion percentage
        total_features = cultivation_state.get("total_features", 0)
        completed_features = state_counts.get("COMPLETED", 0)
        
        if total_features > 0:
            completion_percentage = (completed_features / total_features) * 100
        else:
            completion_percentage = 0
            
        return {
            "operation_id": operation_id,
            "total_features": total_features,
            "started_features": started_features,
            "feature_statuses": feature_statuses,
            "state_counts": state_counts,
            "completion_percentage": completion_percentage,
            "timestamp": datetime.now().isoformat()
        }