"""
Error Traceback System for FFTT

Implements advanced error tracing capabilities to track error propagation through the system,
allowing for root cause identification and comprehensive error recovery.
"""

import asyncio
import logging
import time
import traceback
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple, Set, Callable, Awaitable, TypeVar, Generic, DefaultDict
from collections import defaultdict, deque

from resources.common import ErrorSeverity
from resources.errors import ErrorClassification, ErrorContext, ResourceError

logger = logging.getLogger(__name__)

class TracebackNodeType(Enum):
    """Types of nodes in the error traceback graph"""
    ERROR = "ERROR"           # An actual error occurrence
    COMPONENT = "COMPONENT"   # A system component 
    OPERATION = "OPERATION"   # A specific operation
    RESOURCE = "RESOURCE"     # A system resource
    TRANSITION = "TRANSITION" # A phase transition
    CHECKPOINT = "CHECKPOINT" # A system checkpoint

@dataclass
class TracebackNode:
    """Node in the error traceback graph"""
    node_id: str
    node_type: TracebackNodeType
    label: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0  # Weight for graph traversal algorithms

@dataclass
class TracebackEdge:
    """Edge in the error traceback graph representing relationships"""
    source_id: str
    target_id: str
    relationship: str  # e.g., "caused", "affected", "detected_in", "depends_on"
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0  # Weight for graph traversal algorithms

