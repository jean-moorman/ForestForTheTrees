"""
Test CLI argument parsing functionality from run_phase_one.py

This module tests the complete command-line interface argument parsing,
covering all modes and options that are missing from existing E2E tests.
"""

import pytest
import sys
import os
import tempfile
import json
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path
from io import StringIO

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from run_phase_one import parse_arguments, run_cli_mode, PhaseOneCLI


class TestCLIArgumentParsing:
    """Test command-line argument parsing functionality."""
    
    def test_default_gui_mode(self):
        """Test that GUI mode is default when no arguments provided."""
        with patch('sys.argv', ['run_phase_one.py']):
            args = parse_arguments()
            
            # Default should be GUI mode
            assert not args.cli
            assert not args.debug
            assert not args.interactive
            assert not args.prompt
            assert not args.file
            assert args.gui or (not args.cli and not args.debug)  # GUI is default
    
    def test_cli_mode_flag(self):
        """Test --cli flag activates CLI mode."""
        with patch('sys.argv', ['run_phase_one.py', '--cli']):
            args = parse_arguments()
            
            assert args.cli
            assert not args.gui
            assert not args.debug
    
    def test_debug_mode_flag(self):
        """Test --debug flag activates debug CLI mode."""
        with patch('sys.argv', ['run_phase_one.py', '--debug']):
            args = parse_arguments()
            
            assert args.debug
            assert not args.gui
            assert not args.cli
    
    def test_interactive_mode_flag(self):
        """Test --interactive flag activates interactive mode."""
        with patch('sys.argv', ['run_phase_one.py', '--interactive']):
            args = parse_arguments()
            
            assert args.interactive
            assert not args.gui
    
    def test_prompt_argument(self):
        """Test -p/--prompt argument for single prompt execution."""
        test_prompt = "Create a simple web application"
        
        with patch('sys.argv', ['run_phase_one.py', '-p', test_prompt]):
            args = parse_arguments()
            
            assert args.prompt == test_prompt
            assert not args.file
            assert not args.interactive
    
    def test_file_argument(self):
        """Test -f/--file argument for file input."""
        test_file = "test_prompt.txt"
        
        with patch('sys.argv', ['run_phase_one.py', '-f', test_file]):
            args = parse_arguments()
            
            assert args.file == test_file
            assert not args.prompt
            assert not args.interactive
    
    def test_output_argument(self):
        """Test -o/--output argument for output file."""
        test_output = "result.json"
        
        with patch('sys.argv', ['run_phase_one.py', '-p', 'test', '-o', test_output]):
            args = parse_arguments()
            
            assert args.output == test_output
            assert args.prompt == 'test'
    
    def test_log_level_argument(self):
        """Test --log-level argument for logging configuration."""
        with patch('sys.argv', ['run_phase_one.py', '--log-level', 'DEBUG']):
            args = parse_arguments()
            
            assert args.log_level == 'DEBUG'
    
    def test_log_file_argument(self):
        """Test --log-file argument for log file configuration."""
        test_log_file = "custom.log"
        
        with patch('sys.argv', ['run_phase_one.py', '--log-file', test_log_file]):
            args = parse_arguments()
            
            assert args.log_file == test_log_file
    
    def test_mutually_exclusive_mode_groups(self):
        """Test that mutually exclusive mode arguments are properly handled."""
        # GUI and CLI should be mutually exclusive
        with patch('sys.argv', ['run_phase_one.py', '--gui', '--cli']):
            with pytest.raises(SystemExit):  # argparse exits on conflict
                parse_arguments()
    
    def test_mutually_exclusive_input_groups(self):
        """Test that mutually exclusive input arguments are properly handled."""
        # Prompt and file should be mutually exclusive
        with patch('sys.argv', ['run_phase_one.py', '-p', 'test', '-f', 'test.txt']):
            with pytest.raises(SystemExit):  # argparse exits on conflict
                parse_arguments()
    
    def test_all_log_levels(self):
        """Test all valid log levels are accepted."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR']
        
        for level in valid_levels:
            with patch('sys.argv', ['run_phase_one.py', '--log-level', level]):
                args = parse_arguments()
                assert args.log_level == level
    
    def test_invalid_log_level(self):
        """Test invalid log level is rejected."""
        with patch('sys.argv', ['run_phase_one.py', '--log-level', 'INVALID']):
            with pytest.raises(SystemExit):  # argparse exits on invalid choice
                parse_arguments()
    
    def test_help_message_content(self):
        """Test that help message contains expected information."""
        with patch('sys.argv', ['run_phase_one.py', '--help']):
            # Capture help output
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                with pytest.raises(SystemExit):  # --help causes exit
                    parse_arguments()
                
                help_output = mock_stdout.getvalue()
                
                # Check for key help content
                assert 'Phase One Standalone Runner' in help_output
                assert '--gui' in help_output
                assert '--cli' in help_output
                assert '--debug' in help_output
                assert '-p' in help_output or '--prompt' in help_output
                assert '-f' in help_output or '--file' in help_output
    
    def test_complex_argument_combinations(self):
        """Test complex but valid argument combinations."""
        # CLI mode with prompt and output
        with patch('sys.argv', ['run_phase_one.py', '--cli', '-p', 'test prompt', '-o', 'output.json', '--log-level', 'DEBUG']):
            args = parse_arguments()
            
            assert args.cli
            assert args.prompt == 'test prompt'
            assert args.output == 'output.json'
            assert args.log_level == 'DEBUG'
    
    def test_cli_mode_determination(self):
        """Test the CLI mode determination logic from run_phase_one.py main()."""
        # Test cases that should trigger CLI mode
        cli_triggering_args = [
            ['--cli'],
            ['--debug'],
            ['--interactive'],
            ['-p', 'test prompt'],
            ['-f', 'test.txt']
        ]
        
        for args_list in cli_triggering_args:
            with patch('sys.argv', ['run_phase_one.py'] + args_list):
                args = parse_arguments()
                
                # Replicate the CLI mode determination logic from main()
                cli_mode = args.cli or args.debug or args.interactive or args.prompt or args.file
                assert cli_mode, f"Arguments {args_list} should trigger CLI mode"


class TestCLIArgumentEdgeCases:
    """Test edge cases and error conditions in argument parsing."""
    
    def test_empty_prompt_argument(self):
        """Test behavior with empty prompt argument."""
        with patch('sys.argv', ['run_phase_one.py', '-p', '']):
            args = parse_arguments()
            
            # Should accept empty prompt (validation happens later)
            assert args.prompt == ''
    
    def test_whitespace_only_prompt(self):
        """Test behavior with whitespace-only prompt."""
        with patch('sys.argv', ['run_phase_one.py', '-p', '   \t\n   ']):
            args = parse_arguments()
            
            assert args.prompt == '   \t\n   '
    
    def test_long_prompt_argument(self):
        """Test behavior with very long prompt argument."""
        long_prompt = "Create a web application " * 100  # Very long prompt
        
        with patch('sys.argv', ['run_phase_one.py', '-p', long_prompt]):
            args = parse_arguments()
            
            assert args.prompt == long_prompt
    
    def test_special_characters_in_prompt(self):
        """Test prompts with special characters."""
        special_prompt = "Create app with \"quotes\", 'apostrophes', and $pecial characters! @#$%^&*()"
        
        with patch('sys.argv', ['run_phase_one.py', '-p', special_prompt]):
            args = parse_arguments()
            
            assert args.prompt == special_prompt
    
    def test_unicode_in_prompt(self):
        """Test prompts with Unicode characters."""
        unicode_prompt = "Créer une application web avec émojis 🚀🌟 and 中文字符"
        
        with patch('sys.argv', ['run_phase_one.py', '-p', unicode_prompt]):
            args = parse_arguments()
            
            assert args.prompt == unicode_prompt
    
    def test_file_path_edge_cases(self):
        """Test various file path formats."""
        file_paths = [
            "simple.txt",
            "/absolute/path/file.txt", 
            "./relative/path/file.txt",
            "../parent/dir/file.txt",
            "file with spaces.txt",
            "file-with-dashes.txt",
            "file_with_underscores.txt"
        ]
        
        for file_path in file_paths:
            with patch('sys.argv', ['run_phase_one.py', '-f', file_path]):
                args = parse_arguments()
                assert args.file == file_path
    
    def test_output_path_edge_cases(self):
        """Test various output file path formats."""
        output_paths = [
            "result.json",
            "/tmp/output.json",
            "./results/output.json",
            "output with spaces.json",
            "output-with-dashes.json"
        ]
        
        for output_path in output_paths:
            with patch('sys.argv', ['run_phase_one.py', '-p', 'test', '-o', output_path]):
                args = parse_arguments()
                assert args.output == output_path


@pytest.mark.asyncio
class TestCLIExecutionFlow:
    """Test the actual CLI execution flow from run_phase_one.py main()."""
    
    async def test_run_cli_mode_with_prompt(self):
        """Test run_cli_mode function with prompt argument."""
        # Create mock args
        mock_args = MagicMock()
        mock_args.interactive = False
        mock_args.debug = False
        mock_args.prompt = "Create a simple calculator"
        mock_args.file = None
        mock_args.output = None
        
        # Mock PhaseOneCLI
        with patch('run_phase_one.PhaseOneCLI') as mock_cli_class:
            mock_cli = MagicMock()
            mock_cli_class.return_value = mock_cli
            mock_cli.run_single_prompt = AsyncMock()
            mock_cli.cleanup = AsyncMock()
            
            # Test execution
            await run_cli_mode(mock_args)
            
            # Verify CLI was created and methods called
            mock_cli_class.assert_called_once()
            mock_cli.run_single_prompt.assert_called_once_with("Create a simple calculator", None)
            mock_cli.cleanup.assert_called_once()
    
    async def test_run_cli_mode_with_file(self):
        """Test run_cli_mode function with file argument."""
        # Create temporary file with test prompt
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            test_prompt = "Create a task management system"
            temp_file.write(test_prompt)
            temp_file_path = temp_file.name
        
        try:
            # Create mock args
            mock_args = MagicMock()
            mock_args.interactive = False
            mock_args.debug = False
            mock_args.prompt = None
            mock_args.file = temp_file_path
            mock_args.output = None
            
            # Mock PhaseOneCLI
            with patch('run_phase_one.PhaseOneCLI') as mock_cli_class:
                mock_cli = MagicMock()
                mock_cli_class.return_value = mock_cli
                mock_cli.run_single_prompt = AsyncMock()
                mock_cli.cleanup = AsyncMock()
                
                # Test execution
                await run_cli_mode(mock_args)
                
                # Verify CLI was created and methods called with file content
                mock_cli_class.assert_called_once()
                mock_cli.run_single_prompt.assert_called_once_with(test_prompt, None)
                mock_cli.cleanup.assert_called_once()
        
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)
    
    async def test_run_cli_mode_with_output_file(self):
        """Test run_cli_mode function with output file argument."""
        # Create temporary output file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as output_file:
            output_file_path = output_file.name
        
        try:
            # Create mock args
            mock_args = MagicMock()
            mock_args.interactive = False
            mock_args.debug = False
            mock_args.prompt = "Create a blog platform"
            mock_args.file = None
            mock_args.output = output_file_path
            
            # Mock PhaseOneCLI
            with patch('run_phase_one.PhaseOneCLI') as mock_cli_class:
                mock_cli = MagicMock()
                mock_cli_class.return_value = mock_cli
                mock_cli.run_single_prompt = AsyncMock()
                mock_cli.cleanup = AsyncMock()
                
                # Test execution
                await run_cli_mode(mock_args)
                
                # Verify CLI was created and methods called with output file
                mock_cli_class.assert_called_once()
                mock_cli.run_single_prompt.assert_called_once_with("Create a blog platform", output_file_path)
                mock_cli.cleanup.assert_called_once()
        
        finally:
            # Clean up temporary file
            if os.path.exists(output_file_path):
                os.unlink(output_file_path)
    
    async def test_run_cli_mode_interactive(self):
        """Test run_cli_mode function in interactive mode."""
        # Create mock args
        mock_args = MagicMock()
        mock_args.interactive = True
        mock_args.debug = False
        mock_args.prompt = None
        mock_args.file = None
        
        # Mock PhaseOneCLI
        with patch('run_phase_one.PhaseOneCLI') as mock_cli_class:
            mock_cli = MagicMock()
            mock_cli_class.return_value = mock_cli
            mock_cli.run_interactive_mode = AsyncMock()
            mock_cli.cleanup = AsyncMock()
            
            # Test execution
            await run_cli_mode(mock_args)
            
            # Verify CLI was created and interactive mode called
            mock_cli_class.assert_called_once()
            mock_cli.run_interactive_mode.assert_called_once()
            mock_cli.cleanup.assert_called_once()
    
    async def test_run_cli_mode_debug(self):
        """Test run_cli_mode function in debug mode."""
        # Create mock args
        mock_args = MagicMock()
        mock_args.interactive = False
        mock_args.debug = True
        mock_args.prompt = None
        mock_args.file = None
        
        # Mock PhaseOneCLI
        with patch('run_phase_one.PhaseOneCLI') as mock_cli_class:
            mock_cli = MagicMock()
            mock_cli_class.return_value = mock_cli
            mock_cli.run_interactive_mode = AsyncMock()
            mock_cli.cleanup = AsyncMock()
            
            # Test execution
            await run_cli_mode(mock_args)
            
            # Verify CLI was created and interactive mode called (debug falls back to interactive)
            mock_cli_class.assert_called_once()
            mock_cli.run_interactive_mode.assert_called_once()
            mock_cli.cleanup.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])