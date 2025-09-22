# Data Model: Enhanced Agent Framework

## Core Entities

### Agent
- **agent_id**: Unique identifier for agent instance
- **config**: Configuration including execution patterns, memory settings
- **session_id**: Current conversation session identifier
- **status**: Current agent state (idle, thinking, executing, error)
- **created_at**: Agent instantiation timestamp
- **last_active**: Last interaction timestamp

**Relationships**: Has many Conversations, has one MemorySystem, has many Tools

**State Transitions**:
- idle → thinking (on user input)
- thinking → executing (when tools needed)
- executing → thinking (tool results received)
- thinking → idle (response complete)
- any → error (on failure)

### ExecutionContext
- **context_id**: Unique execution context identifier
- **agent_id**: Associated agent
- **execution_pattern**: Selected pattern (react, planning, auto, simple)
- **current_step**: Current step in reasoning chain
- **reasoning_steps**: Array of reasoning steps taken
- **tool_calls**: History of tool invocations
- **memory_accessed**: Memory entries accessed during execution
- **start_time**: Execution start timestamp
- **completion_time**: Execution completion timestamp

**Relationships**: Belongs to Agent, has many ReasoningSteps, has many ToolCalls

### ReasoningStep
- **step_id**: Unique step identifier
- **execution_context_id**: Parent execution context
- **step_type**: Type (thought, action, observation, summary)
- **content**: Step content/reasoning
- **metadata**: Additional step-specific data
- **created_at**: Step timestamp
- **duration_ms**: Time taken for this step

**Relationships**: Belongs to ExecutionContext

### MemoryEntry
- **entry_id**: Unique memory entry identifier
- **agent_id**: Associated agent
- **session_id**: Session where memory was created
- **content**: Memory content/information
- **entry_type**: Type (conversation, fact, procedure, concept)
- **importance_score**: Importance rating (0.0 to 1.0)
- **created_at**: Entry creation timestamp
- **last_accessed**: Last access timestamp
- **access_count**: Number of times accessed
- **decay_factor**: Temporal decay multiplier
- **relationships**: Graph relationships to other entries

**Relationships**: Belongs to Agent, has many MemoryRelationships

**Validation Rules**:
- importance_score must be between 0.0 and 1.0
- content cannot be empty
- created_at must be valid timestamp

### MemoryRelationship
- **relationship_id**: Unique relationship identifier
- **source_entry_id**: Source memory entry
- **target_entry_id**: Target memory entry
- **relationship_type**: Type (causes, relates_to, contradicts, supports)
- **strength**: Relationship strength (0.0 to 1.0)
- **created_at**: Relationship creation timestamp

**Relationships**: Connects MemoryEntry to MemoryEntry

### Tool
- **tool_id**: Unique tool identifier
- **name**: Tool name
- **description**: Tool description
- **tool_type**: Type (local, mcp_server, rest_api)
- **connection_info**: Connection configuration
- **schema**: Tool input/output schema
- **status**: Tool status (active, inactive, error)
- **last_used**: Last usage timestamp
- **usage_count**: Number of times used

**Relationships**: Belongs to Agent through ToolRegistration

### ToolCall
- **call_id**: Unique tool call identifier
- **execution_context_id**: Associated execution context
- **tool_id**: Tool that was called
- **input_data**: Input provided to tool
- **output_data**: Tool response/output
- **success**: Whether call succeeded
- **error_message**: Error details if failed
- **start_time**: Call start timestamp
- **end_time**: Call completion timestamp
- **latency_ms**: Call duration in milliseconds

**Relationships**: Belongs to ExecutionContext and Tool

### Conversation
- **conversation_id**: Unique conversation identifier
- **agent_id**: Associated agent
- **session_id**: Session identifier
- **messages**: Array of conversation messages
- **summary**: Conversation summary
- **created_at**: Conversation start timestamp
- **last_message_at**: Last message timestamp
- **message_count**: Total number of messages

**Relationships**: Belongs to Agent, has many Messages

### Message
- **message_id**: Unique message identifier
- **conversation_id**: Parent conversation
- **role**: Message role (user, agent, system)
- **content**: Message content
- **metadata**: Additional message data
- **timestamp**: Message timestamp

**Relationships**: Belongs to Conversation

### BenchmarkResult
- **result_id**: Unique result identifier
- **benchmark_name**: Name of benchmark test
- **agent_config**: Agent configuration used
- **score**: Benchmark score
- **metrics**: Detailed performance metrics
- **comparison_framework**: Framework compared against
- **execution_time**: Time taken for benchmark
- **memory_usage**: Memory consumption during test
- **created_at**: Benchmark execution timestamp

**Validation Rules**:
- score must be numeric and positive
- execution_time must be positive
- memory_usage must be positive

### LLMConfig (SIMPLIFIED)
- **provider**: Provider name (openai, anthropic, ollama, etc.)
- **model**: Model name (gpt-4, claude-3-sonnet, etc.)
- **api_key**: Authentication key
- **temperature**: Generation temperature (0.0-1.0)
- **max_tokens**: Maximum tokens to generate
- **stream**: Whether to enable streaming (boolean)

**Rationale**: Simple configuration object, avoid complex provider abstraction

### BenchmarkResult (SIMPLIFIED)
- **framework_name**: Framework tested (mini_agent, langchain, etc.)
- **test_cases**: List of test scenarios
- **results**: List of response times and outputs
- **average_time**: Average response time
- **success_rate**: Percentage of successful responses
- **timestamp**: When benchmark was run

**Rationale**: Simple result storage, avoid complex comparison hierarchies

## Knowledge Graph Schema

### Concept Nodes
- **concept_id**: Unique concept identifier
- **name**: Concept name
- **type**: Concept type (entity, action, attribute, relationship)
- **definition**: Concept definition
- **confidence**: Confidence in concept accuracy (0.0 to 1.0)
- **source_entries**: Memory entries that define this concept

### Concept Relationships
- **relationship_id**: Unique relationship identifier
- **source_concept**: Source concept
- **target_concept**: Target concept
- **relationship_type**: Semantic relationship type
- **strength**: Relationship strength
- **evidence_count**: Number of supporting memory entries

## Temporal Management

### Decay Functions
- **Linear Decay**: importance * (1 - decay_rate * time_elapsed)
- **Exponential Decay**: importance * exp(-decay_rate * time_elapsed)
- **Usage-based**: importance * (access_count / (access_count + decay_threshold))

### Freshness Scoring
- **Temporal Relevance**: Combines creation time, last access, and usage frequency
- **Content Relevance**: Semantic similarity to current context
- **Importance Weighting**: Balances temporal and content factors

## Index Strategies

### Memory Search Indices
- **Semantic Index**: Vector embeddings for content similarity
- **BM25 Index**: Traditional text search capabilities
- **Temporal Index**: Time-based access patterns
- **Graph Index**: Relationship traversal optimization

### Performance Optimization
- **Cache Layers**: Redis for frequently accessed data
- **Batch Operations**: Efficient bulk memory operations
- **Connection Pooling**: Database connection management
- **Query Optimization**: Indexed queries for common patterns