class ErrorTracebackGraph:
    """
    Directed graph representing error propagation and relationships across the system.
    Enables traversal for root cause analysis and impact assessment.
    """
    def __init__(self):
        self._nodes: Dict[str, TracebackNode] = {}
        self._edges: List[TracebackEdge] = []
        # Indices for faster lookups
        self._node_type_index: DefaultDict[TracebackNodeType, List[str]] = defaultdict(list)
        self._outgoing_edges: DefaultDict[str, List[int]] = defaultdict(list)  # node_id -> list of edge indices
        self._incoming_edges: DefaultDict[str, List[int]] = defaultdict(list)  # node_id -> list of edge indices
        self._relationship_index: DefaultDict[str, List[int]] = defaultdict(list)  # relationship -> list of edge indices
        # Locking for thread safety
        self._lock = asyncio.Lock()
        
    async def add_node(self, node: TracebackNode) -> str:
        """Add a node to the graph, returns the node ID"""
        async with self._lock:
            if node.node_id in self._nodes:
                # Update metadata if node already exists
                self._nodes[node.node_id].metadata.update(node.metadata)
                return node.node_id
                
            self._nodes[node.node_id] = node
            self._node_type_index[node.node_type].append(node.node_id)
            return node.node_id
    
    async def add_edge(self, edge: TracebackEdge) -> int:
        """Add an edge to the graph, returns the edge index"""
        async with self._lock:
            # Verify nodes exist
            if edge.source_id not in self._nodes:
                raise ValueError(f"Source node {edge.source_id} does not exist")
            if edge.target_id not in self._nodes:
                raise ValueError(f"Target node {edge.target_id} does not exist")
                
            # Add edge
            edge_idx = len(self._edges)
            self._edges.append(edge)
            self._outgoing_edges[edge.source_id].append(edge_idx)
            self._incoming_edges[edge.target_id].append(edge_idx)
            self._relationship_index[edge.relationship].append(edge_idx)
            return edge_idx
    
    async def get_node(self, node_id: str) -> Optional[TracebackNode]:
        """Get a node by ID"""
        async with self._lock:
            return self._nodes.get(node_id)
    
    async def get_nodes_by_type(self, node_type: TracebackNodeType) -> List[TracebackNode]:
        """Get all nodes of a given type"""
        async with self._lock:
            return [self._nodes[node_id] for node_id in self._node_type_index.get(node_type, [])]
    
    async def get_outgoing_edges(self, node_id: str) -> List[TracebackEdge]:
        """Get all edges originating from a node"""
        async with self._lock:
            return [self._edges[edge_idx] for edge_idx in self._outgoing_edges.get(node_id, [])]
    
    async def get_incoming_edges(self, node_id: str) -> List[TracebackEdge]:
        """Get all edges targeting a node"""
        async with self._lock:
            return [self._edges[edge_idx] for edge_idx in self._incoming_edges.get(node_id, [])]
    
    async def find_roots(self, node_id: str, max_depth: int = 10) -> List[str]:
        """
        Find potential root causes by traversing incoming edges up to max_depth.
        Returns a list of node IDs that have no incoming edges (potential root causes).
        """
        async with self._lock:
            visited: Set[str] = set()
            roots: List[str] = []
            
            async def dfs(current_id: str, depth: int):
                if depth <= 0 or current_id in visited:
                    return
                
                visited.add(current_id)
                incoming = [self._edges[edge_idx] for edge_idx in self._incoming_edges.get(current_id, [])]
                
                if not incoming:
                    # This is a root node (no incoming edges)
                    roots.append(current_id)
                    return
                
                # Continue traversal up the chain
                for edge in incoming:
                    await dfs(edge.source_id, depth - 1)
            
            await dfs(node_id, max_depth)
            return roots
    
    async def find_impact(self, node_id: str, max_depth: int = 10) -> List[str]:
        """
        Find impacted nodes by traversing outgoing edges up to max_depth.
        Returns a list of impacted node IDs.
        """
        async with self._lock:
            visited: Set[str] = set()
            impacted: List[str] = []
            
            async def dfs(current_id: str, depth: int):
                if depth <= 0 or current_id in visited:
                    return
                
                visited.add(current_id)
                if current_id != node_id:  # Don't include the starting node
                    impacted.append(current_id)
                
                # Continue traversal down the chain
                outgoing = [self._edges[edge_idx] for edge_idx in self._outgoing_edges.get(current_id, [])]
                for edge in outgoing:
                    await dfs(edge.target_id, depth - 1)
            
            await dfs(node_id, max_depth)
            return impacted
    
    async def find_related_errors(self, error_id: str, max_depth: int = 5) -> List[str]:
        """Find related error nodes to a given error"""
        async with self._lock:
            if error_id not in self._nodes or self._nodes[error_id].node_type != TracebackNodeType.ERROR:
                return []
            
            # Find both upstream and downstream errors
            all_related: Set[str] = set()
            
            # Get upstream errors (potential causes)
            upstream = await self.find_roots(error_id, max_depth)
            for node_id in upstream:
                if node_id in self._nodes and self._nodes[node_id].node_type == TracebackNodeType.ERROR:
                    all_related.add(node_id)
            
            # Get downstream errors (potential effects)
            downstream = await self.find_impact(error_id, max_depth)
            for node_id in downstream:
                if node_id in self._nodes and self._nodes[node_id].node_type == TracebackNodeType.ERROR:
                    all_related.add(node_id)
            
            return list(all_related)
    
    async def get_error_chain(self, error_id: str) -> Tuple[List[str], List[str]]:
        """
        Get the complete error chain (both causes and effects).
        Returns a tuple of (causes, effects) as lists of error node IDs.
        """
        causes = await self.find_roots(error_id)
        effects = await self.find_impact(error_id)
        return causes, effects
    
    async def get_error_trace(self, error_id: str) -> Dict[str, Any]:
        """
        Generate a comprehensive error trace for visualization and analysis.
        Returns a structured representation of the error chain.
        """
        node = await self.get_node(error_id)
        if not node or node.node_type != TracebackNodeType.ERROR:
            return {"error": "Invalid error ID", "error_id": error_id}
        
        causes, effects = await self.get_error_chain(error_id)
        
        # Gather related components
        components = set()
        operations = set()
        resources = set()
        
        async def gather_context(node_id: str):
            incoming = await self.get_incoming_edges(node_id)
            outgoing = await self.get_outgoing_edges(node_id)
            
            for edge in incoming + outgoing:
                related_id = edge.source_id if edge.target_id == node_id else edge.target_id
                related_node = await self.get_node(related_id)
                if related_node:
                    if related_node.node_type == TracebackNodeType.COMPONENT:
                        components.add(related_id)
                    elif related_node.node_type == TracebackNodeType.OPERATION:
                        operations.add(related_id)
                    elif related_node.node_type == TracebackNodeType.RESOURCE:
                        resources.add(related_id)
        
        # Gather context for the main error
        await gather_context(error_id)
        
        # Gather context for causes and effects
        for cause_id in causes:
            await gather_context(cause_id)
        
        for effect_id in effects:
            await gather_context(effect_id)
        
        # Compile the complete trace
        trace = {
            "error_id": error_id,
            "error_info": {
                "label": node.label,
                "timestamp": node.timestamp.isoformat(),
                "metadata": node.metadata
            },
            "causes": [
                {
                    "error_id": cause_id,
                    "info": (await self.get_node(cause_id)).metadata if await self.get_node(cause_id) else {}
                }
                for cause_id in causes if cause_id != error_id
            ],
            "effects": [
                {
                    "error_id": effect_id,
                    "info": (await self.get_node(effect_id)).metadata if await self.get_node(effect_id) else {}
                }
                for effect_id in effects if effect_id != error_id
            ],
            "components": [
                {
                    "component_id": comp_id,
                    "info": (await self.get_node(comp_id)).metadata if await self.get_node(comp_id) else {}
                }
                for comp_id in components
            ],
            "operations": [
                {
                    "operation_id": op_id,
                    "info": (await self.get_node(op_id)).metadata if await self.get_node(op_id) else {}
                }
                for op_id in operations
            ],
            "resources": [
                {
                    "resource_id": res_id,
                    "info": (await self.get_node(res_id)).metadata if await self.get_node(res_id) else {}
                }
                for res_id in resources
            ]
        }
        
        return trace
    
    async def prune_old_entries(self, max_age: timedelta = timedelta(days=7)):
        """Remove entries older than max_age to prevent unbounded growth"""
        async with self._lock:
            cutoff = datetime.now() - max_age
            
            # Find nodes to remove
            nodes_to_remove = [
                node_id for node_id, node in self._nodes.items()
                if node.timestamp < cutoff
            ]
            
            # Find edges to remove (either connected to removed nodes or old themselves)
            edges_to_remove = [
                i for i, edge in enumerate(self._edges)
                if edge.timestamp < cutoff or 
                edge.source_id in nodes_to_remove or 
                edge.target_id in nodes_to_remove
            ]
            
            # Remove edges (need to update indices)
            for edge_idx in sorted(edges_to_remove, reverse=True):
                edge = self._edges[edge_idx]
                self._outgoing_edges[edge.source_id].remove(edge_idx)
                self._incoming_edges[edge.target_id].remove(edge_idx)
                self._relationship_index[edge.relationship].remove(edge_idx)
                # Remove the edge
                self._edges.pop(edge_idx)
                
                # Update indices for shifted edges
                for i in range(edge_idx, len(self._edges)):
                    # Update all references to this edge
                    for node_id, edges in self._outgoing_edges.items():
                        for j, e_idx in enumerate(edges):
                            if e_idx > edge_idx:
                                self._outgoing_edges[node_id][j] -= 1
                    
                    for node_id, edges in self._incoming_edges.items():
                        for j, e_idx in enumerate(edges):
                            if e_idx > edge_idx:
                                self._incoming_edges[node_id][j] -= 1
                    
                    for rel, edges in self._relationship_index.items():
                        for j, e_idx in enumerate(edges):
                            if e_idx > edge_idx:
                                self._relationship_index[rel][j] -= 1
            
            # Remove nodes
            for node_id in nodes_to_remove:
                node = self._nodes.pop(node_id)
                self._node_type_index[node.node_type].remove(node_id)
                
                # Clean up empty lists
                if not self._node_type_index[node.node_type]:
                    del self._node_type_index[node.node_type]
                
                if node_id in self._outgoing_edges:
                    del self._outgoing_edges[node_id]
                
                if node_id in self._incoming_edges:
                    del self._incoming_edges[node_id]
            
            # Log pruning stats
            logger.info(f"Pruned {len(nodes_to_remove)} nodes and {len(edges_to_remove)} edges from error traceback graph")


