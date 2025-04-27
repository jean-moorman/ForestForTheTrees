"""
Standalone implementation of the dependency validator.

This module provides a self-contained implementation of the dependency validation
system which does not rely on the main codebase's interfaces. This is useful
for demonstration purposes and for testing the validation logic independently.
"""

import asyncio
import json
from typing import Dict, List, Any, Optional, Set, Tuple, Type, TypeVar
from dataclasses import dataclass, field
from enum import Enum, auto
from collections import defaultdict
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DependencyType(Enum):
    """Types of dependencies between components."""
    PRIMARY = auto()
    SECONDARY = auto()
    AUXILIARY = auto()
    COMPONENT_TO_FEATURE = auto()
    FEATURE_TO_FUNCTIONALITY = auto()
    HIERARCHICAL = auto()  # Special type for hierarchical dependencies
    
class ResourceState(Enum):
    """States for resources in the system."""
    INITIALIZED = auto()
    ACTIVE = auto()
    PAUSED = auto()
    VALIDATING = auto()
    PROPAGATING = auto()
    FAILED = auto()
    TERMINATED = auto()
    ERROR = auto()

class DependencyValidator:
    """
    Validates dependency relationships between components.
    
    This class provides methods to validate:
    1. Data flow structure
    2. Structural breakdown of components
    3. Cross-consistency between data flow and structure
    """
    
    def __init__(self):
        """Initialize the validator."""
        self._validation_errors = []
        self._data_flow = None
        self._structural_breakdown = None
        self._validation_history = []
        
    def validate_data_flow(self, data_flow: Dict[str, Any]) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Validate data flow structure in real-time.
        
        Args:
            data_flow: The data flow structure to validate
            
        Returns:
            Tuple of (is_valid, errors)
        """
        errors = []
        
        # Verify data flow basic structure
        if not isinstance(data_flow, dict):
            errors.append({
                "error_type": "invalid_data_flow_structure",
                "message": "Data flow must be a dictionary"
            })
            return False, errors
            
        # Verify data flows
        if "data_flows" not in data_flow:
            errors.append({
                "error_type": "missing_data_flows",
                "message": "Data flow must contain 'data_flows' key"
            })
            return False, errors
            
        flows = data_flow.get("data_flows", [])
        
        # Track source-destination pairs to detect duplicates
        flow_pairs = set()
        
        # Check each flow
        for i, flow in enumerate(flows):
            # Check required fields
            required_fields = ["source", "destination", "data_type"]
            for field in required_fields:
                if field not in flow:
                    errors.append({
                        "error_type": "missing_field",
                        "flow_index": i,
                        "field": field,
                        "message": f"Flow missing required field: {field}"
                    })
            
            # Skip further validation if required fields are missing
            if any(field not in flow for field in required_fields):
                continue
                
            # Check for self-reference
            if flow["source"] == flow["destination"]:
                errors.append({
                    "error_type": "self_reference",
                    "flow_index": i,
                    "source": flow["source"],
                    "message": f"Flow cannot have same source and destination: {flow['source']}"
                })
                
            # Check for duplicate flows
            flow_pair = (flow["source"], flow["destination"])
            if flow_pair in flow_pairs:
                errors.append({
                    "error_type": "duplicate_flow",
                    "flow_index": i,
                    "source": flow["source"],
                    "destination": flow["destination"],
                    "message": f"Duplicate flow from {flow['source']} to {flow['destination']}"
                })
            flow_pairs.add(flow_pair)
            
        # Check for cycles in the data flow graph
        graph = defaultdict(set)
        for flow in flows:
            if "source" in flow and "destination" in flow:
                graph[flow["source"]].add(flow["destination"])
                
        # Detect cycles using DFS
        visited = set()
        recursion_stack = set()
        
        def has_cycle(node):
            visited.add(node)
            recursion_stack.add(node)
            
            for neighbor in graph[node]:
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in recursion_stack:
                    errors.append({
                        "error_type": "data_flow_cycle",
                        "cycle_node": node,
                        "cycle_next": neighbor,
                        "message": f"Cycle detected in data flow: {node} -> {neighbor}"
                    })
                    return True
                    
            recursion_stack.remove(node)
            return False
            
        for node in graph:
            if node not in visited:
                if has_cycle(node):
                    break
                    
        # Store data flow for cross-validation
        self._data_flow = data_flow
        
        # Record validation event
        self.record_validation_event(
            "data_flow",
            "success" if len(errors) == 0 else "failure",
            errors
        )
                    
        # Return validation result
        return len(errors) == 0, errors
        
    def validate_structural_breakdown(self, structure: Dict[str, Any]) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Validate structural breakdown in real-time.
        
        Args:
            structure: The structural breakdown to validate
            
        Returns:
            Tuple of (is_valid, errors)
        """
        errors = []
        
        # Verify structure basic format
        if not isinstance(structure, dict):
            errors.append({
                "error_type": "invalid_structure_format",
                "message": "Structure must be a dictionary"
            })
            return False, errors
            
        # Verify components are present
        if "ordered_components" not in structure:
            errors.append({
                "error_type": "missing_components",
                "message": "Structure must contain 'ordered_components' key"
            })
            return False, errors
            
        components = structure.get("ordered_components", [])
        
        # Track component names to detect duplicates
        component_names = set()
        component_sequence_numbers = set()
        
        # Check each component
        for i, component in enumerate(components):
            # Check required fields
            required_fields = ["name", "sequence_number", "dependencies"]
            for field in required_fields:
                if field not in component:
                    errors.append({
                        "error_type": "missing_field",
                        "component_index": i,
                        "field": field,
                        "message": f"Component missing required field: {field}"
                    })
            
            # Skip further validation if required fields are missing
            if any(field not in component for field in required_fields):
                continue
                
            # Check for duplicate names
            if component["name"] in component_names:
                errors.append({
                    "error_type": "duplicate_component_name",
                    "component_index": i,
                    "name": component["name"],
                    "message": f"Duplicate component name: {component['name']}"
                })
            component_names.add(component["name"])
            
            # Check for duplicate sequence numbers
            if component["sequence_number"] in component_sequence_numbers:
                errors.append({
                    "error_type": "duplicate_sequence_number",
                    "component_index": i,
                    "sequence_number": component["sequence_number"],
                    "message": f"Duplicate sequence number: {component['sequence_number']}"
                })
            component_sequence_numbers.add(component["sequence_number"])
            
            # Check dependencies exist
            if "dependencies" in component and "required" in component["dependencies"]:
                for dep in component["dependencies"]["required"]:
                    if dep not in component_names and i > 0:  # Allow forward references for first component
                        errors.append({
                            "error_type": "undefined_dependency",
                            "component_index": i,
                            "component_name": component["name"],
                            "dependency": dep,
                            "message": f"Component {component['name']} depends on undefined component: {dep}"
                        })
        
        # Check for cycles in dependency graph
        graph = defaultdict(set)
        for component in components:
            if "name" in component and "dependencies" in component and "required" in component["dependencies"]:
                name = component["name"]
                for dep in component["dependencies"]["required"]:
                    graph[name].add(dep)
                    
        # Detect cycles using DFS
        visited = set()
        recursion_stack = set()
        
        def has_cycle(node):
            visited.add(node)
            recursion_stack.add(node)
            
            for neighbor in graph[node]:
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in recursion_stack:
                    errors.append({
                        "error_type": "dependency_cycle",
                        "cycle_node": node,
                        "cycle_next": neighbor,
                        "message": f"Cycle detected in component dependencies: {node} -> {neighbor}"
                    })
                    return True
                    
            recursion_stack.remove(node)
            return False
            
        for node in graph:
            if node not in visited:
                if has_cycle(node):
                    break
        
        # Store structural breakdown for cross-validation
        self._structural_breakdown = structure
        
        # Record validation event
        self.record_validation_event(
            "structural_breakdown",
            "success" if len(errors) == 0 else "failure",
            errors
        )
                
        # Return validation result
        return len(errors) == 0, errors
        
    def validate_cross_consistency(self, data_flow: Optional[Dict[str, Any]] = None, 
                                 structure: Optional[Dict[str, Any]] = None) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Validate cross-consistency between data flow and structural breakdown.
        
        Args:
            data_flow: The data flow structure to validate (or use stored value)
            structure: The structural breakdown to validate (or use stored value)
            
        Returns:
            Tuple of (is_valid, errors)
        """
        errors = []
        
        # Use provided values or stored values
        data_flow = data_flow or self._data_flow
        structure = structure or self._structural_breakdown
        
        # Ensure both data flow and structural breakdown are available
        if data_flow is None or structure is None:
            errors.append({
                "error_type": "missing_validation_data",
                "message": "Both data flow and structural breakdown must be provided for cross-validation"
            })
            return False, errors
        
        # Extract components from structure
        components = []
        if isinstance(structure, dict) and "ordered_components" in structure:
            for comp in structure.get("ordered_components", []):
                if "name" in comp:
                    components.append(comp["name"])
        
        component_set = set(components)
        
        # Extract flows from data flow
        flows = []
        if isinstance(data_flow, dict) and "data_flows" in data_flow:
            flows = data_flow.get("data_flows", [])
            
        # Check each flow references valid components
        for i, flow in enumerate(flows):
            if "source" in flow and flow["source"] != "external" and flow["source"] not in component_set:
                errors.append({
                    "error_type": "flow_invalid_source",
                    "flow_index": i,
                    "source": flow["source"],
                    "message": f"Flow references non-existent source component: {flow['source']}"
                })
                
            if "destination" in flow and flow["destination"] != "external" and flow["destination"] not in component_set:
                errors.append({
                    "error_type": "flow_invalid_destination",
                    "flow_index": i,
                    "destination": flow["destination"],
                    "message": f"Flow references non-existent destination component: {flow['destination']}"
                })
                
        # Verify component dependencies align with data flows
        flow_dependencies = defaultdict(set)
        for flow in flows:
            if "source" in flow and "destination" in flow:
                if flow["source"] != "external" and flow["destination"] != "external":
                    flow_dependencies[flow["destination"]].add(flow["source"])
                    
        for i, comp in enumerate(structure.get("ordered_components", [])):
            if "name" not in comp or "dependencies" not in comp or "required" not in comp["dependencies"]:
                continue
                
            comp_name = comp["name"]
            comp_deps = set(comp["dependencies"]["required"])
            flow_deps = flow_dependencies.get(comp_name, set())
            
            # Check if data flow dependencies are reflected in structural dependencies
            for flow_dep in flow_deps:
                if flow_dep not in comp_deps:
                    errors.append({
                        "error_type": "missing_structural_dependency",
                        "component_name": comp_name,
                        "data_flow_dependency": flow_dep,
                        "message": f"Component {comp_name} has data flow from {flow_dep} but missing structural dependency"
                    })
                    
            # Check if structural dependencies have corresponding data flows
            for struct_dep in comp_deps:
                if struct_dep not in flow_deps and struct_dep in component_set:
                    errors.append({
                        "error_type": "missing_data_flow",
                        "component_name": comp_name,
                        "structural_dependency": struct_dep,
                        "message": f"Component {comp_name} depends on {struct_dep} but no data flow exists"
                    })
        
        # Record validation event
        self.record_validation_event(
            "cross_consistency",
            "success" if len(errors) == 0 else "failure",
            errors
        )
        
        return len(errors) == 0, errors
    
    def record_validation_event(self, event_type: str, status: str, errors: List[Dict[str, Any]] = None) -> None:
        """Record a validation event for history and metrics tracking."""
        event = {
            "event_type": event_type,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "errors": errors or []
        }
        
        self._validation_history.append(event)
        
    async def determine_responsible_agent(self, errors: List[Dict[str, Any]]) -> Optional[str]:
        """
        Analyze validation errors to determine which agent is responsible for correction.
        
        Returns "data_flow_agent" or "structural_agent" based on error analysis.
        """
        # Count error types to make a decision
        data_flow_errors = 0
        structural_errors = 0
        
        for error in errors:
            error_type = error.get("error_type", "")
            
            # Data flow error types
            if error_type in [
                "invalid_data_flow_structure", "missing_data_flows", "self_reference",
                "duplicate_flow", "data_flow_cycle", "flow_invalid_source", 
                "flow_invalid_destination", "missing_data_flow"
            ]:
                data_flow_errors += 1
                
            # Structural error types
            elif error_type in [
                "invalid_structure_format", "missing_components", "duplicate_component_name",
                "duplicate_sequence_number", "undefined_dependency", "dependency_cycle",
                "missing_structural_dependency"
            ]:
                structural_errors += 1
        
        # Make a decision
        if data_flow_errors > structural_errors:
            return "data_flow_agent"
        elif structural_errors > data_flow_errors:
            return "structural_agent"
        elif data_flow_errors > 0:  # If tied but errors exist, fix data flow first
            return "data_flow_agent"
        else:
            return None  # No errors or cannot determine
            
    async def prepare_agent_feedback(self, agent_type: str, errors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Prepare feedback for the agent to correct errors.
        
        Args:
            agent_type: Either "data_flow_agent" or "structural_agent"
            errors: List of validation errors
            
        Returns:
            Dictionary with feedback information for the agent
        """
        # Filter errors relevant to this agent
        relevant_errors = []
        
        if agent_type == "data_flow_agent":
            error_types = [
                "invalid_data_flow_structure", "missing_data_flows", "self_reference",
                "duplicate_flow", "data_flow_cycle", "flow_invalid_source", 
                "flow_invalid_destination", "missing_data_flow"
            ]
        else:  # structural_agent
            error_types = [
                "invalid_structure_format", "missing_components", "duplicate_component_name",
                "duplicate_sequence_number", "undefined_dependency", "dependency_cycle",
                "missing_structural_dependency"
            ]
            
        for error in errors:
            if error.get("error_type", "") in error_types:
                relevant_errors.append(error)
                
        # Prepare feedback for the agent
        return {
            "agent_type": agent_type,
            "error_count": len(relevant_errors),
            "errors": relevant_errors,
            "timestamp": datetime.now().isoformat(),
            "correction_required": len(relevant_errors) > 0
        }
        
    async def get_validation_summary(self) -> Dict[str, Any]:
        """Get a summary of validation results."""
        return {
            "data_flow_validated": self._data_flow is not None,
            "structural_breakdown_validated": self._structural_breakdown is not None,
            "cross_consistency_validated": any(event["event_type"] == "cross_consistency" for event in self._validation_history),
            "validation_history": self._validation_history,
            "latest_validation_time": self._validation_history[-1]["timestamp"] if self._validation_history else None,
            "overall_status": "success" if all(event["status"] == "success" for event in self._validation_history) else "failure"
        }


