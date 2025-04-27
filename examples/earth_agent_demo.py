"""
Earth Agent Demo for FFTT

This script demonstrates how to use the Earth Agent to validate guideline updates
across different abstraction tiers (component, feature, functionality), with
reflection and revision for improved validation quality.
"""

import asyncio
import json
import logging
from datetime import datetime

from resources.earth_agent import EarthAgent, AbstractionTier

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def component_tier_example():
    """Example of component tier validation."""
    logger.info("=== Component Tier Validation Example ===")
    earth_agent = EarthAgent(max_iterations=2)  # Set max reflection iterations to 2
    
    # Current component structure
    current_components = {
        "ordered_components": [
            {
                "id": "data_access",
                "name": "Data Access Layer",
                "description": "Handles database operations and data retrieval",
                "responsibilities": ["database operations", "data caching", "query optimization"],
                "dependencies": {"required": []}
            },
            {
                "id": "business_logic",
                "name": "Business Logic Layer",
                "description": "Implements core business rules and workflows",
                "responsibilities": ["business rules", "workflow execution", "validation"],
                "dependencies": {"required": ["data_access"]}
            }
        ]
    }
    
    # Proposed update - adds a new component with circular dependency (will be rejected)
    proposed_invalid_update = {
        "ordered_components": [
            {
                "id": "data_access",
                "name": "Data Access Layer",
                "description": "Handles database operations and data retrieval",
                "responsibilities": ["database operations", "data caching", "query optimization"],
                "dependencies": {"required": ["api_interface"]}  # Creates circular dependency
            },
            {
                "id": "business_logic",
                "name": "Business Logic Layer",
                "description": "Implements core business rules and workflows",
                "responsibilities": ["business rules", "workflow execution", "validation"],
                "dependencies": {"required": ["data_access"]}
            },
            {
                "id": "api_interface",
                "name": "API Interface Layer",
                "description": "Handles external API interactions",
                "responsibilities": ["API routing", "request validation", "response formatting"],
                "dependencies": {"required": ["business_logic"]}
            }
        ]
    }
    
    # Validate the invalid update (should be rejected due to circular dependency)
    logger.info("Validating invalid component update with circular dependency...")
    
    # First with reflection (default)
    invalid_result_with_reflection = await earth_agent.process_guideline_update(
        abstraction_tier="COMPONENT",
        agent_id="component_architect",
        current_guideline=current_components,
        proposed_update=proposed_invalid_update,
        with_reflection=True
    )
    
    logger.info(f"Invalid update with reflection - accepted: {invalid_result_with_reflection[0]}")
    if not invalid_result_with_reflection[0]:
        validation_result = invalid_result_with_reflection[2].get("validation_result", {})
        logger.info(f"Rejection reason (with reflection): {validation_result.get('explanation', 'Unknown')}")
    
    # Now without reflection for comparison
    invalid_result_no_reflection = await earth_agent.process_guideline_update(
        abstraction_tier="COMPONENT",
        agent_id="component_architect",
        current_guideline=current_components,
        proposed_update=proposed_invalid_update,
        with_reflection=False
    )
    
    logger.info(f"Invalid update without reflection - accepted: {invalid_result_no_reflection[0]}")
    if not invalid_result_no_reflection[0]:
        validation_result = invalid_result_no_reflection[2].get("validation_result", {})
        logger.info(f"Rejection reason (without reflection): {validation_result.get('explanation', 'Unknown')}")
        
    # Proposed update - adds a new component correctly
    proposed_valid_update = {
        "ordered_components": [
            {
                "id": "data_access",
                "name": "Data Access Layer",
                "description": "Handles database operations and data retrieval",
                "responsibilities": ["database operations", "data caching", "query optimization"],
                "dependencies": {"required": []}
            },
            {
                "id": "business_logic",
                "name": "Business Logic Layer",
                "description": "Implements core business rules and workflows",
                "responsibilities": ["business rules", "workflow execution", "validation"],
                "dependencies": {"required": ["data_access"]}
            },
            {
                "id": "api_interface",
                "name": "API Interface Layer",
                "description": "Handles external API interactions",
                "responsibilities": ["API routing", "request validation", "response formatting"],
                "dependencies": {"required": ["business_logic"]}
            }
        ]
    }
    
    # Validate the valid update
    logger.info("Validating valid component update...")
    valid_result = await earth_agent.process_guideline_update(
        abstraction_tier="COMPONENT",
        agent_id="component_architect",
        current_guideline=current_components,
        proposed_update=proposed_valid_update
    )
    
    logger.info(f"Valid update accepted: {valid_result[0]}")
    if valid_result[0]:
        validation_result = valid_result[2].get("validation_result", {})
        logger.info(f"Approval category: {validation_result.get('validation_category', 'Unknown')}")
        
        # Check if there's dependency context that was used
        metadata = valid_result[2].get("metadata", {})
        if "affected_downstream_components" in metadata:
            logger.info(f"Affected downstream components: {metadata['affected_downstream_components']}")

