import logging
import time
import asyncio
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime
from dataclasses import dataclass, field

from phase_two.agents.agent_base import PhaseTwoAgentBase
from resources import (
    EventQueue, 
    StateManager, 
    AgentContextManager, 
    CacheManager, 
    MetricsManager, 
    ErrorHandler,
    MemoryMonitor,
    SystemMonitor,
    ResourceEventTypes
)

from phase_two.testing.system.executor import SystemTestExecutor
from phase_two.testing.system.analysis import SystemTestAnalysisAgent
from phase_two.testing.system.review import SystemTestReviewAgent
from phase_two.testing.system.debug import SystemTestDebugAgent
from phase_two.testing.system.validation import SystemValidationManager

logger = logging.getLogger(__name__)

@dataclass
class SystemTestingResult:
    """Container for complete system testing process results."""
    execution_id: str
    analysis_id: str
    review_id: str
    debug_id: str
    validation_id: str
    status: str
    component_count: int
    test_count: int
    execution_results: Dict[str, Any] = field(default_factory=dict)
    analysis_results: Dict[str, Any] = field(default_factory=dict)
    review_results: Dict[str, Any] = field(default_factory=dict)
    debug_results: Dict[str, Any] = field(default_factory=dict)
    validation_results: Dict[str, Any] = field(default_factory=dict)
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "execution_id": self.execution_id,
            "analysis_id": self.analysis_id,
            "review_id": self.review_id,
            "debug_id": self.debug_id,
            "validation_id": self.validation_id,
            "status": self.status,
            "component_count": self.component_count,
            "test_count": self.test_count,
            "execution_results": self.execution_results,
            "analysis_results": self.analysis_results,
            "review_results": self.review_results,
            "debug_results": self.debug_results,
            "validation_results": self.validation_results,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "total_duration": (self.end_time - self.start_time) if self.end_time else None
        }


