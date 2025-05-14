"""
Phase Communication Broker for Phase Two
-------------------------------------
Implements standard message formats, callbacks for phase transitions,
secure context sharing, and timeout/heartbeat mechanisms.
"""

import logging
import asyncio
import uuid
import json
from typing import Dict, Any, List, Optional, Callable, Awaitable, Set, Union
from datetime import datetime, timedelta
import time

from resources import (
    EventQueue,
    StateManager,
    MetricsManager,
    PhaseCoordinationIntegration,
    PhaseType,
    ResourceEventTypes
)

logger = logging.getLogger(__name__)

# Type for message handlers
MessageHandler = Callable[[Dict[str, Any]], Awaitable[Optional[Dict[str, Any]]]]

# Standard message types
class MessageType:
    # Control messages
    HEARTBEAT = "heartbeat"
    PHASE_TRANSITION = "phase_transition"
    STATUS_REQUEST = "status_request"
    STATUS_RESPONSE = "status_response"
    
    # Data messages
    CONTEXT_SHARED = "context_shared"
    CONTEXT_REQUEST = "context_request"
    CONTEXT_RESPONSE = "context_response"
    
    # Event messages
    PHASE_STARTED = "phase_started"
    PHASE_COMPLETED = "phase_completed"
    PHASE_FAILED = "phase_failed"
    
    # Custom messages
    CUSTOM = "custom"

