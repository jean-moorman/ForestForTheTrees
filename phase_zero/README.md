# Phase Zero

## Overview
Phase Zero is the feedback and analysis subsystem for Phase One in the FFTT framework. It provides quality assurance and feedback for various Phase One refinement agents.

This module has been refactored from a monolithic file into a package structure for better maintainability, readability, and extensibility.

## Package Structure

### Base Infrastructure (`base.py`)
- `AnalysisState` - Enum for tracking agent analysis states
- `MetricsSnapshot` - Data class for system metrics
- `BaseAnalysisAgent` - Base class with resource management for all analysis agents

### Utilities (`utils.py`)
- Timeout management
- Memory tracking
- Agent execution helpers

### Agent Groups
Agents are organized by domain/category:

- **Monitoring** (`agents/monitoring.py`)
  - `MonitoringAgent` - System monitoring and metrics analysis

- **Description Analysis** (`agents/description_analysis.py`)
  - `SunAgent` - Critical description issues
  - `ShadeAgent` - Critical description gaps
  - `WindAgent` - Critical description conflicts

- **Requirement Analysis** (`agents/requirement_analysis.py`)
  - `SoilAgent` - Critical requirement gaps
  - `MicrobialAgent` - Critical guideline conflicts
  - `RainAgent` - Critical requirement issues

- **Data Flow Analysis** (`agents/data_flow.py`)
  - `RootSystemAgent` - Critical data flow gaps
  - `MycelialAgent` - Critical guideline conflicts for data flow
  - `WormAgent` - Critical data flow issues

- **Structural Analysis** (`agents/structural.py`)
  - `InsectAgent` - Critical structure gaps
  - `BirdAgent` - Critical guideline conflicts for structure
  - `TreeAgent` - Critical structural issues

- **Optimization** (`agents/optimization.py`)
  - `PollinatorAgent` - Component optimization opportunities

- **Synthesis** (`agents/synthesis.py`)
  - `EvolutionAgent` - System adaptations based on analysis results

### Validation Mechanisms
- **Earth Mechanism** (`validation/earth.py`) - Validates guideline updates
- **Water Mechanism** (`validation/water.py`) - Propagates guideline updates to downstream components

### Orchestration (`orchestrator.py`)
The `PhaseZeroOrchestrator` class coordinates all agents and processes metrics with proper resource management.

## Backward Compatibility
All components are re-exported from the main `phase_zero.py` file for backward compatibility with existing code.

## Usage
You can import components either directly from the package structure or from the main module:

```python
# Direct import from package structure
from phase_zero.agents.monitoring import MonitoringAgent
from phase_zero.orchestrator import PhaseZeroOrchestrator

# Or import from main module (backward compatible)
from phase_zero import MonitoringAgent, PhaseZeroOrchestrator
```