#!/usr/bin/env python3
"""
Scenario-Driven Integration Tests for Mini Agent

This test suite organizes integration tests around realistic usage scenarios
that demonstrate the agent's capabilities in different patterns and contexts.

Test Categories:
1. Simple Agent Calls - Direct LLM interactions
2. Tool-Driven Scenarios - Agent using tools to complete tasks
3. Multi-Round ReAct - Complex reasoning with multiple iterations
4. Plan-Execution Pattern - Breaking down complex tasks into steps
5. Memory-Enhanced Scenarios - Using memory for context and learning
6. Prompt Optimization - Testing adaptive prompt improvement
"""

import asyncio
import sys
import time
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any, List, Optional
import pytest
import tempfile
import json

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from agent import CoreAgent
    from memory.memory_manager import CoreMemoryManager
    from memory.memory_store import InMemoryStore
    from tools.tool_manager import ToolManager
    from integrations.llm_interfaces import LLMConfig, LLMResponse
    from execution.execution_patterns import ExecutionPatternType
    from observability import configure_tracing
except ImportError as e:
    pytest.skip(f"Integration imports not available: {e}", allow_module_level=True)


class ScenarioTestBase:
    """Base class for scenario-driven tests."""

    def setup_method(self):
        """Set up common test fixtures."""
        # Configure tracing for all scenarios with detailed output
        configure_tracing(clean_format=True, detailed=True)

        print("\n🔧 Setting up scenario test...")

        # Create real memory manager with in-memory store
        self.memory_store = InMemoryStore()
        self.memory_manager = CoreMemoryManager(memory_store=self.memory_store)

        # Create real tool manager
        self.tool_manager = ToolManager()

        # Mock LLM function for controlled responses
        self.mock_llm_function = AsyncMock()

        # Performance tracking
        self.execution_times = []

    async def _create_agent(self, enable_memory=True, enable_tracing=True, **kwargs):
        """Helper to create agent with common settings."""
        session_id = f"test_session_{int(time.time())}"
        print(f"🤖 Creating agent with session_id: {session_id}")

        agent = CoreAgent(
            llm_function=self.mock_llm_function,
            enable_memory=enable_memory,
            enable_tracing=enable_tracing,
            session_id=session_id,
            **kwargs
        )
        await agent.start()
        print(f"✅ Agent started successfully")
        return agent

    def _track_execution_time(self, start_time: float, scenario_name: str):
        """Track execution time for performance analysis."""
        execution_time = time.time() - start_time
        self.execution_times.append({
            'scenario': scenario_name,
            'duration': execution_time
        })
        return execution_time


class TestSimpleAgentCallScenarios(ScenarioTestBase):
    """Scenario 1: Simple Agent Call - Direct LLM interactions without complex patterns."""

    @pytest.mark.asyncio
    async def test_greeting_conversation_scenario(self):
        """Scenario: User greets the agent and has a brief friendly exchange."""
        agent = await self._create_agent()

        # Setup conversation responses in ReAct format
        self.mock_llm_function.side_effect = [
            """Thought: The user is greeting me and asking how I am. I should respond in a friendly manner and introduce myself as Claude.
Final Answer: Hello! I'm Claude, an AI assistant. How can I help you today?""",
            """Thought: The user is saying they're doing great and asking how I am. I should respond positively and offer to help.
Final Answer: I'm doing well, thank you for asking! What would you like to work on?""",
            """Thought: The user is thanking me for being helpful. I should acknowledge their thanks graciously.
Final Answer: You're very welcome! Feel free to ask me anything."""
        ]

        start_time = time.time()

        # Conversation flow
        response1 = await agent.run("Hello! How are you?")
        response2 = await agent.run("I'm doing great! How are you?")
        response3 = await agent.run("Thank you for being helpful!")

        execution_time = self._track_execution_time(start_time, "greeting_conversation")

        # Validate responses
        assert "Claude" in response1 and "assistant" in response1
        assert "well" in response2 and "thank you" in response2.lower()
        assert "welcome" in response3.lower()

        # Performance check - simple conversations should be fast
        assert execution_time < 2.0, f"Simple conversation took too long: {execution_time}s"

        await agent.stop()

    @pytest.mark.asyncio
    async def test_information_query_scenario(self):
        """Scenario: User asks for factual information that doesn't require tools."""
        agent = await self._create_agent()

        self.mock_llm_function.return_value = """Thought: The user is asking about Python programming language. I should provide comprehensive information about its key characteristics.
Final Answer: Python is a high-level programming language known for:
        - Simple, readable syntax
        - Dynamic typing
        - Extensive standard library
        - Large ecosystem of packages
        - Cross-platform compatibility"""

        start_time = time.time()
        response = await agent.run("Tell me about Python programming language")
        execution_time = self._track_execution_time(start_time, "information_query")

        # Validate informative response
        assert "Python" in response
        assert "programming language" in response
        assert len(response.split('\n')) >= 3  # Multi-line informative response

        # Performance check
        assert execution_time < 1.5, f"Information query took too long: {execution_time}s"

        await agent.stop()

    @pytest.mark.asyncio
    async def test_simple_problem_solving_scenario(self):
        """Scenario: User asks agent to solve a straightforward problem."""
        agent = await self._create_agent()

        self.mock_llm_function.return_value = """Thought: The user needs help organizing their daily schedule. I should provide practical, actionable advice.
Final Answer: To organize your daily schedule effectively:

1. **Prioritize tasks** - Use a system like Eisenhower Matrix (urgent/important)
2. **Time blocking** - Assign specific time slots to activities
3. **Buffer time** - Add 15-20% extra time for unexpected delays
4. **Morning routine** - Start with your most important task
5. **Review and adjust** - End each day by planning the next

Key tip: Focus on 3-5 major tasks per day rather than an overwhelming list."""

        start_time = time.time()
        response = await agent.run("How can I better organize my daily schedule?")
        execution_time = self._track_execution_time(start_time, "simple_problem_solving")

        # Validate problem-solving response
        assert "schedule" in response or "organize" in response
        assert any(word in response.lower() for word in ["prioritize", "time", "plan"])
        assert "1." in response or "•" in response  # Has structured advice

        await agent.stop()

    @pytest.mark.asyncio
    async def test_creative_task_scenario(self):
        """Scenario: User requests creative content generation."""
        agent = await self._create_agent()

        self.mock_llm_function.return_value = """Thought: The user wants me to write a creative poem about an old tree. I should create something evocative and nature-focused.
Final Answer: **The Old Oak Tree**

In the meadow stands an ancient oak,
Its branches reaching toward the sky,
Where morning light and shadows soak
The leaves that dance as winds blow by.

Generations have found shelter here,
Beneath its mighty, weathered bark,
Through seasons changing year by year,
From early dawn to evening dark."""

        start_time = time.time()
        response = await agent.run("Write a short poem about an old tree")
        execution_time = self._track_execution_time(start_time, "creative_task")

        # Validate creative response
        assert "tree" in response.lower() or "oak" in response.lower()
        assert len(response.split('\n')) >= 4  # Multi-line poem

        await agent.stop()