class SystemTestingOrchestrator(PhaseTwoAgentBase):
    """
    Orchestrates the complete system testing workflow.
    
    Responsibilities:
    - Coordinates system test execution, analysis, review, debugging, and validation
    - Manages the flow of information between testing agents
    - Provides a unified interface for the system testing process
    - Tracks and reports on system testing progress
    """
    
    def __init__(self,
                 event_queue: EventQueue,
                 state_manager: StateManager,
                 context_manager: AgentContextManager,
                 cache_manager: CacheManager,
                 metrics_manager: MetricsManager,
                 error_handler: ErrorHandler,
                 memory_monitor: Optional[MemoryMonitor] = None,
                 system_monitor: Optional[SystemMonitor] = None):
        """Initialize the system testing orchestrator."""
        super().__init__(
            "system_testing_orchestrator",
            event_queue,
            state_manager,
            context_manager,
            cache_manager,
            metrics_manager,
            error_handler,
            memory_monitor
        )
        
        # Initialize specialized testing agents
        self._executor = SystemTestExecutor(
            event_queue, state_manager, context_manager, cache_manager, 
            metrics_manager, error_handler, memory_monitor
        )
        
        self._analyzer = SystemTestAnalysisAgent(
            event_queue, state_manager, context_manager, cache_manager, 
            metrics_manager, error_handler, memory_monitor
        )
        
        self._reviewer = SystemTestReviewAgent(
            event_queue, state_manager, context_manager, cache_manager, 
            metrics_manager, error_handler, memory_monitor
        )
        
        self._debugger = SystemTestDebugAgent(
            event_queue, state_manager, context_manager, cache_manager, 
            metrics_manager, error_handler, memory_monitor
        )
        
        self._validator = SystemValidationManager(
            event_queue, state_manager, context_manager, cache_manager, 
            metrics_manager, error_handler, memory_monitor
        )
        
        # Keep track of system testing sessions
        self._testing_sessions: Dict[str, SystemTestingResult] = {}
        
        # Register with system monitor if available
        self._system_monitor = system_monitor
        if self._system_monitor:
            asyncio.create_task(
                self._system_monitor.register_component("system_testing_orchestrator", {
                    "type": "orchestrator",
                    "description": "Orchestrates system testing workflow",
                })
            )
    
    async def execute_system_testing(self, 
                                   components: List[Dict[str, Any]],
                                   system_tests: List[Dict[str, Any]],
                                   system_requirements: Dict[str, Any],
                                   session_id: str,
                                   execution_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute the complete system testing workflow.
        
        Args:
            components: List of components to test
            system_tests: List of system tests to execute
            system_requirements: System requirements for validation
            session_id: Unique identifier for this testing session
            execution_config: Optional configuration for test execution
            
        Returns:
            Dictionary containing the results of the system testing process
        """
        logger.info(f"Starting system testing workflow for session {session_id} with {len(components)} components and {len(system_tests)} tests")
        
        # Record workflow start
        start_time = time.time()
        await self._metrics_manager.record_metric(
            "system_testing:start",
            1.0,
            metadata={
                "session_id": session_id,
                "component_count": len(components),
                "test_count": len(system_tests)
            }
        )
        
        # Emit event for workflow start
        await self._event_queue.emit(
            ResourceEventTypes.SYSTEM_TESTING_STARTED.value,
            {
                "session_id": session_id,
                "component_count": len(components),
                "test_count": len(system_tests),
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # Create unique IDs for each phase
        execution_id = f"exec_{session_id}"
        analysis_id = f"analysis_{session_id}"
        review_id = f"review_{session_id}"
        debug_id = f"debug_{session_id}"
        validation_id = f"validation_{session_id}"
        
        # Initialize testing session
        testing_session = SystemTestingResult(
            execution_id=execution_id,
            analysis_id=analysis_id,
            review_id=review_id,
            debug_id=debug_id,
            validation_id=validation_id,
            status="running",
            component_count=len(components),
            test_count=len(system_tests),
            start_time=start_time
        )
        
        self._testing_sessions[session_id] = testing_session
        
        try:
            # Step 1: Execute system tests
            logger.info(f"[{session_id}] Step 1/5: Executing system tests")
            execution_result = await self._executor.execute_system_tests(
                components=components,
                system_tests=system_tests,
                system_requirements=system_requirements,
                execution_id=execution_id
            )
            
            testing_session.execution_results = execution_result
            await self._emit_phase_complete_event("SYSTEM_TEST_EXECUTION_COMPLETED", session_id, "execution")
            
            # Check if the tests failed and analysis is needed
            failed_tests = execution_result.get("failed_tests", 0)
            if failed_tests > 0:
                # Step 2: Analyze test failures
                logger.info(f"[{session_id}] Step 2/5: Analyzing {failed_tests} test failures")
                analysis_result = await self._analyzer.analyze_test_failures(
                    test_results=execution_result,
                    components=components,
                    analysis_id=analysis_id
                )
                
                testing_session.analysis_results = analysis_result
                await self._emit_phase_complete_event("SYSTEM_TEST_ANALYSIS_COMPLETED", session_id, "analysis")
                
                # Step 3: Review analysis and generate recommendations
                logger.info(f"[{session_id}] Step 3/5: Reviewing analysis results")
                review_result = await self._reviewer.review_analysis(
                    analysis_report=analysis_result,
                    system_requirements=system_requirements,
                    review_id=review_id
                )
                
                testing_session.review_results = review_result
                await self._emit_phase_complete_event("SYSTEM_TEST_REVIEW_COMPLETED", session_id, "review")
                
                # Step 4: Debug and fix issues
                logger.info(f"[{session_id}] Step 4/5: Debugging and fixing issues")
                debug_result = await self._debugger.implement_fixes(
                    review_report=review_result,
                    components=components,
                    debug_id=debug_id
                )
                
                testing_session.debug_results = debug_result
                await self._emit_phase_complete_event("SYSTEM_TEST_DEBUG_COMPLETED", session_id, "debug")
            else:
                logger.info(f"[{session_id}] All tests passed, skipping analysis, review, and debug phases")
                # Add placeholder results for skipped phases
                testing_session.analysis_results = {
                    "status": "skipped",
                    "message": "All tests passed, analysis not needed"
                }
                testing_session.review_results = {
                    "status": "skipped",
                    "message": "All tests passed, review not needed"
                }
                testing_session.debug_results = {
                    "status": "skipped",
                    "message": "All tests passed, debugging not needed"
                }
            
            # Step 5: Validate system against requirements
            logger.info(f"[{session_id}] Step 5/5: Validating system against requirements")
            validation_result = await self._validator.validate_system(
                system_requirements=system_requirements,
                test_execution_result=execution_result,
                components=components,
                validation_id=validation_id
            )
            
            testing_session.validation_results = validation_result
            await self._emit_phase_complete_event("SYSTEM_VALIDATION_COMPLETED", session_id, "validation")
            
            # Update session status and end time
            testing_session.status = "completed"
            testing_session.end_time = time.time()
            
            # Create final result
            final_result = testing_session.to_dict()
            
            # Store session result
            await self._state_manager.set_state(
                f"system_testing:{session_id}",
                {
                    "session_id": session_id,
                    "status": "completed",
                    "component_count": len(components),
                    "test_count": len(system_tests),
                    "execution_id": execution_id,
                    "validation_id": validation_id,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            # Record workflow completion
            await self._metrics_manager.record_metric(
                "system_testing:complete",
                1.0,
                metadata={
                    "session_id": session_id,
                    "status": "completed",
                    "execution_time": time.time() - start_time,
                    "component_count": len(components),
                    "test_count": len(system_tests),
                    "passed_tests": execution_result.get("passed_tests", 0),
                    "failed_tests": execution_result.get("failed_tests", 0)
                }
            )
            
            # Emit event for workflow completion
            await self._event_queue.emit(
                ResourceEventTypes.SYSTEM_TESTING_COMPLETED.value,
                {
                    "session_id": session_id,
                    "status": "completed",
                    "component_count": len(components),
                    "test_count": len(system_tests),
                    "execution_time": time.time() - start_time,
                    "components": components,  # Include components for monitoring
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            logger.info(f"Completed system testing workflow for session {session_id} in {time.time() - start_time:.2f} seconds")
            return final_result
            
        except Exception as e:
            # Handle workflow errors
            logger.error(f"Error in system testing workflow for session {session_id}: {str(e)}", exc_info=True)
            
            # Update session status
            testing_session.status = "error"
            testing_session.end_time = time.time()
            
            # Record error
            await self._metrics_manager.record_metric(
                "system_testing:error",
                1.0,
                metadata={
                    "session_id": session_id,
                    "error": str(e),
                    "execution_time": time.time() - start_time
                }
            )
            
            # Emit error event
            await self._event_queue.emit(
                ResourceEventTypes.SYSTEM_TESTING_ERROR.value,
                {
                    "session_id": session_id,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            return {
                "status": "error",
                "session_id": session_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _emit_phase_complete_event(self, event_type: str, session_id: str, phase: str):
        """Emit an event for phase completion."""
        await self._event_queue.emit(
            getattr(ResourceEventTypes, event_type).value,
            {
                "session_id": session_id,
                "phase": phase,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    async def get_testing_session(self, session_id: str) -> Dict[str, Any]:
        """Get the status and results of a testing session."""
        # Check in-memory cache first
        if session_id in self._testing_sessions:
            return self._testing_sessions[session_id].to_dict()
        
        # Try to retrieve from state manager
        state = await self._state_manager.get_state(f"system_testing:{session_id}")
        if state:
            return state
        
        # Not found
        return {
            "status": "not_found",
            "message": f"No testing session found with ID {session_id}"
        }
    
    async def get_phase_result(self, session_id: str, phase: str) -> Dict[str, Any]:
        """Get the results of a specific phase in a testing session."""
        testing_session = self._testing_sessions.get(session_id)
        
        if not testing_session:
            # Try to retrieve from state manager
            state = await self._state_manager.get_state(f"system_testing:{session_id}")
            if not state:
                return {
                    "status": "not_found",
                    "message": f"No testing session found with ID {session_id}"
                }
            
            # Get the phase-specific ID from state
            phase_id = state.get(f"{phase}_id")
            if not phase_id:
                return {
                    "status": "not_found",
                    "message": f"No {phase} phase ID found for session {session_id}"
                }
            
            # Get the phase-specific result
            if phase == "execution":
                return await self._executor.get_execution_result(phase_id)
            elif phase == "analysis":
                # Try to get from cache
                cached_result = await self._cache_manager.get(f"system_test_analysis:{phase_id}")
                if cached_result:
                    return cached_result
                return {
                    "status": "not_found",
                    "message": f"Analysis result not found for ID {phase_id}"
                }
            elif phase == "review":
                # Try to get from cache
                cached_result = await self._cache_manager.get(f"system_test_review:{phase_id}")
                if cached_result:
                    return cached_result
                return {
                    "status": "not_found",
                    "message": f"Review result not found for ID {phase_id}"
                }
            elif phase == "debug":
                # Try to get from cache
                cached_result = await self._cache_manager.get(f"system_test_debug:{phase_id}")
                if cached_result:
                    return cached_result
                return {
                    "status": "not_found",
                    "message": f"Debug result not found for ID {phase_id}"
                }
            elif phase == "validation":
                return await self._validator.get_validation_result(phase_id)
            else:
                return {
                    "status": "error",
                    "message": f"Unknown phase: {phase}"
                }
        
        # Get phase-specific results from in-memory session
        if phase == "execution":
            return testing_session.execution_results
        elif phase == "analysis":
            return testing_session.analysis_results
        elif phase == "review":
            return testing_session.review_results
        elif phase == "debug":
            return testing_session.debug_results
        elif phase == "validation":
            return testing_session.validation_results
        else:
            return {
                "status": "error",
                "message": f"Unknown phase: {phase}"
            }
    
    async def generate_comprehensive_report(self, session_id: str) -> Dict[str, Any]:
        """Generate a comprehensive report for the testing session."""
        # Get testing session
        testing_session = await self.get_testing_session(session_id)
        
        if testing_session.get("status") == "not_found":
            return testing_session
        
        # Get detailed validation report
        validation_id = testing_session.get("validation_id")
        validation_report = await self._validator.generate_validation_report(validation_id)
        
        # Generate executive summary
        summary = self._generate_executive_summary(testing_session, validation_report)
        
        # Generate report
        report = {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "title": "Comprehensive System Testing Report",
            "executive_summary": summary,
            "validation_status": validation_report.get("summary", {}).get("validation_status", "Unknown"),
            "test_results": {
                "total_tests": testing_session.get("test_count", 0),
                "passed_tests": testing_session.get("execution_results", {}).get("passed_tests", 0),
                "failed_tests": testing_session.get("execution_results", {}).get("failed_tests", 0)
            },
            "issue_summary": self._generate_issue_summary(testing_session),
            "action_plan": validation_report.get("action_plan", {}),
            "detailed_results": {
                "execution": testing_session.get("execution_results", {}),
                "validation": validation_report
            }
        }
        
        # Include analysis, review, and debug if they were performed
        if testing_session.get("analysis_results", {}).get("status") != "skipped":
            report["detailed_results"]["analysis"] = testing_session.get("analysis_results", {})
            report["detailed_results"]["review"] = testing_session.get("review_results", {})
            report["detailed_results"]["debug"] = testing_session.get("debug_results", {})
        
        return report
    
    def _generate_executive_summary(self, 
                                  testing_session: Dict[str, Any], 
                                  validation_report: Dict[str, Any]) -> Dict[str, Any]:
        """Generate an executive summary of the testing results."""
        execution_results = testing_session.get("execution_results", {})
        
        total_tests = execution_results.get("total_tests", 0)
        passed_tests = execution_results.get("passed_tests", 0)
        failed_tests = execution_results.get("failed_tests", 0)
        
        validation_summary = validation_report.get("summary", {})
        validation_status = validation_summary.get("validation_status", "Unknown")
        validation_coverage = validation_summary.get("validation_coverage", 0)
        
        # Determine overall status
        if failed_tests == 0 and validation_status in ["Fully Validated", "Substantially Validated"]:
            overall_status = "Excellent"
        elif failed_tests == 0 and validation_status == "Partially Validated":
            overall_status = "Good"
        elif failed_tests > 0 and validation_status in ["Substantially Validated", "Partially Validated"]:
            overall_status = "Fair"
        else:
            overall_status = "Needs Improvement"
        
        return {
            "overall_status": overall_status,
            "test_summary": f"{passed_tests}/{total_tests} tests passed ({(passed_tests/total_tests*100) if total_tests > 0 else 0:.1f}%)",
            "validation_summary": f"{validation_status} ({validation_coverage:.1f}% coverage)",
            "component_count": testing_session.get("component_count", 0),
            "execution_time": testing_session.get("total_duration"),
            "completed_at": datetime.fromtimestamp(testing_session.get("end_time", time.time())).isoformat()
        }
    
    def _generate_issue_summary(self, testing_session: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary of issues found during testing."""
        # Extract issues from different phases
        test_failures = testing_session.get("execution_results", {}).get("failed_tests", 0)
        
        # If no test failures, return empty summary
        if test_failures == 0:
            return {
                "total_issues": 0,
                "message": "No issues found during testing"
            }
        
        # Extract patterns from analysis
        patterns = testing_session.get("analysis_results", {}).get("patterns", [])
        high_priority_patterns = [p for p in patterns if p.get("priority") == "high"]
        
        # Extract recommendations from review
        recommendations = testing_session.get("review_results", {}).get("recommendations", [])
        high_priority_recommendations = [r for r in recommendations if r.get("priority") == "high"]
        
        # Get fixes from debug
        fixes = testing_session.get("debug_results", {}).get("fixes", [])
        verified_fixes = [f for f in fixes if f.get("verified", False)]
        
        return {
            "total_issues": test_failures,
            "identified_patterns": len(patterns),
            "high_priority_patterns": len(high_priority_patterns),
            "recommendations": len(recommendations),
            "high_priority_recommendations": len(high_priority_recommendations),
            "implemented_fixes": len(fixes),
            "verified_fixes": len(verified_fixes),
            "resolution_percentage": (len(verified_fixes) / test_failures * 100) if test_failures > 0 else 0
        }