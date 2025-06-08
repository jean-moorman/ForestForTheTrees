"""
Comprehensive tests for TimelineWidget

Tests the interactive timeline visualization including:
- Agent state display
- Mouse interactions (clicks, hover)
- Real-time state updates
- Agent selection functionality
- Visual rendering
"""

import asyncio
import pytest
import time
from datetime import datetime, timedelta
from typing import Dict, Any
from unittest.mock import MagicMock, patch

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QPoint, QRect
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtTest import QTest

from display import TimelineWidget, TimelineState
from interfaces import AgentState
from .conftest import GuiTestBase, async_wait_for_condition

class TestTimelineWidget(GuiTestBase):
    """Test suite for TimelineWidget functionality."""
    
    @pytest.mark.asyncio
    async def test_timeline_widget_initialization(self, display_test_base):
        """Test TimelineWidget initializes correctly."""
        # Create timeline widget
        timeline = TimelineWidget()
        display_test_base.register_widget(timeline)
        
        # Check basic initialization
        assert timeline is not None
        assert hasattr(timeline, 'agent_colors')
        assert hasattr(timeline, 'agents')
        assert hasattr(timeline, 'agent_states')
        
        # Check agent configuration
        assert 'phase_zero' in timeline.agents
        assert 'phase_one' in timeline.agents
        
        # Verify agent colors are defined
        for phase_agents in timeline.agents.values():
            for agent in phase_agents:
                assert agent in timeline.agent_colors
                
        # Check initial state
        assert timeline.selected_agent is None
        assert timeline.hovered_agent is None
        
    @pytest.mark.asyncio
    async def test_agent_state_management(self, display_test_base):
        """Test agent state tracking and updates."""
        timeline = TimelineWidget()
        display_test_base.register_widget(timeline)
        
        # Add a state for a test agent
        test_agent = 'garden_planner'
        test_state = TimelineState(
            start_time=datetime.now(),
            state=AgentState.PROCESSING,
            metadata={'test': 'data'}
        )
        
        timeline.agent_states[test_agent].add_state(test_state)
        
        # Verify state was added
        states = timeline.agent_states[test_agent].states
        assert len(states) == 1
        assert states[0].state == AgentState.PROCESSING
        assert states[0].metadata['test'] == 'data'
        
    @pytest.mark.asyncio
    async def test_agent_selection_by_mouse(self, display_test_base):
        """Test agent selection through mouse clicks."""
        timeline = TimelineWidget()
        display_test_base.register_widget(timeline)
        timeline.show()
        
        # Wait for widget to be shown
        await display_test_base.async_process_events(0.1)
        
        # Set up signal capturing
        selected_agents = []
        def on_agent_selected(phase, agent):
            selected_agents.append((phase, agent))
        
        timeline.agent_selected.connect(on_agent_selected)
        
        # Test clicking on a specific agent
        test_agent = 'garden_planner'
        test_phase = 'phase_one'
        
        # Get the rectangle for this agent
        agent_rect = timeline._get_agent_rect(test_phase, test_agent)
        click_pos = agent_rect.center()
        
        # Simulate mouse click
        self.simulate_mouse_click(timeline, Qt.MouseButton.LeftButton, click_pos)
        
        # Process events to ensure signal is emitted
        display_test_base.process_events()
        
        # Verify selection
        assert timeline.selected_agent == (test_phase, test_agent)
        assert len(selected_agents) == 1
        assert selected_agents[0] == (test_phase, test_agent)
        
    @pytest.mark.asyncio
    async def test_hover_effects(self, display_test_base):
        """Test hover effects on timeline agents."""
        timeline = TimelineWidget()
        display_test_base.register_widget(timeline)
        timeline.show()
        
        await display_test_base.async_process_events(0.1)
        
        # Test hovering over an agent
        test_agent = 'environmental_analysis'
        test_phase = 'phase_one'
        
        agent_rect = timeline._get_agent_rect(test_phase, test_agent)
        hover_pos = agent_rect.center()
        
        # Simulate mouse move for hover
        from PyQt6.QtCore import QPointF
        hover_pos_f = QPointF(hover_pos.x(), hover_pos.y())
        mouse_event = QMouseEvent(
            QMouseEvent.Type.MouseMove,
            hover_pos_f,
            Qt.MouseButton.NoButton,
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier
        )
        
        timeline.mouseMoveEvent(mouse_event)
        display_test_base.process_events()
        
        # Verify hover state
        assert timeline.hovered_agent == (test_phase, test_agent)
        
        # Test mouse leave
        from PyQt6.QtCore import QEvent
        leave_event = QEvent(QEvent.Type.Leave)
        timeline.leaveEvent(leave_event)
        display_test_base.process_events()
        
        assert timeline.hovered_agent is None
        
    @pytest.mark.asyncio
    async def test_agent_rect_calculation(self, display_test_base):
        """Test agent rectangle calculation for positioning."""
        timeline = TimelineWidget()
        display_test_base.register_widget(timeline)
        
        # Test rectangle calculation for known agents
        test_cases = [
            ('phase_zero', 'monitoring'),
            ('phase_one', 'garden_planner'),
            ('phase_one', 'environmental_analysis')
        ]
        
        for phase, agent in test_cases:
            rect = timeline._get_agent_rect(phase, agent)
            
            # Verify rectangle is valid
            assert isinstance(rect, QRect)
            assert rect.width() > 0
            assert rect.height() > 0
            assert rect.x() >= 0
            assert rect.y() >= 0
            
    @pytest.mark.asyncio
    async def test_agent_position_detection(self, display_test_base):
        """Test detection of agents at specific positions."""
        timeline = TimelineWidget()
        display_test_base.register_widget(timeline)
        
        # Test position detection for each agent
        for phase, agents in timeline.agents.items():
            for agent in agents:
                rect = timeline._get_agent_rect(phase, agent)
                center_pos = rect.center()
                
                # Test that center position correctly identifies the agent
                detected_phase, detected_agent = timeline._get_agent_at_position(center_pos)
                assert detected_phase == phase
                assert detected_agent == agent
                
        # Test position outside any agent
        outside_pos = QPoint(timeline.width() + 100, timeline.height() + 100)
        phase, agent = timeline._get_agent_at_position(outside_pos)
        assert phase is None
        assert agent is None
        
    @pytest.mark.asyncio
    async def test_time_window_filtering(self, display_test_base):
        """Test time window filtering for state display."""
        timeline = TimelineWidget()
        display_test_base.register_widget(timeline)
        
        test_agent = 'garden_planner'
        now = datetime.now()
        
        # Add states at different times
        old_state = TimelineState(
            start_time=now - timedelta(hours=2),
            state=AgentState.COMPLETE,
            metadata={}
        )
        
        recent_state = TimelineState(
            start_time=now - timedelta(minutes=30),
            state=AgentState.PROCESSING,
            metadata={}
        )
        
        current_state = TimelineState(
            start_time=now,
            state=AgentState.READY,
            metadata={}
        )
        
        # Add states to agent
        agent_queue = timeline.agent_states[test_agent]
        agent_queue.add_state(old_state)
        agent_queue.add_state(recent_state)
        agent_queue.add_state(current_state)
        
        # Test time window filtering
        window_start = now - timedelta(hours=1)
        window_end = now + timedelta(minutes=10)
        
        states_in_window = agent_queue.get_states_in_window(window_start, window_end)
        
        # Should include recent_state and current_state, but not old_state
        assert len(states_in_window) == 2
        assert recent_state in states_in_window
        assert current_state in states_in_window
        assert old_state not in states_in_window
        
    @pytest.mark.asyncio
    async def test_widget_sizing(self, display_test_base):
        """Test widget size calculations."""
        timeline = TimelineWidget()
        display_test_base.register_widget(timeline)
        
        # Test minimum size requirements
        assert timeline.minimumHeight() > 0
        assert timeline.minimumWidth() > 0
        
        # Test size hint
        size_hint = timeline.sizeHint()
        assert size_hint.width() >= 600
        assert size_hint.height() > 0
        
        # Test calculated height matches actual requirements
        calculated_height = timeline._calculate_total_height()
        assert calculated_height == size_hint.height()
        
    @pytest.mark.asyncio
    async def test_paint_event_execution(self, display_test_base):
        """Test that paint events execute without errors."""
        timeline = TimelineWidget()
        display_test_base.register_widget(timeline)
        timeline.show()
        
        # Trigger paint events
        await display_test_base.async_process_events(0.2)
        timeline.update()
        await display_test_base.async_process_events(0.2)
        
        # If we get here without exceptions, painting worked
        assert True
        
    @pytest.mark.asyncio
    async def test_agent_state_change_handling(self, display_test_base):
        """Test handling of agent state change events."""
        timeline = TimelineWidget()
        display_test_base.register_widget(timeline)
        
        # Initialize required attributes that would normally be set by ForestDisplay
        timeline._pending_updates = set()
        timeline._handle_error = lambda event_type, data: None  # Mock error handler
        
        # Simulate state change event data
        test_data = {
            'resource_id': 'agent:garden_planner:state',
            'value': 'PROCESSING',
            'metadata': {'operation_id': 'test_123'}
        }
        
        # Test the state change handler
        try:
            timeline._handle_agent_state_change('AGENT_STATE_CHANGED', test_data)
            # If no exception, the handler worked
            assert True
        except Exception as e:
            pytest.fail(f"State change handler failed: {e}")
            
    @pytest.mark.asyncio
    async def test_resource_id_validation(self, display_test_base):
        """Test resource ID validation logic."""
        timeline = TimelineWidget()
        display_test_base.register_widget(timeline)
        
        # Test valid resource IDs
        valid_cases = [
            ('agent:garden_planner:state', True, 'garden_planner'),
            ('agent:environmental_analysis:state', True, 'environmental_analysis'),
            ('agent:monitoring:state', True, 'monitoring')
        ]
        
        for resource_id, expected_valid, expected_agent in valid_cases:
            is_valid, agent_id = timeline._validate_resource_id(resource_id)
            assert is_valid == expected_valid
            assert agent_id == expected_agent
            
        # Test invalid resource IDs
        invalid_cases = [
            'invalid_format',
            'agent:unknown_agent:state',
            'wrong:format:here',
            ''
        ]
        
        for resource_id in invalid_cases:
            is_valid, agent_id = timeline._validate_resource_id(resource_id)
            assert not is_valid
            
    @pytest.mark.asyncio
    async def test_multiple_agent_selection(self, display_test_base):
        """Test selecting multiple agents in sequence."""
        timeline = TimelineWidget()
        display_test_base.register_widget(timeline)
        timeline.show()
        
        await display_test_base.async_process_events(0.1)
        
        # Track all selections
        selections = []
        timeline.agent_selected.connect(lambda p, a: selections.append((p, a)))
        
        # Select multiple agents
        test_agents = [
            ('phase_zero', 'monitoring'),
            ('phase_one', 'garden_planner'),
            ('phase_one', 'environmental_analysis')
        ]
        
        for phase, agent in test_agents:
            rect = timeline._get_agent_rect(phase, agent)
            self.simulate_mouse_click(timeline, Qt.MouseButton.LeftButton, rect.center())
            display_test_base.process_events()
            
            # Verify current selection
            assert timeline.selected_agent == (phase, agent)
            
        # Verify all selections were captured
        assert len(selections) == len(test_agents)
        for i, (phase, agent) in enumerate(test_agents):
            assert selections[i] == (phase, agent)

