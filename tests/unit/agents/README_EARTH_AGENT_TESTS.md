# Earth Agent Comprehensive Test Suite

This directory contains a comprehensive test suite for the Earth Agent's core validation logic, designed to test real functionality without relying on mocks that could hide actual system issues.

## 🎯 Test Philosophy

These tests follow the principle of **testing real functionality** rather than mocking critical components. The goal is to:

- **Expose Real Issues**: Use actual Earth Agent validation logic with real LLM processing
- **Test Actual Behavior**: Validate decision-making accuracy with real Garden Planner outputs  
- **Exercise Full Workflows**: Test reflection-revision cycles with real system components
- **Verify Integration**: Ensure proper interaction between Earth Agent and other system components

## 📁 Test Structure

### Unit Tests

#### `test_earth_agent_validation_core.py`
**Core validation logic and basic functionality**
- Input structure validation with various malformed inputs
- Validation history tracking and management
- Issue severity counting and classification
- Validation cycle counter operations
- State updates based on validation results
- Error response creation and handling
- Metrics recording functionality

#### `test_earth_agent_validation_accuracy.py`  
**Validation decision accuracy with real scenarios**
- High-quality outputs that should be APPROVED
- Poor-quality outputs that should be REJECTED
- Moderate outputs that should be CORRECTED
- Misaligned outputs that contradict user requests
- Issue type and severity classification accuracy
- Validation decision rule adherence
- Consistency testing across multiple runs

#### `test_earth_agent_reflection_revision.py`
**Reflection and revision workflow testing**
- Reflection process with borderline validation cases
- Complex scenarios requiring detailed analysis
- Error handling in reflection workflows
- State persistence during reflection
- Circuit breaker integration with reflection
- Revision quality improvement verification
- Critical improvement detection logic

#### `test_earth_agent_error_handling.py`
**Comprehensive error handling and edge cases**
- None and empty input handling
- Non-dictionary input types
- Missing required fields
- Circuit breaker failure scenarios
- State manager error handling
- Memory tracking failures
- Large input processing
- Unicode and special character support
- Validation cycle edge cases

### Integration Tests

#### `test_earth_agent_full_validation_workflow.py`
**Complete end-to-end validation workflows**
- Simple user request validation workflow
- Complex multi-requirement validation scenarios
- Multiple refinement cycle workflows
- Garden Planner Validator integration
- Metrics and state tracking throughout process
- Error recovery in full workflow
- Real Garden Planner output processing

## 🚀 Running Tests

### Run All Tests
```bash
# Run complete test suite
python run_earth_agent_tests.py

# Or use pytest directly
python -m pytest . -v --asyncio-mode=auto
```

### Run Specific Test Categories
```bash
# Core validation logic
python run_earth_agent_tests.py core

# Validation accuracy
python run_earth_agent_tests.py accuracy  

# Reflection and revision
python run_earth_agent_tests.py reflection

# Error handling
python run_earth_agent_tests.py errors

# Integration tests
python run_earth_agent_tests.py integration
```

### Run Individual Test Files
```bash
# Core functionality tests
python -m pytest test_earth_agent_validation_core.py -v

# Accuracy tests (may take longer due to LLM processing)
python -m pytest test_earth_agent_validation_accuracy.py -v

# Reflection tests
python -m pytest test_earth_agent_reflection_revision.py -v

# Error handling tests  
python -m pytest test_earth_agent_error_handling.py -v
```

## 📊 Test Coverage Areas

### ✅ Covered Areas

1. **Input Validation**
   - Structure validation with various input types
   - Required field verification
   - Type checking and error handling

2. **Core Validation Logic**
   - Validation decision accuracy (APPROVED/CORRECTED/REJECTED)
   - Issue classification by type and severity
   - Validation history tracking
   - Cycle management

3. **Reflection-Revision Process**
   - Reflection triggering conditions
   - Critical improvement detection
   - Revision application logic
   - Quality improvement verification

4. **Error Handling**
   - Malformed input handling
   - Component failure recovery
   - Edge case processing
   - Graceful degradation

5. **Integration Workflows**
   - End-to-end validation processes
   - Garden Planner Validator coordination
   - State management throughout workflow
   - Metrics tracking and reporting

### 🎯 Test Quality Features

1. **Real LLM Processing**: Tests use actual Earth Agent prompts and LLM responses
2. **Realistic Data**: Garden Planner outputs represent real-world scenarios
3. **No Critical Mocking**: Avoids mocking core validation logic that could hide issues
4. **Comprehensive Scenarios**: Covers excellent, poor, borderline, and problematic cases
5. **Error Resilience**: Tests system behavior under various failure conditions

## 🔧 Test Configuration

### Resource Setup
Tests use real resource managers:
- `EventQueue` for event handling
- `StateManager` for persistent state
- `MetricsManager` for tracking
- `MemoryMonitor` for resource monitoring
- `HealthTracker` for agent health

### Test Timeouts
- Standard tests: 30 seconds per test
- LLM processing tests: 60-120 seconds per test
- Integration tests: 300 seconds per test

### Async Test Support
All tests use `pytest-asyncio` with `asyncio-mode=auto` for proper async/await support.

## 📈 Expected Test Outcomes

### Unit Tests
- **Core Tests**: Should pass quickly (~30 seconds total)
- **Accuracy Tests**: May take 5-10 minutes due to real LLM processing
- **Reflection Tests**: May take 3-5 minutes due to reflection workflows
- **Error Tests**: Should pass quickly (~1 minute total)

### Integration Tests
- **Full Workflow Tests**: May take 10-15 minutes due to complete validation cycles

### Test Result Interpretation
- ✅ **PASSED**: Functionality working as expected
- ❌ **FAILED**: Issue detected in Earth Agent logic
- ⚠️ **TIMEOUT**: LLM processing took longer than expected (may need retry)

## 🐛 Debugging Failed Tests

### Common Issues
1. **LLM Processing Timeouts**: Increase timeout values or retry
2. **Resource Conflicts**: Ensure proper cleanup between tests
3. **State Persistence**: Check state manager initialization
4. **Circuit Breaker Issues**: Verify circuit breaker configuration

### Debug Commands
```bash
# Run with detailed output
python -m pytest test_earth_agent_validation_core.py -v -s --tb=long

# Run single test with debugging
python -m pytest test_earth_agent_validation_core.py::TestEarthAgentValidationCore::test_input_structure_validation_valid_output -v -s
```

## 🔍 Test Verification

These tests verify that the Earth Agent:

1. **Correctly validates** Garden Planner outputs against user requests
2. **Accurately classifies** issues by type and severity
3. **Properly applies** reflection and revision workflows
4. **Handles errors** gracefully without crashing
5. **Integrates properly** with other system components
6. **Maintains state** correctly throughout validation processes
7. **Records metrics** accurately for monitoring and analysis

The comprehensive nature of these tests ensures that the Earth Agent's sophisticated validation logic works reliably in real-world scenarios.