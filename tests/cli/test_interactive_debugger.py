"""
Test Interactive Debugger functionality from run_phase_one.py

This module tests the PhaseOneDebugger class and all its interactive commands,
covering the 15+ debugger commands that are completely missing from existing tests.
"""

import pytest
import asyncio
import json
import time
from unittest.mock import AsyncMock, MagicMock, patch
from io import StringIO
from datetime import datetime

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from run_phase_one import PhaseOneDebugger


class MockPhaseOneOrchestrator:
    """Mock PhaseOneOrchestrator for testing the debugger."""
    
    def __init__(self):
        self.process_task_calls = []
        self.metrics_calls = []
        self.status_calls = []
        
    async def process_task(self, prompt, operation_id=None):
        """Mock process_task method."""
        self.process_task_calls.append((prompt, operation_id))
        return {
            "status": "success",
            "operation_id": operation_id,
            "execution_time": 45.2,
            "structural_components": [
                {"name": "User Authentication", "type": "security", "dependencies": []},
                {"name": "Data Management", "type": "core", "dependencies": ["User Authentication"]}
            ],
            "system_requirements": {
                "task_analysis": {
                    "interpreted_goal": "Create a web application",
                    "technical_requirements": {
                        "languages": ["JavaScript", "Python"],
                        "frameworks": ["React", "Flask"]
                    }
                }
            }
        }
    
    async def get_workflow_status(self, operation_id):
        """Mock get_workflow_status method."""
        self.status_calls.append(operation_id)
        return {
            "operation_id": operation_id,
            "status": "completed",
            "current_agent": "tree_placement_planner",
            "start_time": "2023-01-01T10:00:00",
            "end_time": "2023-01-01T10:45:00"
        }
    
    async def get_agent_metrics(self, agent_id):
        """Mock get_agent_metrics method."""
        self.metrics_calls.append(agent_id)
        return {
            "agent_id": agent_id,
            "status": "success",
            "execution_count": 3,
            "average_execution_time": 15.5,
            "last_execution": "2023-01-01T10:30:00"
        }


@pytest.fixture
def mock_orchestrator():
    """Create a mock orchestrator for testing."""
    return MockPhaseOneOrchestrator()


@pytest.fixture
def debugger(mock_orchestrator):
    """Create a PhaseOneDebugger instance for testing."""
    return PhaseOneDebugger(mock_orchestrator)


class TestPhaseOneDebuggerInitialization:
    """Test PhaseOneDebugger initialization."""
    
    def test_debugger_initialization(self, debugger, mock_orchestrator):
        """Test debugger initializes correctly."""
        assert debugger.phase_one == mock_orchestrator
        assert debugger.current_operation_id is None
        assert debugger.workflow_state == {}
        assert debugger.agent_metrics == {}
        assert debugger.step_mode is False
        assert debugger.break_points == set()
    
    def test_debugger_logger_setup(self, debugger):
        """Test debugger logger is properly configured."""
        assert debugger.logger is not None
        assert debugger.logger.name.endswith('.debugger')


