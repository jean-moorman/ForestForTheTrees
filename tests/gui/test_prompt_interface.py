"""
Comprehensive tests for PromptInterface and async operations

Tests the user input interface including:
- Prompt input and validation
- Submit button state management
- Signal emission for prompt submission
- Async operation integration
- User interaction handling
- Input/output flow
"""

import asyncio
import pytest
import time
from typing import List
from unittest.mock import MagicMock, AsyncMock

from PyQt6.QtWidgets import QLineEdit, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtTest import QTest

from display import PromptInterface, AsyncHelper, AsyncWorker
from .conftest import GuiTestBase, TestSignalWaiter, async_wait_for_condition

class TestPromptInterface(GuiTestBase):
    """Test suite for PromptInterface functionality."""
    
    @pytest.mark.asyncio
    async def test_prompt_interface_initialization(self, display_test_base):
        """Test PromptInterface initializes correctly."""
        prompt_interface = PromptInterface()
        display_test_base.register_widget(prompt_interface)
        
        # Check basic initialization
        assert prompt_interface is not None
        assert isinstance(prompt_interface.layout(), QHBoxLayout)
        
        # Check UI components
        assert hasattr(prompt_interface, 'prompt_input')
        assert hasattr(prompt_interface, 'submit_button')
        assert isinstance(prompt_interface.prompt_input, QLineEdit)
        assert isinstance(prompt_interface.submit_button, QPushButton)
        
        # Check initial state
        assert prompt_interface.prompt_input.text() == ""
        assert not prompt_interface.submit_button.isEnabled()
        assert prompt_interface.prompt_input.placeholderText() == "Enter your task prompt..."
        assert prompt_interface.submit_button.text() == "Submit"
        
    @pytest.mark.asyncio
    async def test_submit_button_state_management(self, display_test_base):
        """Test submit button enable/disable based on input."""
        prompt_interface = PromptInterface()
        display_test_base.register_widget(prompt_interface)
        
        # Initially disabled
        assert not prompt_interface.submit_button.isEnabled()
        
        # Enable when text is entered
        prompt_interface.prompt_input.setText("Test prompt")
        display_test_base.process_events()
        assert prompt_interface.submit_button.isEnabled()
        
        # Disable when text is cleared
        prompt_interface.prompt_input.clear()
        display_test_base.process_events()
        assert not prompt_interface.submit_button.isEnabled()
        
        # Test with whitespace-only text
        prompt_interface.prompt_input.setText("   ")
        display_test_base.process_events()
        assert not prompt_interface.submit_button.isEnabled()
        
        # Test with mixed content
        prompt_interface.prompt_input.setText("  Valid prompt  ")
        display_test_base.process_events()
        assert prompt_interface.submit_button.isEnabled()
        
    @pytest.mark.asyncio
    async def test_prompt_submission_signal(self, display_test_base):
        """Test prompt submission signal emission."""
        prompt_interface = PromptInterface()
        display_test_base.register_widget(prompt_interface)
        
        # Set up signal capture
        submitted_prompts = []
        prompt_interface.prompt_submitted.connect(lambda text: submitted_prompts.append(text))
        
        # Enter test prompt
        test_prompt = "Create a web application"
        prompt_interface.prompt_input.setText(test_prompt)
        display_test_base.process_events()
        
        # Submit via button click
        self.simulate_mouse_click(prompt_interface.submit_button)
        display_test_base.process_events()
        
        # Verify signal emission
        assert len(submitted_prompts) == 1
        assert submitted_prompts[0] == test_prompt
        
        # Verify input is cleared after submission
        assert prompt_interface.prompt_input.text() == ""
        assert not prompt_interface.submit_button.isEnabled()
        
    @pytest.mark.asyncio
    async def test_prompt_submission_enter_key(self, display_test_base):
        """Test prompt submission via Enter key."""
        prompt_interface = PromptInterface()
        display_test_base.register_widget(prompt_interface)
        
        # Set up signal capture
        submitted_prompts = []
        prompt_interface.prompt_submitted.connect(lambda text: submitted_prompts.append(text))
        
        # Enter test prompt
        test_prompt = "Test Enter key submission"
        prompt_interface.prompt_input.setText(test_prompt)
        display_test_base.process_events()
        
        # Submit via Enter key
        self.simulate_key_press(prompt_interface.prompt_input, Qt.Key.Key_Return)
        display_test_base.process_events()
        
        # Verify signal emission
        assert len(submitted_prompts) == 1
        assert submitted_prompts[0] == test_prompt
        
        # Verify input is cleared
        assert prompt_interface.prompt_input.text() == ""
        
    @pytest.mark.asyncio
    async def test_interface_disable_during_processing(self, display_test_base):
        """Test interface disabling during prompt processing."""
        prompt_interface = PromptInterface()
        display_test_base.register_widget(prompt_interface)
        
        # Enter prompt
        prompt_interface.prompt_input.setText("Test prompt")
        display_test_base.process_events()
        assert prompt_interface.isEnabled()
        
        # Simulate submission processing
        prompt_interface.setEnabled(False)
        display_test_base.process_events()
        
        # Interface should be disabled
        assert not prompt_interface.isEnabled()
        assert not prompt_interface.prompt_input.isEnabled()
        assert not prompt_interface.submit_button.isEnabled()
        
        # Reset interface
        prompt_interface.reset()
        display_test_base.process_events()
        
        # Interface should be re-enabled
        assert prompt_interface.isEnabled()
        
    @pytest.mark.asyncio
    async def test_prompt_interface_reset(self, display_test_base):
        """Test prompt interface reset functionality."""
        prompt_interface = PromptInterface()
        display_test_base.register_widget(prompt_interface)
        
        # Set up initial state (disabled during processing)
        prompt_interface.prompt_input.setText("Some text")
        prompt_interface.setEnabled(False)
        display_test_base.process_events()
        
        # Reset interface
        prompt_interface.reset()
        display_test_base.process_events()
        
        # Should be enabled and focused
        assert prompt_interface.isEnabled()
        # Note: Focus testing in Qt can be unreliable in headless mode
        
    @pytest.mark.asyncio
    async def test_long_prompt_handling(self, display_test_base):
        """Test handling of very long prompts."""
        prompt_interface = PromptInterface()
        display_test_base.register_widget(prompt_interface)
        
        # Create a very long prompt
        long_prompt = "Create a comprehensive web application " * 100  # Very long text
        
        # Set up signal capture
        submitted_prompts = []
        prompt_interface.prompt_submitted.connect(lambda text: submitted_prompts.append(text))
        
        # Enter long prompt
        prompt_interface.prompt_input.setText(long_prompt)
        display_test_base.process_events()
        
        # Should enable submit button
        assert prompt_interface.submit_button.isEnabled()
        
        # Submit
        self.simulate_mouse_click(prompt_interface.submit_button)
        display_test_base.process_events()
        
        # Should handle long prompt
        assert len(submitted_prompts) == 1
        assert submitted_prompts[0] == long_prompt
        
    @pytest.mark.asyncio
    async def test_special_characters_in_prompt(self, display_test_base):
        """Test handling of special characters in prompts."""
        prompt_interface = PromptInterface()
        display_test_base.register_widget(prompt_interface)
        
        # Test prompts with special characters
        special_prompts = [
            "Create a web app with UTF-8: ñáéíóú",
            "Handle symbols: @#$%^&*()_+-={}[]|\\:;\"'<>?,./",
            "Multi-line\nprompt\nwith\nbreaks",
            "Prompt with\ttabs\tand    spaces",
            "Emojis: 🌲🔥💧🌍"
        ]
        
        submitted_prompts = []
        prompt_interface.prompt_submitted.connect(lambda text: submitted_prompts.append(text))
        
        for special_prompt in special_prompts:
            # Clear previous
            prompt_interface.prompt_input.clear()
            
            # Enter special prompt
            prompt_interface.prompt_input.setText(special_prompt)
            display_test_base.process_events()
            
            # Submit
            self.simulate_mouse_click(prompt_interface.submit_button)
            display_test_base.process_events()
            
        # Verify all special prompts were handled
        assert len(submitted_prompts) == len(special_prompts)
        for i, expected in enumerate(special_prompts):
            assert submitted_prompts[i] == expected


