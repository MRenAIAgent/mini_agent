# Integration Tests

This directory contains integration tests for the Mini Agent framework, including both mock-based and real API integration tests.

## Test Types

### 1. Mock Integration Tests
- **Files**: `test_*.py` (excluding `test_real_llm_integration.py`)
- **Purpose**: Test component interactions with mocked dependencies
- **Requirements**: No external API keys required
- **Speed**: Fast (< 1 minute)

### 2. Real API Integration Tests
- **File**: `test_real_llm_integration.py`
- **Purpose**: End-to-end testing with real OpenAI API calls
- **Requirements**: OpenAI API key and internet connection
- **Speed**: Moderate to slow (2-10 minutes depending on tests)

## Setup

### Environment Configuration

1. **Create a `.env` file** in the project root:
```bash
# Required for real API tests
OPENAI_API_KEY=your_openai_api_key_here

# Optional configuration
ENABLE_REAL_LLM_TESTS=true
TEST_MODEL=gpt-4-turbo-2024-04-09
INTEGRATION_TEST_TIMEOUT=30
```

2. **Install dependencies**:
```bash
pip install python-dotenv pytest pytest-asyncio
```

3. **Get an OpenAI API key**:
   - Visit: https://platform.openai.com/api-keys
   - Create a new API key
   - Add it to your `.env` file

## Running Tests

### Quick Commands

```bash
# Check environment setup
python run_integration_tests.py --check-env

# Run basic real API tests (recommended first run)
python run_integration_tests.py --run-basic

# Run all real API tests
python run_integration_tests.py --run-all

# Run mock integration tests (no API key needed)
python run_integration_tests.py --run-mock
```

### Manual pytest Commands

```bash
# Run only mock integration tests
pytest tests/integration/ -m "integration and not real_api" -v

# Run only real API tests
pytest tests/integration/test_real_llm_integration.py -m "real_api" -v

# Run basic real API tests (fast subset)
pytest tests/integration/test_real_llm_integration.py::TestRealLLMIntegration::test_basic_llm_call -v

# Run all tests except slow performance tests
pytest tests/integration/test_real_llm_integration.py -m "real_api and not slow" -v

# Run only performance tests
pytest tests/integration/test_real_llm_integration.py -m "real_api and slow" -v
```

### Test Selection by Marker

- `real_api`: Tests requiring real API calls
- `slow`: Long-running tests (>30 seconds)
- `integration`: All integration tests
- `unit`: Unit tests (not integration)

## Test Categories

### Real LLM Integration (`TestRealLLMIntegration`)

Tests core LLM functionality with real API calls:

- ✅ **Basic LLM Call**: Simple question-answer
- ✅ **Complex Reasoning**: Multi-step problem solving
- ✅ **Execution Patterns**: SIMPLE, REACT, PLANNING patterns
- ✅ **Memory Integration**: Context persistence across calls
- ✅ **Streaming**: Real-time response streaming
- ✅ **Error Handling**: API error scenarios

### Real Agent Workflows (`TestRealAgentWorkflows`)

Tests complete agent workflows:

- ✅ **Conversation Flow**: Multi-turn conversations
- ✅ **Problem Solving**: Complex task completion
- ✅ **Creative Writing**: Content generation capabilities

### Real Tool Integration (`TestRealToolIntegration`)

Tests tool usage with real LLM:

- ✅ **Tool Usage**: Calculator tool integration
- ✅ **Tool Workflows**: Multi-step tool operations

### Performance Metrics (`TestRealPerformanceMetrics`)

Tests performance characteristics:

- ⚡ **Response Time**: API response speed
- ⚡ **Concurrent Requests**: Parallel request handling

## Expected Results

### Successful Test Indicators

- **Response Quality**: Relevant, coherent responses
- **No Mock Artifacts**: Responses don't contain "mock" or "test"
- **Functional Features**: Memory, tools, patterns work correctly
- **Performance**: Reasonable response times (< 10 seconds)

### Common Issues

1. **API Key Issues**:
   ```
   Error: OPENAI_API_KEY not found in environment
   ```
   **Solution**: Add API key to `.env` file

2. **Rate Limiting**:
   ```
   Error: Rate limit exceeded
   ```
   **Solution**: Wait and retry, or upgrade API plan

3. **Network Issues**:
   ```
   Error: Connection timeout
   ```
   **Solution**: Check internet connection

4. **Model Availability**:
   ```
   Error: Model not found
   ```
   **Solution**: Verify model name in `.env` file

## Cost Considerations

Real API tests consume OpenAI tokens:

- **Basic tests**: ~500-1000 tokens (~$0.01-0.02)
- **Comprehensive tests**: ~2000-5000 tokens (~$0.04-0.10)
- **Performance tests**: ~1000-3000 tokens (~$0.02-0.06)

**Total cost per full test run**: ~$0.10-0.20

To minimize costs:
1. Use `--run-basic` for development
2. Set low `max_tokens` in test configs
3. Use `temperature=0.1` for consistent responses

## Development Workflow

1. **Start with mock tests**:
   ```bash
   python run_integration_tests.py --run-mock
   ```

2. **Test basic real API functionality**:
   ```bash
   python run_integration_tests.py --run-basic
   ```

3. **Run comprehensive tests before deployment**:
   ```bash
   python run_integration_tests.py --run-all
   ```

4. **Performance testing for optimization**:
   ```bash
   python run_integration_tests.py --run-perf
   ```

## Continuous Integration

For CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Run Integration Tests
  env:
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
  run: |
    python run_integration_tests.py --check-env
    python run_integration_tests.py --run-basic
```

**Note**: Store API keys as secrets in your CI/CD platform.

## Troubleshooting

### Environment Check
```bash
python run_integration_tests.py --check-env
```

### Debug Mode
```bash
pytest tests/integration/test_real_llm_integration.py::test_name -v -s --tb=long
```

### Verbose Output
```bash
pytest tests/integration/ -v -s --capture=no
```

## Contributing

When adding new integration tests:

1. **Mock tests**: Add to existing test files
2. **Real API tests**: Add to `test_real_llm_integration.py`
3. **Mark appropriately**: Use `@pytest.mark.real_api` for API tests
4. **Consider cost**: Keep token usage reasonable
5. **Test independently**: Ensure tests don't depend on each other