"""
Unit tests for System Prompt Loading and Integration

Tests the system prompt loading infrastructure and integration with Phase Zero agents:
- PhaseZeroPromptLoader functionality
- Prompt loading from FFTT_system_prompts modules
- Agent-prompt integration
- Cache management
- Error handling and fallbacks
"""
import pytest
import importlib
from unittest.mock import MagicMock, patch, mock_open
from typing import Dict, Optional

from phase_zero.prompt_loader import (
    PhaseZeroPromptLoader, 
    AgentType, 
    PromptType, 
    prompt_loader
)


class TestPromptLoaderEnums:
    """Test prompt loader enum definitions."""
    
    def test_prompt_type_enum(self):
        """Test PromptType enum values."""
        # Verify all expected prompt types exist
        expected_types = [
            "PHASE_ONE_INITIAL",
            "PHASE_ONE_REFLECTION", 
            "PHASE_ONE_REVISION",
            "PHASE_TWO_INITIAL",
            "PHASE_THREE_INITIAL"
        ]
        
        for prompt_type in expected_types:
            assert hasattr(PromptType, prompt_type)
            
        # Verify enum values
        assert PromptType.PHASE_ONE_INITIAL.value == "phase_one_initial"
        assert PromptType.PHASE_ONE_REFLECTION.value == "phase_one_reflection"
        assert PromptType.PHASE_ONE_REVISION.value == "phase_one_revision"
        assert PromptType.PHASE_TWO_INITIAL.value == "phase_two_initial"
        assert PromptType.PHASE_THREE_INITIAL.value == "phase_three_initial"
    
    def test_agent_type_enum(self):
        """Test AgentType enum values."""
        # Verify all expected agent types exist
        expected_agents = [
            "SUN", "SHADE", "SOIL", "MICROBIAL", "WORM", 
            "MYCELIAL", "TREE", "BIRD", "POLLINATOR", "EVOLUTION"
        ]
        
        for agent_type in expected_agents:
            assert hasattr(AgentType, agent_type)
            
        # Verify enum values match agent names
        assert AgentType.SUN.value == "sun"
        assert AgentType.SHADE.value == "shade"
        assert AgentType.SOIL.value == "soil"
        assert AgentType.MICROBIAL.value == "microbial"
        assert AgentType.WORM.value == "worm"
        assert AgentType.MYCELIAL.value == "mycelial"
        assert AgentType.TREE.value == "tree"
        assert AgentType.BIRD.value == "bird"
        assert AgentType.POLLINATOR.value == "pollinator"
        assert AgentType.EVOLUTION.value == "evolution"


class TestPhaseZeroPromptLoaderInitialization:
    """Test PhaseZeroPromptLoader initialization."""
    
    def test_prompt_loader_initialization(self):
        """Test prompt loader initializes with correct mappings."""
        loader = PhaseZeroPromptLoader()
        
        # Verify cache is initialized empty
        assert loader._prompt_cache == {}
        
        # Verify agent modules mapping exists for all agents
        for agent_type in AgentType:
            assert agent_type in loader._agent_modules
            module_path = loader._agent_modules[agent_type]
            assert module_path.startswith("FFTT_system_prompts.phase_zero.phase_one_contractor.")
            assert module_path.endswith(f"{agent_type.value}_agent")
        
        # Verify prompt variable mapping exists
        assert len(loader._prompt_variable_mapping) > 0
        
        # Verify all agent/prompt combinations have mappings
        for agent_type in AgentType:
            for prompt_type in PromptType:
                key = (agent_type, prompt_type)
                assert key in loader._prompt_variable_mapping
    
    def test_agent_module_mappings(self):
        """Test agent module path mappings are correct."""
        loader = PhaseZeroPromptLoader()
        
        # Test specific agent mappings
        assert loader._agent_modules[AgentType.SUN] == "FFTT_system_prompts.phase_zero.phase_one_contractor.sun_agent"
        assert loader._agent_modules[AgentType.EVOLUTION] == "FFTT_system_prompts.phase_zero.phase_one_contractor.evolution_agent"
        assert loader._agent_modules[AgentType.POLLINATOR] == "FFTT_system_prompts.phase_zero.phase_one_contractor.pollinator_agent"
    
    def test_prompt_variable_mappings(self):
        """Test prompt variable name mappings are correct."""
        loader = PhaseZeroPromptLoader()
        
        # Test specific variable mappings
        sun_initial = loader._prompt_variable_mapping[(AgentType.SUN, PromptType.PHASE_ONE_INITIAL)]
        assert sun_initial == "phase_one_initial_description_analysis_prompt"
        
        evolution_initial = loader._prompt_variable_mapping[(AgentType.EVOLUTION, PromptType.PHASE_ONE_INITIAL)]
        assert evolution_initial == "phase_one_evolution_strategies_prompt"
        
        shade_reflection = loader._prompt_variable_mapping[(AgentType.SHADE, PromptType.PHASE_ONE_REFLECTION)]
        assert shade_reflection == "phase_one_initial_description_reflection_prompt"


