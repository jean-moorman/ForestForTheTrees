"""
Demonstrates the integration between Earth and Water agents for guideline validation and propagation.

This example shows how:
1. Earth agent validates guideline updates
2. Water agent propagates approved updates to affected downstream agents with rich contextual information
3. Downstream agents integrate the updates into their guidelines
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

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
from resources.earth_agent import EarthAgent, AbstractionTier
from resources.water_agent import WaterAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Sample data for the demonstration
SAMPLE_COMPONENT_UPDATE = {
    "ordered_components": [
        {
            "name": "api",
            "sequence_number": 1,
            "dependencies": {
                "required": [],
                "optional": []
            }
        },
        {
            "name": "core",
            "sequence_number": 2,
            "dependencies": {
                "required": ["api"],
                "optional": []
            }
        },
        {
            "name": "database",
            "sequence_number": 3,
            "dependencies": {
                "required": ["api", "core"],
                "optional": []
            }
        }
    ]
}

SAMPLE_FEATURE_UPDATE = {
    "component_id": "api",
    "features": [
        {
            "id": "authentication",
            "name": "User Authentication",
            "description": "Handles user login and session management",
            "dependencies": []
        },
        {
            "id": "authorization",
            "name": "User Authorization",
            "description": "Controls access to protected resources",
            "dependencies": ["authentication"]
        }
    ]
}

# Mock downstream agents for the demonstration
mock_agents = {
    "garden_planner": {},
    "environmental_analysis": {},
    "root_system": {},
    "tree_placement": {}
}

async def setup_resources():
    """Set up shared resources for the agents."""
    # Create shared resources
    event_queue = EventQueue()
    await event_queue.start()
    
    state_manager = StateManager(event_queue)
    context_manager = AgentContextManager(event_queue)
    cache_manager = CacheManager(event_queue)
    metrics_manager = MetricsManager(event_queue)
    error_handler = ErrorHandler(event_queue)
    memory_monitor = MemoryMonitor(event_queue)
    
    # Register mock agents
    for agent_id, guideline in mock_agents.items():
        await state_manager.set_state(
            f"agent:{agent_id}:guideline",
            guideline,
            resource_type=ResourceType.STATE
        )
    
    return {
        "event_queue": event_queue,
        "state_manager": state_manager,
        "context_manager": context_manager,
        "cache_manager": cache_manager,
        "metrics_manager": metrics_manager,
        "error_handler": error_handler,
        "memory_monitor": memory_monitor
    }

async def initialize_agents(resources):
    """Initialize Earth and Water agents."""
    # Create Earth agent with LLM capabilities
    earth_agent = EarthAgent(
        agent_id="earth_agent",
        event_queue=resources["event_queue"],
        state_manager=resources["state_manager"],
        context_manager=resources["context_manager"],
        cache_manager=resources["cache_manager"],
        metrics_manager=resources["metrics_manager"],
        error_handler=resources["error_handler"],
        memory_monitor=resources["memory_monitor"],
        model="claude-3-7-sonnet-20250219"
    )
    
    # Create Water agent with LLM capabilities
    water_agent = WaterAgent(
        agent_id="water_agent",
        event_queue=resources["event_queue"],
        state_manager=resources["state_manager"],
        context_manager=resources["context_manager"],
        cache_manager=resources["cache_manager"],
        metrics_manager=resources["metrics_manager"],
        error_handler=resources["error_handler"],
        memory_monitor=resources["memory_monitor"],
        earth_agent=earth_agent,
        model="claude-3-7-sonnet-20250219"
    )
    
    return earth_agent, water_agent

async def demonstrate_component_validation_and_propagation(earth_agent, water_agent):
    """Demonstrate component-level guideline validation and propagation."""
    logger.info("=== Component Tier Validation and Propagation ===")
    
    # Current guideline (empty for this demo)
    current_guideline = {}
    
    # Validate the component update
    logger.info("Validating component guideline update...")
    validation_result = await earth_agent.validate_guideline_update(
        abstraction_tier=AbstractionTier.COMPONENT,
        agent_id="garden_planner",
        current_guideline=current_guideline,
        proposed_update=SAMPLE_COMPONENT_UPDATE,
        operation_id="demo_component_update"
    )
    
    # Print the validation result
    logger.info(f"Validation result: {validation_result.get('validation_result', {}).get('validation_category')}")
    
    # If approved, propagate the update
    if validation_result.get("validation_result", {}).get("validation_category") in ["APPROVED", "CORRECTED"]:
        logger.info("Update approved. Propagating to affected agents with rich context...")
        
        # Get the final update to propagate (either corrected or original)
        update_to_propagate = validation_result.get("corrected_update") or SAMPLE_COMPONENT_UPDATE
        
        # Propagate the update
        propagation_result = await water_agent.coordinate_propagation(
            origin_agent_id="garden_planner",
            validated_update=update_to_propagate,
            validation_result=validation_result
        )
        
        # Print propagation result
        logger.info(f"Propagation success: {propagation_result.success}")
        logger.info(f"Affected agents: {propagation_result.metrics.get('affected_count', 0)}")
        if propagation_result.failures:
            logger.warning(f"Propagation failures: {len(propagation_result.failures)}")
            for failure in propagation_result.failures:
                logger.warning(f"  - {failure.get('agent_id')}: {failure.get('reason')}")
    else:
        logger.warning("Update rejected. No propagation needed.")
        issues = validation_result.get("detected_issues", [])
        for issue in issues:
            logger.warning(f"  - {issue.get('issue_type')}: {issue.get('description')}")

async def demonstrate_feature_validation_and_propagation(earth_agent, water_agent):
    """Demonstrate feature-level guideline validation and propagation."""
    logger.info("\n=== Feature Tier Validation and Propagation ===")
    
    # Current guideline (empty for this demo)
    current_guideline = {
        "component_id": "api",
        "features": []
    }
    
    # Validate the feature update
    logger.info("Validating feature guideline update...")
    validation_result = await earth_agent.validate_guideline_update(
        abstraction_tier=AbstractionTier.FEATURE,
        agent_id="garden_planner",
        current_guideline=current_guideline,
        proposed_update=SAMPLE_FEATURE_UPDATE,
        operation_id="demo_feature_update"
    )
    
    # Print the validation result
    logger.info(f"Validation result: {validation_result.get('validation_result', {}).get('validation_category')}")
    
    # If approved, propagate the update
    if validation_result.get("validation_result", {}).get("validation_category") in ["APPROVED", "CORRECTED"]:
        logger.info("Update approved. Propagating to affected agents with rich context...")
        
        # Get the final update to propagate (either corrected or original)
        update_to_propagate = validation_result.get("corrected_update") or SAMPLE_FEATURE_UPDATE
        
        # Propagate the update
        propagation_result = await water_agent.coordinate_propagation(
            origin_agent_id="garden_planner",
            validated_update=update_to_propagate,
            validation_result=validation_result
        )
        
        # Print propagation result
        logger.info(f"Propagation success: {propagation_result.success}")
        logger.info(f"Affected agents: {propagation_result.metrics.get('affected_count', 0)}")
        if propagation_result.failures:
            logger.warning(f"Propagation failures: {len(propagation_result.failures)}")
            for failure in propagation_result.failures:
                logger.warning(f"  - {failure.get('agent_id')}: {failure.get('reason')}")
    else:
        logger.warning("Update rejected. No propagation needed.")
        issues = validation_result.get("detected_issues", [])
        for issue in issues:
            logger.warning(f"  - {issue.get('issue_type')}: {issue.get('description')}")

async def examine_results(state_manager):
    """Examine the final state of the system after validation and propagation."""
    logger.info("\n=== System State After Validation and Propagation ===")
    
    # Check agent guideline states
    for agent_id in mock_agents.keys():
        guideline = await state_manager.get_state(f"agent:{agent_id}:guideline")
        logger.info(f"Agent {agent_id} guideline:")
        logger.info(f"  {json.dumps(guideline, indent=2)}")
    
    # Get recent updates from agents
    for agent_id in mock_agents.keys():
        # Check for any update keys
        update_keys = await state_manager.list_keys(f"agent:{agent_id}:guideline_update:")
        if update_keys:
            logger.info(f"\nRecent updates for {agent_id}:")
            for key in update_keys[-3:]:  # Show last 3 updates
                update = await state_manager.get_state(key)
                if update:
                    # Extract rich context if available
                    rich_context = update.get("propagation_context", {}).get("rich_context", {})
                    adaptation_guidance = update.get("adaptation_guidance", {})
                    
                    logger.info(f"  Update ID: {key.split(':')[-1]}")
                    logger.info(f"  From: {update.get('origin_agent_id')}")
                    logger.info(f"  Status: {update.get('status')}")
                    
                    # Show sample of rich context if available
                    if rich_context and "update_context" in rich_context:
                        rationale = rich_context["update_context"].get("origin_context", {}).get("change_rationale", "No rationale provided")
                        logger.info(f"  Change rationale: {rationale}")
                        
                        # Show a sample of impact
                        impacts = rich_context["update_context"].get("impact_context", {}).get("direct_impacts", [])
                        if impacts:
                            logger.info(f"  Impact: {impacts[0].get('description', 'No impact description')}")
                    
                    # Show sample of adaptation guidance if available
                    if adaptation_guidance and "adaptation_guidance" in adaptation_guidance:
                        overview = adaptation_guidance["adaptation_guidance"].get("integration_overview", {})
                        logger.info(f"  Integration approach: {overview.get('integration_approach', 'Not specified')}")
                        logger.info(f"  Complexity: {overview.get('estimated_complexity', 'Not specified')}")
    
    # Get Earth agent validation history
    validation_history = await state_manager.list_keys("earth_validation:")
    if validation_history:
        logger.info("\nEarth Agent validation operations:")
        for key in validation_history[-5:]:  # Show last 5 validations
            validation = await state_manager.get_state(key)
            if validation and validation.get("status") == "completed":
                logger.info(f"  Operation: {key.split(':')[-1]}")
                logger.info(f"  Tier: {validation.get('tier')}")
                result = validation.get("result", {}).get("validation_result", {})
                logger.info(f"  Category: {result.get('validation_category')}")
                logger.info(f"  Is valid: {result.get('is_valid')}")
    
    # Get Water agent propagation history
    propagation_history = await state_manager.list_keys("water_agent:result:")
    if propagation_history:
        logger.info("\nWater Agent propagation operations:")
        for key in propagation_history[-5:]:  # Show last 5 propagations
            propagation = await state_manager.get_state(key)
            if propagation:
                logger.info(f"  Request: {propagation.get('request_id')}")
                logger.info(f"  Success: {propagation.get('success')}")
                metrics = propagation.get("metrics", {})
                logger.info(f"  Affected: {metrics.get('affected_count')}")
                logger.info(f"  Success rate: {metrics.get('success_count')}/{metrics.get('affected_count')}")

async def main():
    """Main function to run the demonstration."""
    try:
        logger.info("Starting Enhanced Earth-Water integration demonstration")
        logger.info("This demo showcases the integration between Earth and Water agents")
        logger.info("with the Water Agent now providing rich contextual information using LLM")
        
        # Setup resources
        resources = await setup_resources()
        
        # Initialize agents
        earth_agent, water_agent = await initialize_agents(resources)
        
        # Demonstrate component validation and propagation
        await demonstrate_component_validation_and_propagation(earth_agent, water_agent)
        
        # Demonstrate feature validation and propagation
        await demonstrate_feature_validation_and_propagation(earth_agent, water_agent)
        
        # Examine final results
        await examine_results(resources["state_manager"])
        
        logger.info("Demonstration completed successfully")
        
    except Exception as e:
        logger.error(f"Error in demonstration: {str(e)}", exc_info=True)
    finally:
        # Cleanup resources
        try:
            if 'resources' in locals():
                event_queue = resources.get("event_queue")
                if event_queue:
                    await event_queue.stop()
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())