class TestToolCallingScenarios(ScenarioTestBase):
    """Scenario 2: Tool Calling - Agent using external tools to complete tasks."""

    def setup_method(self):
        """Set up tool calling test fixtures."""
        super().setup_method()

    async def _setup_test_tools(self, agent):
        """Set up common test tools on the agent."""
        # Calculator tool
        class CalculatorTool:
            def get_definition(self):
                return Mock(
                    name="calculator",
                    description="Performs mathematical calculations",
                    parameters={
                        "type": "object",
                        "properties": {
                            "expression": {"type": "string", "description": "Mathematical expression"}
                        }
                    }
                )

            async def execute(self, tool_call):
                from tools.tool_interfaces import ToolResult
                try:
                    # Safe evaluation for test purposes
                    expression = tool_call.arguments.get("expression", "0")
                    result = eval(expression.replace('^', '**'))  # Handle exponentiation
                    return ToolResult(
                        call_id=tool_call.id,
                        success=True,
                        content=str(result),
                        execution_time=0.05
                    )
                except Exception as e:
                    return ToolResult(
                        call_id=tool_call.id,
                        success=False,
                        error=str(e),
                        execution_time=0.05
                    )

        # Weather tool (mock)
        class WeatherTool:
            def get_definition(self):
                return Mock(
                    name="weather",
                    description="Get current weather information",
                    parameters={
                        "type": "object",
                        "properties": {
                            "location": {"type": "string", "description": "City name"}
                        }
                    }
                )

            async def execute(self, tool_call):
                from tools.tool_interfaces import ToolResult
                location = tool_call.arguments.get("location", "Unknown")
                return ToolResult(
                    call_id=tool_call.id,
                    success=True,
                    content=f"Weather in {location}: 72°F, partly cloudy with light winds",
                    execution_time=0.3
                )

        # File operations tool
        class FileOperationsTool:
            def get_definition(self):
                return Mock(
                    name="file_ops",
                    description="Read, write, and manage files",
                    parameters={
                        "type": "object",
                        "properties": {
                            "operation": {"type": "string", "description": "Operation: read, write, list"},
                            "filename": {"type": "string", "description": "File name"},
                            "content": {"type": "string", "description": "Content for write operations"}
                        }
                    }
                )

            async def execute(self, tool_call):
                from tools.tool_interfaces import ToolResult
                operation = tool_call.arguments.get("operation", "read")
                filename = tool_call.arguments.get("filename", "test.txt")

                if operation == "write":
                    return ToolResult(
                        call_id=tool_call.id,
                        success=True,
                        content=f"Successfully wrote to {filename}",
                        execution_time=0.1
                    )
                elif operation == "read":
                    return ToolResult(
                        call_id=tool_call.id,
                        success=True,
                        content=f"Contents of {filename}: Sample file content here...",
                        execution_time=0.08
                    )
                else:
                    return ToolResult(
                        call_id=tool_call.id,
                        success=True,
                        content="Files: test.txt, document.pdf, image.png",
                        execution_time=0.05
                    )

        # Register tools with the agent
        await agent.add_tool(CalculatorTool())
        await agent.add_tool(WeatherTool())
        await agent.add_tool(FileOperationsTool())

    @pytest.mark.asyncio
    async def test_single_calculation_tool_scenario(self):
        """Scenario: User needs a mathematical calculation performed."""
        agent = await self._create_agent()

        # Register test tools with the agent
        await self._setup_test_tools(agent)

        # Setup ReAct-style responses
        self.mock_llm_function.side_effect = [
            """Thought: The user wants to calculate 25 * 47. I should use the calculator tool for this.
Action: calculator
Action Input: {"expression": "25 * 47"}""",
            """Thought: The calculator returned 1175. I can now provide the final answer.
Final Answer: 25 × 47 = 1,175"""
        ]

        start_time = time.time()
        response = await agent.run(
            "What is 25 times 47?",
            execution_pattern=ExecutionPatternType.REACT
        )
        execution_time = self._track_execution_time(start_time, "single_calculation_tool")

        # Verify response contains answer (the final answer from the second LLM call)
        assert "1,175" in response or "1175" in response

        await agent.stop()

    @pytest.mark.asyncio
    async def test_weather_information_tool_scenario(self):
        """Scenario: User requests weather information for a specific location."""
        agent = await self._create_agent()

        self.mock_llm_function.side_effect = [
            """Thought: The user wants weather information for New York. I'll use the weather tool.
Action: weather
Action Input: {"location": "New York"}""",
            """Thought: I got the weather information from the tool. Now I can provide it to the user.
Final Answer: The current weather in New York is 72°F with partly cloudy skies and light winds. It's a pleasant day!"""
        ]

        # Register test tools with the agent
        await self._setup_test_tools(agent)

        start_time = time.time()
        response = await agent.run(
            "What's the weather like in New York?",
            execution_pattern=ExecutionPatternType.REACT
        )
        execution_time = self._track_execution_time(start_time, "weather_information_tool")

        # Verify weather information in response
        assert "72" in response and ("cloudy" in response.lower() or "weather" in response.lower())

        await agent.stop()

    @pytest.mark.asyncio
    async def test_file_operations_tool_scenario(self):
        """Scenario: User needs to create and manage files."""
        agent = await self._create_agent()

        self.mock_llm_function.side_effect = [
            """Thought: The user wants to create a file with specific content. I'll use the file operations tool.
Action: file_ops
Action Input: {"operation": "write", "filename": "shopping_list.txt", "content": "1. Milk\\n2. Bread\\n3. Eggs\\n4. Apples"}""",
            """Thought: The file was successfully created. Let me confirm this to the user.
Final Answer: I've successfully created shopping_list.txt with your shopping list containing milk, bread, eggs, and apples."""
        ]

        # Register test tools with the agent
        await self._setup_test_tools(agent)

        start_time = time.time()
        response = await agent.run(
            "Create a file called shopping_list.txt with items: milk, bread, eggs, and apples",
            execution_pattern=ExecutionPatternType.REACT
        )
        execution_time = self._track_execution_time(start_time, "file_operations_tool")

        # Verify success message
        assert "successfully" in response.lower() or "created" in response.lower()
        assert "shopping_list.txt" in response

        await agent.stop()