class TestPromptLoading:
    """Test prompt loading functionality."""
    
    @patch('phase_zero.prompt_loader.importlib.import_module')
    def test_successful_prompt_loading(self, mock_import):
        """Test successful prompt loading from module."""
        # Mock module with prompt variable
        mock_module = MagicMock()
        mock_module.phase_one_initial_description_analysis_prompt = "Test Sun Agent Prompt"
        mock_import.return_value = mock_module
        
        loader = PhaseZeroPromptLoader()
        
        # Test loading prompt
        prompt = loader.get_prompt(AgentType.SUN, PromptType.PHASE_ONE_INITIAL)
        
        # Verify prompt was loaded
        assert prompt == "Test Sun Agent Prompt"
        
        # Verify module was imported correctly
        mock_import.assert_called_once_with("FFTT_system_prompts.phase_zero.phase_one_contractor.sun_agent")
        
        # Verify prompt was cached
        cache_key = (AgentType.SUN, PromptType.PHASE_ONE_INITIAL)
        assert loader._prompt_cache[cache_key] == "Test Sun Agent Prompt"
    
    @patch('phase_zero.prompt_loader.importlib.import_module')
    def test_prompt_caching(self, mock_import):
        """Test prompt caching functionality."""
        # Mock module
        mock_module = MagicMock()
        mock_module.phase_one_initial_description_analysis_prompt = "Cached Prompt"
        mock_import.return_value = mock_module
        
        loader = PhaseZeroPromptLoader()
        
        # Load prompt twice
        prompt1 = loader.get_prompt(AgentType.SUN, PromptType.PHASE_ONE_INITIAL)
        prompt2 = loader.get_prompt(AgentType.SUN, PromptType.PHASE_ONE_INITIAL)
        
        # Verify both calls return same prompt
        assert prompt1 == "Cached Prompt"
        assert prompt2 == "Cached Prompt"
        
        # Verify module was only imported once (cached on second call)
        mock_import.assert_called_once()
    
    @patch('phase_zero.prompt_loader.importlib.import_module')
    def test_module_import_error(self, mock_import):
        """Test handling of module import errors."""
        # Mock import error
        mock_import.side_effect = ImportError("Module not found")
        
        loader = PhaseZeroPromptLoader()
        
        # Test loading prompt with import error
        prompt = loader.get_prompt(AgentType.SUN, PromptType.PHASE_ONE_INITIAL)
        
        # Verify None is returned for import error
        assert prompt is None
        
        # Verify None is cached
        cache_key = (AgentType.SUN, PromptType.PHASE_ONE_INITIAL)
        assert loader._prompt_cache[cache_key] is None
    
    @patch('phase_zero.prompt_loader.importlib.import_module')
    def test_missing_prompt_variable(self, mock_import):
        """Test handling when prompt variable doesn't exist in module."""
        # Mock module without the expected prompt variable
        mock_module = MagicMock()
        mock_module.some_other_variable = "Other content"
        # Don't set the expected prompt variable
        del mock_module.phase_one_initial_description_analysis_prompt
        mock_import.return_value = mock_module
        
        loader = PhaseZeroPromptLoader()
        
        # Test loading prompt when variable doesn't exist
        prompt = loader.get_prompt(AgentType.SUN, PromptType.PHASE_ONE_INITIAL)
        
        # Verify None is returned
        assert prompt is None
    
    def test_invalid_agent_type(self):
        """Test handling of invalid agent type."""
        loader = PhaseZeroPromptLoader()
        
        # Remove an agent type from the mapping temporarily
        original_mapping = loader._agent_modules.copy()
        del loader._agent_modules[AgentType.SUN]
        
        try:
            # Test loading prompt for unmapped agent
            prompt = loader.get_prompt(AgentType.SUN, PromptType.PHASE_ONE_INITIAL)
            
            # Verify None is returned
            assert prompt is None
        finally:
            # Restore original mapping
            loader._agent_modules = original_mapping
    
    def test_invalid_prompt_type(self):
        """Test handling of invalid prompt type for agent."""
        loader = PhaseZeroPromptLoader()
        
        # Remove a prompt mapping temporarily
        original_mapping = loader._prompt_variable_mapping.copy()
        del loader._prompt_variable_mapping[(AgentType.SUN, PromptType.PHASE_ONE_INITIAL)]
        
        try:
            # Test loading unmapped prompt
            prompt = loader.get_prompt(AgentType.SUN, PromptType.PHASE_ONE_INITIAL)
            
            # Verify None is returned
            assert prompt is None
        finally:
            # Restore original mapping
            loader._prompt_variable_mapping = original_mapping


