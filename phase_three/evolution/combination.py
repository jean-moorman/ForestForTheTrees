import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Set

from resources import (
    ResourceType, 
    StateManager, 
    MetricsManager, 
    EventQueue
)

from phase_three.evolution.strategies import FeatureEvolutionStrategy

logger = logging.getLogger(__name__)

class FeatureCombinationStrategy(FeatureEvolutionStrategy):
    """Strategy for combining multiple features into a unified feature"""
    
    async def combine_features(self, 
                             combination_candidates: List[Dict[str, Any]],
                             evaluation_data: Dict[str, Any],
                             feature_development_manager: Any) -> Dict[str, Any]:
        """Combine multiple features into a unified feature.
        
        Args:
            combination_candidates: List of features marked for combination
            evaluation_data: Evaluation data with combination suggestions
            feature_development_manager: Manager for starting feature development
            
        Returns:
            Dict containing combination results
        """
        logger.info(f"Combining {len(combination_candidates)} features based on evolutionary selection")
        
        try:
            # Extract feature IDs to combine
            feature_ids = [candidate["feature_id"] for candidate in combination_candidates]
            
            # Find the combination pattern from evaluation data
            combination_pattern = None
            for adaptation in evaluation_data.get("adaptations", []):
                if adaptation.get("strategy", "").lower().startswith("combin") and \
                   any(feature_id in adaptation.get("addresses", []) for feature_id in feature_ids):
                    combination_pattern = adaptation
                    break
            
            if not combination_pattern:
                # Check evolution opportunities
                evolution_opportunities = evaluation_data.get("phase_zero_feedback", {}).get(
                    "evolution_opportunities", {}
                )
                for combo in evolution_opportunities.get("feature_combinations", []):
                    if all(feature_id in combo.get("features", []) for feature_id in feature_ids):
                        combination_pattern = combo
                        break
            
            # If still no pattern, create a default one
            if not combination_pattern:
                combination_pattern = {
                    "strategy": "Combine related features",
                    "implementation": "Merge functionality while eliminating redundancy",
                    "benefits": ["Reduced complexity", "Improved cohesion", "Simplified dependencies"]
                }
            
            # Create a new combined feature ID
            combined_id = f"combined_{'_'.join(feature_ids)}_{int(datetime.now().timestamp())}"
            
            # Get statuses for all features
            feature_statuses = {}
            for feature_id in feature_ids:
                status = await feature_development_manager.get_feature_status(feature_id)
                if not status or "error" in status:
                    logger.warning(f"Could not retrieve status for feature {feature_id}")
                    continue
                feature_statuses[feature_id] = status
            
            if not feature_statuses:
                return {
                    "status": "error",
                    "error": "Could not retrieve status for any features to combine",
                    "feature_ids": feature_ids
                }
            
            # Collect all dependencies from all features
            all_dependencies = set()
            for status in feature_statuses.values():
                all_dependencies.update(status.get("dependencies", []))
            
            # Remove the features being combined from dependencies
            all_dependencies = all_dependencies.difference(feature_ids)
            
            # Create combined name and description
            feature_names = [status.get("feature_name", "Unknown") for status in feature_statuses.values()]
            combined_name = f"Combined: {' + '.join(feature_names)}"
            combined_description = f"Combined feature created from: {', '.join(feature_names)}"
            
            # Disable original features
            for feature_id in feature_ids:
                await self._disable_feature(feature_id)
            
            # Start development of the combined feature
            combined_feature = {
                "id": combined_id,
                "name": combined_name,
                "description": combined_description,
                "combined_from": feature_ids,
                "dependencies": list(all_dependencies),
                "combination_pattern": combination_pattern
            }
            
            # Start development of the combined feature
            combination_result = await feature_development_manager.start_feature_development(combined_feature)
            
            # Record the combination relationship in state manager
            await self._state_manager.set_state(
                f"feature:combination:{combined_id}",
                {
                    "combined_id": combined_id,
                    "original_ids": feature_ids,
                    "timestamp": datetime.now().isoformat(),
                    "rationale": combination_pattern.get("implementation", "")
                },
                ResourceType.STATE
            )
            
            # Record the combination metric
            await self._metrics_manager.record_metric(
                "feature:evolution:combination_created",
                1.0,
                metadata={
                    "combined_id": combined_id,
                    "original_count": len(feature_ids),
                    "original_ids": feature_ids
                }
            )
            
            return {
                "status": "success",
                "combined_id": combined_id,
                "original_ids": feature_ids,
                "combination_pattern": combination_pattern.get("implementation", ""),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error combining features: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "feature_ids": feature_ids if 'feature_ids' in locals() else []
            }