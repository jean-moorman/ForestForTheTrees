"""
Foundation Refinement Agent for Phase One Critical Decision Making

This agent serves as the decision bottleneck for Phase One, analyzing Phase Zero
feedback and Air Agent historical context to determine if system recursion is needed.
"""
import asyncio
import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

from resources import (
    EventQueue, StateManager, AgentContextManager, CacheManager, 
    MetricsManager, ErrorHandler, MemoryMonitor, HealthTracker
)
from resources.monitoring import CircuitBreaker, CircuitOpenError
from resources.air_agent import provide_refinement_context
from interfaces import AgentInterface

from phase_one.agents.base import ReflectiveAgent
from phase_one.models.refinement import RefinementContext, AgentPromptConfig
from phase_one.monitoring.circuit_breakers import CircuitBreakerDefinition

logger = logging.getLogger(__name__)

class FoundationRefinementAgent(ReflectiveAgent):
    """
    Foundation Refinement Agent - Critical decision bottleneck for Phase One.
    
    Responsibilities:
    1. Analyze Phase Zero feedback for critical failures
    2. Integrate Air Agent historical context
    3. Determine root cause and responsible agent
    4. Make refinement decisions (recursion vs. proceed)
    5. Provide specific guidance for agent refinement
    """
    
    def __init__(
        self,
        event_queue: EventQueue,
        state_manager: StateManager,
        context_manager: AgentContextManager,
        cache_manager: CacheManager,
        metrics_manager: MetricsManager,
        error_handler: ErrorHandler,
        memory_monitor: MemoryMonitor = None,
        health_tracker: HealthTracker = None,
        max_refinement_cycles: int = 5
    ):
        """
        Initialize the Foundation Refinement Agent.
        
        Args:
            max_refinement_cycles: Maximum number of refinement cycles allowed
        """
        # Create prompt config for refinement agent
        prompt_config = AgentPromptConfig(
            system_prompt_base_path="FFTT_system_prompts.phase_one.garden_foundation_refinement_agent",
            initial_prompt_name="task_foundation_refinement_prompt",
            reflection_prompt_name="task_foundation_reflection_prompt",
            refinement_prompt_name="task_foundation_revision_prompt"
        )
        
        # Circuit breaker definitions removed - protection now at API level
        
        super().__init__(
            agent_id="foundation_refinement_agent",
            event_queue=event_queue,
            state_manager=state_manager,
            context_manager=context_manager,
            cache_manager=cache_manager,
            metrics_manager=metrics_manager,
            error_handler=error_handler,
            memory_monitor=memory_monitor,
            prompt_config=prompt_config,
            health_tracker=health_tracker
        )
        
        self._max_refinement_cycles = max_refinement_cycles
        self._current_cycle = 0
        
        # Initialize refinement state tracking
        self._refinement_history = []
        self._current_operation_id = None
        
    async def analyze_phase_one_outputs(
        self,
        phase_one_result: Dict[str, Any],
        phase_zero_feedback: Dict[str, Any],
        operation_id: str
    ) -> Dict[str, Any]:
        """
        Analyze Phase One outputs with Phase Zero feedback to determine refinement needs.
        
        Args:
            phase_one_result: Complete Phase One workflow result
            phase_zero_feedback: Phase Zero quality assurance feedback
            operation_id: Operation identifier for tracking
            
        Returns:
            Refinement analysis with decision and guidance
        """
        self._current_operation_id = operation_id
        
        try:
            logger.info(f"Starting foundation refinement analysis for operation {operation_id}")
            
            # Get Air Agent historical context
            air_context = await self._get_air_agent_context(operation_id)
            
            # Prepare analysis input
            analysis_input = await self._prepare_analysis_input(
                phase_one_result,
                phase_zero_feedback,
                air_context,
                operation_id
            )
            
            # Perform refinement analysis with circuit breaker protection
            refinement_result = await self._circuit_breakers["refinement_analysis"].execute(
                lambda: self._execute_refinement_analysis(analysis_input, operation_id)
            )
            
            # Additional safety check in case circuit breaker returns malformed result
            if not isinstance(refinement_result, dict) or "refinement_analysis" not in refinement_result:
                logger.warning(f"Circuit breaker returned malformed result for operation {operation_id}")
                refinement_result = {
                    "refinement_analysis": {
                        "critical_failure": {
                            "category": "none_detected",
                            "description": "Circuit breaker returned malformed result - proceeding to Phase Two",
                            "evidence": [],
                            "phase_zero_signals": []
                        },
                        "root_cause": {
                            "responsible_agent": "none",
                            "failure_point": "circuit_breaker_malformed_result",
                            "causal_chain": [],
                            "verification_steps": []
                        },
                        "refinement_action": {
                            "action": "proceed_to_phase_two",
                            "justification": "Circuit breaker returned malformed result, proceeding safely",
                            "specific_guidance": {
                                "current_state": "Circuit breaker malformed result",
                                "required_state": "Phase Two ready",
                                "adaptation_path": ["Proceed with current outputs"]
                            }
                        }
                    },
                    "confidence_assessment": "low",
                    "analysis_metadata": {
                        "malformed_result": True,
                        "circuit_breaker_issue": True
                    }
                }
            
            # Store analysis result
            await self._store_refinement_result(refinement_result, operation_id)
            
            # Update refinement history (handle potential malformed results)
            decision = "unknown"
            confidence = "low"
            if isinstance(refinement_result, dict):
                decision = refinement_result.get("refinement_analysis", {}).get("refinement_action", {}).get("action", "unknown")
                confidence = "high" if refinement_result.get("confidence_assessment") == "high" else "medium"
            
            self._refinement_history.append({
                "operation_id": operation_id,
                "cycle": self._current_cycle,
                "timestamp": datetime.now().isoformat(),
                "decision": decision,
                "confidence": confidence
            })
            
            logger.info(f"Foundation refinement analysis completed for operation {operation_id}")
            return refinement_result
            
        except CircuitOpenError:
            logger.error(f"Refinement analysis circuit open for operation {operation_id}")
            return await self._handle_circuit_open_error("refinement_analysis", operation_id)
            
        except Exception as e:
            logger.error(f"Foundation refinement analysis failed for operation {operation_id}: {e}")
            await self._error_handler.handle_error(
                self.interface_id,
                str(e),
                {"operation_id": operation_id, "phase": "refinement_analysis"}
            )
            raise
    
    async def _get_air_agent_context(self, operation_id: str) -> Dict[str, Any]:
        """Get historical context from Air Agent for refinement decisions."""
        try:
            # Get refinement context from Air Agent
            air_context = await provide_refinement_context(
                agent_id="foundation_refinement_agent",
                decision_type="phase_one_refinement",
                current_context={
                    "operation_id": operation_id,
                    "phase": "phase_one",
                    "refinement_cycle": self._current_cycle
                }
            )
            
            logger.info(f"Retrieved Air Agent context for operation {operation_id}")
            return air_context
            
        except Exception as e:
            logger.warning(f"Failed to get Air Agent context for operation {operation_id}: {e}")
            # Return minimal context if Air Agent fails
            return {
                "historical_patterns": [],
                "success_strategies": [],
                "failure_patterns": [],
                "recommendations": ["No historical context available due to Air Agent error"]
            }
    
    async def _prepare_analysis_input(
        self,
        phase_one_result: Dict[str, Any],
        phase_zero_feedback: Dict[str, Any],
        air_context: Dict[str, Any],
        operation_id: str
    ) -> str:
        """Prepare the analysis input for the refinement agent."""
        
        # Extract Phase One agent outputs
        agents_data = phase_one_result.get("agents", {})
        final_output = phase_one_result.get("final_output", {})
        
        # Extract Phase Zero analysis signals
        phase_zero_analysis = phase_zero_feedback.get("deep_analysis", {})
        evolution_synthesis = phase_zero_feedback.get("evolution_synthesis", {})
        
        # Build comprehensive analysis context
        analysis_context = {
            "operation_id": operation_id,
            "refinement_cycle": self._current_cycle,
            "phase_one_outputs": {
                "task_analysis": final_output.get("task_analysis", {}),
                "environmental_analysis": final_output.get("environmental_analysis", {}),
                "data_architecture": final_output.get("data_architecture", {}),
                "component_architecture": final_output.get("component_architecture", {}),
                "agent_success_status": {
                    agent: result.get("success", False) 
                    for agent, result in agents_data.items()
                }
            },
            "phase_zero_feedback": {
                "monitoring_analysis": phase_zero_feedback.get("monitoring_analysis", {}),
                "deep_analysis": phase_zero_analysis,
                "evolution_synthesis": evolution_synthesis,
                "critical_signals": self._extract_critical_signals(phase_zero_analysis)
            },
            "air_agent_context": air_context,
            "system_metrics": {
                "timestamp": datetime.now().isoformat(),
                "max_cycles_remaining": self._max_refinement_cycles - self._current_cycle
            }
        }
        
        # Format as structured prompt input
        return f"""
Please analyze the following Phase One outputs and Phase Zero feedback to determine if critical failures exist that require system refinement:

## Phase One Outputs Analysis
{json.dumps(analysis_context["phase_one_outputs"], indent=2)}

## Phase Zero Quality Assurance Feedback
{json.dumps(analysis_context["phase_zero_feedback"], indent=2)}

## Air Agent Historical Context
{json.dumps(analysis_context["air_agent_context"], indent=2)}

## System Context
- Operation ID: {operation_id}
- Current Refinement Cycle: {self._current_cycle}
- Max Cycles Remaining: {self._max_refinement_cycles - self._current_cycle}

Based on this comprehensive analysis, determine if any critical failures exist that would require specific Phase One agents to refine their outputs, or if the system should proceed to Phase Two.
"""
    
    def _extract_critical_signals(self, phase_zero_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract critical signals from Phase Zero deep analysis."""
        critical_signals = []
        
        # Check each Phase Zero agent for critical issues
        for agent_name, agent_analysis in phase_zero_analysis.items():
            if isinstance(agent_analysis, dict):
                # Look for error flags or critical issues
                if agent_analysis.get("error") or agent_analysis.get("status") == "failure":
                    critical_signals.append({
                        "agent": agent_name,
                        "signal_type": "error",
                        "description": agent_analysis.get("error", "Agent processing failure"),
                        "severity": "high"
                    })
                
                # Look for specific analysis flags (this would depend on Phase Zero agent output structure)
                if isinstance(agent_analysis, dict) and "flag_raised" in agent_analysis:
                    if agent_analysis.get("flag_raised"):
                        critical_signals.append({
                            "agent": agent_name,
                            "signal_type": agent_analysis.get("flag_type", "unknown"),
                            "description": agent_analysis.get("flag_description", "Critical issue detected"),
                            "severity": agent_analysis.get("severity", "medium")
                        })
        
        return critical_signals
    
    async def _execute_refinement_analysis(
        self, 
        analysis_input: str, 
        operation_id: str
    ) -> Dict[str, Any]:
        """Execute the core refinement analysis using the agent's LLM processing."""
        
        # Use the base ReflectiveAgent's process_with_validation method
        result = await self.process_with_validation(
            conversation=analysis_input,
            system_prompt_info=(
                "FFTT_system_prompts.phase_one.garden_foundation_refinement_agent",
                "task_foundation_refinement_prompt"
            )
        )
        
        # Validate the result structure
        if not isinstance(result, dict) or "refinement_analysis" not in result:
            logger.warning(f"Unexpected refinement analysis result format for operation {operation_id}")
            # Return a safe default indicating no critical failure
            return {
                "refinement_analysis": {
                    "critical_failure": {
                        "category": "none_detected",
                        "description": "No critical failures detected - proceeding to Phase Two",
                        "evidence": [],
                        "phase_zero_signals": []
                    },
                    "root_cause": {
                        "responsible_agent": "none",
                        "failure_point": "no_failure_detected",
                        "causal_chain": [],
                        "verification_steps": []
                    },
                    "refinement_action": {
                        "action": "proceed_to_phase_two",
                        "justification": "Analysis result was malformed, proceeding safely",
                        "specific_guidance": {
                            "current_state": "Phase One completed",
                            "required_state": "Phase Two ready",
                            "adaptation_path": ["Proceed with current outputs"]
                        }
                    }
                },
                "confidence_assessment": "low",
                "analysis_metadata": {
                    "malformed_result": True,
                    "original_result": str(result)[:500]  # Truncated for storage
                }
            }
        
        return result
    
    async def _store_refinement_result(
        self, 
        refinement_result: Dict[str, Any], 
        operation_id: str
    ) -> None:
        """Store the refinement analysis result."""
        await self._state_manager.set_state(
            f"phase_one:refinement_analysis:{operation_id}",
            {
                "result": refinement_result,
                "timestamp": datetime.now().isoformat(),
                "agent_id": self.interface_id,
                "cycle": self._current_cycle
            },
            "STATE"
        )
        
        # Also store in refinement history
        await self._state_manager.set_state(
            f"phase_one:refinement_history:{operation_id}",
            self._refinement_history,
            "STATE"
        )
    
    async def _handle_circuit_open_error(
        self, 
        circuit_name: str, 
        operation_id: str
    ) -> Dict[str, Any]:
        """Handle circuit breaker open errors by returning safe defaults."""
        logger.error(f"Circuit breaker {circuit_name} open for operation {operation_id}")
        
        # Return safe default - proceed to Phase Two rather than risk infinite loops
        return {
            "refinement_analysis": {
                "critical_failure": {
                    "category": "circuit_breaker_open",
                    "description": f"Refinement analysis circuit breaker open - proceeding to Phase Two",
                    "evidence": [
                        {
                            "source": "circuit_breaker",
                            "observation": f"Circuit {circuit_name} is open",
                            "impact": "Cannot perform refinement analysis"
                        }
                    ],
                    "phase_zero_signals": []
                },
                "root_cause": {
                    "responsible_agent": "none",
                    "failure_point": "circuit_breaker_protection",
                    "causal_chain": ["Circuit breaker opened due to repeated failures"],
                    "verification_steps": ["Check circuit breaker status", "Review failure logs"]
                },
                "refinement_action": {
                    "action": "proceed_to_phase_two",
                    "justification": "Circuit breaker protection activated - avoiding potential infinite loops",
                    "specific_guidance": {
                        "current_state": "Circuit breaker open",
                        "required_state": "Proceed with available outputs",
                        "adaptation_path": ["Use current Phase One outputs", "Monitor for issues in Phase Two"]
                    }
                }
            },
            "confidence_assessment": "low",
            "circuit_breaker_protection": True
        }
    
    def should_proceed_to_phase_two(self, refinement_result: Dict[str, Any]) -> bool:
        """
        Determine if the system should proceed to Phase Two based on refinement analysis.
        
        Args:
            refinement_result: Result from foundation refinement analysis
            
        Returns:
            True if should proceed to Phase Two, False if refinement is needed
        """
        if not refinement_result or "refinement_analysis" not in refinement_result:
            # If analysis failed, proceed safely to Phase Two
            return True
        
        refinement_action = refinement_result.get("refinement_analysis", {}).get("refinement_action", {})
        action = refinement_action.get("action", "proceed_to_phase_two")
        
        # Actions that require recursion
        recursion_actions = {
            "reanalyze_task",
            "revise_environment", 
            "restructure_data_flow",
            "reorganize_components"
        }
        
        # Check if we've exceeded max cycles
        if self._current_cycle >= self._max_refinement_cycles:
            logger.warning(f"Maximum refinement cycles ({self._max_refinement_cycles}) reached, proceeding to Phase Two")
            return True
        
        # Proceed to Phase Two if action is not a recursion action
        return action not in recursion_actions
    
    def get_refinement_target_agent(self, refinement_result: Dict[str, Any]) -> Optional[str]:
        """
        Get the target agent for refinement based on analysis result.
        
        Args:
            refinement_result: Result from foundation refinement analysis
            
        Returns:
            Target agent name for refinement, or None if no refinement needed
        """
        if not refinement_result or "refinement_analysis" not in refinement_result:
            return None
        
        root_cause = refinement_result.get("refinement_analysis", {}).get("root_cause", {})
        responsible_agent = root_cause.get("responsible_agent", "none")
        
        # Map responsible agent to actual agent names
        agent_mapping = {
            "garden_planner": "garden_planner",
            "environmental_analysis": "environmental_analysis", 
            "root_system_architect": "root_system_architect",
            "tree_placement_planner": "tree_placement_planner"
        }
        
        return agent_mapping.get(responsible_agent)
    
    def get_refinement_guidance(self, refinement_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract specific refinement guidance for the target agent.
        
        Args:
            refinement_result: Result from foundation refinement analysis
            
        Returns:
            Refinement guidance for the target agent
        """
        if not refinement_result or "refinement_analysis" not in refinement_result:
            return {}
        
        refinement_action = refinement_result.get("refinement_analysis", {}).get("refinement_action", {})
        
        return {
            "action": refinement_action.get("action"),
            "justification": refinement_action.get("justification"),
            "specific_guidance": refinement_action.get("specific_guidance", {}),
            "current_state": refinement_action.get("specific_guidance", {}).get("current_state"),
            "required_state": refinement_action.get("specific_guidance", {}).get("required_state"), 
            "adaptation_path": refinement_action.get("specific_guidance", {}).get("adaptation_path", [])
        }
    
    def increment_cycle(self) -> None:
        """Increment the current refinement cycle."""
        self._current_cycle += 1
        
    def reset_cycle(self) -> None:
        """Reset the refinement cycle counter."""
        self._current_cycle = 0