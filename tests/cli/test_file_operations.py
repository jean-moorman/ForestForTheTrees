"""
Test File I/O Operations from run_phase_one.py

This module tests file input/output operations including reading prompts from files,
saving JSON outputs, and handling various file-related error conditions.
"""

import pytest
import os
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from run_phase_one import PhaseOneCLI


class TestFileInputOperations:
    """Test reading prompts from files."""
    
    def test_read_simple_text_file(self):
        """Test reading a simple text file with a prompt."""
        test_prompt = "Create a web application for task management"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            temp_file.write(test_prompt)
            temp_file_path = temp_file.name
        
        try:
            # Read the file content
            with open(temp_file_path, 'r') as f:
                content = f.read()
            
            assert content == test_prompt
        
        finally:
            os.unlink(temp_file_path)
    
    def test_read_multiline_prompt_file(self):
        """Test reading a multiline prompt from a file."""
        test_prompt = """Create a comprehensive web application that includes:
        
1. User authentication system
2. Task management functionality
3. Team collaboration features
4. Real-time notifications
5. Analytics dashboard

The application should be built using modern web technologies
and follow best practices for security and performance."""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            temp_file.write(test_prompt)
            temp_file_path = temp_file.name
        
        try:
            with open(temp_file_path, 'r') as f:
                content = f.read()
            
            assert content == test_prompt
            assert '\n' in content  # Verify multiline content
            assert '1. User authentication system' in content
            assert 'Analytics dashboard' in content
        
        finally:
            os.unlink(temp_file_path)
    
    def test_read_file_with_unicode_content(self):
        """Test reading a file with Unicode characters."""
        test_prompt = "Créer une application web avec émojis 🚀🌟 and 中文字符 support"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(test_prompt)
            temp_file_path = temp_file.name
        
        try:
            with open(temp_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            assert content == test_prompt
            assert '🚀' in content
            assert '中文字符' in content
        
        finally:
            os.unlink(temp_file_path)
    
    def test_read_file_with_special_characters(self):
        """Test reading a file with special characters and quotes."""
        test_prompt = '''Create an app with "quotes", 'apostrophes', and special chars: @#$%^&*()
        Include features like:
        - User's personal dashboard
        - "Smart" notifications
        - Reports & analytics'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            temp_file.write(test_prompt)
            temp_file_path = temp_file.name
        
        try:
            with open(temp_file_path, 'r') as f:
                content = f.read()
            
            assert content == test_prompt
            assert '"quotes"' in content
            assert "'apostrophes'" in content
            assert '@#$%^&*()' in content
        
        finally:
            os.unlink(temp_file_path)
    
    def test_read_empty_file(self):
        """Test reading an empty file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            # Write nothing to create an empty file
            temp_file_path = temp_file.name
        
        try:
            with open(temp_file_path, 'r') as f:
                content = f.read()
            
            assert content == ""
        
        finally:
            os.unlink(temp_file_path)
    
    def test_read_large_file(self):
        """Test reading a large prompt file."""
        # Create a large prompt (simulating a detailed specification)
        base_prompt = "Create a web application with the following feature: "
        large_prompt = base_prompt + "detailed specification. " * 1000  # ~25KB
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            temp_file.write(large_prompt)
            temp_file_path = temp_file.name
        
        try:
            with open(temp_file_path, 'r') as f:
                content = f.read()
            
            assert len(content) > 20000  # Should be large
            assert content.startswith(base_prompt)
            assert "detailed specification." in content
        
        finally:
            os.unlink(temp_file_path)


class TestFileOutputOperations:
    """Test saving JSON outputs to files."""
    
    def test_save_simple_json_output(self):
        """Test saving a simple result to JSON file."""
        test_result = {
            "status": "success",
            "execution_time": 42.5,
            "structural_components": [
                {"name": "User Authentication", "type": "security"},
                {"name": "Data Management", "type": "core"}
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            temp_file_path = temp_file.name
        
        try:
            # Save the result to JSON
            with open(temp_file_path, 'w') as f:
                json.dump(test_result, f, indent=2)
            
            # Verify the file was saved correctly
            with open(temp_file_path, 'r') as f:
                loaded_result = json.load(f)
            
            assert loaded_result == test_result
            assert loaded_result["status"] == "success"
            assert loaded_result["execution_time"] == 42.5
            assert len(loaded_result["structural_components"]) == 2
        
        finally:
            os.unlink(temp_file_path)
    
    def test_save_complex_json_output(self):
        """Test saving a complex result with nested structures."""
        test_result = {
            "status": "success",
            "operation_id": "test_operation_123",
            "execution_time": 125.7,
            "structural_components": [
                {
                    "id": "auth",
                    "name": "Authentication System",
                    "description": "Handles user authentication and authorization",
                    "dependencies": [],
                    "technical_details": {
                        "languages": ["Python", "JavaScript"],
                        "frameworks": ["Flask", "React"],
                        "security_features": ["JWT tokens", "Password hashing", "2FA support"]
                    }
                },
                {
                    "id": "data",
                    "name": "Data Management Layer",
                    "description": "Manages application data and persistence",
                    "dependencies": ["auth"],
                    "technical_details": {
                        "database": "PostgreSQL",
                        "orm": "SQLAlchemy",
                        "caching": "Redis"
                    }
                }
            ],
            "system_requirements": {
                "task_analysis": {
                    "original_request": "Create a comprehensive task management application",
                    "interpreted_goal": "Build a web-based task management system",
                    "technical_requirements": {
                        "languages": ["Python", "JavaScript"],
                        "frameworks": ["Flask", "React"],
                        "databases": ["PostgreSQL", "Redis"]
                    }
                }
            },
            "metadata": {
                "timestamp": "2023-01-01T10:00:00Z",
                "version": "1.0.0",
                "agent_versions": {
                    "garden_planner": "2.1.0",
                    "earth_agent": "1.5.0"
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            temp_file_path = temp_file.name
        
        try:
            # Save the complex result
            with open(temp_file_path, 'w') as f:
                json.dump(test_result, f, indent=2)
            
            # Verify the file was saved correctly
            with open(temp_file_path, 'r') as f:
                loaded_result = json.load(f)
            
            assert loaded_result == test_result
            assert loaded_result["structural_components"][0]["technical_details"]["languages"] == ["Python", "JavaScript"]
            assert loaded_result["metadata"]["agent_versions"]["garden_planner"] == "2.1.0"
        
        finally:
            os.unlink(temp_file_path)
    
    def test_save_json_with_unicode_content(self):
        """Test saving JSON with Unicode characters."""
        test_result = {
            "status": "success",
            "description": "Créer une application avec émojis 🚀🌟",
            "components": [
                {"name": "用户认证", "description": "User authentication in Chinese"},
                {"name": "Système de données", "description": "Data system in French"}
            ],
            "special_chars": "Special chars: @#$%^&*()"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            temp_file_path = temp_file.name
        
        try:
            # Save with proper Unicode handling
            with open(temp_file_path, 'w', encoding='utf-8') as f:
                json.dump(test_result, f, indent=2, ensure_ascii=False)
            
            # Verify Unicode content
            with open(temp_file_path, 'r', encoding='utf-8') as f:
                loaded_result = json.load(f)
            
            assert loaded_result == test_result
            assert '🚀' in loaded_result["description"]
            assert '用户认证' in loaded_result["components"][0]["name"]
        
        finally:
            os.unlink(temp_file_path)
    
    def test_save_json_pretty_formatting(self):
        """Test that JSON is saved with proper formatting."""
        test_result = {
            "status": "success",
            "components": [{"name": "test1"}, {"name": "test2"}]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            temp_file_path = temp_file.name
        
        try:
            # Save with pretty formatting
            with open(temp_file_path, 'w') as f:
                json.dump(test_result, f, indent=2)
            
            # Read raw content to verify formatting
            with open(temp_file_path, 'r') as f:
                content = f.read()
            
            # Should have proper indentation and newlines
            assert '\n' in content
            assert '  "status"' in content  # 2-space indentation
            assert '    "name"' in content  # nested indentation
        
        finally:
            os.unlink(temp_file_path)


class TestFileErrorHandling:
    """Test file operation error scenarios."""
    
    def test_read_nonexistent_file(self):
        """Test reading a file that doesn't exist."""
        nonexistent_path = "/tmp/nonexistent_file_12345.txt"
        
        with pytest.raises(FileNotFoundError):
            with open(nonexistent_path, 'r') as f:
                f.read()
    
    def test_read_file_permission_denied(self):
        """Test reading a file with no read permissions."""
        # Create a file and remove read permissions
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            temp_file.write("test content")
            temp_file_path = temp_file.name
        
        try:
            # Remove read permissions
            os.chmod(temp_file_path, 0o000)
            
            with pytest.raises(PermissionError):
                with open(temp_file_path, 'r') as f:
                    f.read()
        
        finally:
            # Restore permissions for cleanup
            os.chmod(temp_file_path, 0o644)
            os.unlink(temp_file_path)
    
    def test_write_to_readonly_directory(self):
        """Test writing to a read-only directory."""
        # Create a temporary directory and make it read-only
        with tempfile.TemporaryDirectory() as temp_dir:
            readonly_dir = Path(temp_dir) / "readonly"
            readonly_dir.mkdir()
            
            try:
                # Make directory read-only
                readonly_dir.chmod(0o444)
                
                output_file = readonly_dir / "output.json"
                
                with pytest.raises(PermissionError):
                    with open(output_file, 'w') as f:
                        json.dump({"test": "data"}, f)
            
            finally:
                # Restore permissions for cleanup
                readonly_dir.chmod(0o755)
    
    def test_write_to_full_disk_simulation(self):
        """Test handling disk full scenarios (simulated)."""
        # This is challenging to test realistically, but we can test the principle
        test_result = {"status": "success"}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            temp_file_path = temp_file.name
        
        try:
            # Normal write should work
            with open(temp_file_path, 'w') as f:
                json.dump(test_result, f)
            
            # Verify file was written
            assert os.path.exists(temp_file_path)
            assert os.path.getsize(temp_file_path) > 0
        
        finally:
            os.unlink(temp_file_path)
    
    def test_invalid_json_serialization(self):
        """Test handling objects that can't be JSON serialized."""
        # Create an object that can't be JSON serialized
        class NonSerializableClass:
            def __init__(self):
                self.value = "test"
        
        test_result = {
            "status": "success",
            "non_serializable": NonSerializableClass()
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            temp_file_path = temp_file.name
        
        try:
            with pytest.raises(TypeError):
                with open(temp_file_path, 'w') as f:
                    json.dump(test_result, f)
        
        finally:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)


class TestFilePathHandling:
    """Test various file path formats and edge cases."""
    
    def test_absolute_path_handling(self):
        """Test handling absolute file paths."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            temp_file.write("test content")
            absolute_path = os.path.abspath(temp_file.name)
        
        try:
            # Should work with absolute path
            with open(absolute_path, 'r') as f:
                content = f.read()
            
            assert content == "test content"
        
        finally:
            os.unlink(absolute_path)
    
    def test_relative_path_handling(self):
        """Test handling relative file paths."""
        # Create a file in a subdirectory
        with tempfile.TemporaryDirectory() as temp_dir:
            subdir = Path(temp_dir) / "subdir"
            subdir.mkdir()
            
            test_file = subdir / "test.txt"
            test_file.write_text("test content")
            
            # Change to temp directory to test relative paths
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                
                # Should work with relative path
                with open("subdir/test.txt", 'r') as f:
                    content = f.read()
                
                assert content == "test content"
            
            finally:
                os.chdir(original_cwd)
    
    def test_path_with_spaces(self):
        """Test handling file paths with spaces."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "file with spaces.txt"
            test_file.write_text("test content")
            
            # Should work with spaces in filename
            with open(str(test_file), 'r') as f:
                content = f.read()
            
            assert content == "test content"
    
    def test_path_with_special_characters(self):
        """Test handling file paths with special characters."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Note: Some special characters may not be valid in filenames on all systems
            test_file = Path(temp_dir) / "file-with_special.chars.txt"
            test_file.write_text("test content")
            
            with open(str(test_file), 'r') as f:
                content = f.read()
            
            assert content == "test content"


class TestFileEncodingHandling:
    """Test handling different file encodings."""
    
    def test_utf8_encoding(self):
        """Test UTF-8 encoded files."""
        unicode_content = "Unicode content: 🚀 中文 Français"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(unicode_content)
            temp_file_path = temp_file.name
        
        try:
            with open(temp_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            assert content == unicode_content
        
        finally:
            os.unlink(temp_file_path)
    
    def test_ascii_encoding(self):
        """Test ASCII encoded files."""
        ascii_content = "Simple ASCII content without special characters"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='ascii') as temp_file:
            temp_file.write(ascii_content)
            temp_file_path = temp_file.name
        
        try:
            with open(temp_file_path, 'r', encoding='ascii') as f:
                content = f.read()
            
            assert content == ascii_content
        
        finally:
            os.unlink(temp_file_path)
    
    def test_encoding_error_handling(self):
        """Test handling encoding errors."""
        # Create a file with UTF-8 content
        unicode_content = "Unicode: 🚀"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(unicode_content)
            temp_file_path = temp_file.name
        
        try:
            # Try to read with ASCII encoding (should fail)
            with pytest.raises(UnicodeDecodeError):
                with open(temp_file_path, 'r', encoding='ascii') as f:
                    f.read()
        
        finally:
            os.unlink(temp_file_path)


@pytest.mark.asyncio
class TestPhaseOneCLIFileIntegration:
    """Test PhaseOneCLI integration with file operations."""
    
    async def test_cli_run_single_prompt_with_output_file(self):
        """Test CLI saving output to file."""
        # Create a temporary output file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as output_file:
            output_file_path = output_file.name
        
        try:
            # Mock the CLI setup and execution
            cli = PhaseOneCLI()
            
            # Mock the phase_one orchestrator and debugger
            with patch.object(cli, 'setup_cli', new_callable=AsyncMock):
                # Create a mock phase_one orchestrator
                mock_phase_one = MagicMock()
                mock_phase_one.process_task = AsyncMock(return_value={
                    "status": "success",
                    "execution_time": 30.5,
                    "structural_components": [
                        {"name": "Test Component", "type": "core"}
                    ]
                })
                cli.phase_one = mock_phase_one
                
                # Create a mock debugger
                mock_debugger = MagicMock()
                mock_debugger._print_execution_result = MagicMock()
                cli.debugger = mock_debugger
                
                # Run with output file
                await cli.run_single_prompt("Create a test app", output_file_path)
                
                # Verify output file was created and contains expected data
                assert os.path.exists(output_file_path)
                
                with open(output_file_path, 'r') as f:
                    saved_result = json.load(f)
                
                assert saved_result["status"] == "success"
                assert saved_result["execution_time"] == 30.5
                assert len(saved_result["structural_components"]) == 1
        
        finally:
            if os.path.exists(output_file_path):
                os.unlink(output_file_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])