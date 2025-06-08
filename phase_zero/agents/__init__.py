from phase_zero.agents.monitoring import MonitoringAgent
from phase_zero.agents.description_analysis import SunAgent, ShadeAgent
from phase_zero.agents.requirement_analysis import SoilAgent, MicrobialAgent
from phase_zero.agents.data_flow import MycelialAgent, WormAgent
from phase_zero.agents.structural import BirdAgent, TreeAgent
from phase_zero.agents.optimization import PollinatorAgent
from phase_zero.agents.synthesis import EvolutionAgent

__all__ = [
    'MonitoringAgent',
    'SunAgent',        # Dual-perspective description analysis
    'ShadeAgent',      # Dual-perspective description conflicts
    'SoilAgent',       # Dual-perspective requirements analysis
    'MicrobialAgent',  # Dual-perspective requirements conflicts
    'MycelialAgent',   # Dual-perspective data flow conflicts
    'WormAgent',       # Dual-perspective data flow analysis
    'BirdAgent',       # Dual-perspective structural conflicts
    'TreeAgent',       # Dual-perspective structural analysis
    'PollinatorAgent', # Enhanced cross-guideline optimization
    'EvolutionAgent'   # Enhanced dual-perspective synthesis
]