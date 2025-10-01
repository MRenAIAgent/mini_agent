# Scenario-Driven Integration Tests

## Overview

The scenario-driven integration tests provide comprehensive validation of the Mini Agent system through realistic usage patterns. Instead of testing individual components in isolation, these tests verify that the agent works correctly in real-world scenarios that users would actually encounter.

## Test Structure

### 6 Scenario Categories

#### 1. **Simple Agent Calls** (`TestSimpleAgentCallScenarios`)
Direct LLM interactions without complex patterns.

**Scenarios:**
- `test_greeting_conversation_scenario` - Friendly conversation exchange
- `test_information_query_scenario` - Factual information requests
- `test_simple_problem_solving_scenario` - Straightforward advice/guidance
- `test_creative_task_scenario` - Creative content generation

**Performance Target:** < 2 seconds per scenario

#### 2. **Tool Calling** (`TestToolCallingScenarios`)
Agent using external tools to complete tasks.

**Scenarios:**
- `test_single_calculation_tool_scenario` - Mathematical calculations
- `test_weather_information_tool_scenario` - External API data retrieval
- `test_file_operations_tool_scenario` - File creation and management

**Tools Available:**
- Calculator tool (math expressions)
- Weather tool (location-based queries)
- File operations tool (read/write/list)

#### 3. **Multi-Round ReAct** (`TestMultiRoundReActScenarios`)
Complex reasoning with multiple iterations.

**Scenarios:**
- `test_research_and_analysis_scenario` - Multi-step comparative analysis
- `test_complex_calculation_scenario` - Financial calculations with multiple steps
- `test_problem_solving_with_constraints_scenario` - Optimization problems

**Performance Target:** < 5 seconds per scenario

#### 4. **Plan-Execution Pattern** (`TestPlanExecutionScenarios`)
Breaking down complex tasks into structured steps.

**Scenarios:**
- `test_project_planning_scenario` - E-commerce website launch planning
- `test_learning_curriculum_scenario` - Structured ML learning plan
- `test_business_strategy_scenario` - Go-to-market strategy development

**Expected Output:** Structured plans with phases, timelines, and actionable steps

#### 5. **Memory-Enhanced** (`TestMemoryEnhancedScenarios`)
Using memory for context and learning.

**Scenarios:**
- `test_personalized_conversation_scenario` - Adapting to user preferences
- `test_project_context_retention_scenario` - Maintaining project context across sessions
- `test_learning_progress_tracking_scenario` - Tracking and adapting to learning progress

**Memory Features:**
- Preference tracking
- Context retention
- Progressive difficulty adaptation

#### 6. **Prompt Optimization** (`TestPromptOptimizationScenarios`)
Testing adaptive prompt improvement.

**Scenarios:**
- `test_response_quality_improvement_scenario` - Learning from feedback
- `test_domain_adaptation_scenario` - Adapting to user's domain expertise
- `test_communication_style_optimization_scenario` - Style adaptation based on interactions

## Running Tests

### Quick Start
```bash
# Check environment
python run_scenario_tests.py --check-env

# Run all scenarios
python run_scenario_tests.py --run-all

# Run specific category
python run_scenario_tests.py --run-category simple
```

### Available Commands

#### Environment Check
```bash
python run_scenario_tests.py --check-env
```
Validates:
- Python version (≥3.8)
- pytest availability
- Required dependencies (rich, structlog, pytest)
- Test file existence

#### Run All Scenarios
```bash
python run_scenario_tests.py --run-all
```
Executes all 6 scenario categories and provides comprehensive results.

#### Run Specific Category
```bash
python run_scenario_tests.py --run-category <category>
```
Categories: `simple`, `tools`, `react`, `planning`, `memory`, `optimization`

#### Performance Testing
```bash
python run_scenario_tests.py --run-performance
```
Focuses on performance benchmarks and timing analysis.

#### Interactive Mode
```bash
python run_scenario_tests.py --run-interactive
```
Menu-driven interface for selective test execution.

## Test Architecture

### Base Class: `ScenarioTestBase`
Common setup and utilities for all scenario tests:
- Tracing configuration
- Memory manager setup
- Tool manager setup
- Mock LLM function
- Performance tracking

### Mock LLM Responses
Tests use carefully crafted mock responses that simulate realistic LLM behavior:

```python
# Example: ReAct pattern response
self.mock_llm_function.side_effect = [
    """Thought: The user wants to calculate 25 * 47. I should use the calculator tool.
Action: calculator
Action Input: {"expression": "25 * 47"}""",
    """Thought: The calculator returned 1175. I can now provide the final answer.
Final Answer: 25 × 47 = 1,175"""
]
```

