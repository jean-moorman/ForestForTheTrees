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
- **System Monitoring Agent**: Processes system metrics to give reports and recovery recommendations
- **Refinement Agents**: Core agents that handle decision bottlenecks in the system operation

## Project Structure
The project is organized into the following key directories:
- `FFTT_system_prompts/`: Contains system prompts for all agents
- `resources/`: Core resource management functionality
- `tests/`: Test modules for all components
- `examples/`: Example usage of key components

## Earth Agent
The Earth Agent is responsible for validating potential updates to foundational guidelines. For example, if an agent decides to revise its output, this is considered a guideline update and has to be validated by the Earth agent. 

The Earth agent examines the before and after state of the guidelines to:
1. Detect system-breaking changes and flag them
2. Correct guidelines that are feasible but incorrect
3. Provide explanations for rejected updates

Earth agent validations happen at three abstraction tiers:
- **Component Tier**: High-level structural components (Phase 1)
- **Feature Tier**: Features within components (Phase 2a)  
- **Functionality Tier**: Implementation details (Phase 3a)

### Usage Example
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
```

## Development
Refer to the CLAUDE.md file for detailed development guidelines and instructions.

## License
This project is licensed under the MIT License - see the LICENSE file for details.