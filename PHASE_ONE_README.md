# Phase One Testing Suite

This directory contains tools for testing Phase One functionality independently of Phase Two and later phases. This allows for easier development and testing of Phase One components without dependencies on incomplete parts of the system.

## Components

1. **phase_one_test.py** - A standalone GUI application mirroring main.py but only using Phase One functionality.
2. **phase_one_cli.py** - A command-line interface for testing Phase One without requiring the GUI.
3. **run_phase_one.py** - A utility script providing a unified interface for running the various Phase One tests.

## Running the Tests

### GUI Application

To run the Phase One GUI test application:

```bash
./run_phase_one.py gui
```

This will launch a PyQt6 GUI similar to the main application, but only with Phase One capabilities.

**Note**: The test applications use a minimal implementation of the Phase Zero orchestrator (defined in `phase_one_minimal_phase_zero.py`) to satisfy dependencies in the PhaseOneOrchestrator initialization. They also use a fixed subclass of PhaseOneOrchestrator that properly initializes the Phase One agents with agent_id parameters.

### CLI Application

To run the Phase One CLI test application:

```bash
# Interactive mode (default)
./run_phase_one.py cli

# Process a prompt directly
./run_phase_one.py cli -p "Create a habit tracking app"

# Process a prompt from a file
./run_phase_one.py cli -f prompt.txt

# Save results to a file
./run_phase_one.py cli -p "Create a habit tracking app" -o results.json
```

### Pytest Tests

To run the Phase One pytest test suite:

```bash
# Run all Phase One tests
./run_phase_one.py test

# Run a specific test file
./run_phase_one.py test -f tests/test_phase_one_workflow.py

# Run with additional pytest arguments
./run_phase_one.py test -a "--asyncio-mode=auto --log-cli-level=DEBUG"
```

## System Flow

The Phase One system flow includes:

1. **Garden Planner agent** with **Earth agent** validation
   - Earth agent validates project overview against user request
   - Feedback loop for refinement if issues are detected

2. **Environmental Analysis agent** analyzes requirements

3. **Root System agent** creates core data flow

4. **Tree Placement Planner agent** delineates structural components

All agents undergo output validation and self-reflection/revision with a maximum number of iterations.

## Water Agent Integration

The Water Agent facilitates cooperation between sequential agents by:
- Mediating handoffs between agents
- Detecting and resolving misunderstandings
- Ensuring context is properly transferred between agents

## Output Format

The final output from Phase One includes:

1. Validated task analysis from Garden Planner
2. Environmental analysis of requirements
3. Data architecture from Root System Architect
4. Component architecture with structural components from Tree Placement Planner

This output would normally be passed to Phase Two for component implementation, but the testing suite allows examining the Phase One output directly.