# Testing Quick Reference

## Run Tests

```bash
# All tests
./scripts/run_all_tests.sh

# By type
pytest tests/unit/           # Unit (4s)
pytest tests/integration/    # Integration (60s)
pytest tests/e2e/           # E2E (5min)
pytest tests/load/          # Load (2min)

# Specific test
pytest tests/unit/test_metrics.py::test_name -v

# With coverage
pytest tests/ --cov=src --cov-report=html
```

## Key Metrics

- **Total Tests:** 378+
- **Coverage:** 96%
- **Pass Rate:** 100%
- **Status:** ✅ READY

## CI/CD

Tests run automatically on:
- Every push
- Every PR
- Nightly builds

## Support

- **Docs:** docs/testing/
- **Issues:** GitHub Issues
- **Contact:** team@mcp-memory.com