class TestAsyncHelper(GuiTestBase):
    """Test suite for AsyncHelper functionality."""
    
    @pytest.mark.asyncio
    async def test_async_helper_initialization(self, display_test_base):
        """Test AsyncHelper initializes correctly."""
        # Create a mock parent
        parent = MagicMock()
        async_helper = AsyncHelper(parent)
        
        # Check initialization
        assert async_helper.parent == parent
        assert not async_helper._shutdown
        assert isinstance(async_helper._workers, list)
        assert len(async_helper._workers) == 0
        
    @pytest.mark.asyncio
    async def test_run_coroutine_success(self, display_test_base):
        """Test successful coroutine execution."""
        parent = MagicMock()
        async_helper = AsyncHelper(parent)
        
        # Define test coroutine
        async def test_coro():
            await asyncio.sleep(0.1)
            return "success_result"
        
        # Set up result capture
        results = []
        def capture_result(result):
            results.append(result)
        
        # Run coroutine
        async_helper.run_coroutine(test_coro(), callback=capture_result)
        
        # Wait for completion
        await display_test_base.async_process_events(0.3)
        
        # Verify result
        assert len(results) == 1
        assert results[0] == "success_result"
        
        # Workers should be cleaned up
        assert len(async_helper._workers) == 0
        
    @pytest.mark.asyncio
    async def test_run_coroutine_error(self, display_test_base):
        """Test coroutine execution with error."""
        parent = MagicMock()
        parent._handle_error = MagicMock()
        async_helper = AsyncHelper(parent)
        
        # Define failing coroutine
        async def failing_coro():
            await asyncio.sleep(0.1)
            raise ValueError("Test error")
        
        # Run coroutine
        async_helper.run_coroutine(failing_coro())
        
        # Wait for completion
        await display_test_base.async_process_events(0.3)
        
        # Error should be handled
        parent._handle_error.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_async_helper_shutdown(self, display_test_base):
        """Test AsyncHelper shutdown functionality."""
        parent = MagicMock()
        async_helper = AsyncHelper(parent)
        
        # Create long-running coroutine
        async def long_coro():
            await asyncio.sleep(10)  # Will be cancelled
            return "should_not_complete"
        
        # Start coroutine
        async_helper.run_coroutine(long_coro())
        
        # Verify worker was added
        assert len(async_helper._workers) == 1
        
        # Shutdown
        async_helper.stop_all()
        
        # Should set shutdown flag
        assert async_helper._shutdown
        
        # Wait for cleanup
        await display_test_base.async_process_events(0.2)
        
        # Workers should be cleaned up
        assert len(async_helper._workers) == 0
        
    @pytest.mark.asyncio
    async def test_async_helper_reject_after_shutdown(self, display_test_base):
        """Test that AsyncHelper rejects new tasks after shutdown."""
        parent = MagicMock()
        async_helper = AsyncHelper(parent)
        
        # Shutdown first
        async_helper.stop_all()
        
        # Try to run coroutine after shutdown
        async def test_coro():
            return "should_be_rejected"
        
        # Should log warning and not execute
        async_helper.run_coroutine(test_coro())
        
        # No workers should be created
        assert len(async_helper._workers) == 0


