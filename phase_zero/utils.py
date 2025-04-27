import json
import asyncio
from typing import Dict, Any, Callable, Coroutine
from datetime import datetime
import logging

from resources import ResourceEventTypes, ResourceType, HealthStatus

logger = logging.getLogger(__name__)

async def with_timeout(coro: Coroutine, 
                       timeout_seconds: float, 
                       operation_name: str,
                       event_queue=None,
                       health_tracker=None,
                       metrics_manager=None):
    """Execute a coroutine with a timeout and monitoring."""
    try:
        # Update health status for operation start
        if health_tracker:
            await health_tracker.update_health(
                f"operation_{operation_name}",
                HealthStatus(
                    status="HEALTHY",
                    source="phase_zero_orchestrator",
                    description=f"Starting operation {operation_name}",
                    metadata={"timeout": timeout_seconds}
                )
            )
        
        # Start timer
        start_time = datetime.now()
        
        # Execute with timeout
        result = await asyncio.wait_for(coro, timeout=timeout_seconds)
        
        # Calculate execution time
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Record execution time metric
        if metrics_manager:
            await metrics_manager.record_metric(
                f"operation:{operation_name}:execution_time",
                execution_time,
                metadata={"success": True}
            )
        
        # Update health status for operation completion
        if health_tracker:
            await health_tracker.update_health(
                f"operation_{operation_name}",
                HealthStatus(
                    status="HEALTHY",
                    source="phase_zero_orchestrator",
                    description=f"Operation {operation_name} completed",
                    metadata={"execution_time": execution_time}
                )
            )
        
        return result
        
    except asyncio.TimeoutError:
        logger.error(f"Operation {operation_name} timed out after {timeout_seconds}s")
        
        # Record timeout metric
        if metrics_manager:
            await metrics_manager.record_metric(
                "operation_timeouts",
                1.0,
                metadata={"operation": operation_name}
            )
        
        # Update health status for operation timeout
        if health_tracker:
            await health_tracker.update_health(
                f"operation_{operation_name}",
                HealthStatus(
                    status="CRITICAL",
                    source="phase_zero_orchestrator",
                    description=f"Operation {operation_name} timed out after {timeout_seconds}s",
                    metadata={"timeout": timeout_seconds}
                )
            )
        
        # Emit timeout event
        if event_queue:
            await event_queue.emit(
                ResourceEventTypes.TIMEOUT_OCCURRED.value,
                {
                    "operation": operation_name,
                    "timeout": timeout_seconds,
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        raise


async def get_phase_one_outputs(cache_manager, state_manager) -> Dict[str, Dict]:
    """Get phase one outputs with caching."""
    cache_key = "phase_one_outputs"
    
    # Try cache first
    cached = await cache_manager.get_cache(cache_key)
    if cached:
        return cached
        
    # Get from state manager
    outputs = {}
    for output_type in ["garden_planner", "environmental_analysis", "root_system", "tree_placement"]:
        state = await state_manager.get_state(f"{output_type}_output")
        if not state:
            raise ValueError(f"Required Phase 1 output missing: {output_type}")
        outputs[f"{output_type}_output"] = state
        
    # Cache results
    await cache_manager.set_cache(
        cache_key,
        outputs,
        metadata={"timestamp": datetime.now().isoformat()}
    )
    
    return outputs
    

async def get_system_state(state_manager) -> Dict[str, Any]:
    """Get current system state."""
    return {
        "phase_zero": await state_manager.get_state("phase_zero:orchestrator"),
        "system_monitor": await state_manager.get_state("system_monitor:state"),
        "timestamp": datetime.now().isoformat()
    }


async def execute_agent_with_monitoring(agent, args, timeout=60, 
                                       health_tracker=None, 
                                       metrics_manager=None,
                                       event_queue=None,
                                       state_manager=None,
                                       revision_attempts=None):
    """Execute an agent with monitoring and timeout protection."""
    agent_id = agent.interface_id
    execution_start_time = datetime.now()
    
    # Initialize revision tracking for this agent if not already present
    if revision_attempts is not None and agent_id not in revision_attempts:
        revision_attempts[agent_id] = 0
    
    # Update health status for agent execution
    if health_tracker:
        await health_tracker.update_health(
            f"execution_{agent_id}",
            HealthStatus(
                status="HEALTHY",
                source="phase_zero_orchestrator",
                description=f"Starting execution of agent {agent_id}"
            )
        )
    
    try:
        # Execute with timeout - ensure args are passed correctly
        if hasattr(agent, 'process') and callable(agent.process):
            # If agent has a public process method
            result = await with_timeout(
                agent.process(*args) if isinstance(args, tuple) else agent.process(args),
                timeout,  # seconds timeout
                f"agent_execution_{agent_id}",
                event_queue=event_queue,
                health_tracker=health_tracker,
                metrics_manager=metrics_manager
            )
        else:
            # Fall back to _process
            result = await with_timeout(
                agent._process(*args) if isinstance(args, tuple) else agent._process(args),
                timeout,
                f"agent_execution_{agent_id}",
                event_queue=event_queue,
                health_tracker=health_tracker,
                metrics_manager=metrics_manager
            )
        
        # Record successful execution time
        execution_time = (datetime.now() - execution_start_time).total_seconds()
        if metrics_manager:
            await metrics_manager.record_metric(
                f"agent:{agent_id}:execution_time",
                execution_time,
                metadata={"success": True}
            )
        
        # Update health status for successful execution
        if health_tracker:
            await health_tracker.update_health(
                f"execution_{agent_id}",
                HealthStatus(
                    status="HEALTHY",
                    source="phase_zero_orchestrator",
                    description=f"Agent {agent_id} executed successfully",
                    metadata={"execution_time": execution_time}
                )
            )
        
        return result
        
    except asyncio.TimeoutError:
        logger.warning(f"Agent {agent_id} timed out")
        
        # Increment revision attempts and log
        if revision_attempts is not None:
            revision_attempts[agent_id] += 1
            logger.info(f"Agent {agent_id} revision attempt #{revision_attempts[agent_id]} due to timeout")
            
            # Store basic metadata about the revision
            if state_manager:
                await state_manager.set_state(
                    f"phase_zero:revision:{agent_id}:{revision_attempts[agent_id]}",
                    {
                        "agent_id": agent_id,
                        "attempt": revision_attempts[agent_id],
                        "timestamp": datetime.now().isoformat(),
                        "reason": "timeout",
                        "timeout_seconds": timeout
                    },
                    resource_type=ResourceType.STATE
                )
        
        # Record timeout metric
        if metrics_manager:
            await metrics_manager.record_metric(
                f"agent:{agent_id}:timeouts",
                1.0
            )
        
        # Update health status for timeout
        if health_tracker:
            await health_tracker.update_health(
                f"execution_{agent_id}",
                HealthStatus(
                    status="CRITICAL",
                    source="phase_zero_orchestrator",
                    description=f"Agent {agent_id} timed out",
                    metadata={
                        "timeout": timeout, 
                        "revision_attempt": revision_attempts.get(agent_id, 0) if revision_attempts else None
                    }
                )
            )
        
        raise
        
    except Exception as e:
        logger.error(f"Agent {agent_id} error: {str(e)}")
        
        # Increment revision attempts and log
        if revision_attempts is not None:
            revision_attempts[agent_id] += 1
            logger.info(f"Agent {agent_id} revision attempt #{revision_attempts[agent_id]} due to error: {str(e)}")
            
            # Store basic metadata about the revision
            if state_manager:
                await state_manager.set_state(
                    f"phase_zero:revision:{agent_id}:{revision_attempts[agent_id]}",
                    {
                        "agent_id": agent_id,
                        "attempt": revision_attempts[agent_id],
                        "timestamp": datetime.now().isoformat(),
                        "reason": "error",
                        "error": str(e)
                    },
                    resource_type=ResourceType.STATE
                )
        
        # Record error metric
        if metrics_manager:
            await metrics_manager.record_metric(
                f"agent:{agent_id}:errors",
                1.0,
                metadata={
                    "error": str(e), 
                    "revision_attempt": revision_attempts.get(agent_id, 0) if revision_attempts else None
                }
            )
        
        # Update health status for error
        if health_tracker:
            await health_tracker.update_health(
                f"execution_{agent_id}",
                HealthStatus(
                    status="CRITICAL",
                    source="phase_zero_orchestrator",
                    description=f"Agent {agent_id} error: {str(e)}",
                    metadata={
                        "error": str(e), 
                        "revision_attempt": revision_attempts.get(agent_id, 0) if revision_attempts else None
                    }
                )
            )
        
        raise