async def feature_tier_example():
    """Example of feature tier validation."""
    logger.info("\n=== Feature Tier Validation Example ===")
    earth_agent = EarthAgent(max_iterations=2)
    
    # Current feature structure for a component
    current_features = {
        "component_id": "auth_service",
        "features": [
            {
                "id": "user_authentication",
                "name": "User Authentication",
                "description": "Handles user login and session management",
                "responsibilities": ["credential validation", "session creation", "token management"],
                "dependencies": []
            }
        ]
    }
    
    # Proposed update with vague feature definition (should be corrected)
    proposed_unclear_update = {
        "component_id": "auth_service",
        "features": [
            {
                "id": "user_authentication",
                "name": "User Authentication",
                "description": "Handles user login and session management",
                "responsibilities": ["credential validation", "session creation", "token management"],
                "dependencies": []
            },
            {
                "id": "authorization",
                "name": "Authorization",
                "description": "Handles authorization",  # Too vague
                "responsibilities": ["access control"],  # Insufficient detail
                "dependencies": ["user_authentication"]
            }
        ]
    }
    
    # Validate with and without reflection for comparison
    logger.info("Validating unclear feature update that needs correction (with reflection)...")
    correction_result_with_reflection = await earth_agent.process_guideline_update(
        abstraction_tier="FEATURE",
        agent_id="feature_designer",
        current_guideline=current_features,
        proposed_update=proposed_unclear_update,
        with_reflection=True,
        operation_id="feature_correction_with_reflection"
    )
    
    logger.info("Validating unclear feature update that needs correction (without reflection)...")
    correction_result_without_reflection = await earth_agent.process_guideline_update(
        abstraction_tier="FEATURE",
        agent_id="feature_designer",
        current_guideline=current_features,
        proposed_update=proposed_unclear_update,
        with_reflection=False,
        operation_id="feature_correction_without_reflection"
    )
    
    # Compare results with and without reflection
    logger.info(f"Update result with reflection: {correction_result_with_reflection[0]}")
    logger.info(f"Update result without reflection: {correction_result_without_reflection[0]}")
    
    # If the updates were corrected, show the differences
    if correction_result_with_reflection[0] and correction_result_without_reflection[0]:
        # Find the authorization feature in both versions
        corrected_with_reflection = next((f for f in correction_result_with_reflection[1]["features"] if f["id"] == "authorization"), None)
        corrected_without_reflection = next((f for f in correction_result_without_reflection[1]["features"] if f["id"] == "authorization"), None)
        
        if corrected_with_reflection and corrected_without_reflection:
            logger.info("\nComparison of corrected features:")
            logger.info(f"Description with reflection: {corrected_with_reflection['description']}")
            logger.info(f"Description without reflection: {corrected_without_reflection['description']}")
            
            logger.info(f"\nResponsibilities with reflection: {corrected_with_reflection['responsibilities']}")
            logger.info(f"Responsibilities without reflection: {corrected_without_reflection['responsibilities']}")
            
            # Also compare metadata for dependency context usage
            metadata_with = correction_result_with_reflection[2].get("metadata", {})
            metadata_without = correction_result_without_reflection[2].get("metadata", {})
            
            if "affected_features" in metadata_with or "affected_features" in metadata_without:
                logger.info("\nDependency context usage:")
                logger.info(f"With reflection metadata: {metadata_with}")
                logger.info(f"Without reflection metadata: {metadata_without}")

async def functionality_tier_example():
    """Example of functionality tier validation."""
    logger.info("\n=== Functionality Tier Validation Example ===")
    earth_agent = EarthAgent(max_iterations=2)
    
    # Current functionality structure for a feature
    current_functionality = {
        "feature_id": "user_registration",
        "functionalities": [
            {
                "id": "email_validation",
                "name": "Email Validation",
                "description": "Validates user email format and uniqueness",
                "implementation_approach": "Regex pattern matching plus database check",
                "error_handling": ["Invalid format errors", "Duplicate email errors"],
                "dependencies": []
            }
        ]
    }
    
    # Proposed update with implementation issue (inefficient approach)
    proposed_inefficient_update = {
        "feature_id": "user_registration",
        "functionalities": [
            {
                "id": "email_validation",
                "name": "Email Validation",
                "description": "Validates user email format and uniqueness",
                "implementation_approach": "Regex pattern matching plus database check",
                "error_handling": ["Invalid format errors", "Duplicate email errors"],
                "dependencies": []
            },
            {
                "id": "password_validation",
                "name": "Password Validation",
                "description": "Validates password strength and compliance with security policies",
                "implementation_approach": "Sequential character-by-character checking of each rule", # Inefficient
                "error_handling": ["Weak password errors", "Non-compliant password errors"],
                "dependencies": ["email_validation"]
            }
        ]
    }
    
    # Validate the inefficient update with reflection enabled
    logger.info("Validating inefficient functionality implementation with reflection...")
    functionality_result = await earth_agent.process_guideline_update(
        abstraction_tier="FUNCTIONALITY",
        agent_id="implementation_engineer",
        current_guideline=current_functionality,
        proposed_update=proposed_inefficient_update,
        with_reflection=True,
        operation_id="functionality_with_reflection"
    )
    
    logger.info(f"Implementation update result: {functionality_result[0]}")
    validation_category = functionality_result[2].get("validation_result", {}).get("validation_category", "Unknown")
    logger.info(f"Validation category: {validation_category}")
    
    # If corrected, show the improved implementation approach
    if validation_category == "CORRECTED":
        original_pwd = next((f for f in proposed_inefficient_update["functionalities"] 
                            if f["id"] == "password_validation"), None)
        corrected_pwd = next((f for f in functionality_result[1]["functionalities"] 
                             if f["id"] == "password_validation"), None)
        
        if original_pwd and corrected_pwd:
            logger.info(f"Original implementation: {original_pwd['implementation_approach']}")
            logger.info(f"Improved implementation: {corrected_pwd['implementation_approach']}")
            
    # Check revision attempts
    logger.info(f"Revision attempts for functionality validation: {earth_agent.revision_attempts.get('functionality_with_reflection', 0)}")

