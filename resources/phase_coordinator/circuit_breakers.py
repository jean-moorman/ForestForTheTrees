"""
Forest For The Trees (FFTT) Phase Coordination System - Circuit Breakers
---------------------------------------------------
Manages circuit breakers for phase execution.
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from resources.monitoring import CircuitBreaker, CircuitBreakerConfig, CircuitBreakerRegistry
from resources.events import EventQueue, ResourceEventTypes
from resources.state import StateManager, ResourceType
from resources.phase_coordinator.constants import PhaseType, DEFAULT_CIRCUIT_BREAKER_CONFIGS

logger = logging.getLogger(__name__)

class CircuitBreakerManager:
    """Manages circuit breakers for phase execution"""
    
    def __init__(self, 
                event_queue: EventQueue, 
                state_manager: Optional[StateManager] = None,
                circuit_breaker_registry: Optional[CircuitBreakerRegistry] = None,
                custom_circuit_breaker_configs: Optional[Dict[str, Dict[str, Any]]] = None):
        """
        Initialize the circuit breaker manager
        
        Args:
            event_queue: Event queue for circuit breaker events
            state_manager: Optional state manager for persistence
            circuit_breaker_registry: Optional registry for circuit breakers
            custom_circuit_breaker_configs: Optional custom configurations
        """
        self._event_queue = event_queue
        self._state_manager = state_manager
        self._circuit_breaker_registry = circuit_breaker_registry
        
        # Initialize with default configurations
        self._circuit_breaker_configs = {}
        for phase_type, config_dict in DEFAULT_CIRCUIT_BREAKER_CONFIGS.items():
            self._circuit_breaker_configs[phase_type] = CircuitBreakerConfig(
                failure_threshold=config_dict["failure_threshold"],
                recovery_timeout=config_dict["recovery_timeout"],
                failure_window=config_dict["failure_window"]
            )
            
        # Update with custom configurations if provided
        if custom_circuit_breaker_configs:
            for phase_type, config_dict in custom_circuit_breaker_configs.items():
                self._circuit_breaker_configs[phase_type] = CircuitBreakerConfig(
                    failure_threshold=config_dict.get("failure_threshold", 3),
                    recovery_timeout=config_dict.get("recovery_timeout", 60),
                    failure_window=config_dict.get("failure_window", 300)
                )
                logger.info(f"Using custom circuit breaker config for {phase_type}")
        
        # Initialize circuit breakers
        self._phase_circuit_breakers: Dict[str, CircuitBreaker] = {}
        
        # Use circuit breaker registry if provided, otherwise create directly
        if self._circuit_breaker_registry:
            for phase_type in PhaseType:
                cb_id = f"phase_coordinator_{phase_type.value}"
                config = self._circuit_breaker_configs.get(phase_type.value, self._circuit_breaker_configs["phase_one"])
                self._phase_circuit_breakers[phase_type.value] = self._circuit_breaker_registry.get_or_create_circuit_breaker(
                    cb_id, config
                )
                logger.debug(f"Registered circuit breaker {cb_id} with registry")
            
            # Transition circuit breaker
            self._transition_circuit_breaker = self._circuit_breaker_registry.get_or_create_circuit_breaker(
                "phase_transition", 
                self._circuit_breaker_configs["transition"]
            )
        else:
            # Create circuit breakers directly
            for phase_type in PhaseType:
                config = self._circuit_breaker_configs.get(phase_type.value, self._circuit_breaker_configs["phase_one"])
                self._phase_circuit_breakers[phase_type.value] = CircuitBreaker(
                    f"phase_coordinator_{phase_type.value}",
                    event_queue,
                    config
                )
                
            # Transition circuit breaker
            self._transition_circuit_breaker = CircuitBreaker(
                "phase_transition",
                event_queue,
                self._circuit_breaker_configs["transition"]
            )
    
    async def load_circuit_breaker_configs(self) -> None:
        """Load circuit breaker configurations from state manager if available"""
        if not self._state_manager:
            return
            
        try:
            # Try to load saved configurations
            config_entry = await self._state_manager.get_state("phase_coordinator:circuit_breaker_configs")
            if config_entry and hasattr(config_entry, 'state') and isinstance(config_entry.state, dict):
                # Parse saved configs back into CircuitBreakerConfig objects
                loaded_configs = {}
                for phase_type, config_dict in config_entry.state.items():
                    try:
                        loaded_configs[phase_type] = CircuitBreakerConfig(
                            failure_threshold=config_dict.get("failure_threshold", 3),
                            recovery_timeout=config_dict.get("recovery_timeout", 60),
                            failure_window=config_dict.get("failure_window", 300)
                        )
                        logger.debug(f"Loaded circuit breaker config for {phase_type} from state manager")
                    except (KeyError, TypeError) as e:
                        logger.warning(f"Error loading circuit breaker config for {phase_type}: {e}")
                
                # Update configs
                if loaded_configs:
                    self._circuit_breaker_configs.update(loaded_configs)
                    logger.info(f"Loaded {len(loaded_configs)} circuit breaker configurations from state manager")
        except Exception as e:
            logger.warning(f"Error loading circuit breaker configurations: {e}")
    
    async def save_circuit_breaker_configs(self) -> None:
        """Save current circuit breaker configurations to state manager"""
        if not self._state_manager:
            return
            
        try:
            # Convert CircuitBreakerConfig objects to dictionaries
            config_dict = {}
            for phase_type, config in self._circuit_breaker_configs.items():
                if isinstance(config, CircuitBreakerConfig):
                    config_dict[phase_type] = {
                        "failure_threshold": config.failure_threshold,
                        "recovery_timeout": config.recovery_timeout,
                        "failure_window": config.failure_window
                    }
            
            # Save to state manager
            await self._state_manager.set_state(
                "phase_coordinator:circuit_breaker_configs",
                config_dict,
                ResourceType.CONFIGURATION,
                metadata={
                    "updated_at": datetime.now().isoformat(),
                    "component": "phase_coordinator"
                }
            )
            logger.debug("Saved circuit breaker configurations to state manager")
        except Exception as e:
            logger.warning(f"Error saving circuit breaker configurations: {e}")
    
    async def update_circuit_breaker_config(self, phase_type: str, config: CircuitBreakerConfig) -> bool:
        """
        Update circuit breaker configuration for a specific phase type
        
        Args:
            phase_type: The phase type to update configuration for
            config: The new circuit breaker configuration
            
        Returns:
            bool: True if update was successful
        """
        try:
            # Validate phase type
            is_valid = False
            if phase_type == "transition":
                is_valid = True
            else:
                for pt in PhaseType:
                    if pt.value == phase_type:
                        is_valid = True
                        break
            
            if not is_valid:
                logger.warning(f"Invalid phase type for circuit breaker config: {phase_type}")
                return False
            
            # Update config
            self._circuit_breaker_configs[phase_type] = config
            
            # Update actual circuit breaker if it exists
            if phase_type == "transition" and self._transition_circuit_breaker:
                if hasattr(self._transition_circuit_breaker, 'update_config'):
                    self._transition_circuit_breaker.update_config(config)
            elif phase_type in self._phase_circuit_breakers:
                circuit_breaker = self._phase_circuit_breakers[phase_type]
                if hasattr(circuit_breaker, 'update_config'):
                    circuit_breaker.update_config(config)
            
            # Save updated configurations
            await self.save_circuit_breaker_configs()
            
            logger.info(f"Updated circuit breaker configuration for {phase_type}")
            return True
        except Exception as e:
            logger.error(f"Error updating circuit breaker config for {phase_type}: {e}")
            return False
    
    def get_phase_circuit_breaker(self, phase_type: str) -> CircuitBreaker:
        """
        Get the circuit breaker for a phase type
        
        Args:
            phase_type: The phase type
            
        Returns:
            CircuitBreaker: The circuit breaker instance
        """
        return self._phase_circuit_breakers.get(
            phase_type, 
            self._phase_circuit_breakers[PhaseType.ONE.value]  # Default fallback
        )
    
    def get_transition_circuit_breaker(self) -> CircuitBreaker:
        """
        Get the transition circuit breaker
        
        Returns:
            CircuitBreaker: The transition circuit breaker instance
        """
        return self._transition_circuit_breaker
    
    def register_custom_phase_circuit_breaker(self, phase_type: str) -> bool:
        """
        Register a circuit breaker for a custom phase type
        
        Args:
            phase_type: The custom phase type
            
        Returns:
            bool: True if registration was successful
        """
        try:
            # Skip if already registered
            if phase_type in self._phase_circuit_breakers:
                return True
                
            # Create circuit breaker for the phase type
            if not self._circuit_breaker_registry:
                # Create directly
                self._phase_circuit_breakers[phase_type] = CircuitBreaker(
                    f"phase_coordinator_{phase_type}",
                    self._event_queue,
                    self._circuit_breaker_configs.get(phase_type, self._circuit_breaker_configs["phase_one"])
                )
            else:
                # Use registry
                cb_id = f"phase_coordinator_{phase_type}"
                config = self._circuit_breaker_configs.get(phase_type, self._circuit_breaker_configs["phase_one"])
                self._phase_circuit_breakers[phase_type] = self._circuit_breaker_registry.get_or_create_circuit_breaker(
                    cb_id, config
                )
                
            logger.info(f"Registered circuit breaker for custom phase type: {phase_type}")
            return True
        except Exception as e:
            logger.error(f"Error registering circuit breaker for {phase_type}: {e}")
            return False