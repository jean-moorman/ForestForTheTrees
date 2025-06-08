"""
Comprehensive tests for AlertWidget

Tests the alert notification system including:
- Alert creation and display
- Alert level handling (INFO, WARNING, ERROR, CRITICAL)
- Alert pruning and management
- Visual styling and colors
- Multiple alert handling
"""

import pytest
import time
from unittest.mock import MagicMock

from PyQt6.QtWidgets import QTextEdit, QVBoxLayout
from PyQt6.QtCore import Qt

from display import AlertWidget, AlertLevel
from .conftest import GuiTestBase

class TestAlertWidget(GuiTestBase):
    """Test suite for AlertWidget functionality."""
    
    @pytest.mark.asyncio
    async def test_alert_widget_initialization(self, display_test_base):
        """Test AlertWidget initializes correctly."""
        alert_widget = AlertWidget()
        display_test_base.register_widget(alert_widget)
        
        # Check basic initialization
        assert alert_widget is not None
        assert hasattr(alert_widget, 'alerts')
        assert isinstance(alert_widget.alerts, list)
        assert len(alert_widget.alerts) == 0
        
        # Check UI setup
        assert alert_widget.layout() is not None
        assert isinstance(alert_widget.layout(), QVBoxLayout)
        
    @pytest.mark.asyncio
    async def test_add_single_alert(self, display_test_base):
        """Test adding a single alert."""
        alert_widget = AlertWidget()
        display_test_base.register_widget(alert_widget)
        
        # Add an alert
        test_message = "Test alert message"
        alert_widget.add_alert(AlertLevel.INFO, test_message)
        
        # Verify alert was added
        assert len(alert_widget.alerts) == 1
        assert alert_widget.alerts[0] == (AlertLevel.INFO, test_message)
        
        # Verify UI widget was created
        assert alert_widget.layout().count() == 1
        
        # Check the created widget
        alert_display = alert_widget.layout().itemAt(0).widget()
        assert isinstance(alert_display, QTextEdit)
        assert alert_display.toPlainText() == test_message
        assert alert_display.isReadOnly()
        
    @pytest.mark.asyncio
    async def test_alert_level_colors(self, display_test_base):
        """Test that different alert levels get different colors."""
        alert_widget = AlertWidget()
        display_test_base.register_widget(alert_widget)
        
        # Test each alert level
        test_cases = [
            (AlertLevel.INFO, "#4A90E2"),
            (AlertLevel.WARNING, "#F5A623"),
            (AlertLevel.ERROR, "#D0021B"),
            (AlertLevel.CRITICAL, "#B00020")
        ]
        
        for level, expected_color in test_cases:
            # Test color getter
            color = alert_widget._get_alert_color(level)
            assert color == expected_color
            
            # Add alert and check styling
            alert_widget.add_alert(level, f"Test {level.name} message")
            
            # Get the latest alert widget
            latest_widget = alert_widget.layout().itemAt(alert_widget.layout().count() - 1).widget()
            style_sheet = latest_widget.styleSheet()
            assert expected_color in style_sheet
            
    @pytest.mark.asyncio
    async def test_multiple_alerts(self, display_test_base):
        """Test adding multiple alerts."""
        alert_widget = AlertWidget()
        display_test_base.register_widget(alert_widget)
        
        # Add multiple alerts
        alerts_to_add = [
            (AlertLevel.INFO, "First alert"),
            (AlertLevel.WARNING, "Second alert"),
            (AlertLevel.ERROR, "Third alert"),
            (AlertLevel.CRITICAL, "Fourth alert")
        ]
        
        for level, message in alerts_to_add:
            alert_widget.add_alert(level, message)
            
        # Verify all alerts were added
        assert len(alert_widget.alerts) == 4
        assert alert_widget.layout().count() == 4
        
        # Verify alert order (newest should be last)
        for i, (level, message) in enumerate(alerts_to_add):
            assert alert_widget.alerts[i] == (level, message)
            widget = alert_widget.layout().itemAt(i).widget()
            assert widget.toPlainText() == message
            
    @pytest.mark.asyncio
    async def test_alert_pruning(self, display_test_base):
        """Test that old alerts are pruned when limit is exceeded."""
        alert_widget = AlertWidget()
        display_test_base.register_widget(alert_widget)
        
        # Add more than 5 alerts (the default limit)
        for i in range(8):
            alert_widget.add_alert(AlertLevel.INFO, f"Alert {i}")
            
        # Should only keep the latest 5 alerts
        assert alert_widget.layout().count() <= 5
        
        # The remaining alerts should be the most recent ones
        remaining_widgets = []
        for i in range(alert_widget.layout().count()):
            widget = alert_widget.layout().itemAt(i).widget()
            remaining_widgets.append(widget.toPlainText())
            
        # Should contain alerts 3, 4, 5, 6, 7 (the last 5)
        expected_alerts = [f"Alert {i}" for i in range(3, 8)]
        assert remaining_widgets == expected_alerts
        
    @pytest.mark.asyncio
    async def test_alert_widget_properties(self, display_test_base):
        """Test properties of created alert widgets."""
        alert_widget = AlertWidget()
        display_test_base.register_widget(alert_widget)
        
        # Add an alert
        alert_widget.add_alert(AlertLevel.WARNING, "Test alert with properties")
        
        # Get the created widget
        created_widget = alert_widget.layout().itemAt(0).widget()
        
        # Test properties
        assert created_widget.isReadOnly()
        assert created_widget.maximumHeight() == 200
        assert "Test alert with properties" in created_widget.toPlainText()
        
    @pytest.mark.asyncio
    async def test_empty_alert_message(self, display_test_base):
        """Test handling of empty alert messages."""
        alert_widget = AlertWidget()
        display_test_base.register_widget(alert_widget)
        
        # Add alert with empty message
        alert_widget.add_alert(AlertLevel.ERROR, "")
        
        # Should still create the alert
        assert len(alert_widget.alerts) == 1
        assert alert_widget.layout().count() == 1
        
        created_widget = alert_widget.layout().itemAt(0).widget()
        assert created_widget.toPlainText() == ""
        
    @pytest.mark.asyncio
    async def test_long_alert_message(self, display_test_base):
        """Test handling of very long alert messages."""
        alert_widget = AlertWidget()
        display_test_base.register_widget(alert_widget)
        
        # Create a very long message
        long_message = "This is a very long alert message. " * 50
        alert_widget.add_alert(AlertLevel.CRITICAL, long_message)
        
        # Should handle long messages
        assert len(alert_widget.alerts) == 1
        created_widget = alert_widget.layout().itemAt(0).widget()
        assert long_message in created_widget.toPlainText()
        
        # Widget should have word wrap enabled implicitly through QTextEdit
        assert isinstance(created_widget, QTextEdit)
        
    @pytest.mark.asyncio
    async def test_alert_widget_cleanup(self, display_test_base):
        """Test proper cleanup of alert widgets."""
        alert_widget = AlertWidget()
        display_test_base.register_widget(alert_widget)
        
        # Add alerts to trigger pruning
        for i in range(10):
            alert_widget.add_alert(AlertLevel.INFO, f"Alert {i}")
            
        # Process events to ensure widgets are created
        display_test_base.process_events()
        
        # Verify that old widgets are properly cleaned up
        # (This tests the setParent(None) call in _prune_old_alerts)
        assert alert_widget.layout().count() <= 5
        
    @pytest.mark.asyncio
    async def test_alert_levels_enum(self, display_test_base):
        """Test that all AlertLevel enum values work."""
        alert_widget = AlertWidget()
        display_test_base.register_widget(alert_widget)
        
        # Test all enum values
        for level in AlertLevel:
            alert_widget.add_alert(level, f"Test {level.name}")
            
        # Should have 4 alerts (one for each level)
        assert len(alert_widget.alerts) == 4
        assert alert_widget.layout().count() == 4