class TestAsyncWorker(GuiTestBase):
    """Test suite for AsyncWorker functionality."""
    
    @pytest.mark.asyncio
    async def test_async_worker_initialization(self, display_test_base):
        """Test AsyncWorker initializes correctly."""
        async def test_coro():
            return "test"
        
        worker = AsyncWorker(test_coro())
        
        # Check initialization
        assert worker._coro is not None
        assert worker._task is None
        
    @pytest.mark.asyncio
    async def test_async_worker_execution(self, display_test_base):
        """Test AsyncWorker successful execution."""
        async def test_coro():
            await asyncio.sleep(0.1)
            return "worker_result"
        
        worker = AsyncWorker(test_coro())
        
        # Set up signal capture
        results = []
        worker.finished.connect(lambda result: results.append(result))
        
        # Start worker
        worker.start()
        
        # Wait for completion
        await display_test_base.async_process_events(0.3)
        
        # Verify result
        assert len(results) == 1
        assert results[0] == "worker_result"
        
    @pytest.mark.asyncio
    async def test_async_worker_error_handling(self, display_test_base):
        """Test AsyncWorker error handling."""
        async def failing_coro():
            await asyncio.sleep(0.1)
            raise RuntimeError("Worker test error")
        
        worker = AsyncWorker(failing_coro())
        
        # Set up error capture
        errors = []
        worker.error.connect(lambda error_info: errors.append(error_info))
        
        # Start worker
        worker.start()
        
        # Wait for completion
        await display_test_base.async_process_events(0.3)
        
        # Verify error was captured
        assert len(errors) == 1
        assert "Worker test error" in errors[0]['error']
        assert 'traceback' in errors[0]
        
    @pytest.mark.asyncio
    async def test_async_worker_cancellation(self, display_test_base):
        """Test AsyncWorker cancellation."""
        async def long_coro():
            await asyncio.sleep(10)  # Will be cancelled
            return "should_not_complete"
        
        worker = AsyncWorker(long_coro())
        
        # Set up signal capture
        errors = []
        worker.error.connect(lambda error_info: errors.append(error_info))
        
        # Start worker
        worker.start()
        
        # Give it a moment to start
        await asyncio.sleep(0.1)
        
        # Cancel worker
        worker.cancel()
        
        # Wait for cancellation
        await display_test_base.async_process_events(0.2)
        
        # Should receive cancellation error
        assert len(errors) == 1
        assert "cancelled" in errors[0]['error'].lower()


