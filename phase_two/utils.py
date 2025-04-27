import logging
import time
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

def sort_components_by_dependencies(components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Sort components from most fundamental (least dependencies) to least fundamental."""
    # Create a mapping of component IDs to components and dependency counts
    component_map = {}
    dependency_count = {}
    
    for comp in components:
        comp_id = comp.get("id", f"comp_{int(time.time())}")
        dependencies = comp.get("dependencies", [])
        component_map[comp_id] = comp
        dependency_count[comp_id] = len(dependencies)
    
    # Sort components by dependency count (ascending)
    sorted_ids = sorted(dependency_count.keys(), key=lambda x: dependency_count[x])
    sorted_components = [component_map[comp_id] for comp_id in sorted_ids]
    
    return sorted_components

async def use_internal_implementation(phase_coordination, input_data: Dict[str, Any]) -> bool:
    """Determine whether to use internal implementation or coordinator."""
    # Check coordinator health
    try:
        health = await phase_coordination.get_phase_health()
        if health.get("status") != "HEALTHY":
            logger.warning(f"Phase coordinator not healthy: {health.get('description')}")
            return True
    except Exception as e:
        logger.warning(f"Error checking coordination health: {str(e)}")
        return True
        
    # Check if this is a compatibility mode request
    if input_data.get("use_legacy_implementation", False):
        return True
        
    # Otherwise, use coordinator by default for now
    # In a full implementation, we would gradually migrate to the coordinator
    # For now, still use the internal implementation for compatibility
    return True