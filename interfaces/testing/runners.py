"""
Test runner functions for the FFTT system.
"""

import asyncio
import json
import logging
import sys
from typing import Dict, List, Any, Optional

from .test_agent import TestAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_agent_process() -> None:
    """
    Test the AgentInterface process_with_validation functionality.
    """
    logger.info("Initializing test agent")
    print("Initializing test agent")
    test_agent = None
    
    try:
        # Initialize test agent with proper resource managers
        test_agent = TestAgent()
        
        # Ensure the agent is initialized - with a timeout
        try:
            init_success = await asyncio.wait_for(test_agent.initialize(), timeout=5.0)
            if not init_success:
                logger.error("Failed to initialize test agent")
                return
        except asyncio.TimeoutError:
            logger.error("Timeout waiting for agent initialization")
            return
        
        # Define test schema
        test_schema = {
            "type": "object",
            "properties": {
                "message": {"type": "string"},
                "status": {"type": "string"},
                "data": {
                    "type": "object",
                    "properties": {
                        "conversation": {"type": "string"},
                        "phase": {"type": "string"}
                    },
                    "required": ["conversation", "phase"]
                }
            },
            "required": ["message", "status", "data"]
        }
        
        logger.info("Starting process_with_validation test...")
        
        # Test basic processing with proper system_prompt_info
        logger.info("Test 1: Basic Processing")
        result = await test_agent.process_with_validation(
            conversation="Test conversation",
            system_prompt_info=("test_dir", "test_prompt"),  # Add required parameter
            schema=test_schema,
            operation_id="test_op_1"
        )
        logger.info(f"Result: {json.dumps(result, indent=2)}")
        
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}", exc_info=True)
        raise
    finally:
        if test_agent:
            try:
                # Use proper cleanup
                await test_agent.cleanup()
                # Explicitly cancel any remaining tasks
                tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
                for task in tasks:
                    task.cancel()
                logger.info("Test agent cleaned up successfully")
            except Exception as e:
                logger.error(f"Error cleaning up test agent: {str(e)}", exc_info=True)


def run_tests() -> None:
    """
    Run all interface tests.
    """
    logger.info("Running interface tests")
    
    # Set up logging with more detailed format
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the agent process test
    asyncio.run(test_agent_process())


if __name__ == "__main__":
    run_tests()