# 🧪 Running the Test Suite

## Prerequisites

Ensure all dependencies are installed:

```bash
# Install all requirements
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Or install test dependencies specifically
pip install pytest pytest-asyncio pytest-cov
```

## Quick Start

### Run All Tests

```bash
./run_tests.sh
```

### Run Specific Test Categories

```bash
# Unit tests only (fast, no external dependencies)
pytest tests/unit/ -v

# Integration tests (uses real DB and vector store)
pytest tests/integration/ -v

# E2E tests (full user scenarios with verbose output)
pytest tests/e2e/ -v -s
```

### Run Individual Test Files

```bash
# Database integration tests
pytest tests/integration/test_journal_database_integration.py -v

# Service integration tests
pytest tests/integration/test_journal_service_integration.py -v

# MCP integration tests
pytest tests/integration/test_mcp_integration.py -v

# E2E user scenarios
pytest tests/e2e/test_user_scenarios.py -v -s
```

### Run Specific Test Classes or Methods

```bash
# Run a specific test class
pytest tests/unit/test_journal_models.py::TestWorkSession -v

# Run a specific test method
pytest tests/unit/test_journal_models.py::TestWorkSession::test_create_valid_session -v

# Run tests matching a pattern
pytest -k "session" -v
pytest -k "database" -v
pytest -k "concurrent" -v
```

## Coverage Reports

### Generate Coverage Report

```bash
# Terminal report with missing lines
pytest tests/ --cov=src --cov-report=term-missing

# HTML report (opens in browser)
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Coverage for Specific Modules

```bash
# Journal models and service only
pytest tests/ --cov=src.models.journal --cov=src.services.journal_service --cov-report=term

# Repository layer only
pytest tests/ --cov=src.storage.repositories --cov-report=term
```

## Test Markers

Tests are marked with categories for selective execution:

```bash
# Run only unit tests
pytest -m unit -v

# Run only integration tests
pytest -m integration -v

# Run only E2E tests
pytest -m e2e -v -s

# Run everything except slow tests
pytest -m "not slow" -v
```

## Test Output Options

```bash
# Verbose output with full test names
pytest -v

# Very verbose with extra info
pytest -vv

# Show print statements (useful for debugging)
pytest -s

# Show local variables on failure
pytest -l

# Stop on first failure
pytest -x

# Show slowest 10 tests
pytest --durations=10
```

## Debugging Tests

### Run with Debugging

```bash
# Drop into debugger on failure
pytest --pdb

# Drop into debugger at start of test
pytest --trace

# Show full tracebacks
pytest --tb=long

# Show only first and last line of traceback
pytest --tb=line
```

### Capture Logs

```bash
# Show log output
pytest --log-cli-level=INFO

# Show debug logs
pytest --log-cli-level=DEBUG
```

## Parallel Execution

```bash
# Install pytest-xdist for parallel execution
pip install pytest-xdist

# Run tests in parallel (4 workers)
pytest -n 4

# Auto-detect number of CPUs
pytest -n auto
```

## Common Issues

### Import Errors

If you see `ModuleNotFoundError`:

```bash
# Ensure you're in the project root
cd /home/racoon/AgentMemorh/mcp-memory-server

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Verify Python path
echo $PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Database Lock Errors

If tests fail with SQLite lock errors:

```bash
# Clean test databases
rm data/test_*.db
rm -rf data/test_*_chroma

# Run tests sequentially instead of parallel
pytest tests/ -v
```

### Async Test Errors

If async tests fail:

```bash
# Ensure pytest-asyncio is installed
pip install pytest-asyncio

# Check pytest.ini has asyncio_mode = auto
cat pytest.ini | grep asyncio_mode
```

## Expected Test Results

With all dependencies installed:

- **Unit Tests**: ~26 tests, all should pass
- **Integration Tests**: ~23 tests, all should pass
- **E2E Tests**: ~7 tests, all should pass
- **Total**: ~98 tests collected

### Expected Output

```
🧪 Running MCP Memory Server Test Suite
========================================

📦 UNIT TESTS
-------------
Running Model Tests...
✅ Model Tests PASSED

Running Repository Tests...
✅ Repository Tests PASSED

Running Service Tests...
✅ Service Tests PASSED

🔗 INTEGRATION TESTS
--------------------
Running Database Integration...
✅ Database Integration PASSED

Running Service Integration...
✅ Service Integration PASSED

Running MCP Integration...
✅ MCP Integration PASSED

🎬 END-TO-END TESTS
-------------------
Running User Scenarios...
✅ User Scenarios PASSED

📊 GENERATING COVERAGE REPORT
------------------------------
[Coverage report shown here]

========================================
TEST SUMMARY
========================================
Passed: 7
Failed: 0

🎉 ALL TESTS PASSED!
✅ Feature is ready for deployment
```

## CI/CD Integration

The `run_tests.sh` script returns appropriate exit codes:

- `0` = All tests passed
- `1` = Some tests failed

Perfect for CI/CD pipelines:

```yaml
# GitHub Actions example
- name: Run tests
  run: ./run_tests.sh

# GitLab CI example
test:
  script:
    - ./run_tests.sh
```

## Performance Benchmarks

Expected test execution times (approximate):

| Test Suite        | Duration    | Tests  |
| ----------------- | ----------- | ------ |
| Unit Tests        | ~2-5s       | 26     |
| Integration Tests | ~10-20s     | 23     |
| E2E Tests         | ~15-30s     | 7      |
| **Full Suite**    | **~30-60s** | **98** |

_Times vary based on system performance and database/vector store initialization._

## Next Steps

1. **Run the tests**: `./run_tests.sh`
2. **Check coverage**: View the HTML report in `htmlcov/`
3. **Fix failures**: Address any failing tests
4. **Improve coverage**: Add tests for under-covered areas
5. **Document findings**: Note any issues or improvements needed

## Support

If tests fail unexpectedly:

1. Check dependencies are installed
2. Verify you're in the correct directory
3. Clean test databases and retry
4. Check logs for specific errors
5. Review test output carefully

For more help, refer to:

- [pytest documentation](https://docs.pytest.org/)
- [pytest-asyncio documentation](https://pytest-asyncio.readthedocs.io/)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