class ErrorTracebackManager:
    """
    Manager for error traceback with error tracking and visualization capabilities.
    Works alongside the ErrorHandler to provide comprehensive error tracing.
    """
    def __init__(self, event_queue=None):
        self._graph = ErrorTracebackGraph()
        self._event_queue = event_queue
        self._maintenance_task = None
        self._running = False
        self._maintenance_interval = timedelta(hours=6)  # Prune old entries every 6 hours
        
    async def start(self):
        """Start the traceback manager and maintenance tasks"""
        if self._running:
            return
        
        self._running = True
        if self._event_queue:
            # Subscribe to events we need to track errors
            await self._event_queue.subscribe("error_occurred", self._handle_error_event)
            await self._event_queue.subscribe("resource_error_occurred", self._handle_error_event)
            await self._event_queue.subscribe("resource_error_resolved", self._handle_resolution_event)
            await self._event_queue.subscribe("phase_transition", self._handle_phase_transition)
            await self._event_queue.subscribe("checkpoint_created", self._handle_checkpoint_event)
        
        # Start maintenance task
        loop = asyncio.get_event_loop()
        self._maintenance_task = loop.create_task(self._maintenance_loop())
        logger.info("Error traceback manager started")
    
    async def stop(self):
        """Stop the traceback manager"""
        if not self._running:
            return
            
        self._running = False
        
        if self._event_queue:
            # Unsubscribe from events
            await self._event_queue.unsubscribe("error_occurred", self._handle_error_event)
            await self._event_queue.unsubscribe("resource_error_occurred", self._handle_error_event)
            await self._event_queue.unsubscribe("resource_error_resolved", self._handle_resolution_event)
            await self._event_queue.unsubscribe("phase_transition", self._handle_phase_transition)
            await self._event_queue.unsubscribe("checkpoint_created", self._handle_checkpoint_event)
        
        # Stop maintenance task
        if self._maintenance_task and not self._maintenance_task.done():
            self._maintenance_task.cancel()
            try:
                await self._maintenance_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Error traceback manager stopped")
    
    async def _maintenance_loop(self):
        """Background task for periodic maintenance operations"""
        while self._running:
            try:
                # Prune old entries
                await self._graph.prune_old_entries()
                
                # Wait for next maintenance interval
                await asyncio.sleep(self._maintenance_interval.total_seconds())
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in traceback maintenance loop: {e}", exc_info=True)
                await asyncio.sleep(60)  # shorter interval on error
    
    async def _handle_error_event(self, event_data: Dict[str, Any]):
        """Process error events and update the traceback graph"""
        try:
            # Extract info from the event
            error_id = event_data.get("error_id", str(uuid.uuid4()))
            component_id = event_data.get("component_id", "unknown")
            operation = event_data.get("operation", "unknown")
            error_type = event_data.get("error_type", "unknown")
            severity = event_data.get("severity", "UNKNOWN")
            context = event_data.get("context", {})
            correlation_id = context.get("correlation_id", str(uuid.uuid4()))
            
            # Create error node
            error_node = TracebackNode(
                node_id=error_id,
                node_type=TracebackNodeType.ERROR,
                label=f"{error_type} in {component_id}",
                timestamp=datetime.now(),
                metadata={
                    "error_type": error_type,
                    "severity": severity,
                    "message": context.get("error_message", ""),
                    "stacktrace": context.get("stacktrace", ""),
                    "correlation_id": correlation_id,
                    "component_id": component_id,
                    "operation": operation
                }
            )
            await self._graph.add_node(error_node)
            
            # Create component node if needed
            component_node = TracebackNode(
                node_id=f"component:{component_id}",
                node_type=TracebackNodeType.COMPONENT,
                label=component_id,
                metadata={"component_id": component_id}
            )
            await self._graph.add_node(component_node)
            
            # Create operation node if needed
            operation_node = TracebackNode(
                node_id=f"operation:{component_id}:{operation}",
                node_type=TracebackNodeType.OPERATION,
                label=f"{operation} in {component_id}",
                metadata={"component_id": component_id, "operation": operation}
            )
            await self._graph.add_node(operation_node)
            
            # Create edges
            # Error occurred in component
            await self._graph.add_edge(TracebackEdge(
                source_id=f"component:{component_id}",
                target_id=error_id,
                relationship="detected_in"
            ))
            
            # Error occurred during operation
            await self._graph.add_edge(TracebackEdge(
                source_id=f"operation:{component_id}:{operation}",
                target_id=error_id,
                relationship="occurred_during"
            ))
            
            # Check for parent error
            parent_error_id = context.get("parent_error_id")
            if parent_error_id:
                # This error was caused by another error
                if await self._graph.get_node(parent_error_id):
                    await self._graph.add_edge(TracebackEdge(
                        source_id=parent_error_id,
                        target_id=error_id,
                        relationship="caused"
                    ))
            
            # Link to resources if mentioned
            resource_id = context.get("resource_id")
            if resource_id:
                resource_node = TracebackNode(
                    node_id=f"resource:{resource_id}",
                    node_type=TracebackNodeType.RESOURCE,
                    label=resource_id,
                    metadata={"resource_id": resource_id}
                )
                await self._graph.add_node(resource_node)
                
                await self._graph.add_edge(TracebackEdge(
                    source_id=f"resource:{resource_id}",
                    target_id=error_id,
                    relationship="affected_resource"
                ))
            
            # Emit trace event
            if self._event_queue:
                trace = await self._graph.get_error_trace(error_id)
                await self._event_queue.emit(
                    "error_trace_updated",
                    {
                        "error_id": error_id,
                        "trace": trace,
                        "timestamp": datetime.now().isoformat()
                    }
                )
            
        except Exception as e:
            logger.error(f"Error handling error event: {e}", exc_info=True)
    
    async def _handle_resolution_event(self, event_data: Dict[str, Any]):
        """Process error resolution events"""
        try:
            error_id = event_data.get("error_id")
            if not error_id:
                return
            
            error_node = await self._graph.get_node(error_id)
            if error_node:
                # Update the error node metadata
                error_node.metadata["resolved"] = True
                error_node.metadata["resolution_time"] = datetime.now().isoformat()
                error_node.metadata["resolution_info"] = event_data.get("recovery_info", {})
            
            # Emit updated trace
            if self._event_queue and error_node:
                trace = await self._graph.get_error_trace(error_id)
                await self._event_queue.emit(
                    "error_trace_updated",
                    {
                        "error_id": error_id,
                        "trace": trace,
                        "resolved": True,
                        "timestamp": datetime.now().isoformat()
                    }
                )
                
        except Exception as e:
            logger.error(f"Error handling resolution event: {e}", exc_info=True)
    
    async def _handle_phase_transition(self, event_data: Dict[str, Any]):
        """Track phase transitions for context in error traces"""
        try:
            from_phase = event_data.get("from_phase", "unknown")
            to_phase = event_data.get("to_phase", "unknown")
            transition_id = f"transition:{from_phase}_to_{to_phase}:{datetime.now().timestamp()}"
            
            # Create transition node
            transition_node = TracebackNode(
                node_id=transition_id,
                node_type=TracebackNodeType.TRANSITION,
                label=f"Transition from {from_phase} to {to_phase}",
                metadata=event_data
            )
            await self._graph.add_node(transition_node)
            
        except Exception as e:
            logger.error(f"Error handling phase transition: {e}", exc_info=True)
    
    async def _handle_checkpoint_event(self, event_data: Dict[str, Any]):
        """Track checkpoints for context in error traces"""
        try:
            checkpoint_id = event_data.get("checkpoint_id", f"checkpoint:{datetime.now().timestamp()}")
            
            # Create checkpoint node
            checkpoint_node = TracebackNode(
                node_id=checkpoint_id,
                node_type=TracebackNodeType.CHECKPOINT,
                label=f"Checkpoint {checkpoint_id}",
                metadata=event_data
            )
            await self._graph.add_node(checkpoint_node)
            
        except Exception as e:
            logger.error(f"Error handling checkpoint event: {e}", exc_info=True)
    
    async def trace_error(self, error: Exception, component_id: str, operation: str) -> str:
        """
        Register error in the traceback system and return error ID.
        Can be called directly for custom error tracing.
        """
        # Generate error_id
        error_id = f"error:{component_id}:{operation}:{datetime.now().timestamp()}"
        
        # Get correlation ID if available
        correlation_id = getattr(error, 'correlation_id', str(uuid.uuid4()))
        
        # Get parent error ID if available
        parent_error_id = None
        if hasattr(error, 'context') and hasattr(error.context, 'parent_error_id'):
            parent_error_id = error.context.parent_error_id
        
        # Extract error details
        error_type = type(error).__name__
        error_message = str(error)
        tb = getattr(error, '__traceback__', None)
        stacktrace = ''.join(traceback.format_tb(tb)) if tb else "No traceback available"
        
        # Add error node
        error_node = TracebackNode(
            node_id=error_id,
            node_type=TracebackNodeType.ERROR,
            label=f"{error_type} in {component_id}",
            metadata={
                "error_type": error_type,
                "severity": getattr(error, 'severity', "UNKNOWN"),
                "message": error_message,
                "stacktrace": stacktrace,
                "correlation_id": correlation_id,
                "component_id": component_id,
                "operation": operation
            }
        )
        await self._graph.add_node(error_node)
        
        # Add component and operation nodes
        component_node = TracebackNode(
            node_id=f"component:{component_id}",
            node_type=TracebackNodeType.COMPONENT,
            label=component_id,
            metadata={"component_id": component_id}
        )
        await self._graph.add_node(component_node)
        
        operation_node = TracebackNode(
            node_id=f"operation:{component_id}:{operation}",
            node_type=TracebackNodeType.OPERATION,
            label=f"{operation} in {component_id}",
            metadata={"component_id": component_id, "operation": operation}
        )
        await self._graph.add_node(operation_node)
        
        # Create relationships
        await self._graph.add_edge(TracebackEdge(
            source_id=f"component:{component_id}",
            target_id=error_id,
            relationship="detected_in"
        ))
        
        await self._graph.add_edge(TracebackEdge(
            source_id=f"operation:{component_id}:{operation}",
            target_id=error_id,
            relationship="occurred_during"
        ))
        
        # Link to parent error if available
        if parent_error_id and await self._graph.get_node(parent_error_id):
            await self._graph.add_edge(TracebackEdge(
                source_id=parent_error_id,
                target_id=error_id,
                relationship="caused"
            ))
        
        # Link to resource if available
        if hasattr(error, 'resource_id'):
            resource_id = error.resource_id
            resource_node = TracebackNode(
                node_id=f"resource:{resource_id}",
                node_type=TracebackNodeType.RESOURCE,
                label=resource_id,
                metadata={"resource_id": resource_id}
            )
            await self._graph.add_node(resource_node)
            
            await self._graph.add_edge(TracebackEdge(
                source_id=f"resource:{resource_id}",
                target_id=error_id,
                relationship="affected_resource"
            ))
        
        # Emit trace event
        if self._event_queue:
            trace = await self._graph.get_error_trace(error_id)
            await self._event_queue.emit(
                "error_trace_created",
                {
                    "error_id": error_id,
                    "trace": trace,
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        return error_id
    
    async def find_root_cause(self, error_id: str) -> Dict[str, Any]:
        """
        Attempt to identify the root cause of an error by analyzing the error graph.
        Returns comprehensive information about the suspected root cause.
        """
        # Get the error node
        error_node = await self._graph.get_node(error_id)
        if not error_node or error_node.node_type != TracebackNodeType.ERROR:
            return {"error": "Invalid error ID", "error_id": error_id}
        
        # Find potential root causes
        root_ids = await self._graph.find_roots(error_id)
        if not root_ids:
            return {
                "error_id": error_id,
                "root_cause": "unknown",
                "analysis": "No root cause could be determined from the error graph"
            }
        
        # Get the furthest error upchain (root cause)
        root_causes = []
        for root_id in root_ids:
            node = await self._graph.get_node(root_id)
            if node and node.node_type == TracebackNodeType.ERROR:
                root_causes.append({
                    "error_id": root_id,
                    "error_type": node.metadata.get("error_type", "unknown"),
                    "component_id": node.metadata.get("component_id", "unknown"),
                    "operation": node.metadata.get("operation", "unknown"),
                    "timestamp": node.timestamp.isoformat(),
                    "message": node.metadata.get("message", ""),
                    "severity": node.metadata.get("severity", "UNKNOWN")
                })
        
        # Get components and operations involved
        components = set()
        operations = set()
        
        for root_id in root_ids:
            node = await self._graph.get_node(root_id)
            if not node:
                continue
                
            # Check connected components and operations
            edges = await self._graph.get_outgoing_edges(root_id)
            for edge in edges:
                target_node = await self._graph.get_node(edge.target_id)
                if target_node:
                    if target_node.node_type == TracebackNodeType.COMPONENT:
                        components.add(target_node.label)
                    elif target_node.node_type == TracebackNodeType.OPERATION:
                        operations.add(target_node.label)
        
        # Compile results
        result = {
            "error_id": error_id,
            "root_causes": root_causes,
            "components_involved": list(components),
            "operations_involved": list(operations),
            "analysis_timestamp": datetime.now().isoformat()
        }
        
        return result
    
    async def get_error_trace(self, error_id: str) -> Dict[str, Any]:
        """Get the full error trace for an error"""
        return await self._graph.get_error_trace(error_id)
    
    async def find_recent_similar_errors(self, error_type: str, component_id: str, 
                                      time_window: timedelta = timedelta(hours=1)) -> List[Dict[str, Any]]:
        """Find recent similar errors for pattern recognition"""
        cutoff = datetime.now() - time_window
        
        # Get all error nodes
        error_nodes = await self._graph.get_nodes_by_type(TracebackNodeType.ERROR)
        
        # Filter by time, error type, and component
        similar_errors = []
        for node in error_nodes:
            if (node.timestamp >= cutoff and 
                node.metadata.get("error_type") == error_type and
                node.metadata.get("component_id") == component_id):
                similar_errors.append({
                    "error_id": node.node_id,
                    "timestamp": node.timestamp.isoformat(),
                    "message": node.metadata.get("message", ""),
                    "operation": node.metadata.get("operation", "unknown"),
                    "resolved": node.metadata.get("resolved", False)
                })
        
        return similar_errors
    
    async def analyze_error_patterns(self) -> Dict[str, Any]:
        """
        Analyze error patterns across the system to identify recurring issues.
        This can be used for proactive system monitoring and improvement.
        """
        # Get all error nodes from last 24 hours
        cutoff = datetime.now() - timedelta(hours=24)
        error_nodes = await self._graph.get_nodes_by_type(TracebackNodeType.ERROR)
        recent_errors = [node for node in error_nodes if node.timestamp >= cutoff]
        
        # Group by component and error type
        component_errors = defaultdict(lambda: defaultdict(list))
        for node in recent_errors:
            component = node.metadata.get("component_id", "unknown")
            error_type = node.metadata.get("error_type", "unknown")
            component_errors[component][error_type].append(node)
        
        # Analyze patterns
        patterns = []
        for component, error_types in component_errors.items():
            for error_type, errors in error_types.items():
                if len(errors) >= 3:  # Consider it a pattern if seen 3+ times
                    patterns.append({
                        "component": component,
                        "error_type": error_type,
                        "count": len(errors),
                        "first_seen": min(error.timestamp for error in errors).isoformat(),
                        "last_seen": max(error.timestamp for error in errors).isoformat(),
                        "error_ids": [error.node_id for error in errors]
                    })
        
        # Sort patterns by count (most frequent first)
        patterns.sort(key=lambda x: x["count"], reverse=True)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "time_window": "24 hours",
            "total_errors": len(recent_errors),
            "patterns": patterns
        }
    
    async def visualize_error_graph(self, error_id: str = None) -> Dict[str, Any]:
        """
        Generate data for visualizing the error graph.
        If error_id is provided, only include nodes connected to that error.
        This can be used to create graphical representations of error relationships.
        """
        nodes_to_include = set()
        edges_to_include = []
        
        if error_id:
            # Get connected nodes (both up and down the chain)
            roots = await self._graph.find_roots(error_id)
            impacts = await self._graph.find_impact(error_id)
            
            # Include the error node itself
            nodes_to_include.add(error_id)
            
            # Include roots and their connections
            for root_id in roots:
                nodes_to_include.add(root_id)
                # Get path from root to error
                # (simplified - a real implementation would trace the full path)
                edges_to_include.append({
                    "source": root_id,
                    "target": error_id,
                    "relationship": "leads_to"
                })
            
            # Include impacts and their connections
            for impact_id in impacts:
                nodes_to_include.add(impact_id)
                edges_to_include.append({
                    "source": error_id,
                    "target": impact_id,
                    "relationship": "impacts"
                })
            
        else:
            # Include all error nodes and their direct connections
            error_nodes = await self._graph.get_nodes_by_type(TracebackNodeType.ERROR)
            for node in error_nodes:
                nodes_to_include.add(node.node_id)
                
                # Get incoming and outgoing edges
                incoming = await self._graph.get_incoming_edges(node.node_id)
                outgoing = await self._graph.get_outgoing_edges(node.node_id)
                
                # Add connected nodes and edges
                for edge in incoming:
                    nodes_to_include.add(edge.source_id)
                    edges_to_include.append({
                        "source": edge.source_id,
                        "target": node.node_id,
                        "relationship": edge.relationship
                    })
                
                for edge in outgoing:
                    nodes_to_include.add(edge.target_id)
                    edges_to_include.append({
                        "source": node.node_id,
                        "target": edge.target_id, 
                        "relationship": edge.relationship
                    })
        
        # Get node details
        nodes = []
        for node_id in nodes_to_include:
            node = await self._graph.get_node(node_id)
            if node:
                nodes.append({
                    "id": node.node_id,
                    "type": node.node_type.value,
                    "label": node.label,
                    "timestamp": node.timestamp.isoformat(),
                    "metadata": node.metadata
                })
        
        return {
            "nodes": nodes,
            "edges": edges_to_include,
            "timestamp": datetime.now().isoformat(),
            "focused_error": error_id
        }