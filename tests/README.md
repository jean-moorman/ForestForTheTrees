# FFTT Test Suite Documentation

## Overview

This document describes the reorganized and centralized test structure for the Forest For The Trees (FFTT) project. The test suite has been completely restructured to provide better organization, maintainability, and debugging capabilities.

## Directory Structure

```
tests_new/
├── conftest.py                    # Global pytest configuration
├── __init__.py                    # Test package initialization
├── README.md                      # This documentation
├── unit/                          # Unit tests by module
│   ├── __init__.py
│   ├── core/                      # Core system functionality
│   │   ├── agents/                # Agent system tests
│   │   │   └── test_agent.py
│   │   ├── interfaces/            # Interface system tests
│   │   │   ├── test_interface.py
│   │   │   ├── test_interfaces.py
│   │   │   └── test_simple_interface.py
│   │   ├── test_dependency_validation.py
│   │   ├── test_imports.py
│   │   └── test_validation_workflow.py
│   ├── events/                    # Event system tests
│   │   ├── test_event_core.py
│   │   ├── test_event_error_handling.py
│   │   ├── test_event_integration.py
│   │   └── test_thread_safety.py
│   ├── managers/                  # Manager component tests
│   │   ├── test_cache_manager.py
│   │   ├── test_context_manager.py
│   │   ├── test_metrics_manager.py
│   │   ├── test_resource_coordinator.py
│   │   └── test_circuit_breaker_registry.py
│   ├── phases/                    # Phase-specific tests
│   │   ├── test_phase_one_standalone.py
│   │   ├── test_phase_two.py
│   │   ├── test_phase_three.py
│   │   ├── test_phase_four.py
│   │   └── test_phase_coordination.py
│   └── resources/                 # Resource management tests
│       ├── test_state_management.py
│       ├── test_monitoring.py
│       ├── test_circuit_breaker_*.py
│       └── test_state_*.py
├── integration/                   # Integration tests
│   ├── test_system_integration.py
│   ├── test_phase_one_full.py
│   ├── test_phase_one_orchestrator.py
│   └── test_phase_one_workflow.py
├── agents/                        # Agent-specific tests
│   ├── test_water_agent.py
│   ├── test_earth_agent_integration.py
│   ├── test_coordination_interface.py
│   ├── test_sequential_agent_coordinator.py
│   └── test_water_agent_coordinator.py
├── performance/                   # Performance and stress tests
│   ├── test_event_queue_stress.py
│   ├── test_concurrency_stress.py
│   ├── test_prioritized_lock_manager.py
│   ├── test_error_recovery_strategies.py
│   └── test_*_timeout.py
├── system/                        # End-to-end system tests
│   └── (Reserved for future system tests)
├── utilities/                     # Test utilities and helpers
│   └── (Reserved for test utilities)
├── fixtures/                      # Shared test fixtures
│   ├── conftest.py
│   └── (Shared fixtures and test data)
└── runners/                       # Test execution scripts
    ├── run_all_tests.py
    ├── run_unit_tests.py
    ├── run_integration_tests.py
    └── run_performance_tests.py
```

## Test Categories

### 1. Unit Tests (`unit/`)
Test individual components in isolation:
- **Core**: Agent system, interfaces, validation
- **Events**: Event processing, error handling, thread safety
- **Managers**: Cache, context, metrics, resource coordination
- **Phases**: Individual phase logic and coordination
- **Resources**: State management, monitoring, circuit breakers

### 2. Integration Tests (`integration/`)
Test interactions between components:
- Cross-component communication
- Workflow orchestration
- Phase coordination
- System integration scenarios

### 3. Agent Tests (`agents/`)
Test agent-specific functionality:
- Water agent behavior
- Earth agent integration
- Agent coordination
- Agent communication protocols

### 4. Performance Tests (`performance/`)
Test system performance and scalability:
- Stress testing
- Concurrency testing
- Timeout handling
- Memory and resource usage

### 5. System Tests (`system/`)
End-to-end testing (planned):
- Full pipeline testing
- Deployment scenarios
- Real-world usage patterns

## Running Tests

### All Tests
```bash
# Run complete test suite
python tests_new/runners/run_all_tests.py

# Run with coverage
python tests_new/runners/run_all_tests.py --coverage

# Run with minimal output
python tests_new/runners/run_all_tests.py --fast
```