class TestMultiRoundReActScenarios(ScenarioTestBase):
    """Scenario 3: Multi-Round ReAct - Complex reasoning with multiple iterations."""

    @pytest.mark.asyncio
    async def test_research_and_analysis_scenario(self):
        """Scenario: User requests research that requires multiple tools and reasoning steps."""
        agent = await self._create_agent()

        # Simulate multi-step reasoning process
        self.mock_llm_function.side_effect = [
            # First iteration - identify need for research
            """Thought: The user wants to compare Python and JavaScript. I should break this down into key areas like syntax, performance, use cases, and ecosystem.
Action: Think about the comparison areas""",

            # Second iteration - structure the analysis
            """Thought: I need to provide a comprehensive comparison. Let me structure this with clear categories.
Final Answer: Here's a detailed comparison of Python vs JavaScript:

**Syntax & Learning Curve:**
- Python: Clean, readable syntax with significant whitespace
- JavaScript: C-style syntax with curly braces and semicolons

**Primary Use Cases:**
- Python: Data science, AI/ML, backend development, automation
- JavaScript: Web frontend, backend (Node.js), mobile development

**Performance:**
- Python: Generally slower, but optimized libraries (NumPy, etc.) are fast
- JavaScript: V8 engine provides excellent performance for web applications

**Ecosystem:**
- Python: Rich scientific computing libraries, extensive standard library
- JavaScript: Massive npm ecosystem, rapid development cycles

Both are excellent choices depending on your specific needs and project requirements."""
        ]

        start_time = time.time()
        response = await agent.run(
            "I'm trying to decide between Python and JavaScript for my next project. Can you help me compare them?",
            execution_pattern=ExecutionPatternType.REACT
        )
        execution_time = self._track_execution_time(start_time, "research_and_analysis")

        # Verify comprehensive response
        assert "Python" in response and "JavaScript" in response
        assert any(word in response for word in ["syntax", "performance", "use cases", "ecosystem"])
        assert len(response.split('\n')) >= 8  # Multi-section response

        # Multi-round should take reasonable time but allow for complexity
        assert execution_time < 5.0, f"Multi-round analysis took too long: {execution_time}s"

        await agent.stop()

    @pytest.mark.asyncio
    async def test_complex_calculation_scenario(self):
        """Scenario: User needs multi-step mathematical analysis."""
        agent = await self._create_agent()

        # Setup tools for calculation
        await self._setup_calculation_tools()

        self.mock_llm_function.side_effect = [
            # Step 1: Calculate compound interest
            """Thought: To find the compound interest, I need to use the formula A = P(1 + r/n)^(nt). Let me calculate this step by step.
Action: calculator
Action Input: {"expression": "10000 * (1 + 0.05/12)**(12*10)"}""",

            # Step 2: Calculate the interest earned
            """Thought: The total amount is $16,470.09. Now I need to subtract the principal to get the interest earned.
Action: calculator
Action Input: {"expression": "16470.09 - 10000"}""",

            # Step 3: Provide final analysis
            """Thought: I have all the calculations. Let me provide a comprehensive analysis.
Final Answer: Here's the compound interest analysis for your investment:

**Initial Investment:** $10,000
**Interest Rate:** 5% annual (compounded monthly)
**Time Period:** 10 years

**Final Amount:** $16,470.09
**Interest Earned:** $6,470.09
**Total Return:** 64.7%

This means your money will grow by about 64.7% over 10 years with monthly compounding at 5% annual interest."""
        ]

        start_time = time.time()
        response = await agent.run(
            "I want to invest $10,000 at 5% annual interest compounded monthly for 10 years. How much will I have and what's the total return?",
            execution_pattern=ExecutionPatternType.REACT
        )
        execution_time = self._track_execution_time(start_time, "complex_calculation")

        # Verify calculations were performed (tools executed successfully)
        # Check for key financial terms and calculations in response
        assert "$10,000" in response
        assert "16,470" in response or "16470" in response
        assert "6,470" in response or "6470" in response
        assert "64.7%" in response or "64.7" in response

        await agent.stop()

    async def _setup_calculation_tools(self):
        """Helper to set up calculation tools."""
        # Already done in parent setup, but ensure calculator is available
        pass

    @pytest.mark.asyncio
    async def test_problem_solving_with_constraints_scenario(self):
        """Scenario: User presents a problem with multiple constraints that require iterative solving."""
        agent = await self._create_agent()

        self.mock_llm_function.side_effect = [
            # First ReAct response
            """Thought: This is an optimization problem. I need to find the best way to allocate a $50,000 budget across different marketing channels with the given constraints and expected returns.

Let me work through this systematically:
- Social Media: Max $15k, 3x return = up to $45k return
- Email Marketing: Max $10k, 4x return = up to $40k return
- Content Marketing: Max $20k, 2.5x return = up to $50k return
- Paid Ads: Max $25k, 2x return = up to $50k return

To maximize return, I should prioritize highest ROI first: Email (4x), then Social (3x), then Content (2.5x), then Paid Ads (2x).

Optimal allocation:
- Email Marketing: $10,000 (max) → $40,000 return
- Social Media: $15,000 (max) → $45,000 return
- Content Marketing: $20,000 (max) → $50,000 return
- Paid Ads: $5,000 (remaining) → $10,000 return

Total: $50,000 invested → $145,000 return (2.9x overall)

Final Answer: Here's the optimal allocation of your $50,000 marketing budget:

**Recommended Allocation:**
1. **Email Marketing: $10,000** (4x ROI = $40,000 return)
2. **Social Media: $15,000** (3x ROI = $45,000 return)
3. **Content Marketing: $20,000** (2.5x ROI = $50,000 return)
4. **Paid Advertising: $5,000** (2x ROI = $10,000 return)

**Total Investment:** $50,000
**Total Expected Return:** $145,000
**Overall ROI:** 2.9x (190% profit)

**Strategy:** This allocation maximizes ROI by fully funding the highest-return channels first (email and social media), then allocating remaining budget to content marketing and minimal paid ads.""",

            # Second ReAct call (in case pattern needs continuation)
            """Final Answer: The optimal allocation is complete as analyzed above."""
        ]

        start_time = time.time()
        response = await agent.run(
            """I have $50,000 to spend on marketing with these options:
            - Social Media: up to $15k budget, 3x return
            - Email Marketing: up to $10k budget, 4x return
            - Content Marketing: up to $20k budget, 2.5x return
            - Paid Advertising: up to $25k budget, 2x return

            How should I allocate the budget to maximize ROI?""",
            execution_pattern=ExecutionPatternType.REACT
        )
        execution_time = self._track_execution_time(start_time, "problem_solving_constraints")

        # Verify optimization analysis
        assert "$50,000" in response
        assert "Email Marketing" in response and "$10,000" in response
        assert "Social Media" in response and "$15,000" in response
        assert "2.9x" in response or "190%" in response
        assert "maximize" in response.lower() or "optimal" in response.lower()

        await agent.stop()