class TestPromptPreloading:
    """Test prompt preloading functionality."""
    
    @patch('phase_zero.prompt_loader.importlib.import_module')
    def test_preload_all_prompts(self, mock_import):
        """Test preloading all prompts."""
        # Mock modules for all agent types
        def mock_import_side_effect(module_name):
            mock_module = MagicMock()
            # Set all possible prompt variables to avoid attribute errors
            prompt_vars = [
                "phase_one_initial_description_analysis_prompt",
                "description_analysis_reflection_prompt", 
                "description_analysis_revision_prompt",
                "phase_two_initial_description_analysis_prompt",
                "phase_three_initial_description_analysis_prompt",
                "phase_one_initial_description_conflict_analysis_prompt",
                "phase_one_initial_description_reflection_prompt",
                "phase_one_initial_description_revision_prompt",
                "phase_two_initial_description_conflict_analysis_prompt",
                "phase_three_initial_description_conflict_analysis_prompt",
                "phase_one_core_requirements_analysis_prompt",
                "phase_one_core_requirement_reflection_prompt",
                "phase_one_core_requirement_revision_prompt",
                "phase_two_component_requirement_analysis_prompt",
                "phase_three_feature_requirement_analysis_prompt",
                "phase_one_core_requirement_verification_prompt",
                "phase_one_core_requirements_reflection_prompt",
                "phase_one_core_requirements_revision_prompt",
                "phase_two_core_requirements_verification_prompt",
                "phase_three_core_requirements_verification_prompt",
                "phase_one_data_flow_analysis_prompt",
                "data_flow_analysis_reflection_prompt",
                "data_flow_analysis_revision_prompt",
                "phase_two_data_flow_analysis_prompt",
                "phase_three_data_flow_analysis_prompt",
                "phase_one_data_flow_verification_prompt",
                "phase_one_data_flow_reflection_prompt",
                "phase_one_data_flow_revision_prompt",
                "phase_two_data_flow_verification_prompt",
                "phase_three_data_flow_verification_prompt",
                "phase_one_structural_analysis_prompt",
                "structural_analysis_reflection_prompt",
                "structural_analysis_revision_prompt",
                "phase_two_structural_analysis_prompt",
                "phase_three_structural_analysis_prompt",
                "phase_one_structural_component_verification_prompt",
                "phase_one_structural_component_reflection_prompt",
                "phase_one_structural_component_revision_prompt",
                "phase_two_structural_component_verification_prompt",
                "phase_three_structural_component_verification_prompt",
                "phase_one_cross_guideline_optimization_analysis_prompt",
                "cross_guideline_optimization_reflection_prompt",
                "cross_guideline_optimization_revision_prompt",
                "phase_two_cross_guideline_optimization_analysis_prompt",
                "phase_three_cross_guideline_optimization_analysis_prompt",
                "phase_one_evolution_strategies_prompt",
                "phase_one_evolution_reflection_prompt",
                "phase_one_evolution_revision_prompt",
                "phase_two_evolution_strategies_prompt",
                "phase_three_evolution_strategies_prompt"
            ]
            
            for var in prompt_vars:
                setattr(mock_module, var, f"Mock prompt for {var}")
            
            return mock_module
        
        mock_import.side_effect = mock_import_side_effect
        
        loader = PhaseZeroPromptLoader()
        
        # Preload all prompts
        loader.preload_all_prompts()
        
        # Verify all prompts were loaded
        total_combinations = len(AgentType) * len(PromptType)
        assert len(loader._prompt_cache) == total_combinations
        
        # Verify all prompts are not None (successful loading)
        successful_loads = sum(1 for prompt in loader._prompt_cache.values() if prompt is not None)
        assert successful_loads == total_combinations
    
    @patch('phase_zero.prompt_loader.importlib.import_module')
    def test_preload_with_some_failures(self, mock_import):
        """Test preloading when some prompts fail to load."""
        # Mock import to succeed for some modules and fail for others
        def mock_import_side_effect(module_name):
            if "sun_agent" in module_name:
                raise ImportError("Sun agent module not found")
            
            mock_module = MagicMock()
            # Set a basic prompt to avoid attribute errors
            setattr(mock_module, "phase_one_initial_description_analysis_prompt", "Mock prompt")
            return mock_module
        
        mock_import.side_effect = mock_import_side_effect
        
        loader = PhaseZeroPromptLoader()
        
        # Preload all prompts
        loader.preload_all_prompts()
        
        # Verify cache contains all combinations
        total_combinations = len(AgentType) * len(PromptType)
        assert len(loader._prompt_cache) == total_combinations
        
        # Verify some prompts are None (failed) and some are loaded
        none_count = sum(1 for prompt in loader._prompt_cache.values() if prompt is None)
        success_count = sum(1 for prompt in loader._prompt_cache.values() if prompt is not None)
        
        assert none_count > 0  # Some failures
        assert success_count > 0  # Some successes