@pytest.mark.asyncio
class TestPromptInterfaceIntegration:
    """Integration tests for PromptInterface with async operations."""
    
    async def test_prompt_interface_with_async_processing(self, display_test_base):
        """Test PromptInterface integration with async processing."""
        prompt_interface = PromptInterface()
        display_test_base.register_widget(prompt_interface)
        
        # Create async helper for processing
        async_helper = AsyncHelper(MagicMock())
        
        # Set up processing function
        processed_prompts = []
        async def process_prompt(prompt):
            await asyncio.sleep(0.1)  # Simulate processing time
            processed_prompts.append(prompt)
            return f"Processed: {prompt}"
        
        # Connect prompt submission to async processing
        def handle_prompt_submission(prompt):
            prompt_interface.setEnabled(False)  # Disable during processing
            
            def on_complete(result):
                processed_prompts.append(f"Completed: {result}")
                prompt_interface.reset()  # Re-enable interface
                
            async_helper.run_coroutine(process_prompt(prompt), callback=on_complete)
        
        prompt_interface.prompt_submitted.connect(handle_prompt_submission)
        
        # Submit test prompt
        test_prompt = "Integration test prompt"
        prompt_interface.prompt_input.setText(test_prompt)
        self.simulate_mouse_click(prompt_interface.submit_button)
        
        # Wait for processing
        await display_test_base.async_process_events(0.3)
        
        # Verify processing occurred
        assert len(processed_prompts) >= 1
        assert test_prompt in processed_prompts[0]
        
        # Interface should be re-enabled
        assert prompt_interface.isEnabled()
        
    async def test_prompt_interface_performance(self, display_test_base):
        """Test PromptInterface performance with rapid inputs."""
        prompt_interface = PromptInterface()
        display_test_base.register_widget(prompt_interface)
        
        # Rapid text input simulation
        start_time = time.time()
        
        for i in range(100):
            prompt_interface.prompt_input.setText(f"Rapid input {i}")
            display_test_base.app.processEvents()
            
        end_time = time.time()
        
        # Should handle rapid input efficiently
        input_time = end_time - start_time
        assert input_time < 1.0, f"Rapid input took too long: {input_time}s"
        
        # Final state should be correct
        assert "Rapid input 99" in prompt_interface.prompt_input.text()
        assert prompt_interface.submit_button.isEnabled()
        
    async def test_prompt_interface_memory_management(self, display_test_base):
        """Test PromptInterface memory management with many submissions."""
        prompt_interface = PromptInterface()
        display_test_base.register_widget(prompt_interface)
        
        # Track submissions
        submissions = []
        prompt_interface.prompt_submitted.connect(lambda text: submissions.append(text))
        
        # Submit many prompts
        for i in range(50):
            prompt_interface.prompt_input.setText(f"Memory test prompt {i}")
            self.simulate_mouse_click(prompt_interface.submit_button)
            display_test_base.process_events()
            
        # All submissions should be captured
        assert len(submissions) == 50
        
        # Interface should remain responsive
        assert prompt_interface.prompt_input.text() == ""
        assert not prompt_interface.submit_button.isEnabled()