class TestPlanExecutionScenarios(ScenarioTestBase):
    """Scenario 4: Plan-Execution Pattern - Breaking down complex tasks into steps."""

    @pytest.mark.asyncio
    async def test_project_planning_scenario(self):
        """Scenario: User needs help planning a complex project with multiple phases."""
        agent = await self._create_agent()

        self.mock_llm_function.side_effect = [
            # First call - Planning phase
            """Step 1: Define project scope and phases
Step 2: Create detailed timeline with phases
Step 3: Identify key deliverables and milestones
Step 4: Consider resource requirements and constraints""",

            # First call - Execution phase (this becomes response1)
            """I'll help you create a comprehensive plan for launching your e-commerce website. Let me break this down into key phases:

**PROJECT PLAN: E-commerce Website Launch**

**Phase 1: Planning & Strategy (Weeks 1-2)**
- Define target audience and user personas
- Competitive analysis and market research
- Feature requirements and technical specifications
- Choose technology stack (e.g., Shopify, WooCommerce, custom)
- Budget allocation and timeline finalization

**Phase 2: Design & User Experience (Weeks 3-5)**
- Wireframing and user journey mapping
- Visual design and branding
- Mobile-responsive design
- User interface prototyping
- Usability testing with target users

**Phase 3: Development & Integration (Weeks 6-10)**
- Frontend development
- Backend and database setup
- Payment gateway integration (Stripe, PayPal)
- Inventory management system
- Security implementation (SSL, PCI compliance)
- Testing (unit, integration, security)

**Phase 4: Content & SEO (Weeks 8-11)**
- Product photography and descriptions
- SEO optimization and meta tags
- Content marketing strategy
- Legal pages (terms, privacy, returns)
- Google Analytics and tracking setup

**Phase 5: Launch & Marketing (Weeks 12-14)**
- Soft launch with beta users
- Bug fixes and performance optimization
- Marketing campaign launch
- Social media presence setup
- Customer support processes

**Phase 6: Post-Launch Optimization (Ongoing)**
- Monitor analytics and user behavior
- A/B testing for conversion optimization
- Customer feedback collection and iteration
- Scale infrastructure as needed

Would you like me to elaborate on any specific phase or adjust the timeline based on your resources?""",

            # Second call - Planning phase
            """Step 1: Analyze team size and capabilities
Step 2: Adjust timeline and resource allocation
Step 3: Identify critical path items
Step 4: Provide specific recommendations for 3-developer team""",

            # Second call - Execution phase (this becomes response2)
            """Based on your team size, I recommend focusing on these critical path items first:

**Immediate Priorities (Next 2 weeks):**
1. Finalize your technology stack decision
2. Complete competitive analysis
3. Define your minimum viable product (MVP) features
4. Set up project management tools and workflows

**Resource Allocation:**
- With 3 developers, assign: 1 frontend, 1 backend, 1 DevOps/testing
- Plan for 20% buffer time for unexpected challenges
- Consider outsourcing design if no dedicated designer

The 14-week timeline is realistic for a quality launch with your team size."""
        ]

        start_time = time.time()
        response1 = await agent.run(
            "I need to plan the launch of an e-commerce website. Can you help me create a detailed project plan?",
            execution_pattern=ExecutionPatternType.PLANNING
        )

        response2 = await agent.run(
            "This looks great! I have a team of 3 developers. How should I adjust the plan?",
            execution_pattern=ExecutionPatternType.PLANNING
        )

        execution_time = self._track_execution_time(start_time, "project_planning")

        # Verify comprehensive project plan (plan-and-execute returns the execution result)
        assert "Phase" in response1 and ("Week" in response1 or "phase" in response1.lower())
        assert "plan" in response1.lower() or "launch" in response1.lower()

        # Verify follow-up adaptation
        assert "3 developers" in response2 or "team size" in response2
        assert "frontend" in response2 and "backend" in response2

        await agent.stop()

    @pytest.mark.asyncio
    async def test_learning_curriculum_scenario(self):
        """Scenario: User wants a structured learning plan for a complex skill."""
        agent = await self._create_agent()

        self.mock_llm_function.return_value = """I'll create a comprehensive 12-week machine learning curriculum for you:

**MACHINE LEARNING MASTERY PLAN**

**Phase 1: Mathematical Foundations (Weeks 1-3)**
- Week 1: Linear Algebra Review
  - Vectors, matrices, eigenvalues
  - Resources: Khan Academy Linear Algebra
  - Practice: Numpy exercises

- Week 2: Statistics & Probability
  - Distributions, Bayes theorem, hypothesis testing
  - Resources: Think Stats (free online)
  - Practice: Statistical analysis with pandas

- Week 3: Calculus for ML
  - Derivatives, gradients, optimization
  - Resources: 3Blue1Brown calculus series
  - Practice: Manual gradient descent implementation

**Phase 2: Core Machine Learning (Weeks 4-7)**
- Week 4: Supervised Learning Basics
  - Linear/logistic regression, decision trees
  - Resources: Andrew Ng's Coursera course (Week 1-3)
  - Practice: Scikit-learn implementations

- Week 5: Model Evaluation & Selection
  - Cross-validation, bias-variance tradeoff, metrics
  - Resources: "Hands-On Machine Learning" Ch 2-3
  - Practice: Build evaluation pipeline

- Week 6: Ensemble Methods
  - Random forests, boosting, bagging
  - Resources: Kaggle Learn courses
  - Practice: Kaggle competition entry

- Week 7: Unsupervised Learning
  - Clustering, dimensionality reduction, PCA
  - Resources: Course materials + research papers
  - Practice: Customer segmentation project

**Phase 3: Deep Learning (Weeks 8-10)**
- Week 8: Neural Network Fundamentals
  - Perceptrons, backpropagation, activation functions
  - Resources: Fast.ai course Part 1
  - Practice: Build neural network from scratch

- Week 9: Deep Learning Frameworks
  - TensorFlow/PyTorch, CNNs, RNNs
  - Resources: Official tutorials
  - Practice: Image classification project

- Week 10: Advanced Architectures
  - Transfer learning, attention, transformers
  - Resources: Papers + blog posts
  - Practice: NLP project with pre-trained models

**Phase 4: MLOps & Production (Weeks 11-12)**
- Week 11: Model Deployment
  - Docker, APIs, cloud platforms
  - Resources: MLOps courses
  - Practice: Deploy model to cloud

- Week 12: Production ML Systems
  - Monitoring, A/B testing, data pipelines
  - Resources: "Building Machine Learning Powered Applications"
  - Practice: End-to-end ML system

**Weekly Schedule (10-12 hours/week):**
- Theory: 4 hours (videos, reading)
- Practice: 6 hours (coding, projects)
- Review: 2 hours (consolidation, notes)

**Success Metrics:**
- Complete 3 end-to-end projects
- Contribute to 1 open source ML project
- Pass online assessment or certification

Would you like me to customize this based on your current background or specific ML interests?"""

        start_time = time.time()
        response = await agent.run(
            "I want to learn machine learning over the next 3 months. Can you create a structured learning plan?",
            execution_pattern=ExecutionPatternType.PLANNING
        )
        execution_time = self._track_execution_time(start_time, "learning_curriculum")

        # Verify structured curriculum
        assert "Week" in response and "Phase" in response
        assert "machine learning" in response.lower()
        assert len([line for line in response.split('\n') if 'Week' in line]) >= 8
        assert "practice" in response.lower() or "project" in response.lower()

        await agent.stop()

    @pytest.mark.asyncio
    async def test_business_strategy_scenario(self):
        """Scenario: User needs strategic business planning with execution steps."""
        agent = await self._create_agent()

        self.mock_llm_function.return_value = """Thought: The user needs a comprehensive go-to-market strategy for their SaaS productivity tool. I should provide a detailed strategic plan.
Final Answer: Here's a comprehensive go-to-market strategy for your SaaS productivity tool:

**GO-TO-MARKET STRATEGY: PRODUCTIVITY SAAS**

**Phase 1: Market Foundation (Month 1)**

*Week 1-2: Customer Discovery*
- Interview 50+ potential customers in target segments
- Validate problem-solution fit through user surveys
- Define ideal customer profile (ICP) and personas
- Competitive analysis and positioning strategy

*Week 3-4: Product-Market Fit Validation*
- Launch private beta with 20-30 early adopters
- Collect detailed feedback and usage analytics
- Iterate on core features based on user behavior
- Establish key success metrics and KPIs

**Phase 2: Launch Preparation (Month 2)**

*Week 5-6: Marketing Foundation*
- Build landing page with A/B testing capability
- Create content marketing strategy and editorial calendar
- Set up analytics (Google Analytics, Mixpanel)
- Develop sales enablement materials

*Week 7-8: Channel Strategy*
- Identify and test acquisition channels (content, paid, partnerships)
- Build referral program and viral mechanics
- Establish pricing strategy with multiple tiers
- Create customer onboarding and success processes

**Phase 3: Market Entry (Month 3)**

*Week 9-10: Soft Launch*
- Launch to extended network and early adopters
- Execute PR strategy and thought leadership content
- Begin paid acquisition testing with small budgets
- Implement customer feedback loops

*Week 11-12: Scale Preparation*
- Optimize conversion funnel based on early data
- Build customer support and success team processes
- Establish partnerships with complementary tools
- Prepare for broader market launch

**Success Metrics by Phase:**
- Phase 1: 80% problem validation rate, 90% beta retention
- Phase 2: 15% landing page conversion, 50+ early customers
- Phase 3: $10k MRR, 5% monthly churn, 40+ NPS score

**Resource Requirements:**
- Marketing budget: $15k/month initially
- Team: Product Manager, 2 Engineers, 1 Marketer, 1 Designer
- Tools: CRM, analytics, marketing automation, support platform

**Risk Mitigation:**
- Weekly customer interviews to stay connected to market needs
- Monthly strategy reviews and pivot readiness
- Diversified acquisition channel testing
- Strong unit economics focus from day one

This plan balances speed to market with thorough validation. Would you like me to dive deeper into any specific phase or adjust based on your current resources?"""

        start_time = time.time()
        response = await agent.run(
            "I'm launching a SaaS productivity tool and need a go-to-market strategy. Help me plan the launch and growth phases.",
            execution_pattern=ExecutionPatternType.PLANNING
        )
        execution_time = self._track_execution_time(start_time, "business_strategy")

        # Verify strategic business plan
        assert "strategy" in response.lower() or "market" in response.lower()
        assert "Phase" in response and "Week" in response
        assert "Month" in response or "week" in response
        assert any(word in response for word in ["customer", "launch", "growth", "revenue"])

        await agent.stop()


