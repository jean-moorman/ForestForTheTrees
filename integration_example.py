"""
Demonstration of the dependency validation workflow.

This script shows how to use the DependencyValidator class to validate
data flow and structural breakdown in phase one.
"""

import asyncio
import json
from typing import Dict, Any
from datetime import datetime

from dependency import DependencyValidator
from resources import StateManager, EventQueue

# Sample data for demonstration
VALID_DATA_FLOW = {
    "data_flows": [
        {
            "flow_id": "flow1",
            "source": "componentA",
            "destination": "componentB",
            "data_type": "string",
            "transformation": "none",
            "trigger": "event"
        },
        {
            "flow_id": "flow2",
            "source": "componentB",
            "destination": "componentC",
            "data_type": "string",
            "transformation": "none",
            "trigger": "event"
        }
    ]
}

INVALID_DATA_FLOW = {
    "data_flows": [
        {
            "flow_id": "flow1",
            "source": "componentA", 
            "destination": "componentB",
            "data_type": "string",
            "transformation": "none",
            "trigger": "event"
        },
        {
            "flow_id": "flow2",
            "source": "componentB",
            "destination": "componentA",  # Creates a cycle
            "data_type": "string",
            "transformation": "none",
            "trigger": "event"
        }
    ]
}

VALID_STRUCTURE = {
    "ordered_components": [
        {
            "name": "componentA",
            "sequence_number": 1,
            "dependencies": {
                "required": [],
                "optional": []
            }
        },
        {
            "name": "componentB",
            "sequence_number": 2,
            "dependencies": {
                "required": ["componentA"],
                "optional": []
            }
        },
        {
            "name": "componentC",
            "sequence_number": 3,
            "dependencies": {
                "required": ["componentB"],
                "optional": []
            }
        }
    ]
}

INCONSISTENT_STRUCTURE = {
    "ordered_components": [
        {
            "name": "componentA",
            "sequence_number": 1,
            "dependencies": {
                "required": [],
                "optional": []
            }
        },
        {
            "name": "componentB",
            "sequence_number": 2,
            "dependencies": {
                "required": [],  # Missing dependency on componentA from data flow
                "optional": []
            }
        },
        {
            "name": "componentC",
            "sequence_number": 3,
            "dependencies": {
                "required": ["componentB"],
                "optional": []
            }
        }
    ]
}

async def demonstrate_validation():
    """Demonstrate the validation functionality."""
    print("Starting demonstration of dependency validation")
    
    # Create necessary resources
    event_queue = EventQueue()
    state_manager = StateManager("demo_manager", event_queue)
    
    # Create validator
    validator = DependencyValidator(state_manager)
    
    # 1. Validate data flow
    print("\n1. Validating valid data flow...")
    is_valid, errors = validator.dependency_interface.validate_data_flow(VALID_DATA_FLOW)
    print(f"Result: {'Valid' if is_valid else 'Invalid'} with {len(errors)} errors")
    
    # 2. Validate invalid data flow
    print("\n2. Validating invalid data flow...")
    is_valid, errors = validator.dependency_interface.validate_data_flow(INVALID_DATA_FLOW)
    print(f"Result: {'Valid' if is_valid else 'Invalid'} with {len(errors)} errors")
    if errors:
        print("Errors:")
        for error in errors:
            print(f"  - {error['message']}")
    
    # 3. Validate valid structure
    print("\n3. Validating valid structural breakdown...")
    is_valid, errors = validator.dependency_interface.validate_structural_breakdown(VALID_STRUCTURE)
    print(f"Result: {'Valid' if is_valid else 'Invalid'} with {len(errors)} errors")
    
    # 4. Store valid data flow and structure for cross-validation
    validator._data_flow = VALID_DATA_FLOW
    validator._structural_breakdown = VALID_STRUCTURE
    
    # 5. Cross validate consistent data
    print("\n4. Cross-validating consistent data flow and structure...")
    is_valid, errors = validator.dependency_interface.validate_cross_consistency(VALID_DATA_FLOW, VALID_STRUCTURE)
    print(f"Result: {'Valid' if is_valid else 'Invalid'} with {len(errors)} errors")
    
    # 6. Cross validate inconsistent data
    print("\n5. Cross-validating inconsistent data flow and structure...")
    is_valid, errors = validator.dependency_interface.validate_cross_consistency(VALID_DATA_FLOW, INCONSISTENT_STRUCTURE)
    print(f"Result: {'Valid' if is_valid else 'Invalid'} with {len(errors)} errors")
    if errors:
        print("Errors:")
        for error in errors:
            print(f"  - {error['message']}")
    
    # 7. Determine responsible agent
    print("\n6. Determining responsible agent for errors...")
    responsible_agent = await validator.determine_responsible_agent(errors)
    print(f"Responsible agent: {responsible_agent}")
    
    # 8. Prepare agent feedback
    print("\n7. Preparing feedback for the responsible agent...")
    feedback = await validator.prepare_agent_feedback(responsible_agent, errors)
    print(f"Feedback prepared for {feedback['agent_type']} with {feedback['error_count']} errors")
    
    print("\nDemonstration completed successfully!")

if __name__ == "__main__":
    # Run the demonstration
    asyncio.run(demonstrate_validation())