class TestDebuggerCommands:
    """Test individual debugger commands."""
    
    @pytest.mark.asyncio
    async def test_cmd_help(self, debugger):
        """Test the help command output."""
        with patch('builtins.print') as mock_print:
            await debugger._cmd_help()
            
            # Verify help content was printed
            mock_print.assert_called()
            help_calls = [call.args[0] for call in mock_print.call_args_list]
            help_text = ' '.join(help_calls)
            
            # Check for key workflow steps
            assert "Garden Planner agent" in help_text
            assert "Earth agent validation" in help_text
            assert "Environmental Analysis agent" in help_text
            assert "Root System agent" in help_text
            assert "Tree Placement Planner agent" in help_text
    
    @pytest.mark.asyncio
    async def test_cmd_run_with_prompt(self, debugger, mock_orchestrator):
        """Test the run command with a prompt."""
        test_prompt = "Create a simple web application"
        
        with patch('builtins.print') as mock_print:
            await debugger._cmd_run(test_prompt)
            
            # Verify process_task was called
            assert len(mock_orchestrator.process_task_calls) == 1
            prompt, operation_id = mock_orchestrator.process_task_calls[0]
            assert prompt == test_prompt
            assert operation_id is not None
            assert debugger.current_operation_id == operation_id
            
            # Verify result was printed
            mock_print.assert_called()
            print_text = ' '.join([str(call.args[0]) for call in mock_print.call_args_list])
            assert "PHASE ONE EXECUTION RESULT" in print_text
            assert "SUCCESS" in print_text
    
    @pytest.mark.asyncio
    async def test_cmd_run_empty_prompt(self, debugger):
        """Test the run command with empty prompt."""
        with patch('builtins.print') as mock_print:
            await debugger._cmd_run("")
            
            # Should show error message
            mock_print.assert_called()
            error_calls = [call.args[0] for call in mock_print.call_args_list]
            error_text = ' '.join(error_calls)
            assert "Error: Please provide a prompt" in error_text
    
    @pytest.mark.asyncio
    async def test_cmd_step_mode_toggle(self, debugger):
        """Test stepping mode enable/disable commands."""
        # Test enable
        with patch('builtins.print') as mock_print:
            await debugger._cmd_step()
            assert debugger.step_mode is True
            mock_print.assert_called_with("✅ Step-by-step execution mode enabled")
        
        # Test disable
        with patch('builtins.print') as mock_print:
            await debugger._cmd_nostep()
            assert debugger.step_mode is False
            mock_print.assert_called_with("✅ Step-by-step execution mode disabled")
    
    @pytest.mark.asyncio
    async def test_cmd_status_no_operation(self, debugger):
        """Test status command when no operation is active."""
        with patch('builtins.print') as mock_print:
            await debugger._cmd_status()
            
            mock_print.assert_called_with("No active operation")
    
    @pytest.mark.asyncio
    async def test_cmd_status_with_operation(self, debugger, mock_orchestrator):
        """Test status command with an active operation."""
        # Set up an operation
        debugger.current_operation_id = "test_operation_123"
        
        with patch('builtins.print') as mock_print:
            await debugger._cmd_status()
            
            # Verify get_workflow_status was called
            assert len(mock_orchestrator.status_calls) == 1
            assert mock_orchestrator.status_calls[0] == "test_operation_123"
            
            # Verify status was printed
            mock_print.assert_called()
            status_text = ' '.join([str(call.args[0]) for call in mock_print.call_args_list])
            assert "Workflow Status" in status_text
            assert "test_operation_123" in status_text
    
    @pytest.mark.asyncio
    async def test_cmd_agents_list(self, debugger, mock_orchestrator):
        """Test the agents command listing all agents."""
        with patch('builtins.print') as mock_print:
            await debugger._cmd_agents()
            
            # Verify get_agent_metrics was called for each agent
            expected_agents = ["garden_planner", "earth_agent", "environmental_analysis", 
                             "root_system_architect", "tree_placement_planner"]
            assert len(mock_orchestrator.metrics_calls) == len(expected_agents)
            for agent in expected_agents:
                assert agent in mock_orchestrator.metrics_calls
            
            # Verify agents were printed
            mock_print.assert_called()
            agents_text = ' '.join([str(call.args[0]) for call in mock_print.call_args_list])
            assert "Phase One Agents:" in agents_text
            for agent in expected_agents:
                assert agent in agents_text
    
    @pytest.mark.asyncio
    async def test_cmd_metrics_valid_agent(self, debugger, mock_orchestrator):
        """Test metrics command for a valid agent."""
        agent_id = "garden_planner"
        
        with patch('builtins.print') as mock_print:
            await debugger._cmd_metrics(agent_id)
            
            # Verify get_agent_metrics was called
            assert agent_id in mock_orchestrator.metrics_calls
            
            # Verify metrics were printed as JSON
            mock_print.assert_called()
            metrics_text = ' '.join([str(call.args[0]) for call in mock_print.call_args_list])
            assert f"Metrics for {agent_id}:" in metrics_text
    
    @pytest.mark.asyncio
    async def test_cmd_metrics_no_agent(self, debugger):
        """Test metrics command with no agent specified."""
        with patch('builtins.print') as mock_print:
            await debugger._cmd_metrics("")
            
            mock_print.assert_called_with("Error: Please specify an agent ID. Usage: metrics <agent_id>")
    
    @pytest.mark.asyncio
    async def test_cmd_monitor(self, debugger):
        """Test the monitor command."""
        # Mock phase_one with health tracker
        debugger.phase_one._health_tracker = MagicMock()
        debugger.phase_one._memory_monitor = MagicMock()
        
        with patch('builtins.print') as mock_print:
            await debugger._cmd_monitor()
            
            mock_print.assert_called()
            monitor_text = ' '.join([str(call.args[0]) for call in mock_print.call_args_list])
            assert "System Health Monitor:" in monitor_text
            assert "Health tracking is active" in monitor_text
            assert "Memory monitoring is active" in monitor_text
    
    @pytest.mark.asyncio
    async def test_cmd_breakpoint_valid_stage(self, debugger):
        """Test setting a breakpoint at a valid stage."""
        valid_stage = "garden_planner"
        
        with patch('builtins.print') as mock_print:
            await debugger._cmd_breakpoint(valid_stage)
            
            assert valid_stage in debugger.break_points
            mock_print.assert_called_with(f"✅ Breakpoint set at: {valid_stage}")
    
    @pytest.mark.asyncio
    async def test_cmd_breakpoint_invalid_stage(self, debugger):
        """Test setting a breakpoint at an invalid stage."""
        invalid_stage = "invalid_stage"
        
        with patch('builtins.print') as mock_print:
            await debugger._cmd_breakpoint(invalid_stage)
            
            assert invalid_stage not in debugger.break_points
            mock_print.assert_called()
            breakpoint_text = str(mock_print.call_args[0][0])
            assert "Invalid stage" in breakpoint_text
    
    @pytest.mark.asyncio
    async def test_cmd_breakpoint_list(self, debugger):
        """Test listing current breakpoints."""
        # Set some breakpoints
        debugger.break_points.add("garden_planner")
        debugger.break_points.add("earth_validation")
        
        with patch('builtins.print') as mock_print:
            await debugger._cmd_breakpoint("")
            
            mock_print.assert_called()
            # The implementation prints: "Current breakpoints: ['garden_planner', 'earth_validation']"
            # So we need to check the call args which contains both the message and the list
            call_args = mock_print.call_args[0]
            if len(call_args) >= 2:
                # Called with message and list separately
                breakpoint_text = str(call_args[0]) + str(call_args[1])
            else:
                # Called with formatted string
                breakpoint_text = str(call_args[0])
            assert "garden_planner" in breakpoint_text
            assert "earth_validation" in breakpoint_text
    
    @pytest.mark.asyncio
    async def test_cmd_verbose_logging(self, debugger):
        """Test verbose logging command."""
        with patch('builtins.print') as mock_print:
            with patch('logging.getLogger') as mock_get_logger:
                mock_logger = MagicMock()
                mock_get_logger.return_value = mock_logger
                
                await debugger._cmd_verbose()
                
                # Verify logging level was set to DEBUG
                mock_logger.setLevel.assert_called()
                mock_print.assert_called_with("✅ Verbose logging enabled (DEBUG level)")
    
    @pytest.mark.asyncio
    async def test_cmd_quiet_logging(self, debugger):
        """Test quiet logging command."""
        with patch('builtins.print') as mock_print:
            with patch('logging.getLogger') as mock_get_logger:
                mock_logger = MagicMock()
                mock_get_logger.return_value = mock_logger
                
                await debugger._cmd_quiet()
                
                # Verify logging level was set to WARNING
                mock_logger.setLevel.assert_called()
                mock_print.assert_called_with("✅ Quiet mode enabled (WARNING level)")
    
    @pytest.mark.asyncio
    async def test_cmd_normal_logging(self, debugger):
        """Test normal logging command."""
        with patch('builtins.print') as mock_print:
            with patch('logging.getLogger') as mock_get_logger:
                mock_logger = MagicMock()
                mock_get_logger.return_value = mock_logger
                
                await debugger._cmd_normal()
                
                # Verify logging level was set to INFO
                mock_logger.setLevel.assert_called()
                mock_print.assert_called_with("✅ Normal logging enabled (INFO level)")
    
    @pytest.mark.asyncio
    async def test_cmd_reset(self, debugger):
        """Test reset command."""
        # Set up some state
        debugger.current_operation_id = "test_operation"
        debugger.workflow_state = {"test": "data"}
        debugger.agent_metrics = {"test": "metrics"}
        debugger.step_mode = True
        debugger.break_points.add("test_breakpoint")
        
        with patch('builtins.print') as mock_print:
            await debugger._cmd_reset()
            
            # Verify all state was reset
            assert debugger.current_operation_id is None
            assert debugger.workflow_state == {}
            assert debugger.agent_metrics == {}
            assert debugger.step_mode is False
            assert len(debugger.break_points) == 0
            
            mock_print.assert_called_with("✅ Debugger state reset")
    
    @pytest.mark.asyncio
    async def test_cmd_history(self, debugger):
        """Test history command."""
        debugger.current_operation_id = "test_operation_123"
        
        with patch('builtins.print') as mock_print:
            await debugger._cmd_history()
            
            mock_print.assert_called()
            history_text = ' '.join([str(call.args[0]) for call in mock_print.call_args_list])
            assert "Execution History:" in history_text
            assert "test_operation_123" in history_text
    
    @pytest.mark.asyncio
    async def test_cmd_trace(self, debugger):
        """Test trace command."""
        debugger.current_operation_id = "test_operation_123"
        
        with patch('builtins.print') as mock_print:
            await debugger._cmd_trace()
            
            mock_print.assert_called()
            trace_text = ' '.join([str(call.args[0]) for call in mock_print.call_args_list])
            assert "Execution Trace" in trace_text
            assert "test_operation_123" in trace_text


