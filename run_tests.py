#!/usr/bin/env python3
"""
Simple test runner for the DLP processor tests.
"""

import sys
import subprocess
import os

def run_tests():
    """Run the test suite using pytest."""
    print("🚀 Starting DLP Processor Test Suite...")
    print("=" * 50)
    
    # Check if pytest is available
    try:
        import pytest
        print(f"✅ pytest version {pytest.__version__} found")
    except ImportError:
        print("❌ pytest not found. Installing dependencies...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("✅ Dependencies installed")
    
    # Run tests with coverage
    print("\n🧪 Running tests with coverage...")
    result = subprocess.run([
        sys.executable, "-m", "pytest", 
        "test_dlp_processor.py", 
        "-v", 
        "--cov=dlp_processor",
        "--cov-report=term-missing",
        "--cov-report=html"
    ])
    
    if result.returncode == 0:
        print("\n✅ All tests passed!")
        print("📊 Coverage report generated in htmlcov/ directory")
    else:
        print(f"\n❌ Tests failed with exit code {result.returncode}")
    
    return result.returncode

def run_specific_test(test_name):
    """Run a specific test by name."""
    print(f"🎯 Running specific test: {test_name}")
    result = subprocess.run([
        sys.executable, "-m", "pytest", 
        f"test_dlp_processor.py::{test_name}", 
        "-v"
    ])
    return result.returncode

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Run specific test
        test_name = sys.argv[1]
        exit_code = run_specific_test(test_name)
    else:
        # Run all tests
        exit_code = run_tests()
    
    sys.exit(exit_code)