async def reflection_and_revision_example():
    """Example showing reflection and revision process details."""
    logger.info("\n=== Reflection and Revision Process Details ===")
    
    # Create agent with test operation ID for easy tracking
    earth_agent = EarthAgent(max_iterations=3)
    operation_id = "reflection_demo_operation"
    
    # Set up a simple validation scenario
    current = {
        "ordered_components": [
            {
                "name": "existing_component",
                "dependencies": {"required": []}
            }
        ]
    }
    
    proposed = {
        "ordered_components": [
            {
                "name": "existing_component",
                "dependencies": {"required": []}
            },
            {
                "name": "new_component",
                "description": "A somewhat vague component description", # Intentionally vague
                "responsibilities": ["some functionality"],  # Intentionally unclear
                "dependencies": {"required": ["existing_component"]}
            }
        ]
    }
    
    # Run validation with reflection to observe the process
    logger.info("Running validation with reflection and revision process enabled...")
    result = await earth_agent.process_guideline_update(
        abstraction_tier="COMPONENT",
        agent_id="test_designer",
        current_guideline=current,
        proposed_update=proposed,
        operation_id=operation_id,
        with_reflection=True
    )
    
    # Check how many reflection/revision iterations were performed
    iterations = earth_agent.revision_attempts.get(operation_id, 0)
    logger.info(f"Completed {iterations} reflection/revision iterations")
    
    # Show the final validation result
    logger.info(f"Final validation category: {result[2].get('validation_result', {}).get('validation_category', 'Unknown')}")
    
    # Compare between initial and final result if a revision was done
    if iterations > 0:
        # We need to retrieve the initial result and revisions from the state manager
        # In a real application, you could compare these states with more detail
        logger.info(f"Validation went through {iterations} refinement iterations to improve quality")

async def stats_example(earth_agent):
    """Show validation statistics example."""
    logger.info("\n=== Validation Statistics ===")
    
    # Get validation statistics
    stats = await earth_agent.get_validation_stats()
    
    # Display statistics
    logger.info(f"Total validations performed: {stats['total_validations']}")
    logger.info(f"Approval rate: {stats['approval_rate'] * 100:.1f}%")
    
    logger.info("Validations by tier:")
    for tier, count in stats['validations_by_tier'].items():
        logger.info(f"  - {tier}: {count}")
    
    logger.info("Validations by agent:")
    for agent, count in stats['validations_by_agent'].items():
        logger.info(f"  - {agent}: {count}")
    
    # Show revision attempts statistics
    logger.info("\nRevision attempts by operation:")
    for op_id, attempts in earth_agent.revision_attempts.items():
        logger.info(f"  - {op_id}: {attempts} iterations")

async def main():
    """Run all Earth agent examples."""
    try:
        # Run the component tier example
        await component_tier_example()
        
        # Run the feature tier example
        await feature_tier_example()
        
        # Run the functionality tier example
        await functionality_tier_example()
        
        # Run the reflection/revision details example
        await reflection_and_revision_example()
        
        # Create a single agent instance to show stats across all examples
        earth_agent = EarthAgent()
        
        # Simulate several validations to populate history
        for i in range(5):
            agent_id = f"test_agent_{i % 3}"
            tier = ["COMPONENT", "FEATURE", "FUNCTIONALITY"][i % 3]
            is_valid = i % 2 == 0
            
            # Add to validation history directly for demonstration
            if agent_id not in earth_agent.validation_history:
                earth_agent.validation_history[agent_id] = []
                
            earth_agent.validation_history[agent_id].append({
                "operation_id": f"op_{i}",
                "tier": tier,
                "timestamp": datetime.now().isoformat(),
                "is_valid": is_valid
            })
            
        # Add some revision attempts for demonstration
        earth_agent.revision_attempts = {
            "op_0": 1,
            "op_1": 2,
            "op_2": 3
        }
        
        # Show statistics
        await stats_example(earth_agent)
        
    except Exception as e:
        logger.error(f"Error in Earth agent demo: {str(e)}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())