# Sample data for testing
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
    
    # Create validator
    validator = DependencyValidator()
    
    # 1. Validate data flow
    print("\n1. Validating valid data flow...")
    is_valid, errors = validator.validate_data_flow(VALID_DATA_FLOW)
    print(f"Result: {'Valid' if is_valid else 'Invalid'} with {len(errors)} errors")
    
    # 2. Validate invalid data flow
    print("\n2. Validating invalid data flow...")
    is_valid, errors = validator.validate_data_flow(INVALID_DATA_FLOW)
    print(f"Result: {'Valid' if is_valid else 'Invalid'} with {len(errors)} errors")
    if errors:
        print("Errors:")
        for error in errors:
            print(f"  - {error['message']}")
    
    # 3. Validate valid structure
    print("\n3. Validating valid structural breakdown...")
    is_valid, errors = validator.validate_structural_breakdown(VALID_STRUCTURE)
    print(f"Result: {'Valid' if is_valid else 'Invalid'} with {len(errors)} errors")
    
    # 4. Cross validate consistent data
    print("\n4. Cross-validating consistent data flow and structure...")
    is_valid, errors = validator.validate_cross_consistency(VALID_DATA_FLOW, VALID_STRUCTURE)
    print(f"Result: {'Valid' if is_valid else 'Invalid'} with {len(errors)} errors")
    
    # 5. Cross validate inconsistent data
    print("\n5. Cross-validating inconsistent data flow and structure...")
    is_valid, errors = validator.validate_cross_consistency(VALID_DATA_FLOW, INCONSISTENT_STRUCTURE)
    print(f"Result: {'Valid' if is_valid else 'Invalid'} with {len(errors)} errors")
    if errors:
        print("Errors:")
        for error in errors:
            print(f"  - {error['message']}")
    
    # 6. Determine responsible agent
    print("\n6. Determining responsible agent for errors...")
    responsible_agent = await validator.determine_responsible_agent(errors)
    print(f"Responsible agent: {responsible_agent}")
    
    # 7. Prepare agent feedback
    print("\n7. Preparing feedback for the responsible agent...")
    feedback = await validator.prepare_agent_feedback(responsible_agent, errors)
    print(f"Feedback prepared for {feedback['agent_type']} with {feedback['error_count']} errors")
    
    # 8. Get validation summary
    print("\n8. Getting validation summary...")
    summary = await validator.get_validation_summary()
    print(f"Validation summary: Overall status {summary['overall_status']}")
    print(f"  - Data flow validated: {summary['data_flow_validated']}")
    print(f"  - Structural breakdown validated: {summary['structural_breakdown_validated']}")
    print(f"  - Cross-consistency validated: {summary['cross_consistency_validated']}")
    
    print("\nDemonstration completed successfully!")

if __name__ == "__main__":
    # Run the demonstration
    asyncio.run(demonstrate_validation())