class TestDebuggerExecutionFlow:
    """Test debugger execution flow and stepping."""
    
    @pytest.mark.asyncio
    async def test_step_mode_execution(self, debugger, mock_orchestrator):
        """Test step-by-step execution mode."""
        debugger.step_mode = True
        test_prompt = "Create a simple app"
        
        # Mock user input for stepping
        user_inputs = iter(['', '', 'c'])  # Enter, Enter, then continue
        
        with patch('builtins.input', side_effect=user_inputs):
            with patch('builtins.print'):
                await debugger._cmd_run(test_prompt)
        
        # Verify process_task was eventually called
        assert len(mock_orchestrator.process_task_calls) == 1
    
    @pytest.mark.asyncio
    async def test_step_mode_quit(self, debugger, mock_orchestrator):
        """Test quitting during step-by-step execution."""
        debugger.step_mode = True
        test_prompt = "Create a simple app"
        
        # Mock user input for quitting
        with patch('builtins.input', return_value='q'):
            with patch('builtins.print'):
                await debugger._cmd_run(test_prompt)
        
        # Verify process_task was NOT called (execution was aborted)
        assert len(mock_orchestrator.process_task_calls) == 0
    
    @pytest.mark.asyncio
    async def test_breakpoint_execution(self, debugger):
        """Test execution hitting a breakpoint."""
        # Set a breakpoint on a step that will actually be hit
        debugger.break_points.add("Initializing workflow")
        debugger.step_mode = True
        
        test_prompt = "Create a simple app"
        
        # Mock user input - continue after hitting the breakpoint
        with patch('builtins.input', return_value='c'):
            with patch('builtins.print') as mock_print:
                await debugger._cmd_run(test_prompt)
        
        # Verify breakpoint hit message was shown
        print_calls = [str(call.args[0]) for call in mock_print.call_args_list]
        print_text = ' '.join(print_calls)
        assert "🛑 Breakpoint hit at: Initializing workflow" in print_text