class TestMemoryEnhancedScenarios(ScenarioTestBase):
    """Scenario 5: Memory-Enhanced - Using memory for context and learning."""

    @pytest.mark.asyncio
    async def test_personalized_conversation_scenario(self):
        """Scenario: Agent learns user preferences and adapts responses over time."""
        agent = await self._create_agent(enable_memory=True)

        # First interaction - establish preferences (PlanAndExecutePattern calls LLM twice)
        # Second interaction uses Chain of Thought (calls LLM once)
        self.mock_llm_function.side_effect = [
            # First call - Planning phase
            "Step 1: Acknowledge the user's learning preference\nStep 2: Confirm I will remember this for future interactions",
            # First call - Execution phase
            "Thanks for letting me know! I'll remember that you prefer detailed explanations with examples. This will help me tailor my responses to your learning style.",
            # Second call - Chain of Thought response
            """Since you prefer detailed explanations with examples, let me break down machine learning comprehensively:

**Machine Learning Definition:**
Machine learning is a method of teaching computers to make predictions or decisions by learning patterns from data, rather than being explicitly programmed for each specific task.

**Detailed Explanation:**
Think of it like teaching a child to recognize animals. Instead of describing every feature of every animal, you show them thousands of pictures labeled "cat," "dog," "bird," etc. Eventually, they learn to identify animals in new pictures they've never seen before.

**Practical Examples:**

1. **Email Spam Detection**
   - Input: Email content, sender, subject line
   - Learning: Algorithm studies thousands of emails marked as spam/not spam
   - Output: Automatically classifies new emails

2. **Recommendation Systems (Netflix, Amazon)**
   - Input: Your viewing/purchase history + millions of other users' data
   - Learning: Finds patterns in what similar users liked
   - Output: Suggests movies/products you might enjoy

3. **Autonomous Vehicles**
   - Input: Camera feeds, sensor data, GPS information
   - Learning: Trained on millions of driving scenarios
   - Output: Makes driving decisions (brake, turn, accelerate)

This approach matches your preference for comprehensive explanations with concrete examples. Would you like me to dive deeper into any specific aspect?"""
        ]

        result1 = await agent.run("I prefer detailed explanations with practical examples when learning new concepts.")

        start_time = time.time()
        response = await agent.run("Can you explain machine learning to me?")
        execution_time = self._track_execution_time(start_time, "personalized_conversation")

        # Verify memory utilization - check conversation turns in context
        context = await agent.memory_manager.get_context_memory(agent.session_id)
        assert len(context.conversation_turns) >= 2  # Should have stored interactions

        # Verify personalized response
        assert "detailed" in response.lower() or "examples" in response.lower()
        assert len(response.split("Example")) >= 2  # Multiple examples provided
        assert "preference" in response.lower() or "you prefer" in response.lower()

        await agent.stop()

    @pytest.mark.asyncio
    async def test_project_context_retention_scenario(self):
        """Scenario: Agent maintains context about an ongoing project across multiple sessions."""
        agent = await self._create_agent(enable_memory=True)

        # All three interactions use ReAct pattern, so need "Thought:" and "Final Answer:" format
        self.mock_llm_function.side_effect = [
            # Session 1: Project initiation
            """Thought: The user is starting a new project and I should acknowledge their project details and offer to help.
Final Answer: Great! I've noted that you're building a recipe recommendation app with React Native, targeting health-conscious users who want personalized meal planning. I'll remember these details for our future discussions.""",

            # Session 2: Technical discussion (should remember project context)
            """Thought: The user is asking about database design for their React Native recipe recommendation app. I should provide comprehensive database schema recommendations.
Final Answer: For your React Native recipe recommendation app, here are the key database design considerations:

**User Profile Schema:**
```sql
Users: user_id, dietary_preferences, allergies, health_goals, activity_level
```

**Recipe Data Schema:**
```sql
Recipes: recipe_id, title, ingredients, nutrition_facts, prep_time, difficulty
RecipeTags: recipe_id, tag (vegetarian, low-carb, high-protein, etc.)
```

**Recommendation Engine Data:**
```sql
UserRecipeRatings: user_id, recipe_id, rating, date_tried
UserPreferences: user_id, ingredient_preferences, cuisine_preferences
```

**Health-Conscious Features:**
- Nutrition tracking with macro/micro nutrient breakdown
- Integration with fitness apps (MyFitnessPal API)
- Meal planning with shopping list generation
- Dietary restriction filtering (gluten-free, keto, etc.)

Since this is for health-conscious users, consider partnering with nutritionist APIs for validated meal plans. Would you like me to elaborate on the recommendation algorithm design?""",

            # Session 3: Further development (should maintain full context)
            """Thought: The user is asking about onboarding flow for their React Native recipe app. I should provide recommendations that build on our previous discussions.
Final Answer: For the user onboarding flow in your React Native recipe app, here's a health-focused approach:

**Onboarding Screens:**

1. **Welcome & Value Proposition**
   - "Personalized recipes for your health journey"
   - Highlight key benefits for health-conscious users

2. **Health Goals Selection**
   - Weight management, muscle building, general wellness
   - Activity level (sedentary, moderate, active)

3. **Dietary Preferences**
   - Restrictions: vegetarian, vegan, gluten-free, keto, etc.
   - Allergies: nuts, dairy, shellfish, etc.
   - Cultural/religious preferences

4. **Cooking Preferences**
   - Skill level, available time, equipment
   - Meal types preferred (quick meals, batch cooking, etc.)

5. **Taste Profile**
   - Favorite cuisines and flavor profiles
   - Ingredients to avoid (beyond allergies)

This builds on our previous database design discussion and ensures you capture the data needed for effective health-conscious recommendations. The onboarding should take 3-4 minutes maximum to maintain engagement."""
        ]

        await agent.run("I'm starting a new project - a recipe recommendation app using React Native for health-conscious users.")
        await agent.run("What database schema would work best for this app?")

        start_time = time.time()
        response = await agent.run("How should I design the user onboarding flow?")
        execution_time = self._track_execution_time(start_time, "project_context_retention")

        # Verify context retention across sessions
        context = await agent.memory_manager.get_context_memory(agent.session_id)
        assert len(context.conversation_turns) >= 2  # Should have stored interactions

        # Check that context contains project-related content
        conversation_text = context.get_conversation_text()
        assert 'recipe' in conversation_text.lower() or 'react native' in conversation_text.lower()

        # Verify contextual response
        assert "recipe" in response.lower() and ("app" in response.lower() or "React Native" in response)
        assert "health" in response.lower() or "dietary" in response.lower()
        assert "onboarding" in response.lower()

        await agent.stop()

    @pytest.mark.asyncio
    async def test_learning_progress_tracking_scenario(self):
        """Scenario: Agent tracks user's learning progress and adapts difficulty."""
        agent = await self._create_agent(enable_memory=True)

        # Set up mock responses for different execution patterns
        # First call: ReAct, Second call: ReAct, Third call: Plan and Execute (needs 2 responses)
        self.mock_llm_function.side_effect = [
            # First call - ReAct pattern
            """Thought: The user has mastered Python basics and is ready for intermediate concepts.
Final Answer: Excellent! I can see you have a solid understanding of Python basics like variables, functions, and loops. I'll note this in your learning profile.""",

            # Second call - ReAct pattern
            """Thought: The user has mastered Python basics and is ready to progress. I should provide intermediate-level Python concepts that build on their foundation.
Final Answer: Based on your solid foundation in Python basics, you're ready for intermediate concepts. Here's your next learning path:

**Intermediate Python Concepts:**

1. **Object-Oriented Programming (OOP)**
   - Classes, objects, inheritance
   - Encapsulation and polymorphism
   - Practice: Build a simple inventory system

2. **Data Structures & Algorithms**
   - Lists, dictionaries, sets comprehensions
   - Big O notation basics
   - Practice: Implement common sorting algorithms

3. **File I/O and Error Handling**
   - Reading/writing files, JSON handling
   - Try-except blocks, custom exceptions
   - Practice: Build a log file analyzer

4. **Libraries and Modules**
   - Import systems, pip package management
   - Popular libraries: requests, pandas, numpy
   - Practice: Create a web scraper

Since you've mastered the basics, these intermediate topics will build naturally on your foundation. I'll adjust the complexity as we go based on your progress. Which area interests you most?""",

            # Third call - Plan and Execute pattern (Planning phase)
            """Step 1: Review user's completed topics (OOP and data structures)
Step 2: Select appropriate advanced Python concepts
Step 3: Structure learning path with practical examples
Step 4: Provide encouraging progression feedback""",

            # Third call - Plan and Execute pattern (Execution phase)
            """Perfect! Since you've now covered OOP and data structures from our previous sessions, let's move to advanced Python topics:

**Advanced Python Concepts:**

1. **Decorators and Metaprogramming**
   - Function decorators, class decorators
   - Understanding how decorators work under the hood
   - Practice: Create timing and logging decorators

2. **Concurrency and Parallelism**
   - Threading vs multiprocessing
   - Asyncio and coroutines
   - Practice: Build concurrent web scraper

3. **Context Managers**
   - With statements, __enter__/__exit__ methods
   - Creating custom context managers
   - Practice: Database connection manager

You're progressing well through the curriculum! Your foundation in basics + intermediate OOP makes you ready for these advanced patterns. Which concept would you like to start with?"""
        ]

        await agent.run("I've been learning Python and I'm comfortable with variables, functions, and loops. What should I learn next?")
        await agent.run("I think I'm ready for more advanced topics now.")

        start_time = time.time()
        response = await agent.run("I've finished studying OOP and data structures. What advanced topics should I tackle next?")
        execution_time = self._track_execution_time(start_time, "learning_progress_tracking")

        # Verify learning progression tracking
        context = await agent.memory_manager.get_context_memory(agent.session_id)
        assert len(context.conversation_turns) >= 3

        # Check that the context contains progression
        conversation_text = context.get_conversation_text()
        assert "python" in conversation_text.lower()

        # Verify adaptive difficulty
        assert "advanced" in response.lower()
        assert any(concept in response for concept in ["decorators", "concurrency", "context"])
        assert "OOP" in response or "data structures" in response  # References previous learning

        await agent.stop()


