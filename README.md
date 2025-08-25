# DLP Processor Test Suite

A comprehensive test suite for a Data Loss Prevention (DLP) processor that detects Personally Identifiable Information (PII) and Protected Health Information (PHI) in various file formats.

## 🏗️ Architecture

The test suite covers:

- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end workflow testing
- **Edge Cases**: Error handling and boundary conditions
- **Data Validation**: PII/PHI pattern detection accuracy

## 📁 File Structure

```
├── dlp_processor.py          # Main DLP processor implementation
├── test_dlp_processor.py     # Comprehensive test suite
├── requirements.txt          # Python dependencies
├── run_tests.py             # Test runner script
├── pytest.ini              # Pytest configuration
└── README.md               # This file
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run All Tests

```bash
python run_tests.py
```

Or using pytest directly:

```bash
pytest test_dlp_processor.py -v
```

### 3. Run Specific Tests

```bash
# Run a specific test class
pytest test_dlp_processor.py::TestDLPProcessor -v

# Run a specific test method
pytest test_dlp_processor.py::TestDLPProcessor::test_scan_text_file -v

# Run tests with markers
pytest test_dlp_processor.py -m "unit" -v
pytest test_dlp_processor.py -m "integration" -v
```

## 🧪 Test Coverage

### Unit Tests

- **PIIEntity**: Data structure validation
- **ScanResult**: Result object testing
- **DLPProcessor**: Core functionality testing
  - Pattern detection
  - Risk scoring
  - File validation
  - Content sanitization

### Integration Tests

- End-to-end file scanning workflows
- Multiple file type processing
- Batch processing scenarios

### Test Categories

| Category | Description | Examples |
|----------|-------------|----------|
| **Unit** | Individual component testing | Pattern validation, risk calculation |
| **Integration** | Multi-component workflows | File scanning, batch processing |
| **Edge Cases** | Error handling | Invalid files, malformed data |
| **Performance** | Efficiency testing | Large files, multiple entities |

## 📊 Running Tests with Coverage

```bash
# Generate coverage report
pytest test_dlp_processor.py --cov=dlp_processor --cov-report=html

# View coverage in terminal
pytest test_dlp_processor.py --cov=dlp_processor --cov-report=term-missing
```

Coverage reports are generated in the `htmlcov/` directory.

## 🔧 Test Configuration

### Pytest Configuration (`pytest.ini`)

- Verbose output by default
- Custom markers for test categorization
- Warning suppression for cleaner output
- Short traceback format

### Test Markers

- `@pytest.mark.unit`: Unit tests
- `@pytest.mark.integration`: Integration tests
- `@pytest.mark.slow`: Long-running tests

## 📝 Writing New Tests

### Test Naming Convention

- Test files: `test_*.py`
- Test classes: `Test*`
- Test methods: `test_*`

### Example Test Structure

```python
class TestNewFeature:
    """Test cases for new feature."""
    
    @pytest.fixture
    def setup(self):
        """Setup test fixtures."""
        return "test_data"
    
    def test_feature_behavior(self, setup):
        """Test the main behavior of the feature."""
        assert setup == "test_data"
    
    def test_feature_edge_case(self):
        """Test edge case behavior."""
        # Test implementation
        pass
```

### Best Practices

1. **Use fixtures** for common setup
2. **Test one thing** per test method
3. **Use descriptive names** for test methods
4. **Include docstrings** explaining test purpose
5. **Test both success and failure** scenarios

## 🐛 Debugging Tests

### Verbose Output

```bash
pytest test_dlp_processor.py -v -s
```

### Debug Specific Test

```bash
# Run with debugger
pytest test_dlp_processor.py::test_method -s --pdb

# Run with print statements visible
pytest test_dlp_processor.py::test_method -s
```

### Test Discovery

```bash
# List all tests without running
pytest test_dlp_processor.py --collect-only

# Show test collection with markers
pytest test_dlp_processor.py --collect-only -q
```

## 📈 Performance Testing

### Benchmark Tests

```bash
# Run performance tests
pytest test_dlp_processor.py -m "slow" -v

# Skip slow tests
pytest test_dlp_processor.py -m "not slow" -v
```

### Memory Profiling

```bash
# Install memory profiler
pip install memory-profiler

# Run with memory profiling
python -m memory_profiler run_tests.py
```

## 🔒 Security Testing

The test suite includes security-focused tests:

- **Input Validation**: Malicious file paths
- **Data Sanitization**: PII masking verification
- **Access Control**: File permission testing
- **Pattern Validation**: Regex injection prevention

## 🚨 Common Issues

### Import Errors

```bash
# Ensure you're in the correct directory
cd /path/to/project

# Install dependencies
pip install -r requirements.txt
```

### Permission Errors

```bash
# Make test runner executable
chmod +x run_tests.py

# Run with appropriate permissions
sudo python run_tests.py  # If needed
```

### Test Failures

1. Check file paths and permissions
2. Verify test data files exist
3. Review error messages and stack traces
4. Ensure all dependencies are installed

## 🤝 Contributing

### Adding New Tests

1. Create test methods in appropriate test classes
2. Follow naming conventions
3. Include comprehensive assertions
4. Add appropriate markers
5. Update documentation

### Test Data

- Use temporary files for file-based tests
- Clean up resources in fixtures
- Avoid hardcoded paths
- Use realistic test data

## 📚 Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Python Testing Best Practices](https://realpython.com/python-testing/)
- [Test-Driven Development](https://en.wikipedia.org/wiki/Test-driven_development)

## 📞 Support

For issues with the test suite:

1. Check the error messages
2. Review test configuration
3. Verify dependencies
4. Check file permissions
5. Review test data integrity

---

**Happy Testing! 🎉**
