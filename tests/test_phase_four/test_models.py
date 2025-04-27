"""Tests for phase_four models module."""

import unittest
import time
from phase_four.models import (
    CompilerType,
    CompilationState,
    CompilationResult,
    CompilationContext
)


class TestCompilerType(unittest.TestCase):
    """Test cases for CompilerType enum."""
    
    def test_compiler_types_exist(self):
        """Test that all expected compiler types exist."""
        self.assertTrue(hasattr(CompilerType, "FORMAT"))
        self.assertTrue(hasattr(CompilerType, "STYLE"))
        self.assertTrue(hasattr(CompilerType, "LINT"))
        self.assertTrue(hasattr(CompilerType, "TYPE"))
        self.assertTrue(hasattr(CompilerType, "SECURITY"))
        
    def test_compiler_types_unique(self):
        """Test that all compiler types have unique values."""
        values = set()
        for compiler_type in CompilerType:
            self.assertNotIn(compiler_type.value, values)
            values.add(compiler_type.value)


class TestCompilationState(unittest.TestCase):
    """Test cases for CompilationState enum."""
    
    def test_compilation_states_exist(self):
        """Test that all expected compilation states exist."""
        self.assertTrue(hasattr(CompilationState, "PENDING"))
        self.assertTrue(hasattr(CompilationState, "RUNNING"))
        self.assertTrue(hasattr(CompilationState, "FAILED"))
        self.assertTrue(hasattr(CompilationState, "SUCCEEDED"))
        self.assertTrue(hasattr(CompilationState, "ERROR"))
        
    def test_compilation_states_unique(self):
        """Test that all compilation states have unique values."""
        values = set()
        for state in CompilationState:
            self.assertNotIn(state.value, values)
            values.add(state.value)


class TestCompilationResult(unittest.TestCase):
    """Test cases for CompilationResult dataclass."""
    
    def test_init_with_defaults(self):
        """Test initialization with only required fields."""
        result = CompilationResult(compiler_type=CompilerType.FORMAT)
        
        self.assertEqual(result.compiler_type, CompilerType.FORMAT)
        self.assertEqual(result.state, CompilationState.PENDING)
        self.assertFalse(result.success)
        self.assertEqual(result.output, "")
        self.assertEqual(result.error_message, "")
        self.assertEqual(result.execution_time, 0.0)
        self.assertEqual(result.issues, [])
        
    def test_init_with_all_fields(self):
        """Test initialization with all fields."""
        issues = [{"type": "error", "message": "Test issue"}]
        
        result = CompilationResult(
            compiler_type=CompilerType.LINT,
            state=CompilationState.FAILED,
            success=False,
            output="Test output",
            error_message="Test error",
            execution_time=1.5,
            issues=issues
        )
        
        self.assertEqual(result.compiler_type, CompilerType.LINT)
        self.assertEqual(result.state, CompilationState.FAILED)
        self.assertFalse(result.success)
        self.assertEqual(result.output, "Test output")
        self.assertEqual(result.error_message, "Test error")
        self.assertEqual(result.execution_time, 1.5)
        self.assertEqual(result.issues, issues)


class TestCompilationContext(unittest.TestCase):
    """Test cases for CompilationContext dataclass."""
    
    def test_init_with_required_fields(self):
        """Test initialization with only required fields."""
        ctx = CompilationContext(
            feature_code="def test(): pass",
            feature_id="test_feature",
            source_file_path="/tmp/test.py"
        )
        
        self.assertEqual(ctx.feature_code, "def test(): pass")
        self.assertEqual(ctx.feature_id, "test_feature")
        self.assertEqual(ctx.source_file_path, "/tmp/test.py")
        self.assertEqual(ctx.results, {})
        self.assertEqual(ctx.current_stage, CompilerType.FORMAT)
        self.assertEqual(ctx.max_iterations, 5)
        self.assertEqual(ctx.current_iteration, 0)
        # start_time should be close to now
        self.assertAlmostEqual(ctx.start_time, time.time(), delta=2)
        
    def test_init_with_custom_fields(self):
        """Test initialization with custom fields."""
        results = {
            CompilerType.FORMAT: CompilationResult(compiler_type=CompilerType.FORMAT, success=True)
        }
        
        ctx = CompilationContext(
            feature_code="def test(): pass",
            feature_id="test_feature",
            source_file_path="/tmp/test.py",
            results=results,
            current_stage=CompilerType.STYLE,
            max_iterations=10,
            current_iteration=2,
        )
        
        self.assertEqual(ctx.feature_code, "def test(): pass")
        self.assertEqual(ctx.feature_id, "test_feature")
        self.assertEqual(ctx.source_file_path, "/tmp/test.py")
        self.assertEqual(ctx.results, results)
        self.assertEqual(ctx.current_stage, CompilerType.STYLE)
        self.assertEqual(ctx.max_iterations, 10)
        self.assertEqual(ctx.current_iteration, 2)


if __name__ == "__main__":
    unittest.main()