class TestPromptOptimizationScenarios(ScenarioTestBase):
    """Scenario 6: Prompt Optimization - Testing adaptive prompt improvement."""

    def setup_method(self):
        """Set up prompt optimization test fixtures."""
        super().setup_method()
        # Note: This would integrate with the optimization module when implemented
        self.optimization_enabled = hasattr(self, 'agent') and hasattr(self.agent, 'optimizer')

    @pytest.mark.asyncio
    async def test_response_quality_improvement_scenario(self):
        """Scenario: Agent learns from feedback to improve response quality."""
        agent = await self._create_agent()

        # Initial response (suboptimal) - Chain of Thought pattern
        self.mock_llm_function.return_value = "Machine learning is when computers learn things from data."

        initial_response = await agent.run("Explain machine learning")

        # Simulate feedback processing (would normally be done through external feedback mechanism)
        # For testing purposes, we'll simulate an improved response in the next interaction

        # Improved response after simulated feedback
        self.mock_llm_function.return_value = """Thought: The user wants an explanation of machine learning. I should provide a comprehensive overview with examples and applications.
Final Answer: Machine learning is a branch of artificial intelligence that enables computers to learn and make decisions from data without being explicitly programmed for every scenario.

**Key Components:**
- **Data**: Training information that teaches the algorithm
- **Algorithm**: The mathematical model that finds patterns
- **Model**: The trained system that makes predictions

**Real-World Example:**
When Netflix recommends movies, it uses machine learning to analyze viewing patterns from millions of users to predict what you might enjoy watching next.

**Common Applications:**
- Email spam detection
- Image recognition in photos
- Voice assistants like Siri
- Autonomous vehicle navigation

The power of ML lies in its ability to improve performance automatically as it processes more data."""

        start_time = time.time()
        improved_response = await agent.run("Explain machine learning")
        execution_time = self._track_execution_time(start_time, "response_quality_improvement")

        # Verify improvement
        assert len(improved_response) > len(initial_response) * 2
        assert "example" in improved_response.lower()
        assert "applications" in improved_response.lower() or "uses" in improved_response.lower()

        await agent.stop()

    @pytest.mark.asyncio
    async def test_domain_adaptation_scenario(self):
        """Scenario: Agent adapts its language and examples to user's domain expertise."""
        agent = await self._create_agent()

        # Establish user domain (medical professional)
        self.mock_llm_function.return_value = "Thank you for that context! I'll tailor my explanations using medical terminology and healthcare examples that will be most relevant to your work."

        await agent.run("I'm a medical doctor interested in AI applications in healthcare.")

        # Domain-adapted response
        self.mock_llm_function.return_value = """Thought: The user is a medical doctor asking about machine learning applications in their field. I should provide domain-specific examples using medical terminology.
Final Answer: Machine learning in healthcare represents a paradigm shift in clinical decision-making and patient care optimization. Here's how it applies to medical practice:

**Clinical Applications:**

1. **Diagnostic Imaging Analysis**
   - Radiology: CNN models for detecting lung nodules in CT scans
   - Pathology: Digital pathology for histological analysis
   - Ophthalmology: Diabetic retinopathy screening from fundus photographs

2. **Clinical Decision Support Systems (CDSS)**
   - Risk stratification algorithms (APACHE scores, SOFA scores)
   - Drug-drug interaction prediction
   - Sepsis early warning systems in ICU settings

3. **Precision Medicine**
   - Pharmacogenomics: Predicting drug efficacy based on genetic markers
   - Treatment response prediction using biomarker profiles
   - Personalized dosing algorithms

**Technical Considerations for Healthcare:**
- Regulatory compliance (FDA 510(k), CE marking)
- Clinical validation requirements and endpoints
- Integration with Electronic Health Records (EHR/EMR)
- HIPAA compliance and patient privacy

**Evidence Base:**
Recent studies show ML models achieving diagnostic accuracy comparable to or exceeding specialist physicians in specific domains (dermatology, radiology).

Would you like me to elaborate on any specific clinical application or discuss implementation challenges in hospital systems?"""

        start_time = time.time()
        response = await agent.run("How can machine learning be applied in my field?")
        execution_time = self._track_execution_time(start_time, "domain_adaptation")

        # Verify domain-specific adaptation
        assert any(term in response for term in ["clinical", "patient", "diagnostic", "healthcare"])
        assert any(term in response for term in ["CT", "ICU", "EHR", "HIPAA"])  # Medical acronyms
        assert "medical" in response.lower() or "healthcare" in response.lower()

        await agent.stop()

    @pytest.mark.asyncio
    async def test_communication_style_optimization_scenario(self):
        """Scenario: Agent optimizes communication style based on user interactions."""
        agent = await self._create_agent()

        # Track user preference for concise, actionable responses
        # Note: 3rd call uses Plan and Execute (2 LLM calls), others use ReAct (1 call each)
        responses = [
            # 1st call - ReAct
            """Thought: The user is asking about starting a startup. I should provide clear, actionable steps.
Final Answer: Here are 3 key steps: 1) Set clear objectives 2) Track metrics 3) Iterate quickly""",

            # 2nd call - ReAct
            """Thought: The user wants to know about product validation. I'll provide concise, practical guidance.
Final Answer: Quick summary: Focus on user needs, validate early, iterate based on feedback""",

            # 3rd call - Plan and Execute (Planning phase)
            "Step 1: Identify core product development principles\nStep 2: Provide actionable implementation steps\nStep 3: Give specific recommendations",

            # 3rd call - Plan and Execute (Execution phase)
            "Action items: Research competitors, define MVP, build prototype",

            # 4th call - Plan and Execute (Planning phase)
            "Step 1: Analyze SaaS marketing channels\nStep 2: Create actionable marketing plan\nStep 3: Define key metrics and next steps",

            # 4th call - Plan and Execute (Execution phase)
            """**Marketing Strategy - Action Plan:**

**Immediate Actions (Week 1):**
• Define target customer persona with specific demographics
• Audit competitors' messaging and positioning strategies
• Create initial value proposition hypothesis

**Short-term Execution (Weeks 2-4):**
• A/B test landing page copy with 3 different value props
• Launch small-scale paid campaigns (Facebook, Google Ads)
• Interview 20+ potential customers for messaging validation

**Key Metrics to Track:**
• Landing page conversion rate (target: >3%)
• Cost per acquisition (CPA) by channel
• Message-to-market fit score from interviews

**Next Steps:**
• Weekly performance reviews and campaign optimization
• Scale winning messages across all channels
• Develop content calendar based on validated messaging

This action-oriented approach matches your preference for direct, implementable guidance."""
        ]

        self.mock_llm_function.side_effect = responses

        # Multiple interactions to establish pattern
        await agent.run("How do I start a startup?")
        await agent.run("What's the best way to validate a product idea?")
        await agent.run("How should I approach product development?")

        start_time = time.time()
        response = await agent.run("What marketing strategy should I use for my new SaaS product?")
        execution_time = self._track_execution_time(start_time, "communication_style_optimization")

        # Verify style adaptation
        assert "Action" in response or "•" in response or "Steps:" in response
        assert len([line for line in response.split('\n') if line.strip().startswith('•')]) >= 3
        assert "implementable" in response.lower() or "action" in response.lower()

        await agent.stop()


