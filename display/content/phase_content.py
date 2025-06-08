"""
Phase content area for displaying agent information.
"""
import logging
from typing import Dict, Any, Optional

from PyQt6.QtWidgets import QScrollArea, QWidget, QVBoxLayout, QLabel

from interfaces import AgentState
from .agent_output import AgentOutputWidget

logger = logging.getLogger(__name__)


class PhaseContentArea(QScrollArea):
    """Scrollable area for displaying phase-specific content."""
    
    def __init__(self, phase: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.phase = phase
        self._init_ui()
        self._setup_agents()

    def _init_ui(self) -> None:
        """Initialize UI components."""
        self.setWidgetResizable(True)
        self.setMinimumWidth(400)
        
        content = QWidget()
        self.setWidget(content)
        layout = QVBoxLayout(content)
        
        header = QLabel(self.phase.replace('_', ' ').title())
        header.setStyleSheet("font-size: 14px; font-weight: bold")
        layout.addWidget(header)
        
        self.agent_widgets: Dict[str, AgentOutputWidget] = {}

    def _setup_agents(self) -> None:
        """Set up agent configurations."""
        self.agents = {
            'phase_zero': ['monitoring', 'soil', 'microbial', 'root_system', 
                          'mycelial', 'insect', 'bird', 'pollinator', 'evolution'],
            'phase_one': ['garden_planner', 'environmental_analysis', 
                         'root_system_architect', 'tree_placement']
        }

    def update_content(self, agent_outputs: Dict[str, Any], 
                      agent_states: Dict[str, AgentState]) -> None:
        """Update content area with new agent outputs and states."""
        for agent_id, output in agent_outputs.items():
            self._ensure_agent_widget(agent_id)
            self.agent_widgets[agent_id].update_output(
                output, 
                agent_states.get(agent_id, AgentState.READY)
            )

    def _ensure_agent_widget(self, agent_id: str) -> None:
        """Create agent widget if it doesn't exist."""
        if agent_id not in self.agent_widgets:
            widget = AgentOutputWidget(agent_id)
            self.widget().layout().addWidget(widget)
            self.agent_widgets[agent_id] = widget

    def update_phase_one_progress(self, current_agent: str) -> None:
        """Update progress indicators for phase one agents."""
        sequence = self.agents.get('phase_one', [])
        try:
            current_idx = sequence.index(current_agent)
            
            for agent in sequence[:current_idx]:
                if agent in self.agent_widgets:
                    self.agent_widgets[agent].mark_complete()
                
            if current_idx < len(sequence) and current_agent in self.agent_widgets:
                self.agent_widgets[current_agent].show_progress()
                
        except ValueError:
            logger.error(f"Invalid agent {current_agent} in phase one sequence")