# Forest Application Test Suite

This test suite provides comprehensive testing for the Forest Application, focusing on testing real system functionality without mock implementations.

## Test Files

The test suite is organized into the following files:

- **test_main.py**: Tests for the core ForestApplication class and its initialization, event handling, and lifecycle.
- **test_event_queue.py**: Tests for the EventQueue class and event handling mechanisms.
- **test_task_management.py**: Tests for task and thread management features.
- **test_monitoring.py**: Tests for the monitoring components and lifecycle management.
- **conftest.py**: Shared fixtures and pytest configuration.
- **run_tests.py**: Script to run all tests.

## Design Philosophy

The test suite follows these key principles:

1. **Real System Testing**: Tests use actual implementation components rather than mocks to verify real behavior.
2. **Comprehensive Coverage**: Tests cover initialization, event handling, resource management, error handling, and lifecycle management.
3. **Async Testing**: Proper handling of asynchronous operations using asyncio and qasync.
4. **Clean Setup/Teardown**: Each test properly initializes and cleans up resources.
5. **Error Condition Testing**: Tests include error conditions and recovery mechanisms.

## Running Tests

To run the test suite:

```bash
python run_tests.py
```

To run a specific test file:

```bash
pytest -xvs test_main.py
```

To run tests with specific markers:

```bash
pytest -xvs -m "not slow"  # Skip slow tests
pytest -xvs -m "asyncio"   # Run only asyncio tests
```

## Key Test Areas

### ForestApplication Initialization
Tests verify that the application initializes correctly, with all required components properly set up.

### Event Processing
Tests ensure events are properly emitted, dispatched to handlers, and processed in order.

### Task Management
Tests verify that tasks are properly registered, executed, and cleaned up, with proper handling of errors and cancellation.

### Error Handling
Tests confirm that errors are properly caught, logged, and handled at various levels of the application.

### Lifecycle Management
Tests ensure that the application starts up and shuts down cleanly, with proper resource management.

### Monitoring Systems
Tests verify that the monitoring components correctly track system health, memory usage, and circuit breaker status.

## Logging

Test logs are stored in the `test_logs` directory with timestamps for review. The log level can be adjusted in `conftest.py`.

## Dependencies

The test suite requires:

- pytest
- asyncio
- qasync
- PyQt6
- All dependencies of the main application

## Adding New Tests

When adding new tests:

1. Follow the existing pattern of test files and class organization.
2. Use the fixtures provided in `conftest.py` for common setup.
3. Use the `@pytest.mark.asyncio` decorator for tests involving async code.
4. Ensure proper cleanup of resources in each test.
5. Add appropriate documentation for new test cases.