class TestDebuggerResultFormatting:
    """Test debugger result formatting and display."""
    
    def test_print_execution_result_success(self, debugger):
        """Test formatting successful execution results."""
        result = {
            "status": "success",
            "execution_time": 42.5,
            "structural_components": [
                {
                    "name": "User Authentication",
                    "description": "Handles user login and registration",
                    "dependencies": []
                },
                {
                    "name": "Data Management",
                    "description": "Manages application data",
                    "dependencies": ["User Authentication"]
                }
            ],
            "system_requirements": {
                "task_analysis": {
                    "interpreted_goal": "Create a web application",
                    "technical_requirements": {
                        "languages": ["Python", "JavaScript"],
                        "frameworks": ["Flask", "React"]
                    }
                }
            }
        }
        
        with patch('builtins.print') as mock_print:
            debugger._print_execution_result(result)
            
            # Verify formatted output
            print_calls = [str(call.args[0]) for call in mock_print.call_args_list]
            print_text = ' '.join(print_calls)
            
            assert "PHASE ONE EXECUTION RESULT" in print_text
            assert "✅ SUCCESS" in print_text
            assert "42.50 seconds" in print_text
            assert "Structural Components (2)" in print_text
            assert "User Authentication" in print_text
            assert "Data Management" in print_text
            assert "Tech Stack: Python, JavaScript, Flask, React" in print_text
    
    def test_print_execution_result_error(self, debugger):
        """Test formatting error execution results."""
        result = {
            "status": "error",
            "message": "Garden Planner validation failed",
            "execution_time": 15.2
        }
        
        with patch('builtins.print') as mock_print:
            debugger._print_execution_result(result)
            
            # Verify error output
            print_calls = [str(call.args[0]) for call in mock_print.call_args_list]
            print_text = ' '.join(print_calls)
            
            assert "❌ ERROR" in print_text
            assert "Garden Planner validation failed" in print_text
            assert "15.20 seconds" in print_text
    
    def test_print_execution_result_with_refinement(self, debugger):
        """Test formatting results with refinement information."""
        result = {
            "status": "success",
            "execution_time": 68.3,
            "structural_components": [],
            "refinement_analysis": {
                "status": "refinement_executed",
                "target_agent": "garden_planner",
                "cycle": 2
            }
        }
        
        with patch('builtins.print') as mock_print:
            debugger._print_execution_result(result)
            
            # Verify refinement output
            print_calls = [str(call.args[0]) for call in mock_print.call_args_list]
            print_text = ' '.join(print_calls)
            
            assert "Refinement Analysis:" in print_text
            assert "Refinement applied to: garden_planner" in print_text
            assert "Cycle: 2" in print_text


