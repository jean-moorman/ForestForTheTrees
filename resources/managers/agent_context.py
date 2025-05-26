from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union, Set
from enum import Enum, auto
import asyncio
import sys
import logging

from resources.common import ResourceState, ResourceType, InterfaceState, HealthStatus
from resources.errors import (
    ErrorSeverity,
    ResourceOperationError,
    ResourceError,
    ResourceExhaustionError,
    ResourceTimeoutError
)
from resources.events import ResourceEventTypes, EventQueue
from resources.base import (
    BaseManager, 
    MemoryThresholds,
    CleanupConfig,
    CleanupPolicy,
    DEFAULT_AGENT_CIRCUIT_CONFIG
)

logger = logging.getLogger(__name__)

class AgentContextType(Enum):
    FRESH = auto()
    PERSISTENT = auto()
    SLIDING_WINDOW = auto()

class AgentContext:
    def __init__(
        self,
        operation_id: str,
        schema: Dict[str, Any],
        context_type: AgentContextType = AgentContextType.FRESH,
        window_size: Optional[int] = None
    ):
        self.operation_id = operation_id
        self.start_time = datetime.now()
        self.schema = schema
        self.context_type = context_type
        self.window_size = window_size if context_type == AgentContextType.SLIDING_WINDOW else None
        # Store conversations as a simple list of messages
        self.conversation: List[Dict[str, Any]] = []
        # Store other context data separately
        self.metadata: Dict[str, Any] = {}
        self.operation_metadata: Dict[str, Any] = {}

    async def update_data(self, new_data: Dict[str, Any]) -> None:
        """Update context data with simplified conversation handling"""
        logger.debug(f"Updating context {self.operation_id} of type {self.context_type.name}")
        
        # Extract conversation messages if present
        new_messages = new_data.pop("conversation", [])
        
        # Handle different context types
        if self.context_type == AgentContextType.FRESH:
            # For FRESH, just replace both conversation and metadata
            self.conversation = new_messages
            self.metadata = new_data
            return
            
        # For PERSISTENT and SLIDING_WINDOW, append messages and update metadata
        self.conversation.extend(new_messages)
        self.metadata.update(new_data)
        
        # Apply window size limit if needed
        if self.context_type == AgentContextType.SLIDING_WINDOW and self.window_size:
            if len(self.conversation) > self.window_size:
                # Keep only most recent messages within window size
                self.conversation = self.conversation[-self.window_size:]
        
        logger.debug(f"Context updated. Conversation size: {len(self.conversation)}")

    def get_current_data(self) -> Dict[str, Any]:
        """Get the current context data in a format compatible with existing code"""
        result = dict(self.metadata)
        if self.conversation:
            result["conversation"] = self.conversation
        return [result]

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for storage"""
        return {
            "operation_id": self.operation_id,
            "start_time": self.start_time.isoformat(),
            "schema": self.schema,
            "conversation": self.conversation,
            "metadata": self.metadata,
            "window_size": self.window_size,
            "context_type": self.context_type.name,
            "operation_metadata": self.operation_metadata
        }
    
    @classmethod
    def from_dict(cls, data_dict: Dict[str, Any]) -> 'AgentContext':
        """Reconstruct context from dictionary storage"""
        context = cls(
            operation_id=data_dict["operation_id"],
            schema=data_dict["schema"],
            context_type=AgentContextType[data_dict["context_type"]],
            window_size=data_dict.get("window_size")
        )
        
        context.conversation = data_dict.get("conversation", [])
        context.metadata = data_dict.get("metadata", {})
        
        # Restore metadata
        context.operation_metadata = data_dict.get("operation_metadata", {})
        
        return context

    def debug_state(self) -> Dict[str, Any]:
        """Return a debug-friendly representation of current state"""
        return {
            "operation_id": self.operation_id,
            "context_type": self.context_type.name,
            "window_size": self.window_size,
            "conversation_length": len(self.conversation),
            "metadata_keys": list(self.metadata.keys()),
            "start_time": self.start_time.isoformat()
        }

class AgentContextManager(BaseManager):
    """Manages agent contexts with versioning and memory monitoring"""
    def __init__(self, 
                 event_queue: EventQueue,
                 cleanup_config: Optional[CleanupConfig] = None,
                 memory_thresholds: Optional[MemoryThresholds] = None):
        super().__init__(
            event_queue=event_queue,
            circuit_breaker_config=DEFAULT_AGENT_CIRCUIT_CONFIG,
            cleanup_config=cleanup_config or CleanupConfig(
                policy=CleanupPolicy.HYBRID,
                ttl_seconds=7200,  # 2 hour default TTL
                max_size=500       # Default max contexts
            ),
            memory_thresholds=memory_thresholds
        )
        self._agent_contexts: Dict[str, AgentContext] = {}
        self._context_locks: Dict[str, asyncio.Lock] = {}
        self._last_cleanup = datetime.now()
    
    async def create_context(self, 
                        agent_id: str,
                        operation_id: str, 
                        schema: Dict[str, Any],
                        context_type: AgentContextType = AgentContextType.FRESH,
                        window_size: Optional[int] = None) -> AgentContext:
        """Create new agent context"""
        async def _create():
            # For FRESH type, we don't check for existing context
            if context_type != AgentContextType.FRESH:
                if agent_id in self._agent_contexts:
                    if context_type == AgentContextType.SLIDING_WINDOW:
                        # Return existing sliding window context if it exists
                        existing_context = self._agent_contexts.get(agent_id)
                        if existing_context:
                            return existing_context
                    raise ResourceOperationError(
                        message=f"Agent context already exists: {agent_id}",
                        resource_id=agent_id,
                        severity=ErrorSeverity.TRANSIENT,
                        operation="create_context",
                        recovery_strategy="use_existing"
                    )
            
            context = AgentContext(
                operation_id=operation_id,
                schema=schema,
                context_type=context_type,
                window_size=window_size
            )
            
            self._agent_contexts[agent_id] = context
            self._context_locks[agent_id] = asyncio.Lock()
            
            # Monitor memory usage with correct key format
            context_size = (sys.getsizeof(context.conversation) + sys.getsizeof(context.metadata)) / (1024 * 1024)
            await self._memory_monitor.track_resource(
                f"context_{agent_id}", 
                context_size,
                agent_id
            )
            
            if self._memory_thresholds and context_size > self._memory_thresholds.per_resource_max_mb:
                raise ResourceExhaustionError(
                    resource_id=agent_id,
                    operation="create_context",
                    current_usage=context_size,
                    limit=self._memory_thresholds.per_resource_max_mb,
                    resource_type=ResourceType.AGENT_CONTEXT.name,
                    details={"context_type": context_type.name}
                )

            await self.event_bus.emit(
                ResourceEventTypes.AGENT_CONTEXT_UPDATED.value,
                {
                    "agent_id": agent_id,
                    "operation": "created",
                    "context_id": operation_id
                }
            )
            
            return context
            
        return await self.protected_operation("create_context", _create)

    async def get_context(self, context_id: str) -> Optional[AgentContext]:
        """Get agent context by ID"""
        async def _get():
            context = self._agent_contexts.get(context_id)
            if context:
                size = (sys.getsizeof(context.conversation) + sys.getsizeof(context.metadata)) / (1024 * 1024)
                self._memory_monitor._resource_sizes[f"context_{context_id}"] = size
            return context
            
        return await self.protected_operation("get_context", _get)

    async def update_context(self, 
                        context_id: str,
                        data_updates: Dict[str, Any],
                        metadata_updates: Optional[Dict[str, Any]] = None) -> None:
        """Update context data and metadata"""
        async def _update():
            context = self._agent_contexts.get(context_id)
            if not context:
                raise ResourceOperationError(
                    message=f"Context not found: {context_id}",
                    resource_id=context_id,
                    severity=ErrorSeverity.DEGRADED, 
                    operation="update_context"
                )
                
            async with self._context_locks[context_id]:
                # Use the context's update_data method instead of directly updating
                await context.update_data(data_updates)
                if metadata_updates:
                    context.operation_metadata.update(metadata_updates)
                    
                size = (sys.getsizeof(context.conversation) + sys.getsizeof(context.metadata)) / (1024 * 1024)
                self._memory_monitor._resource_sizes[f"context_{context_id}"] = size
                
                # memory threshold check
                if self._memory_thresholds and size > self._memory_thresholds.per_resource_max_mb:
                    raise ResourceExhaustionError(
                        resource_id=context_id,
                        operation="update_context",
                        current_usage=size,
                        limit=self._memory_thresholds.per_resource_max_mb,
                        resource_type=ResourceType.AGENT_CONTEXT.name,
                        details={"operation": "update", "conversation_size": len(context.conversation)}
                    )

        await self.protected_operation("update_context", _update)

    async def _cleanup_resources(self, force: bool = False) -> None:
        """Implement specific resource cleanup for agent contexts
        
        Args:
            force: If True, ignore the check interval and force cleanup of all contexts
        """
        if not self._cleanup_config:
            return
                
        now = datetime.now()
        if not force and (now - self._last_cleanup).seconds < self._cleanup_config.check_interval:
            return
                
        self._last_cleanup = now
        
        expired_contexts = set()
        for agent_id, context in self._agent_contexts.items():
            if force or (now - context.start_time).seconds > self._cleanup_config.ttl_seconds:
                expired_contexts.add(agent_id)
                    
        for agent_id in expired_contexts:
            try:
                await self._cleanup_context(agent_id)
                logger.info(f"Cleaned up agent context: {agent_id}")
            except Exception as e:
                logger.error(f"Error cleaning up context {agent_id}: {e}")
        
        # Report cleanup statistics
        await self.event_bus.emit(
            ResourceEventTypes.METRIC_RECORDED.value,
            {
                "metric": "agent_context_cleanup",
                "value": len(expired_contexts),
                "total_contexts": len(self._agent_contexts),
                "timestamp": datetime.now().isoformat()
            }
        )

    async def _cleanup_context(self, context_id: str) -> None:
        """Clean up a specific context"""
        try:
            if context_id in self._agent_contexts:
                del self._agent_contexts[context_id]
            if context_id in self._context_locks:
                del self._context_locks[context_id]
            self._memory_monitor._resource_sizes.pop(f"context_{context_id}", None)
            
            await self.event_bus.emit(
                ResourceEventTypes.AGENT_CONTEXT_UPDATED.value,
                {
                    "context_id": context_id,
                    "operation": "cleaned_up"
                }
            )
        except Exception as e:
            raise ResourceOperationError(
                message=f"Failed to clean up context {context_id}: {str(e)}",
                resource_id=context_id,
                severity=ErrorSeverity.DEGRADED,
                operation="cleanup_context"
            )

    async def get_health_status(self) -> HealthStatus:
        """Get health status of agent context management"""
        async def _get_health_operation():
            total_contexts = len(self._agent_contexts)
            total_memory = sum(
                self._memory_monitor._resource_sizes.get(f"context_{cid}", 0)
                for cid in self._agent_contexts
            )
            
            status = "HEALTHY"
            description = "Agent context manager operating normally"
            
            if total_contexts > self._cleanup_config.max_size * 0.8:
                status = "DEGRADED"
                description = "High context count, cleanup recommended"
                
            return HealthStatus(
                status=status,
                source="agent_context_manager",
                description=description,
                metadata={
                    "total_contexts": total_contexts,
                    "total_memory_mb": total_memory
                }
            )
        
        return await self.protected_operation("get_health_status", _get_health_operation)