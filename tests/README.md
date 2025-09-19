# Testing Infrastructure

This directory contains a comprehensive testing suite for the therapy booking system with proper mocking and separation of concerns.

## 📁 Directory Structure

```
tests/
├── unit/                    # Unit tests with mocking
│   ├── test_date_parser.py     # Natural language date parsing tests
│   └── test_adk_agent_service.py # ADK agent service logic tests
├── integration/             # Integration tests with mocked external services  
│   ├── test_external_integrations.py # External API integration tests
│   └── test_webhook_api.py         # FastAPI webhook endpoint tests
├── scripts/                # Utility test scripts for manual testing
│   ├── test_natural_date.py       # Manual date parsing verification
│   ├── test_webhook_today.py      # Live webhook testing
│   └── test_complete_booking.py   # End-to-end booking test
├── conftest.py             # Test configuration and fixtures
├── requirements-test.txt   # Testing dependencies
├── run_tests.py           # Python test runner
├── test.bat              # Windows batch test runner
└── README.md             # This file
```

## 🧪 Test Categories

### Unit Tests (`tests/unit/`)
- **Purpose**: Test individual functions and classes in isolation
- **Mocking Strategy**: Mock all external dependencies (databases, APIs, file system)
- **Coverage**: Core business logic, data parsing, validation
- **Example**: Date parser tests with mocked datetime operations

### Integration Tests (`tests/integration/`)
- **Purpose**: Test component interactions with mocked external services
- **Mocking Strategy**: Mock external APIs (Ultramsg, Google ADK) but test real component integration
- **Coverage**: Webhook endpoints, service orchestration, data flow
- **Example**: FastAPI endpoint tests with TestClient and mocked services

### Test Scripts (`tests/scripts/`)
- **Purpose**: Manual testing utilities and debugging tools
- **Usage**: Direct execution for specific testing scenarios
- **Coverage**: Live system testing, debugging, validation
- **Example**: Natural date parsing verification, webhook testing

## 🚀 Running Tests

### Using the Test Runner (Recommended)

```bash
# Install test requirements
python tests/run_tests.py --install

# Run all tests
python tests/run_tests.py

# Run specific test categories
python tests/run_tests.py --unit          # Unit tests only
python tests/run_tests.py --integration   # Integration tests only
python tests/run_tests.py --scripts       # Test scripts only

# With verbose output
python tests/run_tests.py --unit -v

# Generate coverage report
python tests/run_tests.py --coverage

# Check system status
python tests/run_tests.py --status
```

### Using Windows Batch Script

```cmd
REM Install dependencies
test.bat install

REM Run all tests
test.bat

REM Run specific categories
test.bat unit
test.bat integration verbose
test.bat coverage
```

### Using pytest directly

```bash
# Install requirements first
pip install -r tests/requirements-test.txt

# Run unit tests
pytest tests/unit/ -v

# Run integration tests  
pytest tests/integration/ -v

# Run with coverage
pytest tests/unit/ tests/integration/ --cov=therapy_booking_app --cov-report=html
```

## 🛠 Test Configuration

### Dependencies (`requirements-test.txt`)
- **pytest**: Testing framework
- **pytest-asyncio**: Async test support
- **pytest-mock**: Enhanced mocking capabilities
- **httpx**: HTTP client for testing
- **responses**: HTTP request mocking
- **freezegun**: Time/date mocking
- **factory-boy**: Test data generation
- **faker**: Fake data generation

### Configuration (`conftest.py`)
- Test fixtures for common setup
- Database mocking helpers
- API response mocking utilities
- Test data factories

### Pytest Settings (`pyproject.toml`)
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
markers = [
    "unit: Unit tests with mocked dependencies",
    "integration: Integration tests with mocked external services",
    "slow: Slow running tests"
]
```

## 🎯 Mocking Strategy

### Unit Tests
- **Database Operations**: Mock all database calls with predictable responses
- **External APIs**: Mock Google ADK, Ultramsg, and other external services
- **Date/Time**: Use freezegun to control time-dependent tests
- **Threading**: Mock threading operations for deterministic tests

### Integration Tests  
- **External Services**: Mock HTTP endpoints with responses library
- **Internal Services**: Use real service instances with mocked external dependencies
- **Database**: Use in-memory or test database instances
- **File System**: Mock file operations where needed

## 📊 Coverage Reporting

Generate HTML coverage reports:
```bash
pytest tests/unit/ tests/integration/ --cov=therapy_booking_app --cov-report=html
```

View coverage in browser:
```bash
open htmlcov/index.html  # Linux/Mac
start htmlcov/index.html # Windows
```

## 🔧 Adding New Tests

### Unit Test Template
```python
import pytest
from unittest.mock import Mock, patch
from app.services.your_service import YourService

class TestYourService:
    @pytest.fixture
    def mock_dependencies(self):
        with patch('app.services.your_service.external_dependency') as mock:
            yield mock
    
    def test_your_function(self, mock_dependencies):
        # Arrange
        service = YourService()
        mock_dependencies.return_value = "expected_result"
        
        # Act
        result = service.your_function()
        
        # Assert
        assert result == "expected_result"
        mock_dependencies.assert_called_once()
```

### Integration Test Template
```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

class TestYourEndpoint:
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def mock_external_service(self):
        with patch('app.services.external_service') as mock:
            yield mock
    
    def test_your_endpoint(self, client, mock_external_service):
        # Arrange
        mock_external_service.return_value = {"status": "success"}
        
        # Act
        response = client.post("/your-endpoint", json={"data": "test"})
        
        # Assert
        assert response.status_code == 200
        assert response.json()["status"] == "success"
```

## 🐛 Debugging Tests

### Verbose Output
```bash
pytest tests/unit/test_your_test.py -v -s
```

### Specific Test Function
```bash  
pytest tests/unit/test_your_test.py::TestClass::test_function -v
```

### Debug Mode
```bash
pytest tests/unit/test_your_test.py --pdb
```

### Print Statements
Use `pytest -s` to see print statements in tests

## 📝 Best Practices

1. **Test Isolation**: Each test should be independent and not rely on other tests
2. **Meaningful Names**: Test names should clearly describe what they're testing
3. **AAA Pattern**: Arrange, Act, Assert - structure tests clearly
4. **Mock External Dependencies**: Don't make real API calls or database operations in tests
5. **Test Edge Cases**: Include tests for error conditions and boundary cases
6. **Keep Tests Fast**: Unit tests should run quickly, use mocking appropriately
7. **Readable Assertions**: Use clear, descriptive assertion messages

## 🔍 System Requirements

- Python 3.8+
- All dependencies from `requirements-test.txt`
- Access to therapy booking system source code
- Optional: Running therapy booking system for integration tests

## 📚 Additional Resources

- [pytest documentation](https://docs.pytest.org/)
- [unittest.mock documentation](https://docs.python.org/3/library/unittest.mock.html)
- [FastAPI testing guide](https://fastapi.tiangolo.com/tutorial/testing/)
- [Coverage.py documentation](https://coverage.readthedocs.io/)