class TestDebuggerErrorHandling:
    """Test debugger error handling scenarios."""
    
    @pytest.mark.asyncio
    async def test_cmd_run_with_exception(self, debugger, mock_orchestrator):
        """Test run command when process_task raises an exception."""
        # Make process_task raise an exception
        mock_orchestrator.process_task = AsyncMock(side_effect=Exception("Test error"))
        
        test_prompt = "Create a simple app"
        
        with patch('builtins.print') as mock_print:
            await debugger._cmd_run(test_prompt)
            
            # Verify error was handled and printed
            print_calls = [str(call.args[0]) for call in mock_print.call_args_list]
            print_text = ' '.join(print_calls)
            assert "❌ Execution failed" in print_text
            assert "Test error" in print_text
    
    @pytest.mark.asyncio
    async def test_cmd_status_with_exception(self, debugger, mock_orchestrator):
        """Test status command when get_workflow_status raises an exception."""
        debugger.current_operation_id = "test_operation"
        mock_orchestrator.get_workflow_status = AsyncMock(side_effect=Exception("Status error"))
        
        with patch('builtins.print') as mock_print:
            await debugger._cmd_status()
            
            # Verify error was handled
            print_calls = [str(call.args[0]) for call in mock_print.call_args_list]
            print_text = ' '.join(print_calls)
            assert "Error getting status" in print_text
    
    @pytest.mark.asyncio
    async def test_cmd_metrics_with_exception(self, debugger, mock_orchestrator):
        """Test metrics command when get_agent_metrics raises an exception."""
        mock_orchestrator.get_agent_metrics = AsyncMock(side_effect=Exception("Metrics error"))
        
        with patch('builtins.print') as mock_print:
            await debugger._cmd_metrics("garden_planner")
            
            # Verify error was handled
            print_calls = [str(call.args[0]) for call in mock_print.call_args_list]
            print_text = ' '.join(print_calls)
            assert "Error getting metrics" in print_text


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])