class PhaseCommunicationBroker:
    """
    Manages communication between phases.
    
    This class provides:
    1. Standard message formats for cross-phase communication
    2. Callbacks for phase transition events
    3. Secure context sharing between phases
    4. Timeout and heartbeat mechanisms
    """
    
    def __init__(self,
                 event_queue: EventQueue,
                 state_manager: StateManager,
                 metrics_manager: MetricsManager,
                 phase_coordination: PhaseCoordinationIntegration,
                 heartbeat_interval_seconds: int = 30,
                 message_timeout_seconds: int = 60):
        """
        Initialize the PhaseCommunicationBroker.
        
        Args:
            event_queue: EventQueue for emitting events
            state_manager: StateManager for state persistence
            metrics_manager: MetricsManager for metrics recording
            phase_coordination: PhaseCoordinationIntegration for coordination
            heartbeat_interval_seconds: Interval between heartbeats in seconds
            message_timeout_seconds: Timeout for message responses in seconds
        """
        self._event_queue = event_queue
        self._state_manager = state_manager
        self._metrics_manager = metrics_manager
        self._phase_coordination = phase_coordination
        self._heartbeat_interval = heartbeat_interval_seconds
        self._message_timeout = message_timeout_seconds
        
        # Store message handlers by type
        self._message_handlers: Dict[str, List[MessageHandler]] = {}
        
        # Store phase-specific context
        self._phase_contexts: Dict[str, Dict[str, Any]] = {}
        
        # Store pending callbacks for responses
        self._pending_responses: Dict[str, asyncio.Future] = {}
        
        # Store active phase connections
        self._active_phases: Dict[str, Dict[str, Any]] = {}
        
        # Store message history
        self._message_history: Dict[str, List[Dict[str, Any]]] = {}
        
        # Background task for heartbeats
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._running = False
        
        logger.info(f"PhaseCommunicationBroker initialized with heartbeat_interval={heartbeat_interval_seconds}s")
    
    async def start(self) -> None:
        """Start the communication broker."""
        if self._running:
            return
        
        self._running = True
        
        # Start heartbeat task
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        
        # Register to receive events
        await self._event_queue.subscribe(
            ResourceEventTypes.PHASE_COORDINATION_EVENT.value,
            self._handle_coordination_event
        )
        
        logger.info("PhaseCommunicationBroker started")
    
    async def stop(self) -> None:
        """Stop the communication broker."""
        if not self._running:
            return
        
        self._running = False
        
        # Cancel heartbeat task
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
        
        # Unregister event handler
        await self._event_queue.unsubscribe(
            ResourceEventTypes.PHASE_COORDINATION_EVENT.value,
            self._handle_coordination_event
        )
        
        logger.info("PhaseCommunicationBroker stopped")
    
    async def register_phase(self,
                           phase_id: str,
                           phase_type: PhaseType,
                           metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Register a phase with the communication broker.
        
        Args:
            phase_id: ID of the phase
            phase_type: Type of the phase
            metadata: Optional metadata about the phase
            
        Returns:
            Dictionary with registration result
        """
        # Registration info
        registration = {
            "phase_id": phase_id,
            "phase_type": phase_type.value if hasattr(phase_type, "value") else str(phase_type),
            "registered_at": datetime.now().isoformat(),
            "last_heartbeat": datetime.now().isoformat(),
            "metadata": metadata or {},
            "status": "active"
        }
        
        # Store registration
        self._active_phases[phase_id] = registration
        
        # Initialize message history
        self._message_history[phase_id] = []
        
        # Emit registration event
        await self._event_queue.emit(
            ResourceEventTypes.PHASE_COORDINATION_EVENT.value,
            {
                "event_type": "phase_registered",
                "phase_id": phase_id,
                "phase_type": registration["phase_type"],
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # Record metric
        await self._metrics_manager.record_metric(
            "phase_two:communication:phase_registered",
            1.0,
            metadata={
                "phase_id": phase_id,
                "phase_type": registration["phase_type"]
            }
        )
        
        logger.info(f"Registered phase {phase_id} of type {registration['phase_type']}")
        
        return {
            "success": True,
            "phase_id": phase_id,
            "registered_at": registration["registered_at"]
        }
    
    async def unregister_phase(self, phase_id: str) -> Dict[str, Any]:
        """
        Unregister a phase from the communication broker.
        
        Args:
            phase_id: ID of the phase to unregister
            
        Returns:
            Dictionary with unregistration result
        """
        # Check if phase exists
        if phase_id not in self._active_phases:
            return {
                "success": False,
                "phase_id": phase_id,
                "message": f"Phase {phase_id} not found"
            }
        
        # Get phase info
        phase_info = self._active_phases[phase_id]
        
        # Remove from active phases
        del self._active_phases[phase_id]
        
        # Emit unregistration event
        await self._event_queue.emit(
            ResourceEventTypes.PHASE_COORDINATION_EVENT.value,
            {
                "event_type": "phase_unregistered",
                "phase_id": phase_id,
                "phase_type": phase_info["phase_type"],
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # Record metric
        await self._metrics_manager.record_metric(
            "phase_two:communication:phase_unregistered",
            1.0,
            metadata={
                "phase_id": phase_id,
                "phase_type": phase_info["phase_type"]
            }
        )
        
        logger.info(f"Unregistered phase {phase_id}")
        
        return {
            "success": True,
            "phase_id": phase_id,
            "unregistered_at": datetime.now().isoformat()
        }
    
    async def send_message(self,
                         source_phase_id: str,
                         target_phase_id: str,
                         message_type: str,
                         payload: Dict[str, Any],
                         expect_response: bool = False,
                         timeout_seconds: Optional[int] = None) -> Dict[str, Any]:
        """
        Send a message from one phase to another.
        
        Args:
            source_phase_id: ID of the source phase
            target_phase_id: ID of the target phase
            message_type: Type of message (use MessageType constants)
            payload: Message payload
            expect_response: Whether to expect a response
            timeout_seconds: Optional timeout in seconds
            
        Returns:
            Dictionary with send result or response
        """
        # Check if source phase is registered
        if source_phase_id not in self._active_phases:
            return {
                "success": False,
                "message": f"Source phase {source_phase_id} not registered",
                "message_id": None
            }
        
        # Check if target phase is registered
        if target_phase_id not in self._active_phases:
            return {
                "success": False,
                "message": f"Target phase {target_phase_id} not registered",
                "message_id": None
            }
        
        # Generate message ID
        message_id = f"msg_{uuid.uuid4().hex}"
        
        # Create message
        message = {
            "message_id": message_id,
            "source_phase_id": source_phase_id,
            "target_phase_id": target_phase_id,
            "message_type": message_type,
            "payload": payload,
            "timestamp": datetime.now().isoformat(),
            "expects_response": expect_response
        }
        
        # Store in message history
        self._message_history[source_phase_id].append(message)
        
        # Create response future if expecting response
        response_future = None
        if expect_response:
            response_future = asyncio.Future()
            self._pending_responses[message_id] = response_future
        
        # Emit message event
        await self._event_queue.emit(
            ResourceEventTypes.PHASE_COORDINATION_EVENT.value,
            {
                "event_type": "phase_message",
                "message_id": message_id,
                "source_phase_id": source_phase_id,
                "target_phase_id": target_phase_id,
                "message_type": message_type,
                "timestamp": datetime.now().isoformat(),
                "payload": payload
            }
        )
        
        # Record metric
        await self._metrics_manager.record_metric(
            "phase_two:communication:message_sent",
            1.0,
            metadata={
                "message_id": message_id,
                "source_phase_id": source_phase_id,
                "target_phase_id": target_phase_id,
                "message_type": message_type,
                "expects_response": expect_response
            }
        )
        
        # If expecting response, wait for it
        if expect_response:
            timeout = timeout_seconds or self._message_timeout
            try:
                response = await asyncio.wait_for(response_future, timeout=timeout)
                
                # Record response metric
                await self._metrics_manager.record_metric(
                    "phase_two:communication:response_received",
                    1.0,
                    metadata={
                        "message_id": message_id,
                        "source_phase_id": source_phase_id,
                        "target_phase_id": target_phase_id,
                        "response_time_ms": (datetime.now() - datetime.fromisoformat(message["timestamp"])).total_seconds() * 1000
                    }
                )
                
                return response
            except asyncio.TimeoutError:
                # Remove pending response
                if message_id in self._pending_responses:
                    del self._pending_responses[message_id]
                
                # Record timeout metric
                await self._metrics_manager.record_metric(
                    "phase_two:communication:response_timeout",
                    1.0,
                    metadata={
                        "message_id": message_id,
                        "source_phase_id": source_phase_id,
                        "target_phase_id": target_phase_id,
                        "timeout_seconds": timeout
                    }
                )
                
                return {
                    "success": False,
                    "message": f"Response timeout after {timeout} seconds",
                    "message_id": message_id
                }
        
        return {
            "success": True,
            "message_id": message_id
        }
    
    async def respond_to_message(self,
                               message_id: str,
                               response_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Respond to a received message.
        
        Args:
            message_id: ID of the message to respond to
            response_payload: Response payload
            
        Returns:
            Dictionary with response result
        """
        # Check if message is pending response
        if message_id not in self._pending_responses:
            return {
                "success": False,
                "message": f"Message {message_id} not found or not expecting response"
            }
        
        # Get response future
        response_future = self._pending_responses[message_id]
        
        # Set response payload with success status
        response = {
            "success": True,
            "message_id": message_id,
            "payload": response_payload,
            "timestamp": datetime.now().isoformat()
        }
        
        # Set result
        response_future.set_result(response)
        
        # Remove from pending responses
        del self._pending_responses[message_id]
        
        # Record metric
        await self._metrics_manager.record_metric(
            "phase_two:communication:response_sent",
            1.0,
            metadata={
                "message_id": message_id
            }
        )
        
        return {
            "success": True,
            "message_id": message_id
        }
    
    async def register_message_handler(self,
                                     message_type: str,
                                     handler: MessageHandler) -> None:
        """
        Register a handler for messages of a specific type.
        
        Args:
            message_type: Type of message to handle
            handler: Function to handle messages
        """
        # Initialize handler list if needed
        if message_type not in self._message_handlers:
            self._message_handlers[message_type] = []
        
        # Add handler
        self._message_handlers[message_type].append(handler)
        
        logger.info(f"Registered handler for message type {message_type}")
    
    async def unregister_message_handler(self,
                                       message_type: str,
                                       handler: MessageHandler) -> bool:
        """
        Unregister a message handler.
        
        Args:
            message_type: Type of message handled
            handler: Handler function to unregister
            
        Returns:
            True if handler was unregistered
        """
        # Check if message type has handlers
        if message_type not in self._message_handlers:
            return False
        
        # Check if handler is registered
        if handler not in self._message_handlers[message_type]:
            return False
        
        # Remove handler
        self._message_handlers[message_type].remove(handler)
        
        # Remove empty handler lists
        if not self._message_handlers[message_type]:
            del self._message_handlers[message_type]
        
        logger.info(f"Unregistered handler for message type {message_type}")
        
        return True
    
    async def share_context(self,
                          source_phase_id: str,
                          target_phase_id: str,
                          context_data: Dict[str, Any],
                          context_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Share context from one phase to another.
        
        Args:
            source_phase_id: ID of the source phase
            target_phase_id: ID of the target phase
            context_data: Context data to share
            context_id: Optional context identifier
            
        Returns:
            Dictionary with sharing result
        """
        # Generate context ID if not provided
        if not context_id:
            context_id = f"ctx_{uuid.uuid4().hex}"
        
        # Create context key
        context_key = f"{source_phase_id}_to_{target_phase_id}_{context_id}"
        
        # Store context
        if target_phase_id not in self._phase_contexts:
            self._phase_contexts[target_phase_id] = {}
        
        self._phase_contexts[target_phase_id][context_key] = {
            "context_id": context_id,
            "source_phase_id": source_phase_id,
            "target_phase_id": target_phase_id,
            "data": context_data,
            "shared_at": datetime.now().isoformat()
        }
        
        # Send context shared message
        await self.send_message(
            source_phase_id,
            target_phase_id,
            MessageType.CONTEXT_SHARED,
            {
                "context_id": context_id,
                "context_key": context_key,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # Record metric
        await self._metrics_manager.record_metric(
            "phase_two:communication:context_shared",
            1.0,
            metadata={
                "context_id": context_id,
                "source_phase_id": source_phase_id,
                "target_phase_id": target_phase_id,
                "context_size_bytes": len(json.dumps(context_data))
            }
        )
        
        return {
            "success": True,
            "context_id": context_id,
            "context_key": context_key
        }
    
    async def get_shared_context(self,
                               phase_id: str,
                               context_id: str,
                               source_phase_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get shared context for a phase.
        
        Args:
            phase_id: ID of the phase requesting context
            context_id: ID of the context
            source_phase_id: Optional source phase ID to filter
            
        Returns:
            Dictionary with context data
        """
        # Check if phase has any context
        if phase_id not in self._phase_contexts:
            return {
                "success": False,
                "message": f"No context found for phase {phase_id}"
            }
        
        # Find matching context
        matching_contexts = []
        for context_key, context in self._phase_contexts[phase_id].items():
            if context["context_id"] == context_id:
                if source_phase_id is None or context["source_phase_id"] == source_phase_id:
                    matching_contexts.append(context)
        
        # If no matching context found
        if not matching_contexts:
            return {
                "success": False,
                "message": f"Context {context_id} not found for phase {phase_id}"
            }
        
        # Return the most recent matching context
        context = max(matching_contexts, key=lambda c: c["shared_at"])
        
        # Record metric
        await self._metrics_manager.record_metric(
            "phase_two:communication:context_accessed",
            1.0,
            metadata={
                "context_id": context_id,
                "phase_id": phase_id,
                "source_phase_id": context["source_phase_id"]
            }
        )
        
        return {
            "success": True,
            "context_id": context_id,
            "context": context
        }
    
    async def get_active_phases(self) -> Dict[str, Any]:
        """
        Get information about all active phases.
        
        Returns:
            Dictionary with active phases information
        """
        # Get current time
        now = datetime.now()
        
        # Check for inactive phases
        inactive_phases = []
        for phase_id, phase_info in self._active_phases.items():
            # Convert last heartbeat to datetime
            last_heartbeat = datetime.fromisoformat(phase_info["last_heartbeat"])
            
            # Check if phase has missed too many heartbeats (3x interval)
            if (now - last_heartbeat).total_seconds() > self._heartbeat_interval * 3:
                phase_info["status"] = "inactive"
                inactive_phases.append(phase_id)
        
        # Count phases by type
        phase_types = {}
        for phase_info in self._active_phases.values():
            phase_type = phase_info["phase_type"]
            if phase_type not in phase_types:
                phase_types[phase_type] = 0
            phase_types[phase_type] += 1
        
        return {
            "active_count": len(self._active_phases) - len(inactive_phases),
            "inactive_count": len(inactive_phases),
            "total_count": len(self._active_phases),
            "phases_by_type": phase_types,
            "phases": self._active_phases,
            "timestamp": now.isoformat()
        }
    
    async def get_message_history(self,
                                phase_id: Optional[str] = None,
                                limit: int = 100) -> Dict[str, Any]:
        """
        Get message history.
        
        Args:
            phase_id: Optional phase ID to filter history
            limit: Maximum number of messages to return
            
        Returns:
            Dictionary with message history
        """
        if phase_id:
            # Get history for specific phase
            if phase_id not in self._message_history:
                return {
                    "success": False,
                    "message": f"No message history for phase {phase_id}"
                }
            
            messages = self._message_history[phase_id][-limit:]
            
            return {
                "success": True,
                "phase_id": phase_id,
                "message_count": len(messages),
                "messages": messages
            }
        else:
            # Get history for all phases
            all_messages = []
            for phase_messages in self._message_history.values():
                all_messages.extend(phase_messages)
            
            # Sort by timestamp
            all_messages.sort(key=lambda m: m["timestamp"], reverse=True)
            
            # Limit number of messages
            all_messages = all_messages[:limit]
            
            return {
                "success": True,
                "phase_count": len(self._message_history),
                "message_count": len(all_messages),
                "messages": all_messages
            }
    
    async def _heartbeat_loop(self) -> None:
        """Background task to send heartbeats and check for inactive phases."""
        while self._running:
            try:
                # Get current time
                now = datetime.now()
                
                # Send heartbeats to all active phases
                for phase_id, phase_info in list(self._active_phases.items()):
                    # Skip inactive phases
                    if phase_info["status"] == "inactive":
                        continue
                    
                    # Check if phase is really active
                    await self._send_heartbeat(phase_id)
                
                # Wait for next interval
                await asyncio.sleep(self._heartbeat_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {str(e)}")
                await asyncio.sleep(5)  # Short delay before retry
    
    async def _send_heartbeat(self, phase_id: str) -> None:
        """
        Send a heartbeat to a phase.
        
        Args:
            phase_id: ID of the phase
        """
        try:
            # Get phase info
            phase_info = self._active_phases[phase_id]
            
            # Send heartbeat message
            await self.send_message(
                "phase_communication_broker",
                phase_id,
                MessageType.HEARTBEAT,
                {
                    "timestamp": datetime.now().isoformat(),
                    "interval_seconds": self._heartbeat_interval
                },
                expect_response=False
            )
            
            # Update last heartbeat time
            phase_info["last_heartbeat"] = datetime.now().isoformat()
            
        except Exception as e:
            logger.error(f"Error sending heartbeat to phase {phase_id}: {str(e)}")
    
    async def _handle_coordination_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        """
        Handle phase coordination events.
        
        Args:
            event_type: Type of event
            payload: Event payload
        """
        # Only handle phase message events
        if payload.get("event_type") != "phase_message":
            return
        
        # Extract message data
        message_id = payload.get("message_id", "")
        source_phase_id = payload.get("source_phase_id", "")
        target_phase_id = payload.get("target_phase_id", "")
        message_type = payload.get("message_type", "")
        message_payload = payload.get("payload", {})
        
        # Only handle messages targeted to us
        if target_phase_id != "phase_communication_broker":
            # Find handlers for this message type
            handlers = self._message_handlers.get(message_type, [])
            
            # Process with handlers
            for handler in handlers:
                try:
                    response = await handler(payload)
                    
                    # If handler returns a response, send it
                    if response is not None and payload.get("expects_response", False):
                        await self.respond_to_message(message_id, response)
                except Exception as e:
                    logger.error(f"Error in message handler for {message_type}: {str(e)}")
            
            return
        
        # Handle heartbeat responses
        if message_type == MessageType.HEARTBEAT:
            # Update active phase heartbeat
            if source_phase_id in self._active_phases:
                self._active_phases[source_phase_id]["last_heartbeat"] = datetime.now().isoformat()
                self._active_phases[source_phase_id]["status"] = "active"
        
        # Handle status responses
        elif message_type == MessageType.STATUS_RESPONSE:
            # Update active phase status
            if source_phase_id in self._active_phases:
                self._active_phases[source_phase_id].update({
                    "last_heartbeat": datetime.now().isoformat(),
                    "status": "active",
                    "phase_status": message_payload.get("status", "unknown")
                })
        
        # Handle phase transition events
        elif message_type == MessageType.PHASE_TRANSITION:
            source_type = message_payload.get("source_type")
            target_type = message_payload.get("target_type")
            
            # Record transition event
            await self._metrics_manager.record_metric(
                "phase_two:communication:phase_transition",
                1.0,
                metadata={
                    "source_phase_id": source_phase_id,
                    "source_type": source_type,
                    "target_type": target_type
                }
            )