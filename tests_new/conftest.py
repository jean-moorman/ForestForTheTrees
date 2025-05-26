"""
Global pytest configuration for FFTT test suite.
Provides shared fixtures and common setup for all tests.
"""

import pytest
import asyncio
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import test fixtures from the organized test structure
try:
    from tests_new.fixtures.conftest import *
except ImportError:
    pass

try:
    from tests_new.unit.managers.conftest import *
except ImportError:
    pass

try:
    from tests_new.agents.conftest import *
except ImportError:
    pass

@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def temp_dir(tmp_path):
    """Provide a temporary directory for test files."""
    return tmp_path

@pytest.fixture
def mock_agent_config():
    """Provide a mock agent configuration for testing."""
    return {
        "agent_id": "test_agent",
        "timeout": 30,
        "max_retries": 3,
        "enable_logging": True,
        "log_level": "INFO"
    }

@pytest.fixture
def mock_resource_config():
    """Provide a mock resource configuration for testing."""
    return {
        "memory_limit": 1024,
        "cpu_limit": 2,
        "timeout": 60,
        "enable_monitoring": True
    }

# Configure pytest-asyncio for automatic async test detection
pytest_plugins = ["pytest_asyncio"]