"""
Pytest configuration for the new validation test suite.

This configuration sets up test markers, fixtures, and quality gates
for the comprehensive validation testing framework.
"""

import asyncio
import pytest
import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging for tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Reduce noise from common async warnings and verbose modules
import warnings
warnings.filterwarnings("ignore", message=".*was never awaited.*")
warnings.filterwarnings("ignore", message=".*Task was destroyed.*")
warnings.filterwarnings("ignore", message=".*coroutine.*was never awaited.*")
warnings.filterwarnings("ignore", message=".*fixture.*loop.*scope.*")

# Set specific loggers to WARNING to reduce test noise
logging.getLogger("resources.monitoring.memory").setLevel(logging.WARNING)
logging.getLogger("resources.monitoring.circuit_breakers").setLevel(logging.WARNING)
logging.getLogger("interfaces.agent.metrics").setLevel(logging.WARNING)
logging.getLogger("phase_one.validation.coordination").setLevel(logging.WARNING)

def pytest_configure(config):
    """Configure pytest with custom markers and settings."""
    # Register custom markers
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end tests"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )
    config.addinivalue_line(
        "markers", "real_api: marks tests that require real API access"
    )

def pytest_collection_modifyitems(config, items):
    """Automatically add markers to tests based on their location."""
    for item in items:
        # Add markers based on test file location
        if "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
            item.add_marker(pytest.mark.slow)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "performance" in str(item.name.lower()):
            item.add_marker(pytest.mark.performance)
            item.add_marker(pytest.mark.slow)
        
        # Add real_api marker for tests that need API key
        if "real_api" in str(item.fspath) or "TestRealAPIIntegration" in str(item.cls):
            item.add_marker(pytest.mark.real_api)

def pytest_runtest_setup(item):
    """Set up individual test runs."""
    # Skip tests that require API key if not available
    if item.get_closest_marker("real_api"):
        if not os.getenv("ANTHROPIC_API_KEY"):
            pytest.skip("API key required for real API tests")

# Removed custom event_loop fixture to avoid pytest-asyncio conflicts
# pytest-asyncio will manage the event loop automatically

@pytest.fixture
def api_key_available():
    """Check if API key is available for testing."""
    return bool(os.getenv("ANTHROPIC_API_KEY"))

@pytest.fixture
async def clean_test_environment():
    """Provide a clean test environment for each test."""
    # This fixture can be used to ensure tests start with a clean state
    yield
    # Cleanup after test if needed

class TestQualityGates:
    """Quality gates for test execution."""
    
    @staticmethod
    def check_test_coverage(coverage_data):
        """Check that test coverage meets minimum requirements."""
        # Implementation would check coverage metrics
        pass
    
    @staticmethod 
    def check_test_performance(test_results):
        """Check that tests complete within acceptable time limits."""
        # Implementation would check test execution times
        pass
    
    @staticmethod
    def check_test_reliability(test_results):
        """Check that tests are reliable and not flaky."""
        # Implementation would check for test consistency
        pass

# Custom assertions for validation testing
def assert_valid_json_response(response):
    """Assert that a response is valid JSON with expected structure."""
    assert isinstance(response, dict), "Response must be a dictionary"
    assert "error" not in response or response.get("error") is None, f"Response contains error: {response.get('error')}"

def assert_validation_error_structure(error_response):
    """Assert that a validation error response has the expected structure."""
    assert "error" in error_response, "Error response must contain 'error' field"
    error = error_response["error"]
    assert "type" in error, "Error must have a 'type' field"
    assert "message" in error, "Error must have a 'message' field"

def assert_schema_compliance(data, schema):
    """Assert that data complies with the given schema."""
    import jsonschema
    try:
        jsonschema.validate(instance=data, schema=schema)
    except jsonschema.ValidationError as e:
        pytest.fail(f"Data does not comply with schema: {e.message}")

# Make custom assertions available globally
pytest.assert_valid_json_response = assert_valid_json_response
pytest.assert_validation_error_structure = assert_validation_error_structure
pytest.assert_schema_compliance = assert_schema_compliance