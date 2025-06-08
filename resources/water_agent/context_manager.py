"""
Water Agent Persistent Context Manager.

This module provides persistent context management for the Water Agent's coordination
activities, allowing it to store, retrieve, and clean up context information for
agent coordination sessions.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple, Union, Set

from resources.base_resource import BaseResource
from resources.common import ResourceType
from resources.interfaces.base import ICleanupPolicy
from resources.state import StateManager, StateEntry
from resources.events import ResourceEventTypes

logger = logging.getLogger(__name__)


class CoordinationContext:
    """
    Represents a coordination context between two agents.
    
    This class stores all the information related to a coordination session between
    two agents, including misunderstandings, questions, responses, and resolution status.
    """
    
    def __init__(
        self,
        coordination_id: str,
        first_agent_id: str,
        second_agent_id: str,
        mode: str = "standard",
        max_iterations: int = 3,
        severity_threshold: str = "LOW"
    ):
        """
        Initialize a new coordination context.
        
        Args:
            coordination_id: Unique identifier for this coordination session
            first_agent_id: ID of the first agent in the sequence
            second_agent_id: ID of the second agent in the sequence
            mode: Coordination mode (standard, preventive, or interactive)
            max_iterations: Maximum number of iterations allowed
            severity_threshold: Minimum severity level to consider resolved
        """
        self.coordination_id = coordination_id
        self.first_agent_id = first_agent_id
        self.second_agent_id = second_agent_id
        self.mode = mode
        self.max_iterations = max_iterations
        self.severity_threshold = severity_threshold
        
        # Context metadata
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
        self.status = "created"
        
        # Original outputs
        self.first_agent_original_output = None
        self.second_agent_original_output = None
        
        # Coordination data
        self.misunderstandings = []
        self.iterations = []
        self.resolved_issues = set()
        self.unresolved_issues = {}
        
        # Final outputs
        self.first_agent_final_output = None
        self.second_agent_final_output = None
        self.final_status = None
        self.completed_at = None
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the context to a dictionary for storage.
        
        Returns:
            Dictionary representation of the context
        """
        # Convert set to list for JSON serialization
        resolved_issues = list(self.resolved_issues) if isinstance(self.resolved_issues, set) else self.resolved_issues
        
        return {
            "coordination_id": self.coordination_id,
            "first_agent_id": self.first_agent_id,
            "second_agent_id": self.second_agent_id,
            "mode": self.mode,
            "max_iterations": self.max_iterations,
            "severity_threshold": self.severity_threshold,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "status": self.status,
            "first_agent_original_output": self.first_agent_original_output,
            "second_agent_original_output": self.second_agent_original_output,
            "misunderstandings": self.misunderstandings,
            "iterations": self.iterations,
            "resolved_issues": resolved_issues,
            "unresolved_issues": self.unresolved_issues,
            "first_agent_final_output": self.first_agent_final_output,
            "second_agent_final_output": self.second_agent_final_output,
            "final_status": self.final_status,
            "completed_at": self.completed_at
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CoordinationContext':
        """
        Create a CoordinationContext from a dictionary.
        
        Args:
            data: Dictionary representation of the context
            
        Returns:
            CoordinationContext instance
        """
        context = cls(
            coordination_id=data.get("coordination_id", str(uuid.uuid4())),
            first_agent_id=data.get("first_agent_id", "unknown"),
            second_agent_id=data.get("second_agent_id", "unknown"),
            mode=data.get("mode", "standard"),
            max_iterations=data.get("max_iterations", 3),
            severity_threshold=data.get("severity_threshold", "LOW")
        )
        
        # Set all attributes from the dictionary
        context.created_at = data.get("created_at", context.created_at)
        context.updated_at = data.get("updated_at", context.updated_at)
        context.status = data.get("status", context.status)
        context.first_agent_original_output = data.get("first_agent_original_output")
        context.second_agent_original_output = data.get("second_agent_original_output")
        context.misunderstandings = data.get("misunderstandings", [])
        context.iterations = data.get("iterations", [])
        context.resolved_issues = set(data.get("resolved_issues", []))
        context.unresolved_issues = data.get("unresolved_issues", {})
        context.first_agent_final_output = data.get("first_agent_final_output")
        context.second_agent_final_output = data.get("second_agent_final_output")
        context.final_status = data.get("final_status")
        context.completed_at = data.get("completed_at")
        
        return context
    
    def update_iteration(
        self,
        iteration: int,
        first_agent_questions: List[str],
        first_agent_responses: List[str],
        second_agent_questions: List[str],
        second_agent_responses: List[str],
        resolved: List[Dict[str, Any]],
        unresolved: List[Dict[str, Any]]
    ) -> None:
        """
        Update the context with information from a coordination iteration.
        
        Args:
            iteration: Iteration number
            first_agent_questions: Questions asked to the first agent
            first_agent_responses: Responses from the first agent
            second_agent_questions: Questions asked to the second agent
            second_agent_responses: Responses from the second agent
            resolved: List of resolved issues in this iteration
            unresolved: List of unresolved issues remaining
        """
        # Update the updated_at timestamp
        self.updated_at = datetime.now().isoformat()
        
        # Create iteration entry
        iteration_entry = {
            "iteration": iteration,
            "timestamp": datetime.now().isoformat(),
            "first_agent_questions": first_agent_questions,
            "first_agent_responses": first_agent_responses,
            "second_agent_questions": second_agent_questions,
            "second_agent_responses": second_agent_responses,
            "resolved": resolved,
            "unresolved": unresolved
        }
        
        # Add to iterations list
        self.iterations.append(iteration_entry)
        
        # Update resolved and unresolved issues
        for issue in resolved:
            issue_id = issue.get("id")
            if issue_id:
                self.resolved_issues.add(issue_id)
                if issue_id in self.unresolved_issues:
                    del self.unresolved_issues[issue_id]
        
        # Update unresolved issues
        for issue in unresolved:
            issue_id = issue.get("id")
            if issue_id:
                self.unresolved_issues[issue_id] = issue
        
        # Update status
        self.status = "in_progress"
    
    def complete(
        self,
        first_agent_final_output: str,
        second_agent_final_output: str,
        final_status: str
    ) -> None:
        """
        Mark the coordination as complete with final outputs.
        
        Args:
            first_agent_final_output: Final output from the first agent
            second_agent_final_output: Final output from the second agent
            final_status: Final status of the coordination
        """
        self.first_agent_final_output = first_agent_final_output
        self.second_agent_final_output = second_agent_final_output
        self.final_status = final_status
        self.completed_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
        self.status = "completed"
        
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the coordination context.
        
        Returns:
            Dictionary with a summary of the coordination
        """
        # Count misunderstandings by severity
        severity_counts = {}
        for m in self.misunderstandings:
            severity = m.get("severity", "UNKNOWN")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        return {
            "coordination_id": self.coordination_id,
            "first_agent_id": self.first_agent_id,
            "second_agent_id": self.second_agent_id,
            "mode": self.mode,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "misunderstandings_count": len(self.misunderstandings),
            "severity_counts": severity_counts,
            "iterations_count": len(self.iterations),
            "resolved_issues_count": len(self.resolved_issues),
            "unresolved_issues_count": len(self.unresolved_issues),
            "final_status": self.final_status,
            "completed_at": self.completed_at
        }


class WaterAgentContextManager(BaseResource):
    """
    Manages persistent contexts for Water Agent coordination activities.
    
    This class provides methods for storing, retrieving, and cleaning up context
    information for agent coordination sessions.
    """
    
    def __init__(self, resource_id: Optional[str] = None, state_manager: Optional[StateManager] = None, event_bus = None):
        """
        Initialize the context manager.
        
        Args:
            resource_id: Unique identifier for this resource (auto-generated if None)
            state_manager: State manager for persistent storage
            event_bus: Optional event bus for emitting events
        """
        if resource_id is None:
            resource_id = f"water_agent_context_manager_{uuid.uuid4().hex[:8]}"
        super().__init__(resource_id=resource_id, state_manager=state_manager, event_bus=event_bus)
        
        # Coordination context cache
        self._context_cache: Dict[str, CoordinationContext] = {}
        
        # Define cleanup policy
        self.cleanup_policy = ICleanupPolicy.TTL
        
    async def create_coordination_context(
        self,
        first_agent_id: str,
        second_agent_id: str,
        mode: str = "standard",
        max_iterations: int = 3,
        severity_threshold: str = "LOW",
        coordination_id: Optional[str] = None
    ) -> CoordinationContext:
        """
        Create a new coordination context.
        
        Args:
            first_agent_id: ID of the first agent in the sequence
            second_agent_id: ID of the second agent in the sequence
            mode: Coordination mode (standard, preventive, or interactive)
            max_iterations: Maximum number of iterations allowed
            severity_threshold: Minimum severity level to consider resolved
            coordination_id: Optional specific ID for this coordination
            
        Returns:
            New CoordinationContext instance
        """
        # Generate coordination ID if not provided
        if not coordination_id:
            coordination_id = f"coordination_{uuid.uuid4()}"
            
        # Create the context
        context = CoordinationContext(
            coordination_id=coordination_id,
            first_agent_id=first_agent_id,
            second_agent_id=second_agent_id,
            mode=mode,
            max_iterations=max_iterations,
            severity_threshold=severity_threshold
        )
        
        # Store in cache
        self._context_cache[coordination_id] = context
        
        # Persist to state manager
        await self._persist_context(context)
        
        logger.info(f"Created new coordination context {coordination_id} for {first_agent_id} and {second_agent_id}")
        
        # Emit an event for the new context
        await self._emit_event(ResourceEventTypes.RESOURCE_STATE_CHANGED, {
            "coordination_id": coordination_id,
            "first_agent_id": first_agent_id,
            "second_agent_id": second_agent_id,
            "mode": mode,
            "timestamp": datetime.now().isoformat()
        })
        
        return context
        
    async def get_coordination_context(
        self,
        coordination_id: str
    ) -> Optional[CoordinationContext]:
        """
        Get a coordination context by ID.
        
        Args:
            coordination_id: ID of the coordination context to retrieve
            
        Returns:
            CoordinationContext if found, None otherwise
        """
        # Check cache first
        if coordination_id in self._context_cache:
            return self._context_cache[coordination_id]
            
        # Try to load from state manager
        try:
            context_entry = await self._state_manager.get_state(
                f"water_agent:coordination:{coordination_id}",
                ResourceType.STATE
            )
            
            if not context_entry:
                logger.warning(f"Coordination context {coordination_id} not found")
                return None
                
            # Create context from state entry
            if isinstance(context_entry, dict):
                context_data = context_entry
            else:
                # Handle StateEntry objects
                context_data = context_entry.state
                
            context = CoordinationContext.from_dict(context_data)
            
            # Store in cache
            self._context_cache[coordination_id] = context
            
            return context
            
        except Exception as e:
            logger.error(f"Error retrieving coordination context {coordination_id}: {str(e)}")
            return None
    
    async def update_coordination_context(
        self,
        context: CoordinationContext
    ) -> bool:
        """
        Update an existing coordination context.
        
        Args:
            context: Updated coordination context
            
        Returns:
            True if the update was successful, False otherwise
        """
        # Update in cache
        self._context_cache[context.coordination_id] = context
        
        # Persist to state manager
        return await self._persist_context(context)
        
    async def _persist_context(
        self,
        context: CoordinationContext
    ) -> bool:
        """
        Persist a coordination context to the state manager.
        
        Args:
            context: Coordination context to persist
            
        Returns:
            True if the persistence was successful, False otherwise
        """
        try:
            # Convert context to dictionary
            context_dict = context.to_dict()
            
            # Persist to state manager
            await self._state_manager.set_state(
                resource_id=f"water_agent:coordination:{context.coordination_id}",
                state=context_dict,
                metadata={
                    "first_agent_id": context.first_agent_id,
                    "second_agent_id": context.second_agent_id,
                    "mode": context.mode,
                    "created_at": context.created_at,
                    "updated_at": datetime.now().isoformat()
                },
                resource_type=ResourceType.STATE
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error persisting coordination context {context.coordination_id}: {str(e)}")
            return False
            
    async def save_coordination_outputs(
        self,
        coordination_id: str,
        first_agent_output: str,
        second_agent_output: str
    ) -> bool:
        """
        Save the original outputs for a coordination session.
        
        Args:
            coordination_id: ID of the coordination session
            first_agent_output: Original output from the first agent
            second_agent_output: Original output from the second agent
            
        Returns:
            True if the save was successful, False otherwise
        """
        # Get the context
        context = await self.get_coordination_context(coordination_id)
        if not context:
            logger.error(f"Coordination context {coordination_id} not found")
            return False
            
        # Update the context
        context.first_agent_original_output = first_agent_output
        context.second_agent_original_output = second_agent_output
        context.updated_at = datetime.now().isoformat()
        
        # Persist the updated context
        return await self.update_coordination_context(context)
        
    async def update_coordination_iteration(
        self,
        coordination_id: str,
        iteration: int,
        first_agent_questions: List[str],
        first_agent_responses: List[str],
        second_agent_questions: List[str],
        second_agent_responses: List[str],
        resolved: List[Dict[str, Any]],
        unresolved: List[Dict[str, Any]]
    ) -> bool:
        """
        Update a coordination context with iteration information.
        
        Args:
            coordination_id: ID of the coordination session
            iteration: Iteration number
            first_agent_questions: Questions asked to the first agent
            first_agent_responses: Responses from the first agent
            second_agent_questions: Questions asked to the second agent
            second_agent_responses: Responses from the second agent
            resolved: List of resolved issues in this iteration
            unresolved: List of unresolved issues remaining
            
        Returns:
            True if the update was successful, False otherwise
        """
        # Get the context
        context = await self.get_coordination_context(coordination_id)
        if not context:
            logger.error(f"Coordination context {coordination_id} not found")
            return False
            
        # Update the context
        context.update_iteration(
            iteration,
            first_agent_questions,
            first_agent_responses,
            second_agent_questions,
            second_agent_responses,
            resolved,
            unresolved
        )
        
        # Emit an event for the iteration
        await self._emit_event(ResourceEventTypes.RESOURCE_STATE_CHANGED, {
            "coordination_id": coordination_id,
            "iteration": iteration,
            "first_agent_id": context.first_agent_id,
            "second_agent_id": context.second_agent_id,
            "resolved_count": len(resolved),
            "unresolved_count": len(unresolved),
            "timestamp": datetime.now().isoformat()
        })
        
        # Persist the updated context
        return await self.update_coordination_context(context)
        
    async def complete_coordination(
        self,
        coordination_id: str,
        first_agent_final_output: str,
        second_agent_final_output: str,
        final_status: str
    ) -> bool:
        """
        Mark a coordination session as complete.
        
        Args:
            coordination_id: ID of the coordination session
            first_agent_final_output: Final output from the first agent
            second_agent_final_output: Final output from the second agent
            final_status: Final status of the coordination
            
        Returns:
            True if the completion was successful, False otherwise
        """
        # Get the context
        context = await self.get_coordination_context(coordination_id)
        if not context:
            logger.error(f"Coordination context {coordination_id} not found")
            return False
            
        # Update the context
        context.complete(
            first_agent_final_output,
            second_agent_final_output,
            final_status
        )
        
        # Emit an event for the completion
        await self._emit_event(ResourceEventTypes.RESOURCE_STATE_CHANGED, {
            "event_type": "coordination_completed",
            "coordination_id": coordination_id,
            "first_agent_id": context.first_agent_id,
            "second_agent_id": context.second_agent_id,
            "final_status": final_status,
            "iterations_count": len(context.iterations),
            "misunderstandings_count": len(context.misunderstandings),
            "resolved_issues_count": len(context.resolved_issues),
            "unresolved_issues_count": len(context.unresolved_issues),
            "timestamp": datetime.now().isoformat()
        })
        
        # Persist the updated context
        return await self.update_coordination_context(context)
        
    async def list_coordination_contexts(
        self,
        first_agent_id: Optional[str] = None,
        second_agent_id: Optional[str] = None,
        mode: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List coordination contexts with optional filtering.
        
        Args:
            first_agent_id: Optional first agent ID to filter by
            second_agent_id: Optional second agent ID to filter by
            mode: Optional mode to filter by
            status: Optional status to filter by
            limit: Maximum number of contexts to return
            offset: Offset for pagination
            
        Returns:
            List of coordination context summaries
        """
        try:
            # Get all coordination context IDs
            key_prefix = "water_agent:coordination:"
            
            # Use the state manager to get matching keys
            all_keys = await self._state_manager.find_keys(key_prefix)
            
            # Extract context IDs from keys
            context_ids = [key[len(key_prefix):] for key in all_keys]
            
            # Get and filter contexts
            contexts = []
            for context_id in context_ids:
                context = await self.get_coordination_context(context_id)
                if not context:
                    continue
                    
                # Apply filters
                if first_agent_id and context.first_agent_id != first_agent_id:
                    continue
                if second_agent_id and context.second_agent_id != second_agent_id:
                    continue
                if mode and context.mode != mode:
                    continue
                if status and context.status != status:
                    continue
                    
                # Add to list
                contexts.append(context.get_summary())
                
            # Sort by creation time (newest first)
            contexts.sort(key=lambda c: c.get("created_at", ""), reverse=True)
            
            # Apply pagination
            return contexts[offset:offset+limit]
            
        except Exception as e:
            logger.error(f"Error listing coordination contexts: {str(e)}")
            return []
            
    async def delete_coordination_context(
        self,
        coordination_id: str
    ) -> bool:
        """
        Delete a coordination context.
        
        Args:
            coordination_id: ID of the coordination context to delete
            
        Returns:
            True if the deletion was successful, False otherwise
        """
        try:
            # Remove from cache
            if coordination_id in self._context_cache:
                del self._context_cache[coordination_id]
                
            # Remove from state manager
            await self._state_manager.delete_state(
                f"water_agent:coordination:{coordination_id}"
            )
            
            logger.info(f"Deleted coordination context {coordination_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting coordination context {coordination_id}: {str(e)}")
            return False
            
    async def cleanup_old_contexts(
        self,
        max_age_days: int = 7
    ) -> int:
        """
        Clean up old coordination contexts.
        
        Args:
            max_age_days: Maximum age in days to keep contexts
            
        Returns:
            Number of contexts deleted
        """
        try:
            # Get all coordination context IDs
            key_prefix = "water_agent:coordination:"
            
            # Use the state manager to get matching keys
            all_keys = await self._state_manager.find_keys(key_prefix)
            
            # Extract context IDs from keys
            context_ids = [key[len(key_prefix):] for key in all_keys]
            
            # Calculate cutoff date
            cutoff_date = (datetime.now() - timedelta(days=max_age_days)).isoformat()
            
            # Get and filter contexts for deletion
            deleted_count = 0
            for context_id in context_ids:
                context = await self.get_coordination_context(context_id)
                if not context:
                    continue
                    
                # Check if context is older than cutoff
                if context.created_at < cutoff_date:
                    if await self.delete_coordination_context(context_id):
                        deleted_count += 1
                        
            logger.info(f"Cleaned up {deleted_count} old coordination contexts")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old coordination contexts: {str(e)}")
            return 0
            
    async def prune_temporary_data(
        self,
        coordination_id: str,
        keep_final_outputs: bool = True
    ) -> bool:
        """
        Prune temporary data from a coordination context.
        
        This removes intermediate questions, responses, and other temporary data
        from a coordination context, keeping only the final outputs and summary.
        
        Args:
            coordination_id: ID of the coordination context to prune
            keep_final_outputs: Whether to keep the final outputs
            
        Returns:
            True if the pruning was successful, False otherwise
        """
        # Get the context
        context = await self.get_coordination_context(coordination_id)
        if not context:
            logger.error(f"Coordination context {coordination_id} not found")
            return False
            
        # Check if the context is completed
        if context.status != "completed":
            logger.warning(f"Cannot prune incomplete coordination context {coordination_id}")
            return False
            
        # Create a pruned version
        pruned_context = CoordinationContext(
            coordination_id=context.coordination_id,
            first_agent_id=context.first_agent_id,
            second_agent_id=context.second_agent_id,
            mode=context.mode,
            max_iterations=context.max_iterations,
            severity_threshold=context.severity_threshold
        )
        
        # Copy metadata
        pruned_context.created_at = context.created_at
        pruned_context.updated_at = datetime.now().isoformat()
        pruned_context.status = context.status
        pruned_context.misunderstandings = context.misunderstandings
        pruned_context.resolved_issues = context.resolved_issues
        pruned_context.final_status = context.final_status
        pruned_context.completed_at = context.completed_at
        
        # Create a summary of iterations instead of full data
        pruned_context.iterations = []
        for i, iteration in enumerate(context.iterations):
            pruned_iteration = {
                "iteration": i + 1,
                "timestamp": iteration.get("timestamp", ""),
                "first_agent_questions_count": len(iteration.get("first_agent_questions", [])),
                "second_agent_questions_count": len(iteration.get("second_agent_questions", [])),
                "resolved_count": len(iteration.get("resolved", [])),
                "unresolved_count": len(iteration.get("unresolved", []))
            }
            pruned_context.iterations.append(pruned_iteration)
        
        # Keep final outputs if requested
        if keep_final_outputs:
            pruned_context.first_agent_final_output = context.first_agent_final_output
            pruned_context.second_agent_final_output = context.second_agent_final_output
        
        # Update in cache and persist
        self._context_cache[coordination_id] = pruned_context
        success = await self._persist_context(pruned_context)
        
        if success:
            logger.info(f"Pruned temporary data from coordination context {coordination_id}")
        else:
            logger.error(f"Failed to prune temporary data from coordination context {coordination_id}")
            
        return success