@pytest.mark.asyncio
class TestAlertWidgetIntegration:
    """Integration tests for AlertWidget with system components."""
    
    async def test_alert_widget_with_system_monitor(self, display_test_base):
        """Test AlertWidget integration with system monitoring."""
        alert_widget = AlertWidget()
        display_test_base.register_widget(alert_widget)
        
        # Simulate system monitor alerts
        system_alerts = [
            (AlertLevel.WARNING, "Memory usage at 80%"),
            (AlertLevel.CRITICAL, "Circuit breaker opened for agent_1"),
            (AlertLevel.ERROR, "Failed to process event"),
            (AlertLevel.INFO, "System health check completed")
        ]
        
        for level, message in system_alerts:
            alert_widget.add_alert(level, message)
            
        # Process events
        display_test_base.process_events()
        
        # Verify all system alerts are displayed
        assert len(alert_widget.alerts) == 4
        
        # Check that critical alerts have proper styling
        for i in range(alert_widget.layout().count()):
            widget = alert_widget.layout().itemAt(i).widget()
            if "Circuit breaker" in widget.toPlainText():
                assert "#B00020" in widget.styleSheet()  # Critical color
                
    async def test_alert_widget_performance(self, display_test_base):
        """Test AlertWidget performance with rapid alert addition."""
        alert_widget = AlertWidget()
        display_test_base.register_widget(alert_widget)
        
        # Rapidly add many alerts
        start_time = time.time()
        
        for i in range(100):
            level = [AlertLevel.INFO, AlertLevel.WARNING, AlertLevel.ERROR, AlertLevel.CRITICAL][i % 4]
            alert_widget.add_alert(level, f"Rapid alert {i}")
            
        end_time = time.time()
        
        # Should complete quickly (less than 1 second)
        assert (end_time - start_time) < 1.0
        
        # Should only show the last 5 alerts due to pruning
        assert alert_widget.layout().count() <= 5
        
        # Process events to ensure UI is updated
        await display_test_base.async_process_events(0.1)
        
    async def test_alert_widget_memory_management(self, display_test_base):
        """Test AlertWidget memory management with many alerts."""
        alert_widget = AlertWidget()
        display_test_base.register_widget(alert_widget)
        
        # Add many alerts to test memory management
        for i in range(1000):
            alert_widget.add_alert(AlertLevel.INFO, f"Memory test alert {i}")
            
            # Periodically process events
            if i % 100 == 0:
                display_test_base.process_events()
                
        # Should maintain reasonable widget count
        assert alert_widget.layout().count() <= 5
        
        # Internal alerts list should also be managed
        # (In a real implementation, you might want to limit this too)
        assert len(alert_widget.alerts) == 1000  # Current implementation keeps all
        
    async def test_alert_widget_threading_safety(self, display_test_base):
        """Test AlertWidget behavior with concurrent access."""
        alert_widget = AlertWidget()
        display_test_base.register_widget(alert_widget)
        
        # Simulate concurrent alert additions from different sources
        import threading
        import time
        
        def add_alerts(prefix, count):
            for i in range(count):
                alert_widget.add_alert(AlertLevel.WARNING, f"{prefix} Alert {i}")
                time.sleep(0.001)  # Small delay to simulate real conditions
                
        # Note: In a real GUI application, all Qt operations should happen
        # on the main thread. This test is more about verifying the widget
        # can handle rapid sequential updates.
        
        add_alerts("Source1", 10)
        add_alerts("Source2", 10)
        
        # Process events
        display_test_base.process_events()
        
        # Should handle the updates gracefully
        assert alert_widget.layout().count() <= 5