class TestCacheManagement:
    """Test cache management functionality."""
    
    def test_clear_cache(self):
        """Test cache clearing functionality."""
        loader = PhaseZeroPromptLoader()
        
        # Add some items to cache
        loader._prompt_cache[(AgentType.SUN, PromptType.PHASE_ONE_INITIAL)] = "Cached prompt"
        loader._prompt_cache[(AgentType.SHADE, PromptType.PHASE_ONE_REFLECTION)] = "Another prompt"
        
        # Verify cache has items
        assert len(loader._prompt_cache) == 2
        
        # Clear cache
        loader.clear_cache()
        
        # Verify cache is empty
        assert len(loader._prompt_cache) == 0
    
    @patch('phase_zero.prompt_loader.importlib.import_module')
    def test_cache_persistence_across_calls(self, mock_import):
        """Test cache persists across multiple get_prompt calls."""
        # Mock module
        mock_module = MagicMock()
        mock_module.phase_one_initial_description_analysis_prompt = "Persistent prompt"
        mock_import.return_value = mock_module
        
        loader = PhaseZeroPromptLoader()
        
        # Load prompt multiple times
        prompt1 = loader.get_prompt(AgentType.SUN, PromptType.PHASE_ONE_INITIAL)
        prompt2 = loader.get_prompt(AgentType.SUN, PromptType.PHASE_ONE_INITIAL)
        prompt3 = loader.get_prompt(AgentType.SUN, PromptType.PHASE_ONE_INITIAL)
        
        # Verify all return the same cached value
        assert prompt1 == "Persistent prompt"
        assert prompt2 == "Persistent prompt"
        assert prompt3 == "Persistent prompt"
        
        # Verify module was only imported once
        mock_import.assert_called_once()


class TestGlobalPromptLoaderInstance:
    """Test global prompt loader instance."""
    
    def test_global_instance_exists(self):
        """Test global prompt_loader instance exists and is correct type."""
        assert prompt_loader is not None
        assert isinstance(prompt_loader, PhaseZeroPromptLoader)
    
    def test_global_instance_functionality(self):
        """Test global instance has expected functionality."""
        # Test basic functionality
        assert hasattr(prompt_loader, 'get_prompt')
        assert hasattr(prompt_loader, 'preload_all_prompts')
        assert hasattr(prompt_loader, 'clear_cache')
        
        # Test instance variables
        assert hasattr(prompt_loader, '_prompt_cache')
        assert hasattr(prompt_loader, '_agent_modules')
        assert hasattr(prompt_loader, '_prompt_variable_mapping')