### Tool Integration
Tests include realistic tool implementations:
- **Calculator Tool**: Safe math expression evaluation
- **Weather Tool**: Mock weather data responses
- **File Operations Tool**: Simulated file operations

### Performance Tracking
Each test tracks execution time and performance metrics:
```python
start_time = time.time()
response = await agent.run(user_input)
execution_time = self._track_execution_time(start_time, "scenario_name")
```

## Expected Behavior

### Response Quality
- **Informative**: Responses contain relevant, detailed information
- **Structured**: Multi-section responses with clear organization
- **Contextual**: References previous interactions when memory is enabled
- **Actionable**: Provides concrete steps and recommendations

### Performance Benchmarks
- Simple conversations: < 2 seconds
- Tool-based scenarios: < 5 seconds
- Multi-round ReAct: < 5 seconds
- Planning scenarios: < 3 seconds

### Memory Integration
- Context retention across multiple interactions
- Preference learning and adaptation
- Progressive difficulty adjustment
- Domain-specific language adaptation

## Validation Assertions

### Content Validation
```python
# Check for comprehensive responses
assert len(response.split('\n')) >= 4  # Multi-line response
assert "specific_term" in response.lower()
assert any(word in response for word in ["key", "terms"])
```

### Performance Validation
```python
# Timing constraints
assert execution_time < 2.0, f"Scenario took too long: {execution_time}s"
```

### Memory Validation
```python
# Memory storage and retrieval
memories = await self.memory_manager.get_all_memories()
assert len(memories) >= 2
```

### Tool Validation
```python
# Tool execution verification
mock_execute.assert_called()
assert "tool_result" in response
```

## Results and Reporting

### JSON Output
Test results are saved to `scenario_test_results.json`:
```json
{
  "total_scenarios": 18,
  "successful_scenarios": 17,
  "failed_scenarios": 1,
  "total_duration": 45.2,
  "performance_summary": {
    "simple": 1.2,
    "tools": 2.8,
    "react": 4.1
  }
}
```

### Console Summary
```
📋 SCENARIO TEST SUITE SUMMARY
============================================================
Total Scenarios: 18
Successful: 17 ✅
Failed: 1 ❌
Success Rate: 94.4%
Total Duration: 45.20 seconds

📊 Average Performance by Category:
  SIMPLE: 1.20s per scenario
  TOOLS: 2.80s per scenario
  REACT: 4.10s per scenario
```

## Integration with CI/CD

### GitHub Actions Integration
Add to `.github/workflows/scenario-tests.yml`:
```yaml
- name: Run Scenario Tests
  run: |
    python run_scenario_tests.py --run-all

- name: Upload Test Results
  uses: actions/upload-artifact@v3
  with:
    name: scenario-test-results
    path: scenario_test_results.json
```

### Performance Monitoring
Track performance trends over time:
```bash
# Daily performance check
python run_scenario_tests.py --run-performance >> performance_log.txt
```

## Debugging Failed Scenarios

### Common Issues
1. **Mock Response Format**: Ensure mock responses match expected patterns
2. **Timing Issues**: Async operations may need proper await handling
3. **Memory State**: Memory backend state between tests
4. **Tool Registration**: Tools must be properly registered before use

### Debug Commands
```bash
# Run single scenario with verbose output
python -m pytest tests/integration/test_scenario_driven.py::TestSimpleAgentCallScenarios::test_greeting_conversation_scenario -v -s

# Enable tracing for debugging
python -c "from observability import configure_tracing; configure_tracing(detailed=True)"
```

## Extending Scenarios

### Adding New Scenarios
1. Choose appropriate test class based on category
2. Follow naming convention: `test_<scenario_name>_scenario`
3. Include performance tracking
4. Add comprehensive assertions
5. Update documentation

### Adding New Categories
1. Create new test class inheriting from `ScenarioTestBase`
2. Add to `SCENARIO_CATEGORIES` in test runner
3. Implement category-specific setup if needed
4. Update documentation and help text

## Best Practices

### Test Design
- **Realistic Scenarios**: Based on actual user interactions
- **Clear Assertions**: Validate specific expected behaviors
- **Performance Conscious**: Include timing constraints
- **Mock Appropriately**: Realistic but controllable responses

### Maintenance
- **Update Mock Responses**: Keep responses current and realistic
- **Review Performance**: Monitor and update performance benchmarks
- **Scenario Coverage**: Ensure all major use cases are covered
- **Documentation**: Keep scenario descriptions up to date

This scenario-driven approach provides comprehensive validation that the agent works correctly in realistic usage patterns, making it easier to catch integration issues and ensure quality user experiences.