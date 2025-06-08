"""
System Prompt Loader for Phase Zero Agents

Provides centralized loading and management of system prompts for the new dual-perspective 
agent architecture. Handles loading prompts from FFTT_system_prompts/phase_zero/phase_one_contractor/
and mapping them to the appropriate agent contexts.
"""
import importlib
import logging
from typing import Dict, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)

class PromptType(Enum):
    """Types of prompts available for each agent"""
    PHASE_ONE_INITIAL = "phase_one_initial"
    PHASE_ONE_REFLECTION = "phase_one_reflection" 
    PHASE_ONE_REVISION = "phase_one_revision"
    PHASE_TWO_INITIAL = "phase_two_initial"
    PHASE_THREE_INITIAL = "phase_three_initial"

class AgentType(Enum):
    """Available agent types in the new system"""
    SUN = "sun"
    SHADE = "shade"  
    SOIL = "soil"
    MICROBIAL = "microbial"
    WORM = "worm"
    MYCELIAL = "mycelial"
    TREE = "tree"
    BIRD = "bird"
    POLLINATOR = "pollinator"
    EVOLUTION = "evolution"

class PhaseZeroPromptLoader:
    """
    Centralized prompt loader for Phase Zero agents.
    
    Loads system prompts from FFTT_system_prompts/phase_zero/phase_one_contractor/
    and provides them to agents based on their type and the requested prompt type.
    """
    
    def __init__(self):
        self._prompt_cache: Dict[Tuple[AgentType, PromptType], str] = {}
        self._agent_modules: Dict[AgentType, str] = {
            AgentType.SUN: "FFTT_system_prompts.phase_zero.phase_one_contractor.sun_agent",
            AgentType.SHADE: "FFTT_system_prompts.phase_zero.phase_one_contractor.shade_agent",
            AgentType.SOIL: "FFTT_system_prompts.phase_zero.phase_one_contractor.soil_agent", 
            AgentType.MICROBIAL: "FFTT_system_prompts.phase_zero.phase_one_contractor.microbial_agent",
            AgentType.WORM: "FFTT_system_prompts.phase_zero.phase_one_contractor.worm_agent",
            AgentType.MYCELIAL: "FFTT_system_prompts.phase_zero.phase_one_contractor.mycelial_agent",
            AgentType.TREE: "FFTT_system_prompts.phase_zero.phase_one_contractor.tree_agent",
            AgentType.BIRD: "FFTT_system_prompts.phase_zero.phase_one_contractor.bird_agent",
            AgentType.POLLINATOR: "FFTT_system_prompts.phase_zero.phase_one_contractor.pollinator_agent",
            AgentType.EVOLUTION: "FFTT_system_prompts.phase_zero.phase_one_contractor.evolution_agent"
        }
        
        # Mapping of prompt types to actual variable names in the agent modules
        self._prompt_variable_mapping: Dict[Tuple[AgentType, PromptType], str] = {
            # Sun Agent prompts
            (AgentType.SUN, PromptType.PHASE_ONE_INITIAL): "phase_one_initial_description_analysis_prompt",
            (AgentType.SUN, PromptType.PHASE_ONE_REFLECTION): "description_analysis_reflection_prompt",
            (AgentType.SUN, PromptType.PHASE_ONE_REVISION): "description_analysis_revision_prompt",
            (AgentType.SUN, PromptType.PHASE_TWO_INITIAL): "phase_two_initial_description_analysis_prompt",
            (AgentType.SUN, PromptType.PHASE_THREE_INITIAL): "phase_three_initial_description_analysis_prompt",
            
            # Shade Agent prompts
            (AgentType.SHADE, PromptType.PHASE_ONE_INITIAL): "phase_one_initial_description_conflict_analysis_prompt",
            (AgentType.SHADE, PromptType.PHASE_ONE_REFLECTION): "phase_one_initial_description_reflection_prompt",
            (AgentType.SHADE, PromptType.PHASE_ONE_REVISION): "phase_one_initial_description_revision_prompt",
            (AgentType.SHADE, PromptType.PHASE_TWO_INITIAL): "phase_two_initial_description_conflict_analysis_prompt",
            (AgentType.SHADE, PromptType.PHASE_THREE_INITIAL): "phase_three_initial_description_conflict_analysis_prompt",
            
            # Soil Agent prompts
            (AgentType.SOIL, PromptType.PHASE_ONE_INITIAL): "phase_one_core_requirements_analysis_prompt",
            (AgentType.SOIL, PromptType.PHASE_ONE_REFLECTION): "phase_one_core_requirement_reflection_prompt",
            (AgentType.SOIL, PromptType.PHASE_ONE_REVISION): "phase_one_core_requirement_revision_prompt",
            (AgentType.SOIL, PromptType.PHASE_TWO_INITIAL): "phase_two_component_requirement_analysis_prompt",
            (AgentType.SOIL, PromptType.PHASE_THREE_INITIAL): "phase_three_feature_requirement_analysis_prompt",
            
            # Microbial Agent prompts
            (AgentType.MICROBIAL, PromptType.PHASE_ONE_INITIAL): "phase_one_core_requirement_verification_prompt",
            (AgentType.MICROBIAL, PromptType.PHASE_ONE_REFLECTION): "phase_one_core_requirements_reflection_prompt",
            (AgentType.MICROBIAL, PromptType.PHASE_ONE_REVISION): "phase_one_core_requirements_revision_prompt",
            (AgentType.MICROBIAL, PromptType.PHASE_TWO_INITIAL): "phase_two_core_requirements_verification_prompt",
            (AgentType.MICROBIAL, PromptType.PHASE_THREE_INITIAL): "phase_three_core_requirements_verification_prompt",
            
            # Worm Agent prompts
            (AgentType.WORM, PromptType.PHASE_ONE_INITIAL): "phase_one_data_flow_analysis_prompt",
            (AgentType.WORM, PromptType.PHASE_ONE_REFLECTION): "data_flow_analysis_reflection_prompt",
            (AgentType.WORM, PromptType.PHASE_ONE_REVISION): "data_flow_analysis_revision_prompt",
            (AgentType.WORM, PromptType.PHASE_TWO_INITIAL): "phase_two_data_flow_analysis_prompt",
            (AgentType.WORM, PromptType.PHASE_THREE_INITIAL): "phase_three_data_flow_analysis_prompt",
            
            # Mycelial Agent prompts
            (AgentType.MYCELIAL, PromptType.PHASE_ONE_INITIAL): "phase_one_data_flow_verification_prompt",
            (AgentType.MYCELIAL, PromptType.PHASE_ONE_REFLECTION): "phase_one_data_flow_reflection_prompt",
            (AgentType.MYCELIAL, PromptType.PHASE_ONE_REVISION): "phase_one_data_flow_revision_prompt",
            (AgentType.MYCELIAL, PromptType.PHASE_TWO_INITIAL): "phase_two_data_flow_verification_prompt",
            (AgentType.MYCELIAL, PromptType.PHASE_THREE_INITIAL): "phase_three_data_flow_verification_prompt",
            
            # Tree Agent prompts
            (AgentType.TREE, PromptType.PHASE_ONE_INITIAL): "phase_one_structural_analysis_prompt",
            (AgentType.TREE, PromptType.PHASE_ONE_REFLECTION): "structural_analysis_reflection_prompt",
            (AgentType.TREE, PromptType.PHASE_ONE_REVISION): "structural_analysis_revision_prompt",
            (AgentType.TREE, PromptType.PHASE_TWO_INITIAL): "phase_two_structural_analysis_prompt",
            (AgentType.TREE, PromptType.PHASE_THREE_INITIAL): "phase_three_structural_analysis_prompt",
            
            # Bird Agent prompts
            (AgentType.BIRD, PromptType.PHASE_ONE_INITIAL): "phase_one_structural_component_verification_prompt",
            (AgentType.BIRD, PromptType.PHASE_ONE_REFLECTION): "phase_one_structural_component_reflection_prompt",
            (AgentType.BIRD, PromptType.PHASE_ONE_REVISION): "phase_one_structural_component_revision_prompt",
            (AgentType.BIRD, PromptType.PHASE_TWO_INITIAL): "phase_two_structural_component_verification_prompt",
            (AgentType.BIRD, PromptType.PHASE_THREE_INITIAL): "phase_three_structural_component_verification_prompt",
            
            # Pollinator Agent prompts
            (AgentType.POLLINATOR, PromptType.PHASE_ONE_INITIAL): "phase_one_cross_guideline_optimization_analysis_prompt",
            (AgentType.POLLINATOR, PromptType.PHASE_ONE_REFLECTION): "cross_guideline_optimization_reflection_prompt",
            (AgentType.POLLINATOR, PromptType.PHASE_ONE_REVISION): "cross_guideline_optimization_revision_prompt",
            (AgentType.POLLINATOR, PromptType.PHASE_TWO_INITIAL): "phase_two_cross_guideline_optimization_analysis_prompt",
            (AgentType.POLLINATOR, PromptType.PHASE_THREE_INITIAL): "phase_three_cross_guideline_optimization_analysis_prompt",
            
            # Evolution Agent prompts
            (AgentType.EVOLUTION, PromptType.PHASE_ONE_INITIAL): "phase_one_evolution_strategies_prompt",
            (AgentType.EVOLUTION, PromptType.PHASE_ONE_REFLECTION): "phase_one_evolution_reflection_prompt",
            (AgentType.EVOLUTION, PromptType.PHASE_ONE_REVISION): "phase_one_evolution_revision_prompt",
            (AgentType.EVOLUTION, PromptType.PHASE_TWO_INITIAL): "phase_two_evolution_strategies_prompt",
            (AgentType.EVOLUTION, PromptType.PHASE_THREE_INITIAL): "phase_three_evolution_strategies_prompt",
        }
    
    def get_prompt(self, agent_type: AgentType, prompt_type: PromptType) -> Optional[str]:
        """
        Get a system prompt for the specified agent and prompt type.
        
        Args:
            agent_type: The type of agent requesting the prompt
            prompt_type: The type of prompt needed
            
        Returns:
            The system prompt string, or None if not found
        """
        cache_key = (agent_type, prompt_type)
        
        # Check cache first
        if cache_key in self._prompt_cache:
            return self._prompt_cache[cache_key]
        
        # Load from module
        prompt = self._load_prompt_from_module(agent_type, prompt_type)
        
        # Cache the result (even if None)
        self._prompt_cache[cache_key] = prompt
        
        return prompt
    
    def _load_prompt_from_module(self, agent_type: AgentType, prompt_type: PromptType) -> Optional[str]:
        """
        Load a prompt from the appropriate agent module.
        
        Args:
            agent_type: The type of agent
            prompt_type: The type of prompt
            
        Returns:
            The prompt string, or None if not found
        """
        try:
            # Get module name and variable name
            module_name = self._agent_modules.get(agent_type)
            if not module_name:
                logger.error(f"No module mapping found for agent type: {agent_type}")
                return None
            
            variable_name = self._prompt_variable_mapping.get((agent_type, prompt_type))
            if not variable_name:
                logger.error(f"No variable mapping found for {agent_type}/{prompt_type}")
                return None
            
            # Import module and get prompt
            module = importlib.import_module(module_name)
            
            if not hasattr(module, variable_name):
                logger.error(f"Variable {variable_name} not found in module {module_name}")
                return None
            
            prompt = getattr(module, variable_name)
            logger.debug(f"Successfully loaded prompt {variable_name} from {module_name}")
            
            return prompt
            
        except ImportError as e:
            logger.error(f"Failed to import module {module_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error loading prompt for {agent_type}/{prompt_type}: {e}")
            return None
    
    def preload_all_prompts(self) -> None:
        """
        Preload all available prompts into cache for better performance.
        """
        logger.info("Preloading all phase zero agent prompts...")
        
        for agent_type in AgentType:
            for prompt_type in PromptType:
                self.get_prompt(agent_type, prompt_type)
        
        loaded_count = sum(1 for prompt in self._prompt_cache.values() if prompt is not None)
        total_count = len(self._prompt_cache)
        
        logger.info(f"Preloaded {loaded_count}/{total_count} prompts")
    
    def clear_cache(self) -> None:
        """Clear the prompt cache."""
        self._prompt_cache.clear()
        logger.info("Prompt cache cleared")

# Global instance for use throughout the phase zero module
prompt_loader = PhaseZeroPromptLoader()