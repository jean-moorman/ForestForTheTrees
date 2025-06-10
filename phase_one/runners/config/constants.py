"""
Configuration Constants for Phase One Runners

Contains application-wide constants and configuration values
for the Phase One runner system.
"""

# Application metadata
APP_NAME = "Phase One Standalone Runner"
APP_DESCRIPTION = "Forest For The Trees (FFTT) Phase One execution system"

# Default configuration values
DEFAULT_LOG_LEVEL = 'INFO'
DEFAULT_LOG_FILE = 'run_phase_one.log'
DEFAULT_TIMEOUT_SECONDS = 300  # 5 minutes

# Event queue identifiers
CLI_QUEUE_ID = "phase_one_cli_queue"
GUI_QUEUE_ID = "phase_one_queue"

# Workflow step definitions
PHASE_ONE_STEPS = [
    "garden_planner",
    "earth_agent_validation", 
    "environmental_analysis",
    "root_system_architect",
    "tree_placement_planner",
    "foundation_refinement"
]

# Agent identifiers and descriptions
PHASE_ONE_AGENTS = [
    ("garden_planner", "Garden Planner Agent"),
    ("earth_agent", "Earth Agent (Validation)"),
    ("environmental_analysis", "Environmental Analysis Agent"),
    ("root_system_architect", "Root System Architect Agent"),
    ("tree_placement_planner", "Tree Placement Planner Agent")
]

# Debugging constants
DEBUG_VALID_STAGES = {
    "garden_planner", "earth_validation", "water_coordination",
    "environmental_analysis", "root_system", "tree_placement",
    "air_summary", "fire_decomposition", "phase_zero", "refinement"
}

# Health check intervals (in milliseconds)
HEALTH_CHECK_INTERVAL_MS = 30000  # 30 seconds

# Retry configuration
DEFAULT_MAX_RETRIES = 2
DEFAULT_RETRY_DELAYS = [5.0, 10.0]  # seconds
DEFAULT_BASE_TIMEOUT = 180.0  # 3 minutes