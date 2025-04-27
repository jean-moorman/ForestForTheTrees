from enum import Enum, auto

class FeatureDevelopmentState(Enum):
    """States for feature development process"""
    PLANNING = auto()      # Initial planning phase
    ELABORATION = auto()   # Requirement elaboration
    TEST_CREATION = auto() # Creating tests for the feature
    IMPLEMENTATION = auto() # Implementing the feature
    TESTING = auto()       # Running tests
    INTEGRATION = auto()   # Integrating with other features
    COMPLETED = auto()     # Feature development complete
    FAILED = auto()        # Feature development failed

class FeaturePerformanceMetrics(Enum):
    """Metrics for evaluating feature performance"""
    CODE_QUALITY = auto()    # Static code quality 
    TEST_COVERAGE = auto()   # Test coverage percentage
    BUILD_STABILITY = auto() # Stability of builds
    MAINTAINABILITY = auto() # Code maintainability score
    RUNTIME_EFFICIENCY = auto() # Resource usage efficiency
    INTEGRATION_SCORE = auto() # Integration with other features