### Specific Test Categories
```bash
# Unit tests only
python tests_new/runners/run_unit_tests.py

# Integration tests only
python tests_new/runners/run_integration_tests.py

# Performance tests only
python tests_new/runners/run_performance_tests.py

# Specific test category
python tests_new/runners/run_all_tests.py --unit
python tests_new/runners/run_all_tests.py --integration
python tests_new/runners/run_all_tests.py --agents
python tests_new/runners/run_all_tests.py --performance
```

### Individual Test Files
```bash
# Using pytest directly
python -m pytest tests_new/unit/core/agents/test_agent.py -xvs

# With async support
python -m pytest tests_new/unit/events/test_event_core.py -xvs --asyncio-mode=auto

# With logging
python -m pytest tests_new/integration/ -xvs --log-cli-level=INFO --log-file=test.log
```

## Test Configuration

### Global Configuration
The main `conftest.py` provides:
- Event loop fixtures for async tests
- Common test fixtures
- Temporary directory management
- Mock configurations for agents and resources

### Module-Specific Configuration
Individual modules may have their own `conftest.py` files for:
- Module-specific fixtures
- Setup and teardown procedures
- Mock implementations

## Writing New Tests

### Test Naming
- Test files: `test_*.py`
- Test functions: `test_*`
- Test classes: `Test*`

### Test Organization
1. **Unit tests**: Place in appropriate `unit/` subdirectory
2. **Integration tests**: Place in `integration/`
3. **Agent tests**: Place in `agents/`
4. **Performance tests**: Place in `performance/`

### Import Guidelines
```python
# Use absolute imports from project root
from agent import Agent
from resources.monitoring import CircuitBreaker
from phase_one.orchestrator import PhaseOneOrchestrator

# Use relative imports only within the same test module
from .fixtures import mock_agent_config
```

### Async Test Support
```python
import pytest
import asyncio

@pytest.mark.asyncio
async def test_async_functionality():
    # Async test implementation
    result = await some_async_function()
    assert result is not None
```

## Debugging Tests

### Running with Debug Output
```bash
# Maximum verbosity with logging
python -m pytest tests_new/ -xvs --log-cli-level=DEBUG --capture=no

# Stop on first failure
python -m pytest tests_new/ -x --pdb

# Run specific test with debugging
python -m pytest tests_new/unit/core/agents/test_agent.py::test_agent_initialization -xvs --pdb
```

### Test Logs
Test execution generates logs in:
- `test.log` - General test execution
- `unit_tests.log` - Unit test execution
- `integration_tests.log` - Integration test execution
- `performance_tests.log` - Performance test execution

## Migration from Old Structure

### What Changed
1. **Centralized location**: All tests moved to `tests_new/`
2. **Logical grouping**: Tests organized by functionality and scope
3. **Consistent naming**: All test files follow `test_*.py` pattern
4. **Unified runners**: Consolidated test execution scripts
5. **Updated configuration**: Global and module-specific pytest configuration

### Import Path Updates
Most imports remained the same as they used absolute imports from the project root. Only test-specific imports needed updates.

### Deprecated Files
The following files in the old structure are now deprecated:
- Individual `run_*test*.py` files in various directories
- Scattered test files in root directory
- Old `tests/` directory structure

## Best Practices

### Test Writing
1. **Isolation**: Each test should be independent
2. **Clarity**: Use descriptive test names and docstrings
3. **Coverage**: Aim for comprehensive test coverage
4. **Performance**: Keep unit tests fast, use performance tests for stress testing
5. **Mocking**: Use mocks judiciously, prefer real implementations when possible

### Test Maintenance
1. **Regular updates**: Keep tests updated with code changes
2. **Cleanup**: Remove obsolete tests
3. **Documentation**: Update test documentation
4. **Monitoring**: Track test performance and flakiness

## Future Enhancements

### Planned Additions
1. **System tests**: Full end-to-end testing
2. **Test utilities**: Common test helpers and fixtures
3. **Test data management**: Structured test data handling
4. **Continuous testing**: Integration with CI/CD pipeline
5. **Test reporting**: Enhanced test result reporting and analysis

### Integration Opportunities
1. **Code coverage**: Integration with coverage reporting tools
2. **Test automation**: Automated test execution on code changes
3. **Performance monitoring**: Tracking test execution performance
4. **Quality metrics**: Test quality and maintainability metrics

This centralized test structure provides a solid foundation for maintaining and expanding the FFTT test suite as the project grows.