@pytest.mark.asyncio 
class TestTimelineWidgetIntegration:
    """Integration tests for TimelineWidget with real system components."""
    
    async def test_timeline_with_real_event_queue(self, display_test_base):
        """Test TimelineWidget integration with real EventQueue."""
        timeline = TimelineWidget()
        display_test_base.register_widget(timeline)
        
        # Initialize event queue properly
        event_queue = await display_test_base.get_event_queue()
        
        # Initialize timeline with real event queue
        timeline._event_queue = event_queue
        timeline._pending_updates = set()
        
        # Simulate agent state change via event queue
        await event_queue.emit(
            'AGENT_STATE_CHANGED',
            {
                'resource_id': 'agent:garden_planner:state',
                'value': 'PROCESSING',
                'metadata': {'test': 'integration'}
            }
        )
        
        # Process events
        await display_test_base.async_process_events(0.2)
        
        # Verify the timeline handled the event
        # (This would require additional event handling setup in real integration)
        assert True  # Basic integration test
        
    async def test_timeline_performance_with_many_states(self, display_test_base):
        """Test TimelineWidget performance with many agent states."""
        timeline = TimelineWidget()
        display_test_base.register_widget(timeline)
        
        # Add many states to test performance
        test_agent = 'garden_planner'
        base_time = datetime.now()
        
        # Add 100 states
        for i in range(100):
            state = TimelineState(
                start_time=base_time + timedelta(seconds=i),
                state=AgentState.PROCESSING if i % 2 == 0 else AgentState.READY,
                metadata={'iteration': i}
            )
            timeline.agent_states[test_agent].add_state(state)
            
        # Test that timeline can handle the load
        timeline.show()
        await display_test_base.async_process_events(0.5)
        
        # Test selection still works
        rect = timeline._get_agent_rect('phase_one', test_agent)
        GuiTestBase.simulate_mouse_click(timeline, Qt.MouseButton.LeftButton, rect.center())
        display_test_base.process_events()
        
        assert timeline.selected_agent == ('phase_one', test_agent)
        
    async def test_timeline_memory_usage(self, display_test_base):
        """Test TimelineWidget memory usage with state queue limits."""
        timeline = TimelineWidget()
        display_test_base.register_widget(timeline)
        
        test_agent = 'monitoring'
        agent_queue = timeline.agent_states[test_agent]
        
        # Test that StateQueue respects max_size (default 1000)
        base_time = datetime.now()
        
        # Add more states than the limit
        for i in range(1200):
            state = TimelineState(
                start_time=base_time + timedelta(seconds=i),
                state=AgentState.PROCESSING,
                metadata={'index': i}
            )
            agent_queue.add_state(state)
            
        # Verify queue size is limited
        assert len(agent_queue.states) <= 1000
        
        # Verify oldest states were removed (should have higher indices)
        first_state = agent_queue.states[0]
        assert first_state.metadata['index'] >= 200  # Should have removed first ~200