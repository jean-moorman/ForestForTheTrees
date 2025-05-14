from datetime import datetime
from typing import Dict, Any, Optional, List, Set
import asyncio
import logging
import threading
import uuid
import sys

from resources.events import ResourceEventTypes, EventQueue
from resources.managers.registry import CircuitBreakerRegistry

logger = logging.getLogger(__name__)

class ResourceCoordinator:
    """Centralized coordinator for all resource managers with dependency-aware initialization and shutdown."""
    
    _instance = None
    _lock = threading.RLock()
    
    def __new__(cls, event_queue=None):
        """Singleton implementation with thread safety."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ResourceCoordinator, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self, event_queue):
        """Initialize the resource coordinator."""
        # Only initialize once
        if self._initialized:
            return
            
        with self._lock:
            if not self._initialized:
                self.event_queue = event_queue
                self._managers = {}
                self._dependencies = {}
                self._initialization_order = []
                self._shutdown_order = []
                self._initialized = False
                self._shutting_down = False
                
                # Enhanced dependency tracking
                self._dependency_graph = {}  # For visualization and cycle detection
                self._optional_dependencies = {}  # Dependencies that can be missing
                self._required_dependencies = {}  # Dependencies that must be present
                
                # Component metadata for debugging
                self._component_metadata = {}
                
                # Circuit breaker registry integration
                self._circuit_registry = CircuitBreakerRegistry(event_queue)
                
                # Initialization state tracking
                self._initialization_state = {}  # manager_id -> state (not_started, in_progress, complete, failed)
                
                # Register with EventLoopManager for proper lifecycle management
                from resources.events import EventLoopManager
                EventLoopManager.register_resource("resource_coordinator", self)
                
                self._initialized = True
                logger.debug("ResourceCoordinator initialized")
        
    def register_manager(self, manager_id, manager, dependencies=None, optional_dependencies=None):
        """Register a resource manager with the coordinator with enhanced dependency tracking.
        
        Args:
            manager_id: Unique identifier for the manager
            manager: The manager instance
            dependencies: List of required manager IDs this manager depends on
            optional_dependencies: List of optional manager IDs this manager can use if available
        """
        self._managers[manager_id] = manager
        
        # Store specific dependency types
        self._required_dependencies[manager_id] = dependencies or []
        self._optional_dependencies[manager_id] = optional_dependencies or []
        
        # Combine all dependencies for backward compatibility
        all_dependencies = list(set((dependencies or []) + (optional_dependencies or [])))
        self._dependencies[manager_id] = all_dependencies
        
        # Update dependency graph for visualization
        self._dependency_graph[manager_id] = {
            "required": self._required_dependencies[manager_id],
            "optional": self._optional_dependencies[manager_id]
        }
        
        # Store component metadata
        self._component_metadata[manager_id] = {
            "class": manager.__class__.__name__,
            "register_time": datetime.now().isoformat(),
            "initialized": False,
            "init_time": None,
            "shutdown_time": None
        }
        
        # Default initialization state
        self._initialization_state[manager_id] = "not_started"
        
        # If we've already initialized, initialize this manager now
        if self._initialized:
            async def _delayed_init():
                # Small delay to allow event loop to process other events
                await asyncio.sleep(0.1)
                await self._initialize_manager(manager_id)
                
            asyncio.create_task(_delayed_init())
            
        logger.debug(f"Registered manager {manager_id} with ResourceCoordinator")
        
    async def initialize_all(self):
        """Initialize all registered managers in dependency order with enhanced error handling."""
        if self._initialized:
            logger.warning("ResourceCoordinator already initialized")
            return
            
        logger.info("Starting initialization of all resource managers")
        
        # Calculate initialization order based on dependencies
        try:
            self._initialization_order = self._calculate_initialization_order()
            # Shutdown order is reverse of initialization
            self._shutdown_order = list(reversed(self._initialization_order))
        except Exception as e:
            logger.error(f"Error calculating initialization order: {e}")
            await self.event_queue.emit(
                ResourceEventTypes.RESOURCE_ERROR_OCCURRED.value,
                {
                    "resource_id": "resource_coordinator",
                    "operation": "calculate_initialization_order",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                },
                priority="high"
            )
            raise
        
        # Emit initialization started event
        await self.event_queue.emit(
            ResourceEventTypes.RESOURCE_STATE_CHANGED.value,
            {
                "resource_id": "resource_coordinator",
                "state": "initialization_started",
                "manager_count": len(self._managers),
                "initialization_order": self._initialization_order
            }
        )
        
        # Initialize managers in order with proper error handling
        initialization_results = []
        for manager_id in self._initialization_order:
            # Skip if any required dependency failed
            skip_manager = False
            for dep_id in self._required_dependencies.get(manager_id, []):
                if dep_id in initialization_results and not initialization_results[dep_id]:
                    logger.warning(f"Skipping {manager_id} due to failed dependency {dep_id}")
                    self._initialization_state[manager_id] = "skipped_dep_failure"
                    initialization_results.append((manager_id, False))
                    skip_manager = True
                    break
                    
            if skip_manager:
                continue
                
            # Initialize this manager
            self._initialization_state[manager_id] = "in_progress"
            result = await self._initialize_manager(manager_id)
            self._initialization_state[manager_id] = "complete" if result else "failed"
            initialization_results.append((manager_id, result))
            
            # Update metadata
            self._component_metadata[manager_id]["initialized"] = result
            self._component_metadata[manager_id]["init_time"] = datetime.now().isoformat()
            
            # On failure of critical component, consider stopping initialization
            if not result and manager_id in self._get_critical_managers():
                logger.error(f"Critical manager {manager_id} failed to initialize - stopping initialization")
                
                # Emit critical failure event
                await self.event_queue.emit(
                    ResourceEventTypes.RESOURCE_ERROR_OCCURRED.value,
                    {
                        "resource_id": "resource_coordinator",
                        "operation": "initialize_all",
                        "error": f"Critical manager {manager_id} failed to initialize",
                        "severity": "FATAL",
                        "timestamp": datetime.now().isoformat()
                    },
                    priority="high"
                )
                
                # Stop initializing further managers
                break
        
        # Calculate success rate
        success_count = sum(1 for _, result in initialization_results if result)
        total_count = len(initialization_results)
        
        # Update initialization state
        self._initialized = success_count > 0  # Consider initialized if at least one manager succeeded
        
        # Emit final initialization event
        await self.event_queue.emit(
            ResourceEventTypes.RESOURCE_STATE_CHANGED.value,
            {
                "resource_id": "resource_coordinator",
                "state": "initialized" if self._initialized else "initialization_failed",
                "success_count": success_count,
                "total_count": total_count,
                "success_rate": success_count / total_count if total_count > 0 else 0
            }
        )
        
        logger.info(f"Resource initialization completed: {success_count}/{total_count} managers initialized successfully")
        
    def _get_critical_managers(self):
        """Get the list of critical managers that must initialize successfully."""
        # This could be enhanced with configuration, but for now consider these core components critical
        return ["state_manager", "event_queue", "context_manager"]
        
    async def _initialize_manager(self, manager_id):
        """Initialize a specific manager with proper error handling and dependency verification."""
        manager = self._managers.get(manager_id)
        if not manager:
            logger.error(f"Cannot initialize unknown manager: {manager_id}")
            return False
            
        # Check if required dependencies are initialized
        for dep_id in self._required_dependencies.get(manager_id, []):
            if dep_id not in self._managers:
                logger.error(f"Required dependency {dep_id} for {manager_id} is not registered")
                return False
                
            # Check if dependency was successfully initialized
            if self._initialization_state.get(dep_id) != "complete":
                logger.error(f"Required dependency {dep_id} for {manager_id} is not initialized")
                return False
                
        # Emit initialization event
        try:
            await self.event_queue.emit(
                ResourceEventTypes.RESOURCE_STATE_CHANGED.value,
                {
                    "resource_id": manager_id,
                    "state": "initializing"
                }
            )
        except Exception as e:
            logger.error(f"Error emitting initialization event for {manager_id}: {e}")
            
        try:
            # Create initialization correlation ID for tracking
            correlation_id = f"init_{manager_id}_{str(uuid.uuid4())[:8]}"
            
            # Check if manager has start/initialize method
            if hasattr(manager, 'start') and callable(manager.start):
                logger.debug(f"Starting manager {manager_id} (correlation_id: {correlation_id})")
                await manager.start()
            elif hasattr(manager, 'initialize') and callable(manager.initialize):
                logger.debug(f"Initializing manager {manager_id} (correlation_id: {correlation_id})")
                await manager.initialize()
            else:
                logger.debug(f"Manager {manager_id} has no start/initialize method (correlation_id: {correlation_id})")
                
            # Register manager's circuit breaker with registry if it exists
            if hasattr(manager, '_circuit_breaker') and manager._circuit_breaker:
                try:
                    # Import here to avoid circular imports
                    from resources.monitoring import CircuitBreaker
                    
                    # Determine parent circuit if any
                    parent_circuit = None
                    for dep_id in self._required_dependencies.get(manager_id, []):
                        # Consider first dependency as parent for circuit cascading
                        parent_circuit = dep_id
                        break
                        
                    # Register with circuit breaker registry
                    await self._circuit_registry.register_circuit_breaker(
                        manager_id, 
                        manager._circuit_breaker,
                        parent=parent_circuit
                    )
                except Exception as e:
                    logger.error(f"Error registering circuit breaker for {manager_id}: {e}")
                
            # Emit successful initialization event
            await self.event_queue.emit(
                ResourceEventTypes.RESOURCE_STATE_CHANGED.value,
                {
                    "resource_id": manager_id,
                    "state": "initialized",
                    "correlation_id": correlation_id
                }
            )
            
            # Update component metadata
            self._component_metadata[manager_id]["initialized"] = True
            self._component_metadata[manager_id]["init_time"] = datetime.now().isoformat()
            self._component_metadata[manager_id]["correlation_id"] = correlation_id
            
            return True
        except Exception as e:
            logger.error(f"Error initializing manager {manager_id}: {e}")
            
            # Update component metadata
            self._component_metadata[manager_id]["initialized"] = False
            self._component_metadata[manager_id]["init_error"] = str(e)
            self._component_metadata[manager_id]["init_time"] = datetime.now().isoformat()
            
            # Emit error event
            await self.event_queue.emit(
                ResourceEventTypes.RESOURCE_ERROR_OCCURRED.value,
                {
                    "resource_id": manager_id,
                    "operation": "initialize",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            # Also emit state change for consistency
            await self.event_queue.emit(
                ResourceEventTypes.RESOURCE_STATE_CHANGED.value,
                {
                    "resource_id": manager_id,
                    "state": "initialization_failed",
                    "error": str(e)
                }
            )
            
            return False
            
    def _calculate_initialization_order(self):
        """Calculate initialization order based on dependencies using topological sort with cycle detection."""
        # Implementation of Kahn's algorithm with cycle detection
        
        # Build an adjacency list and in-degree count
        adjacency = {node: [] for node in self._managers}
        in_degree = {node: 0 for node in self._managers}
        
        # Fill adjacency list and in-degree count
        for node, deps in self._required_dependencies.items():
            for dep in deps:
                if dep in self._managers:  # Only consider registered dependencies
                    adjacency[dep].append(node)
                    in_degree[node] += 1
        
        # Start with nodes that have no dependencies
        queue = [node for node, count in in_degree.items() if count == 0]
        result = []
        
        # Process nodes with in-degree of 0
        while queue:
            node = queue.pop(0)
            result.append(node)
            
            # Reduce in-degree of neighbors
            for neighbor in adjacency[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # Check for cycles - if we haven't included all nodes, there must be a cycle
        if len(result) != len(self._managers):
            # Find the cycle to provide better error information
            cycle = self._find_dependency_cycle()
            if cycle:
                cycle_str = " -> ".join(cycle)
                logger.error(f"Circular dependency detected: {cycle_str}")
                raise ValueError(f"Circular dependency detected: {cycle_str}")
            else:
                unprocessed = set(self._managers.keys()) - set(result)
                logger.error(f"Unable to determine initialization order, unprocessed nodes: {unprocessed}")
                # Add remaining nodes to maintain backward compatibility
                result.extend(unprocessed)
        
        return result
    
    def _find_dependency_cycle(self):
        """Find and return a dependency cycle if one exists."""
        visited = set()
        path = []
        path_set = set()
        
        def dfs(node):
            # Already completely processed this node, no cycles here
            if node in visited:
                return None
                
            # Check if we're revisiting a node in the current path (cycle found)
            if node in path_set:
                # Return the cycle
                cycle_start = path.index(node)
                return path[cycle_start:] + [node]
                
            # Add node to current path
            path.append(node)
            path_set.add(node)
            
            # Process dependencies
            for dep in self._required_dependencies.get(node, []):
                if dep in self._managers:  # Only consider registered deps
                    cycle = dfs(dep)
                    if cycle:
                        return cycle
            
            # Remove from current path as we're done with this branch
            path.pop()
            path_set.remove(node)
            
            # Mark as fully visited (all paths explored)
            visited.add(node)
            
            # No cycle found
            return None
            
        # Check from each unvisited node
        for node in self._managers:
            if node not in visited:
                cycle = dfs(node)
                if cycle:
                    return cycle
                    
        return None
        
    async def shutdown(self):
        """Shut down all resource managers in reverse initialization order with enhanced reliability."""
        if self._shutting_down:
            logger.warning("ResourceCoordinator already shutting down")
            return
            
        self._shutting_down = True
        logger.info("Starting orderly shutdown of all resource managers")
        
        # Create shutdown correlation ID for tracking
        shutdown_id = f"shutdown_{str(uuid.uuid4())[:8]}"
        
        # Emit shutdown started event
        try:
            await self.event_queue.emit(
                ResourceEventTypes.RESOURCE_STATE_CHANGED.value,
                {
                    "resource_id": "resource_coordinator",
                    "state": "shutting_down",
                    "manager_count": len(self._managers),
                    "correlation_id": shutdown_id
                },
                priority="high"
            )
        except Exception as e:
            logger.error(f"Error emitting shutdown event: {e}")
        
        # If no explicit shutdown order is defined, use reverse initialization order
        if not self._shutdown_order:
            # If initialization order isn't defined either, use dependency-based calculation
            if not self._initialization_order:
                try:
                    self._initialization_order = self._calculate_initialization_order()
                except Exception as e:
                    logger.error(f"Error calculating initialization order for shutdown: {e}")
                    # Fall back to arbitrary order (all managers)
                    self._initialization_order = list(self._managers.keys())
                    
            # Reverse for shutdown
            self._shutdown_order = list(reversed(self._initialization_order))
        
        # Shutdown in reverse order
        shutdown_results = []
        for manager_id in self._shutdown_order:
            # Skip managers that were never initialized
            if self._initialization_state.get(manager_id) not in ["complete", "in_progress"]:
                logger.debug(f"Skipping shutdown of uninitialized manager {manager_id}")
                continue
                
            result = await self._shutdown_manager(manager_id)
            shutdown_results.append((manager_id, result))
            
            # Update metadata
            self._component_metadata[manager_id]["shutdown_time"] = datetime.now().isoformat()
            self._component_metadata[manager_id]["shutdown_success"] = result
        
        # Report results
        success_count = sum(1 for _, result in shutdown_results if result)
        total_count = len(shutdown_results)
        logger.info(f"Resource shutdown completed: {success_count}/{total_count} successful")
        
        # Emit final event even if event queue is shutting down
        try:
            await self.event_queue.emit(
                ResourceEventTypes.RESOURCE_STATE_CHANGED.value,
                {
                    "resource_id": "resource_coordinator",
                    "state": "shutdown_complete",
                    "success_count": success_count,
                    "total_count": total_count,
                    "correlation_id": shutdown_id
                },
                priority="high"
            )
        except Exception as e:
            logger.error(f"Error emitting final shutdown event: {e}")
        
        # Clean up registry
        try:
            # Reset all flags
            self._shutting_down = False
            self._initialized = False
            
            # Unregister from EventLoopManager
            from resources.events import EventLoopManager
            EventLoopManager.unregister_resource("resource_coordinator")
            
            # Explicitly stop circuit breaker registry
            if hasattr(self, '_circuit_registry'):
                await self._circuit_registry.stop()
                
        except Exception as e:
            logger.error(f"Error during final coordinator cleanup: {e}")
        
    async def _shutdown_manager(self, manager_id):
        """Shutdown a specific manager with timeout and error handling."""
        manager = self._managers.get(manager_id)
        if not manager:
            logger.warning(f"Cannot shutdown unknown manager: {manager_id}")
            return False
            
        try:
            logger.debug(f"Shutting down manager {manager_id}")
            
            # Emit shutdown event
            try:
                await self.event_queue.emit(
                    ResourceEventTypes.RESOURCE_STATE_CHANGED.value,
                    {
                        "resource_id": manager_id,
                        "state": "shutting_down"
                    }
                )
            except Exception as e:
                logger.error(f"Error emitting shutdown event for {manager_id}: {e}")
            
            # Check for stop/shutdown method with timeout
            if hasattr(manager, 'stop') and callable(manager.stop):
                try:
                    await asyncio.wait_for(manager.stop(), timeout=10.0)
                except asyncio.TimeoutError:
                    logger.warning(f"Timeout shutting down manager {manager_id}")
                except Exception as e:
                    logger.error(f"Error shutting down manager {manager_id}: {e}")
                    return False
            elif hasattr(manager, 'shutdown') and callable(manager.shutdown):
                try:
                    await asyncio.wait_for(manager.shutdown(), timeout=10.0)
                except asyncio.TimeoutError:
                    logger.warning(f"Timeout shutting down manager {manager_id}")
                except Exception as e:
                    logger.error(f"Error shutting down manager {manager_id}: {e}")
                    return False
            else:
                # No shutdown method available
                logger.debug(f"Manager {manager_id} has no stop/shutdown method")
                
            # Try to emit completion event, but may fail if event queue is already down
            try:
                await self.event_queue.emit(
                    ResourceEventTypes.RESOURCE_STATE_CHANGED.value,
                    {
                        "resource_id": manager_id,
                        "state": "shutdown_complete"
                    }
                )
            except Exception as e:
                logger.debug(f"Could not emit shutdown complete event for {manager_id}: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Unexpected error shutting down manager {manager_id}: {e}")
            return False
            
    def get_manager(self, manager_id):
        """Get a specific manager by ID."""
        return self._managers.get(manager_id)
        
    def get_all_managers(self):
        """Get all registered managers."""
        return dict(self._managers)
        
    def get_status(self):
        """Get detailed status of all managers with enhanced information."""
        # Basic status
        status = {
            "initialized": self._initialized,
            "shutting_down": self._shutting_down,
            "managers": list(self._managers.keys()),
            "initialization_order": self._initialization_order,
            "shutdown_order": self._shutdown_order,
            "manager_count": len(self._managers)
        }
        
        # Add dependency information
        status["dependencies"] = self._dependency_graph
        
        # Add component states
        status["component_states"] = {
            manager_id: {
                "initialization_state": self._initialization_state.get(manager_id, "unknown"),
                "metadata": self._component_metadata.get(manager_id, {})
            }
            for manager_id in self._managers
        }
        
        # Add circuit breaker information if available
        if hasattr(self, '_circuit_registry'):
            try:
                # Get synchronous status info for now
                circuit_status = {
                    name: {
                        "state": circuit.state.name if hasattr(circuit, 'state') else "UNKNOWN",
                        "parents": self._circuit_registry._reverse_dependencies.get(name, []),
                        "children": self._circuit_registry._relationships.get(name, [])
                    }
                    for name, circuit in self._circuit_registry._circuit_breakers.items()
                }
                status["circuit_breakers"] = circuit_status
            except Exception as e:
                logger.error(f"Error getting circuit breaker status: {e}")
                status["circuit_breakers"] = {"error": str(e)}
        
        return status