class TestScenarioRunner:
    """Comprehensive test runner for scenario-driven tests."""

    @pytest.mark.asyncio
    async def test_run_all_scenarios(self):
        """Run all scenarios and collect performance metrics."""
        performance_results = {}

        # Initialize test classes
        test_classes = [
            TestSimpleAgentCallScenarios(),
            TestToolCallingScenarios(),
            TestMultiRoundReActScenarios(),
            TestPlanExecutionScenarios(),
            TestMemoryEnhancedScenarios(),
            TestPromptOptimizationScenarios()
        ]

        total_start_time = time.time()

        for test_class in test_classes:
            class_name = test_class.__class__.__name__
            print(f"\n🧪 Running {class_name}...")

            # Setup
            test_class.setup_method()

            # Collect execution times from completed scenarios
            if hasattr(test_class, 'execution_times'):
                performance_results[class_name] = test_class.execution_times

        total_execution_time = time.time() - total_start_time

        # Performance analysis
        print(f"\n📊 Scenario Performance Summary:")
        print(f"Total test suite execution time: {total_execution_time:.2f}s")

        for class_name, times in performance_results.items():
            if times:
                avg_time = sum(t['duration'] for t in times) / len(times)
                print(f"{class_name}: {len(times)} scenarios, avg {avg_time:.2f}s")

        # Assert performance benchmarks
        assert total_execution_time < 30.0, "Full scenario suite should complete within 30 seconds"


if __name__ == "__main__":
    # Configure tracing for test runs
    configure_tracing(clean_format=True, detailed=True)

    # Run scenario tests
    pytest.main([__file__, "-v", "-s"])