class TestPromptIntegrationWithAgents:
    """Test prompt integration with actual agent usage patterns."""
    
    @patch('phase_zero.prompt_loader.importlib.import_module')
    def test_agent_prompt_usage_pattern(self, mock_import):
        """Test typical agent prompt usage pattern."""
        # Mock prompt module
        mock_module = MagicMock()
        mock_module.phase_one_initial_description_analysis_prompt = "Sun agent system prompt for task analysis"
        mock_import.return_value = mock_module
        
        loader = PhaseZeroPromptLoader()
        
        # Simulate agent requesting prompt
        agent_type = AgentType.SUN
        prompt_type = PromptType.PHASE_ONE_INITIAL
        
        # Get prompt (as agent would)
        system_prompt = loader.get_prompt(agent_type, prompt_type)
        
        # Verify prompt is available
        assert system_prompt is not None
        assert "Sun agent system prompt" in system_prompt
        
        # Simulate agent using prompt in conversation
        user_input = "Analyze this project description"
        enhanced_conversation = f"{system_prompt}\n\n## Analysis Input\n{user_input}"
        
        # Verify enhanced conversation format
        assert system_prompt in enhanced_conversation
        assert user_input in enhanced_conversation
        assert "## Analysis Input" in enhanced_conversation
    
    @patch('phase_zero.prompt_loader.importlib.import_module')
    def test_multiple_agent_prompt_loading(self, mock_import):
        """Test loading prompts for multiple different agents."""
        # Mock modules for different agents
        def mock_import_side_effect(module_name):
            mock_module = MagicMock()
            if "sun_agent" in module_name:
                mock_module.phase_one_initial_description_analysis_prompt = "Sun prompt"
            elif "evolution_agent" in module_name:
                mock_module.phase_one_evolution_strategies_prompt = "Evolution prompt"
            elif "shade_agent" in module_name:
                mock_module.phase_one_initial_description_conflict_analysis_prompt = "Shade prompt"
            return mock_module
        
        mock_import.side_effect = mock_import_side_effect
        
        loader = PhaseZeroPromptLoader()
        
        # Load prompts for different agents
        sun_prompt = loader.get_prompt(AgentType.SUN, PromptType.PHASE_ONE_INITIAL)
        evolution_prompt = loader.get_prompt(AgentType.EVOLUTION, PromptType.PHASE_ONE_INITIAL) 
        shade_prompt = loader.get_prompt(AgentType.SHADE, PromptType.PHASE_ONE_INITIAL)
        
        # Verify different prompts were loaded
        assert sun_prompt == "Sun prompt"
        assert evolution_prompt == "Evolution prompt"
        assert shade_prompt == "Shade prompt"
        
        # Verify all are cached
        assert len(loader._prompt_cache) == 3
    
    def test_fallback_behavior_without_prompt(self):
        """Test agent behavior when prompt is not available."""
        loader = PhaseZeroPromptLoader()
        
        # Simulate getting None prompt (module not found)
        system_prompt = loader.get_prompt(AgentType.SUN, PromptType.PHASE_ONE_INITIAL)
        
        # In real usage, agents should handle None prompts gracefully
        if system_prompt:
            enhanced_conversation = f"{system_prompt}\n\nUser input here"
        else:
            # Fallback to direct conversation without system prompt
            enhanced_conversation = "User input here"
        
        # Verify fallback works
        assert enhanced_conversation == "User input here"


class TestErrorHandlingAndLogging:
    """Test error handling and logging in prompt loading."""
    
    @patch('phase_zero.prompt_loader.logger')
    @patch('phase_zero.prompt_loader.importlib.import_module')
    def test_import_error_logging(self, mock_import, mock_logger):
        """Test import error logging."""
        # Mock import error
        mock_import.side_effect = ImportError("Test import error")
        
        loader = PhaseZeroPromptLoader()
        
        # Try to load prompt
        prompt = loader.get_prompt(AgentType.SUN, PromptType.PHASE_ONE_INITIAL)
        
        # Verify None returned and error logged
        assert prompt is None
        mock_logger.error.assert_called()
        error_call = mock_logger.error.call_args[0][0]
        assert "Failed to import module" in error_call
    
    @patch('phase_zero.prompt_loader.logger')
    @patch('phase_zero.prompt_loader.importlib.import_module')
    def test_missing_variable_logging(self, mock_import, mock_logger):
        """Test missing variable error logging."""
        # Mock module without expected variable
        mock_module = MagicMock()
        mock_module.some_other_var = "exists"
        # Make hasattr return False for expected variable
        def mock_hasattr(obj, name):
            return name != "phase_one_initial_description_analysis_prompt"
        
        mock_import.return_value = mock_module
        
        loader = PhaseZeroPromptLoader()
        
        with patch('builtins.hasattr', side_effect=mock_hasattr):
            # Try to load prompt
            prompt = loader.get_prompt(AgentType.SUN, PromptType.PHASE_ONE_INITIAL)
        
        # Verify None returned and error logged
        assert prompt is None
        mock_logger.error.assert_called()
        error_call = mock_logger.error.call_args[0][0]
        assert "Variable" in error_call and "not found in module" in error_call
    
    @patch('phase_zero.prompt_loader.logger')
    def test_preload_logging(self, mock_logger):
        """Test preload operation logging."""
        loader = PhaseZeroPromptLoader()
        
        # Mock all prompts to fail loading
        with patch.object(loader, 'get_prompt', return_value=None):
            loader.preload_all_prompts()
        
        # Verify info logs were called
        mock_logger.info.assert_called()
        
        # Check for preload start and completion logs
        info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        assert any("Preloading all phase zero agent prompts" in call for call in info_calls)
        assert any("Preloaded" in call for call in info_calls)