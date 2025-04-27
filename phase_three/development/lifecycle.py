import logging
from datetime import datetime
from typing import Dict, Any

from resources import ResourceType, StateManager, MetricsManager
from phase_three.models.enums import FeatureDevelopmentState

logger = logging.getLogger(__name__)

class FeatureLifecycleManager:
    """Manages the lifecycle of features through development states"""
    
    def __init__(self, state_manager: StateManager, metrics_manager: MetricsManager):
        """Initialize the lifecycle manager.
        
        Args:
            state_manager: Manager for application state
            metrics_manager: Manager for metrics collection
        """
        self._state_manager = state_manager
        self._metrics_manager = metrics_manager
    
    async def update_development_state(self, 
                                     feature_id: str, 
                                     feature_name: str,
                                     state: FeatureDevelopmentState) -> None:
        """Update development state in state manager.
        
        Args:
            feature_id: Feature identifier
            feature_name: Name of the feature
            state: New development state
        """
        await self._state_manager.set_state(
            f"feature:development:{feature_id}",
            {
                "feature_id": feature_id,
                "feature_name": feature_name,
                "state": state.name,
                "timestamp": datetime.now().isoformat()
            },
            ResourceType.STATE
        )
        
        # Record state change metric
        await self._metrics_manager.record_metric(
            "feature:development:state_change",
            1.0,
            metadata={
                "feature_id": feature_id,
                "feature_name": feature_name,
                "state": state.name
            }
        )
        
        logger.info(f"Feature {feature_name} ({feature_id}) state updated to {state.name}")
    
    async def record_development_start(self, feature_id: str, feature_name: str) -> None:
        """Record the start of feature development.
        
        Args:
            feature_id: Feature identifier
            feature_name: Name of the feature
        """
        await self._metrics_manager.record_metric(
            "feature:development:start",
            1.0,
            metadata={
                "feature_id": feature_id,
                "feature_name": feature_name
            }
        )
        
        logger.info(f"Feature development started for {feature_name} ({feature_id})")
    
    async def record_development_completion(self, 
                                          feature_id: str, 
                                          feature_name: str,
                                          overall_score: float) -> None:
        """Record the completion of feature development.
        
        Args:
            feature_id: Feature identifier
            feature_name: Name of the feature
            overall_score: Overall score for the completed feature
        """
        await self._metrics_manager.record_metric(
            "feature:development:complete",
            1.0,
            metadata={
                "feature_id": feature_id,
                "feature_name": feature_name,
                "overall_score": overall_score
            }
        )
        
        logger.info(f"Feature development completed for {feature_name} with score {overall_score}")
    
    async def record_development_error(self, 
                                     feature_id: str, 
                                     feature_name: str,
                                     error: str) -> None:
        """Record a development error.
        
        Args:
            feature_id: Feature identifier
            feature_name: Name of the feature
            error: Error message
        """
        await self._metrics_manager.record_metric(
            "feature:development:error",
            1.0,
            metadata={
                "feature_id": feature_id,
                "feature_name": feature_name,
                "error": error
            }
        )
        
        logger.error(f"Feature development error for {feature_name}: {error}")