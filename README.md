# Forest For The Trees (FFTT)

## Overview
Forest For The Trees (FFTT) is a nature-inspired Python application designed to allow for automated software development via a sophisticated system of LLM agent workflows. The system operation takes place in four phases, handling everything from initial project requirements to code implementation and deployment.

## Key Components

### Phase Structure
1. **Phase 0**: Quality assurance for the various phase refinement agents
2. **Phase 1**: Establishes foundational guidelines prior to testing and implementation
3. **Phase 2**: Systematically develops the software project
4. **Phase 3**: Nested calls to flexibly create feature sets
5. **Phase 4**: Nested calls to build feature tests and implementations with static compilers

### Core Agents
- **Earth Agent**: Validates potential updates to foundational guidelines across all abstraction tiers (component, feature, functionality)
- **Water Agent**: Coordinates propagation of validated guideline updates across the dependency graph, providing rich contextual information to affected downstream agents
- **System Monitoring Agent**: Processes system metrics to give reports and recovery recommendations
- **Refinement Agents**: Subphase-specific manager agents that handle decision bottlenecks in the system operation

## Project Structure
The project is organized into the following key directories:
- `FFTT_system_prompts/`: Contains system prompts for all agents
- `resources/`: Core resource management functionality
- `tests/`: Test modules for all components
- `examples/`: Example usage of key components

## Core Agent Mechanics

### Earth Agent
The Earth Agent is responsible for validating potential updates to foundational guidelines. For example, if an agent decides to revise its output, this is considered a guideline update and has to be validated by the Earth agent. 

The Earth agent examines the before and after state of the guidelines to:
1. Detect system-breaking changes and flag them
2. Correct guidelines that are feasible but incorrect
3. Provide explanations for rejected updates

Earth agent validations happen at three abstraction tiers:
- **Component Tier**: High-level structural components (Phase 1)
- **Feature Tier**: Features within components (Phase 2a)  
- **Functionality Tier**: Implementation details (Phase 3a)

#### Usage Example
```python
from resources.earth_agent import EarthAgent, AbstractionTier

# Create Earth agent
earth_agent = EarthAgent()

# Validate a component-level guideline update
accepted, final_guideline, validation_details = await earth_agent.process_guideline_update(
    abstraction_tier="COMPONENT",
    agent_id="component_architect",
    current_guideline=current_components,
    proposed_update=proposed_update
)

if accepted:
    print("Update accepted with modifications")
    # Use the final_guideline
else:
    print(f"Update rejected: {validation_details['validation_result']['explanation']}")
```

### Water Agent
The Water Agent is responsible for coordinating the propagation of validated guideline updates throughout the system's dependency graph. It ensures that changes made by one agent flow coherently to all dependent downstream agents.

The Water agent's primary responsibilities include:
1. **Dependency Analysis**: Analyzing the system to identify all agents affected by an update
2. **Rich Context Generation**: Creating detailed contextual information explaining why changes are happening and how they impact each specific agent
3. **Adaptation Guidance**: Providing tailored, actionable guidance on how each agent should integrate the changes
4. **Ordered Propagation**: Applying updates in the correct dependency order to ensure system coherence

The Water agent uses LLM-powered capabilities for three critical phases:
- **Propagation Analysis**: Determines which agents are affected and the optimal propagation strategy
- **Context Generation**: Creates rich explanations of the changes and their implications
- **Adaptation Guidance**: Develops tailored implementation recommendations for each affected agent

#### Usage Example
```python
from resources.water_agent import WaterAgent
from interface import get_earth_agent

# Create Water agent (linked to Earth agent)
earth_agent = get_earth_agent()
water_agent = WaterAgent(earth_agent=earth_agent)

# After Earth agent validates an update, propagate it to affected agents
propagation_result = await water_agent.coordinate_propagation(
    origin_agent_id="garden_planner",
    validated_update=validated_update,
    validation_result=validation_result
)

# Check propagation results
if propagation_result.success:
    print(f"Update successfully propagated to {propagation_result.metrics['affected_count']} agents")
else:
    print(f"Propagation had {len(propagation_result.failures)} failures")
```

## Installation
```bash
# Clone the repository
git clone https://github.com/your-username/FFTT.git
cd FFTT

# Install dependencies
pip install -r requirements.txt
```

## Running Tests
```bash
# Run all tests
python -m pytest -xvs --log-cli-level=INFO --log-file=test.log --color=yes

# Run specific test file
python -m pytest -xvs tests/path/to/test_file.py

# Run Earth agent tests
python -m pytest -xvs tests/test_earth_agent.py
```

## Running Examples
```bash
# Run Earth agent demo
python examples/earth_agent_demo.py

# Run Earth-Water integration example
python examples/earth_water_integration.py
```

## Development
Refer to the CLAUDE.md file for detailed development guidelines and instructions.

## License
This project is licensed under the MIT License - see the LICENSE file for details.
