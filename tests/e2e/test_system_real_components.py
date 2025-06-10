#!/usr/bin/env python3
"""
End-to-End System Test - Real Components, No Mocks

This test uses actual system components to test the full prompt submission flow
exactly as it happens in production, helping identify real integration issues.
"""
import asyncio
import logging
import os
import sys
import time
import traceback
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging to capture real system behavior
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Suppress some verbose logging for cleaner output
logging.getLogger("resources.monitoring.circuit_breakers").setLevel(logging.WARNING)
logging.getLogger("resources.events.queue").setLevel(logging.WARNING)

class SystemE2ETest:
    """End-to-end test using real system components."""
    
    def __init__(self):
        self.phase_one_app = None
        self.test_results = {}
        
    async def setup_real_system(self):
        """Set up the actual Phase One system components."""
        logger.info("🔧 Setting up real Phase One system...")
        
        # Set up offscreen rendering to avoid GUI display issues
        os.environ['QT_QPA_PLATFORM'] = 'offscreen'
        
        try:
            # Import actual system components
            from PyQt6.QtWidgets import QApplication
            from run_phase_one import PhaseOneApp, PhaseOneInterface
            from resources.events.loop_management import EventLoopManager
            
            # Create QApplication (required for Qt components)
            self.app = QApplication.instance()
            if self.app is None:
                self.app = QApplication([])
            
            # Create the actual Phase One application
            self.phase_one_app = PhaseOneApp()
            
            # Setup async components (this initializes all real managers and agents)
            await self.phase_one_app.setup_async()
            
            # Get the real Phase One interface
            self.phase_one_interface = PhaseOneInterface(self.phase_one_app.phase_one)
            
            logger.info("✅ Real Phase One system initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to setup real system: {e}", exc_info=True)
            return False
    
    async def test_real_prompt_submission(self):
        """Test actual prompt submission through the real system."""
        logger.info("🎯 Testing real prompt submission...")
        
        test_prompts = [
            "Create a simple calculator application",
            "Build a to-do list manager",
            "Design a basic blog system"
        ]
        
        results = []
        
        for i, prompt in enumerate(test_prompts):
            logger.info(f"📝 Testing prompt {i+1}/{len(test_prompts)}: {prompt[:50]}...")
            
            try:
                # Time the execution
                start_time = time.time()
                
                # Call the REAL process_task method (not mocked)
                result = self.phase_one_interface.process_task(prompt)
                
                end_time = time.time()
                execution_time = end_time - start_time
                
                # Analyze the result
                success = self._analyze_result(result, prompt, execution_time)
                results.append({
                    "prompt": prompt,
                    "success": success,
                    "execution_time": execution_time,
                    "result": result
                })
                
                if success:
                    logger.info(f"✅ Prompt {i+1} succeeded in {execution_time:.2f}s")
                else:
                    logger.error(f"❌ Prompt {i+1} failed in {execution_time:.2f}s")
                    
            except Exception as e:
                logger.error(f"💥 Prompt {i+1} crashed: {e}", exc_info=True)
                results.append({
                    "prompt": prompt,
                    "success": False,
                    "execution_time": 0,
                    "error": str(e),
                    "traceback": traceback.format_exc()
                })
        
        return results
    
    def _analyze_result(self, result, prompt, execution_time):
        """Analyze if a result indicates successful processing."""
        try:
            if not isinstance(result, dict):
                logger.error(f"Result is not a dict: {type(result)}")
                return False
            
            status = result.get("status")
            if status != "success":
                logger.error(f"Result status is not success: {status}")
                return False
            
            phase_one_outputs = result.get("phase_one_outputs")
            if not isinstance(phase_one_outputs, dict):
                logger.error(f"phase_one_outputs is not a dict: {type(phase_one_outputs)}")
                return False
            
            # Check for expected agent outputs
            expected_agents = [
                "garden_planner", "earth_agent", "environmental_analysis", 
                "root_system_architect", "tree_placement_planner"
            ]
            
            found_agents = []
            for agent in expected_agents:
                if agent in phase_one_outputs:
                    found_agents.append(agent)
            
            if len(found_agents) == 0:
                logger.error(f"No expected agent outputs found in result")
                return False
            
            logger.info(f"Found outputs from {len(found_agents)}/{len(expected_agents)} agents: {found_agents}")
            return True
            
        except Exception as e:
            logger.error(f"Error analyzing result: {e}", exc_info=True)
            return False
    
    async def test_agent_metrics_real(self):
        """Test real agent metrics retrieval."""
        logger.info("📊 Testing real agent metrics...")
        
        agent_ids = [
            "garden_planner", "earth_agent", "environmental_analysis",
            "root_system_architect", "tree_placement_planner"
        ]
        
        metrics_results = []
        
        for agent_id in agent_ids:
            try:
                logger.info(f"Getting metrics for {agent_id}...")
                
                # Call the REAL get_agent_metrics method
                metrics = await self.phase_one_interface.get_agent_metrics(agent_id)
                
                # Analyze metrics
                success = self._analyze_metrics(metrics, agent_id)
                metrics_results.append({
                    "agent_id": agent_id,
                    "success": success,
                    "metrics": metrics
                })
                
                if success:
                    logger.info(f"✅ Metrics for {agent_id} retrieved successfully")
                else:
                    logger.error(f"❌ Metrics for {agent_id} failed validation")
                    
            except Exception as e:
                logger.error(f"💥 Metrics for {agent_id} crashed: {e}", exc_info=True)
                metrics_results.append({
                    "agent_id": agent_id,
                    "success": False,
                    "error": str(e)
                })
        
        return metrics_results
    
    def _analyze_metrics(self, metrics, agent_id):
        """Analyze if metrics are valid."""
        try:
            if not isinstance(metrics, dict):
                logger.error(f"Metrics for {agent_id} not a dict: {type(metrics)}")
                return False
            
            if "status" in metrics and metrics["status"] == "error":
                logger.error(f"Metrics for {agent_id} returned error status")
                return False
            
            # Metrics might be empty for agents that haven't run yet
            logger.info(f"Metrics for {agent_id}: {len(metrics)} fields")
            return True
            
        except Exception as e:
            logger.error(f"Error analyzing metrics for {agent_id}: {e}")
            return False
    
    async def test_event_loop_health(self):
        """Test event loop health and context."""
        logger.info("🔄 Testing event loop health...")
        
        try:
            # Import event loop utilities
            from resources.events.loop_management import EventLoopManager
            
            # Check primary loop
            primary_loop = EventLoopManager.get_primary_loop()
            if primary_loop:
                logger.info(f"✅ Primary loop found: {id(primary_loop)}")
                logger.info(f"Primary loop running: {primary_loop.is_running()}")
                logger.info(f"Primary loop closed: {primary_loop.is_closed()}")
            else:
                logger.warning("⚠️ No primary loop found")
            
            # Check current loop
            try:
                current_loop = asyncio.get_running_loop()
                logger.info(f"✅ Current loop: {id(current_loop)}")
            except RuntimeError:
                logger.warning("⚠️ No running loop in current context")
            
            # Check stats
            stats = EventLoopManager.get_stats()
            logger.info(f"📈 EventLoopManager stats: {stats}")
            
            return True
            
        except Exception as e:
            logger.error(f"Event loop health check failed: {e}", exc_info=True)
            return False
    
    async def test_system_components_health(self):
        """Test health of real system components."""
        logger.info("🏥 Testing system components health...")
        
        try:
            # Test event queue
            if hasattr(self.phase_one_app, 'event_queue'):
                queue_stats = self.phase_one_app.event_queue.get_stats()
                logger.info(f"📊 Event queue stats: {queue_stats}")
            
            # Test system monitor
            if hasattr(self.phase_one_app, 'system_monitor'):
                # Try to get system health
                try:
                    health_status = await self.phase_one_app.system_monitor.get_system_health()
                    logger.info(f"💚 System health: {health_status}")
                except Exception as e:
                    logger.warning(f"Could not get system health: {e}")
            
            # Test circuit breakers
            if hasattr(self.phase_one_app, 'circuit_registry'):
                circuit_stats = self.phase_one_app.circuit_registry.get_stats()
                logger.info(f"⚡ Circuit breaker stats: {circuit_stats}")
            
            return True
            
        except Exception as e:
            logger.error(f"System components health check failed: {e}", exc_info=True)
            return False
    
    async def cleanup_real_system(self):
        """Clean up the real system components."""
        logger.info("🧹 Cleaning up real system...")
        
        try:
            if self.phase_one_app:
                # Use the app's cleanup method
                self.phase_one_app.close()
            
            # Quit Qt application
            if hasattr(self, 'app'):
                self.app.quit()
            
            logger.info("✅ System cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}", exc_info=True)
    
    async def run_full_e2e_test(self):
        """Run the complete end-to-end test suite."""
        logger.info("🚀 Starting End-to-End System Test with Real Components")
        logger.info("=" * 60)
        
        overall_success = True
        
        try:
            # Setup
            setup_success = await self.setup_real_system()
            if not setup_success:
                logger.error("💥 System setup failed, aborting test")
                return False
            
            # Test 1: Event loop health
            logger.info("\n" + "=" * 60)
            loop_health = await self.test_event_loop_health()
            overall_success &= loop_health
            
            # Test 2: System components health
            logger.info("\n" + "=" * 60)
            components_health = await self.test_system_components_health()
            overall_success &= components_health
            
            # Test 3: Real prompt submission
            logger.info("\n" + "=" * 60)
            prompt_results = await self.test_real_prompt_submission()
            prompt_success = all(r["success"] for r in prompt_results)
            overall_success &= prompt_success
            
            # Test 4: Agent metrics
            logger.info("\n" + "=" * 60)
            metrics_results = await self.test_agent_metrics_real()
            metrics_success = all(r["success"] for r in metrics_results)
            overall_success &= metrics_success
            
            # Final report
            logger.info("\n" + "=" * 60)
            logger.info("📋 FINAL TEST REPORT")
            logger.info("=" * 60)
            logger.info(f"Setup: {'✅ PASS' if setup_success else '❌ FAIL'}")
            logger.info(f"Event Loop Health: {'✅ PASS' if loop_health else '❌ FAIL'}")
            logger.info(f"Components Health: {'✅ PASS' if components_health else '❌ FAIL'}")
            logger.info(f"Prompt Submission: {'✅ PASS' if prompt_success else '❌ FAIL'}")
            logger.info(f"Agent Metrics: {'✅ PASS' if metrics_success else '❌ FAIL'}")
            logger.info(f"Overall: {'🎉 PASS' if overall_success else '💥 FAIL'}")
            
            # Detailed results
            if not prompt_success:
                logger.info("\n📝 Prompt Submission Details:")
                for result in prompt_results:
                    status = "✅" if result["success"] else "❌"
                    logger.info(f"  {status} {result['prompt'][:40]}...")
                    if not result["success"] and "error" in result:
                        logger.info(f"      Error: {result['error']}")
            
            if not metrics_success:
                logger.info("\n📊 Agent Metrics Details:")
                for result in metrics_results:
                    status = "✅" if result["success"] else "❌"
                    logger.info(f"  {status} {result['agent_id']}")
                    if not result["success"] and "error" in result:
                        logger.info(f"      Error: {result['error']}")
            
            return overall_success
            
        except Exception as e:
            logger.error(f"💥 E2E test crashed: {e}", exc_info=True)
            return False
            
        finally:
            # Always cleanup
            await self.cleanup_real_system()


async def main():
    """Run the end-to-end test."""
    test = SystemE2ETest()
    
    try:
        success = await test.run_full_e2e_test()
        
        if success:
            logger.info("🎉 All tests passed! System is functioning correctly.")
            sys.exit(0)
        else:
            logger.error("💥 Some tests failed. System has issues.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("🛑 Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Test runner crashed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    # Run the test
    asyncio.run(main())