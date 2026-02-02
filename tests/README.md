# Tests

This folder contains the test suite for the FFStudios Chat Bot.

## Test Files

### `conftest.py`

Pytest configuration and shared fixtures for all tests.

### `test_finance_flow.py`

Tests for financial and inventory tracking workflows including:
- Database operations
- Service layer integration
- End-to-end financial flows

## Running Tests

Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

Run all tests:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=src --cov-report=html
```

Run specific test file:
```bash
pytest tests/test_finance_flow.py
```

Run with verbose output:
```bash
pytest -v
```

## Test Structure

Tests follow the Arrange-Act-Assert pattern and use pytest fixtures for:
- Database setup/teardown
- Test data creation
- Service mocking when needed
