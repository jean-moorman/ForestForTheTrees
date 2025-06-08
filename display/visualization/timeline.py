"""
Timeline visualization for agent states.
"""
import logging
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QSize, QRect, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen, QMouseEvent, QFont

from interfaces import AgentState

logger = logging.getLogger(__name__)


@dataclass
class TimelineState:
    """Represents a point-in-time state of an agent."""
    start_time: datetime
    state: AgentState
    metadata: Dict[str, Any]


class StateQueue:
    """Manages a queue of agent states with a maximum size."""
    
    def __init__(self, max_size: int = 1000):
        self.states = deque(maxlen=max_size)
        
    def add_state(self, state: TimelineState) -> None:
        """Add a new state to the queue."""
        self.states.append(state)
        
    def get_states_in_window(self, start: datetime, end: datetime) -> List[TimelineState]:
        """Get all states within a time window."""
        return [s for s in self.states if start <= s.start_time <= end]


class TimelineWidget(QWidget):
    """Timeline visualization widget for agent states."""
    
    # Signal emitted when an agent is selected (phase, agent_name)
    agent_selected = pyqtSignal(str, str)
    
    # Color scheme for different agents
    agent_colors = {
        'monitoring': '#4A90E2', 'soil': '#50E3C2', 'microbial': '#F5A623',
        'root_system': '#7ED321', 'mycelial': '#BD10E0', 'insect': '#9013FE',
        'bird': '#417505', 'pollinator': '#D0021B', 'evolution': '#4A4A4A',
        'garden_planner': '#B8E986', 'environmental_analysis': '#7ED321',
        'root_system_architect': '#417505', 'tree_placement': '#50E3C2'
    }

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._init_state()
        self._init_ui()
        self.setMouseTracking(True)
        self._pending_updates = set()

    def _init_state(self) -> None:
        """Initialize timeline state."""
        self.time_window = timedelta(hours=1)
        self.agents = {
            'phase_zero': ['monitoring', 'soil', 'microbial', 'root_system',
                        'mycelial', 'insect', 'bird', 'pollinator', 'evolution'],
            'phase_one': ['garden_planner', 'environmental_analysis',
                        'root_system_architect', 'tree_placement']
        }
        
        # Initialize agent states dictionary
        self.agent_states = {
            agent: StateQueue() 
            for phase in self.agents.values() 
            for agent in phase
        }
        
        self.selected_agent = None
        self.hovered_agent = None
        self.phase_height = 60   
        self.agent_height = 16   
        self.agent_padding = 2   
        self.phase_padding = 10
        
    def _init_ui(self) -> None:
        """Initialize UI properties."""
        self.setMinimumHeight(self._calculate_total_height())
        self.setMinimumWidth(600)
        # Set widget to use stylesheet background
        self.setAutoFillBackground(True)
        self.setStyleSheet("background-color: white;")

    def _calculate_total_height(self) -> int:
        """Calculate total required height for the widget."""
        phase_header_height = 20  # Space for phase labels
        total_height = phase_header_height  # Start with initial header space
        
        # Add height for each phase
        for phase_name, agents in self.agents.items():
            agents_count = len(agents)
            phase_content_height = agents_count * (self.agent_height + self.agent_padding)
            total_height += phase_header_height + phase_content_height + self.phase_padding
            
        # Remove the extra padding at the end
        total_height -= self.phase_padding
        return total_height

    def _get_agent_rect(self, phase: str, agent: str) -> QRect:
        """Get the rectangle for a specific agent in a specific phase."""
        phase_idx = list(self.agents.keys()).index(phase)
        agent_idx = self.agents[phase].index(agent)
        
        # Calculate Y offset by accumulating heights of all previous phases
        y_offset = self._get_phase_start_y(phase_idx)
        y = y_offset + (agent_idx * (self.agent_height + self.agent_padding))
        
        # Fixed bar width instead of full width
        bar_width = 120
        x = 10  # Left padding
        
        return QRect(x, y, bar_width, self.agent_height)
    
    def _get_phase_start_y(self, phase_idx: int) -> int:
        """Get the Y coordinate where a phase starts."""
        phase_header_height = 20  # Space for phase labels
        y = phase_header_height  # Start with header space
        
        # Add heights of all previous phases
        phase_names = list(self.agents.keys())
        for i in range(phase_idx):
            phase_name = phase_names[i]
            agents_in_phase = len(self.agents[phase_name])
            phase_content_height = agents_in_phase * (self.agent_height + self.agent_padding)
            y += phase_header_height + phase_content_height + self.phase_padding
            
        return y

    def _get_agent_at_position(self, pos) -> tuple[Optional[str], Optional[str]]:
        """Get the agent and phase at the given position."""
        for phase in self.agents:
            for agent in self.agents[phase]:
                rect = self._get_agent_rect(phase, agent)
                if rect.contains(pos):
                    return phase, agent
        return None, None

    def mousePressEvent(self, event) -> None:
        """Handle mouse press events for agent selection."""
        phase, agent = self._get_agent_at_position(event.pos())
        if agent:
            self.selected_agent = (phase, agent)
            # Emit signal to update metrics panel
            self.agent_selected.emit(phase, agent)
            self.update()
        event.accept()

    def mouseMoveEvent(self, event) -> None:
        """Handle mouse move events for hover effects."""
        phase, agent = self._get_agent_at_position(event.pos())
        if (phase, agent) != self.hovered_agent:
            self.hovered_agent = (phase, agent) if agent else None
            self.update()
        event.accept()

    def leaveEvent(self, event) -> None:
        """Handle mouse leave events."""
        if self.hovered_agent:
            self.hovered_agent = None
            self.update()
        if event:
            event.accept()

    def paintEvent(self, event) -> None:
        """Paint the timeline widget."""
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # Draw phases and agents
            for phase_idx, (phase, agents) in enumerate(self.agents.items()):
                # Draw phase label
                font = QFont()
                font.setBold(True)
                painter.setFont(font)
                phase_label = phase.replace('_', ' ').title()
                y_offset = self._get_phase_start_y(phase_idx)
                painter.drawText(10, y_offset - 5, phase_label)

                # Draw agents
                for agent in agents:
                    rect = self._get_agent_rect(phase, agent)
                    
                    # Draw agent background
                    color = QColor(self.agent_colors[agent])
                    if (phase, agent) == self.selected_agent:
                        painter.fillRect(rect, color.darker(120))
                    elif (phase, agent) == self.hovered_agent:
                        painter.fillRect(rect, color.lighter(120))
                    else:
                        painter.fillRect(rect, color)

                    # Draw agent label
                    painter.setPen(Qt.GlobalColor.white)
                    font = QFont()
                    font.setPointSize(10)
                    painter.setFont(font)
                    agent_label = agent.replace('_', ' ').title()
                    painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, agent_label)
        finally:
            painter.end()

    def sizeHint(self) -> QSize:
        """Provide size hint for layout management."""
        return QSize(600, self._calculate_total_height())
    
    def _validate_resource_id(self, resource_id: str) -> Tuple[bool, Optional[str]]:
        """
        Validate resource ID format and extract agent ID.
        
        Args:
            resource_id: Resource identifier string
            
        Returns:
            Tuple of (is_valid, agent_id)
        """
        if not resource_id:
            return False, None
            
        parts = resource_id.split(':')
        if len(parts) != 3 or parts[0] != 'agent':
            return False, None
            
        agent_id = parts[1]
        # Verify agent exists in our configuration
        for phase_agents in self.agents.values():
            if agent_id in phase_agents:
                return True, agent_id
                
        return False, None

    def _handle_agent_state_change(self, event_type: str, data: Dict[str, Any]) -> None:
        """Handle agent state change events."""
        try:
            resource_id = data.get('resource_id', '')
            is_valid, agent_id = self._validate_resource_id(resource_id)
            
            if not is_valid:
                logger.error(f"Invalid resource ID format: {resource_id}")
                return
                
            if agent_id not in self.agent_states:
                logger.error(f"Unknown agent ID: {agent_id}")
                return
                
            try:
                new_state = AgentState[data.get('value', 'READY')]
            except KeyError:
                logger.error(f"Invalid agent state: {data.get('value')}")
                return
                
            # Add new state to timeline
            self.agent_states[agent_id].add_state(TimelineState(
                start_time=datetime.now(),
                state=new_state,
                metadata=data.get('metadata', {})
            ))
            
            # Queue update
            self._pending_updates.add(('agent_state', agent_id))
            
        except Exception as e:
            logger.error(f"Error handling agent state change: {e}")
            from resources import ResourceEventTypes
            self._handle_error(
                ResourceEventTypes.ERROR_OCCURRED.value,
                {'error': str(e), 'source': 'agent_state_handler'}
            )