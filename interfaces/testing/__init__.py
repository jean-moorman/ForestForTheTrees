"""
Testing infrastructure for the FFTT system.
Provides test agents and runners for validating interface functionality.
"""

from .test_agent import TestAgent
from .runners import run_tests, test_agent_process

__all__ = [
    'TestAgent',
    'run_tests',
    'test_agent_process'
]