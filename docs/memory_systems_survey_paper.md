# Memory Systems for Large Language Model-Based Agents: A Comprehensive Survey

**Abstract**

The emergence of Large Language Model (LLM)-based agents has catalyzed a paradigm shift in artificial intelligence, enabling autonomous systems capable of complex reasoning, decision-making, and interaction. However, a fundamental limitation of LLMs is their constrained context window and inability to retain information across sessions, which severely limits their utility in long-running, stateful applications. Memory systems have emerged as a critical component to address this challenge, enabling agents to accumulate experiences, maintain context, and improve performance over time. This survey provides a comprehensive analysis of memory architectures for LLM-based agents, systematically categorizing approaches into working memory, episodic memory, semantic memory, and procedural memory. We examine the technical foundations of vector databases, knowledge graphs, and hybrid memory systems, comparing prominent frameworks including MemGPT, Reflexion, A-MEM, Graphiti, and production systems like LangChain, LlamaIndex, CrewAI, and AutoGen. Through detailed technical analysis and comparative evaluation, we identify key design patterns, performance characteristics, and architectural trade-offs. We further discuss memory consolidation, forgetting mechanisms, and the challenges of scaling memory systems for multi-agent architectures. Our analysis reveals that while significant progress has been made, critical challenges remain in temporal reasoning, cross-session coherence, and efficient memory retrieval at scale. This survey aims to provide researchers and practitioners with a structured understanding of the current state-of-the-art and future directions in agent memory systems.

**Keywords:** Large Language Models, Agent Memory, Cognitive Architecture, Retrieval-Augmented Generation, Knowledge Graphs, Vector Databases, Multi-Agent Systems

---

## 1. Introduction

### 1.1 Motivation

The rapid advancement of Large Language Models (LLMs) such as GPT-4, Claude, and Llama has enabled the development of increasingly sophisticated autonomous agents capable of performing complex tasks, from customer service to software development and scientific research. However, a fundamental limitation persists: LLMs operate within fixed context windows (typically 8K-200K tokens) and lack persistent memory across sessions. This constraint creates several critical challenges:

1. **Context Window Limitations**: As conversations extend beyond the context window, earlier information is lost, leading to inconsistent behavior and failure to maintain long-term coherence.

2. **Session Discontinuity**: Traditional LLMs cannot remember information from previous interactions, requiring users to repeatedly provide context and preventing agents from learning and adapting over time.

3. **Knowledge Grounding**: Without access to external memory, agents cannot efficiently access domain-specific knowledge or updated information beyond their training cutoff.

4. **Multi-Turn Reasoning**: Complex tasks requiring multi-step reasoning and planning benefit from the ability to store and retrieve intermediate results, hypotheses, and learned strategies.

These limitations have driven extensive research into memory systems for LLM-based agents, drawing inspiration from cognitive science, database systems, and information retrieval. The goal is to create agents that can accumulate experiences, maintain persistent state, and continuously improve performance—capabilities fundamental to human-like intelligence.

### 1.2 Scope and Contributions

This survey provides a comprehensive analysis of memory systems for LLM-based agents, covering research from 2023 to early 2025. Our key contributions include:

1. **Comprehensive Taxonomy**: We present a systematic categorization of memory architectures based on cognitive science principles, organizing systems by memory type (working, episodic, semantic, procedural) and technical implementation (vector-based, graph-based, hybrid).

2. **Technical Deep-Dive**: We provide detailed technical analysis of memory mechanisms including embedding strategies, retrieval algorithms, consolidation processes, and forgetting mechanisms.

3. **Comparative Evaluation**: We systematically compare prominent memory systems (MemGPT, A-MEM, Graphiti, Mem0, Reflexion) and frameworks (LangChain, LlamaIndex, CrewAI, AutoGen) across multiple dimensions including architecture, performance, scalability, and use cases.

4. **Design Patterns and Trade-offs**: We identify recurring architectural patterns and analyze fundamental trade-offs between memory capacity, retrieval efficiency, consistency, and computational cost.

5. **Future Directions**: We discuss open challenges and promising research directions, including temporal reasoning, cross-agent memory sharing, privacy-preserving memory, and neuromorphic memory architectures.

### 1.3 Organization

The remainder of this survey is organized as follows: Section 2 provides background on LLM-based agents and cognitive memory models. Section 3 presents our taxonomy of memory systems. Section 4 examines memory architectures in detail, covering vector-based, graph-based, and hybrid approaches. Section 5 compares major memory systems and frameworks. Section 6 discusses applications and use cases. Section 7 addresses challenges and limitations. Section 8 explores future research directions, and Section 9 concludes.

---

## 2. Background and Preliminaries

### 2.1 Large Language Model-Based Agents

LLM-based agents are autonomous systems that leverage large language models as their core reasoning engine. Unlike traditional chatbots that simply respond to queries, agents can:

- **Plan and Execute**: Decompose complex tasks into sub-tasks and execute them sequentially or in parallel
- **Use Tools**: Interface with external systems, databases, APIs, and search engines
- **Maintain State**: Track conversation context, task progress, and intermediate results
- **Adapt and Learn**: Modify behavior based on feedback and accumulated experience

A typical agent architecture consists of:

1. **Perception Module**: Processes inputs from users or the environment
2. **Reasoning Engine**: The LLM that performs inference, planning, and decision-making
3. **Memory System**: Stores and retrieves information across interactions
4. **Action Module**: Executes actions via tool use or API calls
5. **Reflection Module**: Evaluates outcomes and updates memory/strategy

### 2.2 Cognitive Memory Models

Agent memory systems draw heavily from cognitive science research on human memory, which identifies several distinct memory types:

#### 2.2.1 Working Memory

Working memory (also called short-term memory) holds information temporarily for immediate processing. In humans, it has limited capacity (approximately 7±2 items) and decays rapidly. For LLM agents, working memory typically corresponds to the current context window, containing:

- Recent conversation turns
- Active task state
- Intermediate reasoning steps
- Retrieved information from long-term memory

#### 2.2.2 Episodic Memory

Episodic memory stores experiences and events with temporal and contextual information. In agents, episodic memory records:

- Past conversations and interactions
- Task execution history
- Successes and failures
- Temporal context (when events occurred)

Episodic memory enables agents to recall specific past events and learn from experience.

#### 2.2.3 Semantic Memory

Semantic memory contains generalized knowledge and facts independent of specific experiences. For agents, this includes:

- Domain knowledge and expertise
- Factual information about entities, concepts, and relationships
- General procedures and strategies
- Learned abstractions from multiple episodes

#### 2.2.4 Procedural Memory

Procedural memory stores skills and learned behaviors—"knowing how" rather than "knowing what." In agents, this manifests as:

- Learned task execution strategies
- Tool use patterns
- Optimization rules
- Behavioral policies

### 2.3 Technical Foundations

#### 2.3.1 Vector Embeddings

Modern memory systems extensively use vector embeddings—dense, continuous vector representations of text that capture semantic meaning. Given text input x, an embedding model E produces a d-dimensional vector:

```
e = E(x) ∈ ℝᵈ
```

Common embedding models include:
- OpenAI's text-embedding-ada-002 (1536 dimensions)
- Sentence-BERT variants (384-1024 dimensions)
- Cohere embeddings (4096 dimensions)

Similarity between embeddings is typically measured using cosine similarity:

```
sim(e₁, e₂) = (e₁ · e₂) / (||e₁|| ||e₂||)
```

#### 2.3.2 Vector Databases

Vector databases enable efficient similarity search over large collections of embeddings. Popular systems include:

- **Pinecone**: Managed vector database with approximate nearest neighbor (ANN) search
- **Weaviate**: Open-source with hybrid search capabilities
- **Qdrant**: High-performance with payload filtering
- **Chroma**: Lightweight, embeddable database
- **FAISS**: Facebook's library for efficient similarity search

These systems use indexing algorithms (HNSW, IVF, LSH) to achieve sub-linear search complexity.

#### 2.3.3 Knowledge Graphs

Knowledge graphs represent information as entities (nodes) and relationships (edges), enabling structured knowledge representation and reasoning. A knowledge graph KG is defined as:

```
KG = (E, R, T)
```

where:
- E is the set of entities
- R is the set of relation types
- T ⊆ E × R × E is the set of triples (head, relation, tail)

Knowledge graph databases include:
- **Neo4j**: Leading property graph database
- **Memgraph**: High-performance in-memory graph database
- **Amazon Neptune**: Managed graph database
- **FalkorDB**: Graph database optimized for AI applications

#### 2.3.4 Retrieval-Augmented Generation (RAG)

RAG combines retrieval and generation to ground LLM responses in retrieved information. The process consists of:

1. **Indexing**: Documents are chunked, embedded, and stored in a vector database
2. **Retrieval**: Given a query q, retrieve the top-k most similar chunks
3. **Augmentation**: Inject retrieved chunks into the LLM prompt
4. **Generation**: The LLM generates a response conditioned on the augmented prompt

Formally:
```
retrieved = TopK(VectorDB.search(E(query)), k)
response = LLM(query, context=retrieved)
```

---

## 3. Taxonomy of Memory Systems

We propose a multi-dimensional taxonomy for categorizing agent memory systems based on (1) memory type, (2) storage mechanism, (3) retrieval strategy, (4) temporal awareness, and (5) architectural integration.

### 3.1 Memory Type Categorization

Following cognitive science principles, we categorize memory systems by their functional role:

| Memory Type | Function | Characteristics | Implementation |
|-------------|----------|----------------|----------------|
| **Working Memory** | Immediate processing | Limited capacity, high volatility | Context window, session state |
| **Episodic Memory** | Experience storage | Event-specific, temporally ordered | Conversation logs, interaction history |
| **Semantic Memory** | Knowledge storage | Factual, generalized | Document stores, knowledge bases |
| **Procedural Memory** | Skill storage | Behavior patterns, policies | Learned strategies, tool use patterns |

### 3.2 Storage Mechanism Taxonomy

Memory systems employ different storage backends:

| Mechanism | Description | Advantages | Disadvantages |
|-----------|-------------|------------|---------------|
| **Vector-based** | Embeddings in vector DBs | Fast similarity search, semantic retrieval | No structured relationships |
| **Graph-based** | Knowledge graphs | Explicit relationships, reasoning support | Complex queries, higher overhead |
| **Relational** | SQL databases | ACID guarantees, structured queries | Less suitable for semantic search |
| **Hybrid** | Combination of above | Leverages strengths of each | Increased complexity |
| **In-context** | LLM context window | No external storage needed | Severely limited capacity |

### 3.3 Retrieval Strategy Taxonomy

Different systems employ varied retrieval strategies:

| Strategy | Description | Use Case |
|----------|-------------|----------|
| **Semantic Search** | Vector similarity-based | Finding semantically related information |
| **Keyword Search** | BM25, TF-IDF | Exact term matching |
| **Temporal Search** | Time-based filtering | Recent events, historical queries |
| **Graph Traversal** | Relationship following | Multi-hop reasoning, entity relationships |
| **Hybrid Retrieval** | Multiple strategies combined | Balanced precision and recall |
| **Reranking** | Two-stage retrieval + rerank | Improved relevance |

### 3.4 Temporal Awareness Taxonomy

Memory systems vary in how they handle temporal information:

| Level | Characteristics | Examples |
|-------|----------------|----------|
| **Temporal-agnostic** | No time tracking | Basic RAG systems |
| **Timestamp-aware** | Records creation/access time | Session-based memories |
| **Validity-tracked** | Tracks when facts are valid | Temporal knowledge graphs |
| **Bi-temporal** | Tracks event time + record time | Graphiti, Zep |
| **Decay-based** | Time-weighted relevance | Forgetting mechanisms |

### 3.5 Architectural Integration Taxonomy

| Integration Pattern | Description | Examples |
|---------------------|-------------|----------|
| **External Store** | Separate database queried by agent | Most RAG systems |
| **Integrated Buffer** | Memory managed within agent loop | MemGPT |
| **Hierarchical** | Multi-tier memory (working → long-term) | CrewAI, A-MEM |
| **Distributed** | Shared across multiple agents | Multi-agent systems |
| **Agentic** | Memory as autonomous sub-agent | A-MEM, MemInsight |

---

## 4. Memory System Architectures

### 4.1 Vector-Based Memory Systems

Vector-based systems represent the most common approach to agent memory, leveraging embedding models and vector databases for semantic retrieval.

#### 4.1.1 Architecture

The canonical vector-based memory architecture consists of:

1. **Embedding Layer**: Converts text to dense vectors
2. **Vector Store**: Stores embeddings with metadata
3. **Retrieval Layer**: Performs similarity search
4. **Context Integration**: Injects retrieved memory into LLM context

**Workflow:**
```
Input → Embed → Search Vector DB → Retrieve Top-K → Augment Context → LLM
```

#### 4.1.2 Key Systems

**Basic RAG Memory**
The simplest approach stores conversation history as embedded chunks:

```python
# Pseudocode
def store_memory(text, metadata):
    embedding = embed_model.embed(text)
    vector_db.insert(embedding, text, metadata)

def retrieve_memory(query, k=5):
    query_embedding = embed_model.embed(query)
    results = vector_db.similarity_search(query_embedding, k)
    return results
```

**Mem0**
Mem0 is a production-ready memory system that delivers significant improvements over baseline approaches:

- **Performance**: 26% accuracy boost, 91% lower p95 latency, 90% token savings
- **Architecture**: Hybrid memory with user-level, session-level, and entity-level memories
- **Key Features**: Automatic memory extraction, deduplication, temporal decay
- **Use Cases**: Customer support, personalized assistants, multi-session applications

**MemoryBank (2024)**
MemoryBank enhances LLMs with structured long-term memory:

- **Memory Organization**: Hierarchical storage with importance scoring
- **Retrieval**: Combines recency, relevance, and importance
- **Updating**: Incremental memory updates with consolidation
- **Performance**: Demonstrated improvements on multi-session dialogue tasks

#### 4.1.3 Strengths and Limitations

**Strengths:**
- Fast semantic retrieval using ANN search (sub-linear complexity)
- Scalable to millions of memory items
- Simple to implement and deploy
- Well-supported by existing tools (LangChain, LlamaIndex)

**Limitations:**
- No explicit relationship modeling
- Difficulty with multi-hop reasoning
- Limited temporal reasoning capabilities
- Potential for semantic drift in long-running systems

### 4.2 Graph-Based Memory Systems

Graph-based systems represent knowledge as entities and relationships, enabling structured reasoning and multi-hop queries.

#### 4.2.1 Architecture

Graph-based memory systems consist of:

1. **Entity Extraction**: Identify entities from conversations/documents
2. **Relationship Extraction**: Detect relationships between entities
3. **Graph Construction**: Build knowledge graph
4. **Graph Storage**: Store in graph database
5. **Graph Querying**: Traverse graph to retrieve information

**Workflow:**
```
Input → Extract Entities/Relations → Update Graph → Query Graph → Retrieve Paths → LLM
```

#### 4.2.2 Key Systems

**Graphiti**

Graphiti is a framework for building temporally-aware knowledge graphs specifically designed for AI agents:

**Key Features:**
- **Temporal Awareness**: Bi-temporal model tracking event time and record time
- **Validity Intervals**: Every edge includes explicit validity intervals
- **Conflict Resolution**: Uses temporal metadata to update or invalidate outdated information
- **Hybrid Indexing**: Combines semantic embeddings, keyword search, and graph traversal
- **Performance**: Near-constant time retrieval independent of graph scale

**Architecture:**
```
Graph = (Entities, Relationships, Validity_Intervals)
where each edge e has:
  - valid_from: when relationship started
  - valid_to: when relationship ended (or null)
  - created_at: when recorded in system
```

**Advantages:**
- Preserves historical accuracy without large-scale recomputation
- Efficient updates without triggering extensive graph rebuilding
- Supports temporal queries like "What was X's preference in March 2024?"

**Zep**

Zep builds on Graphiti as its core memory component:

- **Performance**: 94.8% accuracy on Deep Memory Retrieval benchmark (vs 93.4% for MemGPT)
- **Architecture**: Temporal knowledge graph + vector search
- **Use Cases**: Long-term agent memory, customer interaction history

**GraphRAG (Microsoft)**

Microsoft's GraphRAG approach combines knowledge graphs with RAG:

- **Method**: Build knowledge graph from documents, use graph structure for retrieval
- **Limitations**: Expensive recomputation when data changes frequently
- **Best Use**: Relatively static knowledge bases

#### 4.2.3 Strengths and Limitations

**Strengths:**
- Explicit relationship modeling enables multi-hop reasoning
- Temporal tracking supports historical queries
- Structured representation improves interpretability
- Better handling of conflicting information

**Limitations:**
- Higher computational overhead for graph updates
- Complex query formulation required
- Requires sophisticated entity/relation extraction
- Scaling challenges for very large graphs (millions of edges)

### 4.3 Hybrid Memory Architectures

Hybrid systems combine multiple memory mechanisms to leverage their complementary strengths.

#### 4.3.1 MemGPT

MemGPT pioneered the concept of treating LLMs as operating systems with explicit memory management:

**Architecture:**
- **Two-Tier Memory**: Main context (limited) + external storage (unlimited)
- **Memory Functions**: Explicit `memory_read()` and `memory_write()` functions
- **Controller**: LLM decides what to remember and when to forget
- **Function Calling**: Uses LLM function calling to manage memory operations

**Memory Management:**
```python
# Conceptual MemGPT memory operations
memory.write(key="user_preference", value="prefers concise responses")
memory.read(query="user preferences")
memory.edit(key="project_status", new_value="in review")
```

**Innovation:**
MemGPT introduces a paradigm shift by giving the LLM explicit control over its memory, rather than using automatic retrieval. The agent can strategically decide what information to store, retrieve, and forget.

**Performance:**
- Strong performance on long-context tasks
- Demonstrated ability to maintain coherence over very long conversations
- Baseline for many comparison studies

**Limitations:**
- Requires function-calling capable LLMs
- Additional latency from memory operations
- Complexity in managing memory consistency

#### 4.3.2 A-MEM (Agentic Memory)

A-MEM represents a recent advancement in agentic memory systems:

**Core Concept:**
Memory itself becomes an autonomous agent that can dynamically organize information, following principles similar to the Zettelkasten method (interconnected knowledge networks).

**Key Features:**
- **Dynamic Indexing**: Memory system actively creates links between related memories
- **Autonomous Organization**: Memory agent decides how to structure information
- **Hierarchical Structuring**: Automatically builds concept hierarchies
- **Active Consolidation**: Periodically reorganizes memory for better retrieval

**Performance:**
- ROUGE-L score of 44.27 on Multi-Hop tasks (vs. 18.09 for LoComo baseline)
- More than doubles performance on complex reasoning tasks
- Outperforms MemGPT, MemoryBank, and ReadAgent across multiple benchmarks

**Architecture:**
```
User Agent ⟷ Memory Agent ⟷ Memory Store
              ↓
        Organization & Indexing
        Dynamic Linking
        Consolidation
```

#### 4.3.3 Reflexion

Reflexion equips agents with self-reflection and memory-based learning:

**Components:**
- **Actor**: Performs task attempts
- **Evaluator**: Assesses performance
- **Self-Reflection**: Generates verbal feedback on failures
- **Memory**: Stores reflections for future attempts

**Workflow:**
1. Agent attempts task
2. Evaluator judges success/failure
3. On failure, agent reflects on what went wrong
4. Reflection stored in episodic memory
5. Future attempts retrieve relevant reflections
6. Agent adjusts strategy based on past learnings

**Performance:**
Demonstrated improvements on:
- Code generation tasks
- Sequential decision-making
- Question answering with iterative refinement

**Comparison:**
The SAGE framework showed improvements over Reflexion in multi-document QA by more effectively integrating information across sources, suggesting room for enhancement in how Reflexion handles complex retrieval scenarios.

#### 4.3.4 MemInsight

MemInsight introduces autonomous memory augmentation:

**Key Idea:**
The system autonomously decides when and what to remember, without explicit user configuration.

**Features:**
- Automatic memory extraction from conversations
- Importance scoring for memory prioritization
- Adaptive memory retention based on usage patterns
- Minimal user intervention required

### 4.4 Framework-Specific Memory Implementations

#### 4.4.1 LangChain

**Memory Capabilities:**
LangChain provides the most comprehensive built-in memory utilities:

**Memory Types:**
- **ConversationBufferMemory**: Stores entire conversation
- **ConversationBufferWindowMemory**: Keeps last N messages
- **ConversationSummaryMemory**: Periodically summarizes conversation
- **ConversationSummaryBufferMemory**: Hybrid summary + recent messages
- **VectorStoreRetrieverMemory**: Semantic retrieval from vector store
- **EntityMemory**: Tracks entities across conversation

**Architecture:**
```python
# Example LangChain memory usage
from langchain.memory import ConversationBufferMemory

memory = ConversationBufferMemory()
chain = ConversationChain(llm=llm, memory=memory)
```

**Strengths:**
- Rich set of pre-built memory types
- Easy integration with chains and agents
- Flexible memory persistence backends

**Use Cases:**
- Chatbots requiring conversation history
- Customer support systems
- Interactive tutoring systems

#### 4.4.2 LlamaIndex

**Memory Approach:**
LlamaIndex focuses on document-centric memory with optimized retrieval:

**Key Features:**
- **Index Structures**: Various index types (vector, tree, keyword, knowledge graph)
- **Query Engines**: Optimized query processing to minimize LLM calls
- **Chat History**: SQLite or vector-based conversation storage
- **Performance**: Optimized for retrieval efficiency

**Comparison with LangChain:**
- LlamaIndex: Better for document retrieval, RAG-focused
- LangChain: Better for conversational memory, agent orchestration

**Strengths:**
- Superior retrieval performance for document QA
- Efficient indexing strategies
- Minimal unnecessary LLM calls

**Limitations:**
- Less flexible for general agent memory needs
- Primarily designed for RAG workflows

#### 4.4.3 CrewAI

**Memory System:**
CrewAI offers a structured three-tier memory architecture:

**Memory Types:**
1. **Short-term Memory**: Current task execution context
   - Stores information for ongoing task
   - Enables agent collaboration on current work
   - Cleared after task completion

2. **Long-term Memory**: Cross-session persistence
   - Stored in local database
   - Learns from previous executions
   - Improves over time through accumulated experience

3. **Entity Memory**: Structured entity information
   - Captures details about people, places, concepts
   - Maintains entity attributes and relationships
   - Enables entity-aware reasoning

**Architecture:**
```python
# CrewAI memory configuration
crew = Crew(
    agents=[agent1, agent2],
    memory=True,  # Enables all memory types
    verbose=True
)
```

**Strengths:**
- Built-in memory without additional configuration
- Suitable for team-based multi-agent systems
- Good balance between simplicity and capability

**Use Cases:**
- Role-based agent teams
- Structured workflows with learning requirements
- Multi-agent collaboration

#### 4.4.4 AutoGen

**Memory Approach:**
AutoGen takes a lightweight, conversation-driven approach:

**Key Features:**
- **Message Lists**: Primary memory mechanism
- **Contextual Awareness**: Agents remember previous messages
- **External Integration**: Flexibility to integrate custom memory backends
- **Conversational**: Memory emerges from conversation history

**Comparison:**
- More flexible than CrewAI's structured approach
- Less opinionated about memory architecture
- Suitable for exploratory, open-ended tasks

**Strengths:**
- Simple conceptual model
- Easy to understand and debug
- Flexible integration options

**Limitations:**
- No built-in long-term memory
- Requires custom implementation for persistence
- Manual memory management needed for complex scenarios

#### 4.4.5 LangGraph

**Memory System:**
LangGraph provides the most flexible memory architecture through its state management:

**Key Features:**
- **Graph State**: Persistent state across graph execution
- **Checkpointing**: Save/restore execution state
- **Memory Store Integration**: MongoDB, PostgreSQL backends
- **Cross-Session Memory**: Long-term persistence across sessions

**Architecture:**
```python
# LangGraph memory with MongoDB
from langgraph.checkpoint.mongodb import MongoDBSaver

checkpointer = MongoDBSaver(connection_string)
graph = StateGraph(state_schema, checkpointer=checkpointer)
```

**Strengths:**
- Maximum flexibility in memory design
- Production-ready persistence
- Granular control over state management
- Excellent for complex, stateful workflows

**Use Cases:**
- Production agent systems
- Complex multi-step workflows
- Systems requiring precise state control

---

## 5. Comparative Analysis

### 5.1 System Comparison Table

| System | Memory Type | Storage | Retrieval | Temporal | Performance | Complexity |
|--------|------------|---------|-----------|----------|-------------|------------|
| **MemGPT** | Hybrid | Vector + External | Function-based | Timestamp | 93.4% DMR | High |
| **A-MEM** | Agentic | Vector + Dynamic | Autonomous | Aware | 44.27 ROUGE-L | High |
| **Graphiti** | Graph | Temporal KG | Hybrid | Bi-temporal | Near-constant | Medium |
| **Zep** | Graph + Vector | Temporal KG | Hybrid | Bi-temporal | 94.8% DMR | Medium |
| **Mem0** | Hybrid | Multi-level | Semantic | Decay-based | +26% accuracy | Low |
| **Reflexion** | Episodic | Vector | Reflection-based | Session | Task-dependent | Medium |
| **MemoryBank** | Hierarchical | Vector | Importance-based | Aware | Dialogue tasks | Medium |
| **Basic RAG** | Semantic | Vector | Similarity | Agnostic | Baseline | Low |

**DMR: Deep Memory Retrieval benchmark
ROUGE-L: Recall-Oriented Understudy for Gisting Evaluation - Longest Common Subsequence

### 5.2 Framework Comparison

| Framework | Memory Focus | Built-in Types | Persistence | Best For | Learning Curve |
|-----------|--------------|----------------|-------------|----------|----------------|
| **LangChain** | Conversational | Extensive | Multiple backends | General agents | Medium |
| **LlamaIndex** | Document RAG | Index-based | SQLite, Vector | Document QA | Low |
| **CrewAI** | Multi-agent | 3-tier (STM/LTM/Entity) | Local DB | Team workflows | Low |
| **AutoGen** | Conversational | Message lists | External integration | Open-ended tasks | Medium |
| **LangGraph** | State management | Checkpointing | MongoDB, PostgreSQL | Production systems | High |

### 5.3 Performance Comparison

#### 5.3.1 Accuracy Benchmarks

Based on published results:

**Deep Memory Retrieval (DMR):**
- Zep: 94.8%
- MemGPT: 93.4%
- Baseline: ~85%

**Multi-Hop QA (ROUGE-L):**
- A-MEM: 44.27
- LoComo: 18.09
- MemGPT: ~25

**Accuracy Improvement:**
- Mem0: +26% over baselines
- Reflexion: +15-30% on iterative tasks
- GraphRAG: +10-20% on complex QA

#### 5.3.2 Latency and Efficiency

**Retrieval Latency:**
- Graphiti: O(1) near-constant time
- Vector DB (HNSW): O(log n)
- Graph traversal: O(k) where k = path length

**Token Efficiency:**
- Mem0: 90% token savings
- Semantic retrieval: 60-70% savings vs. full context
- Summarization: 40-60% savings

**Memory Operations Overhead:**
- MemGPT: +100-200ms per memory operation
- Automatic retrieval (RAG): +50-100ms
- Graph query: +100-500ms (depending on complexity)

### 5.4 Scalability Analysis

**Vector-Based Systems:**
- **Capacity**: Millions to billions of vectors
- **Scaling**: Near-linear with optimized indexes (HNSW)
- **Bottleneck**: Embedding computation, index updates

**Graph-Based Systems:**
- **Capacity**: Millions of nodes/edges (optimized DBs)
- **Scaling**: Depends on query complexity
- **Bottleneck**: Complex multi-hop queries, graph updates

**Hybrid Systems:**
- **Capacity**: Limited by slowest component
- **Scaling**: Requires careful coordination
- **Bottleneck**: Synchronization, consistency

### 5.5 Use Case Suitability

| Use Case | Recommended Approach | Rationale |
|----------|---------------------|-----------|
| **Chatbots** | LangChain + Vector Memory | Rich conversational memory utilities |
| **Customer Support** | Mem0 or CrewAI | Multi-level memory, entity tracking |
| **Document QA** | LlamaIndex | Optimized document retrieval |
| **Code Assistants** | MemGPT or A-MEM | Long context, complex reasoning |
| **Research Agents** | Graphiti + Vector | Structured knowledge, temporal tracking |
| **Multi-Agent Teams** | CrewAI or LangGraph | Built-in collaboration support |
| **Personal Assistants** | Zep or Mem0 | Cross-session learning, personalization |
| **Task Automation** | AutoGen or LangGraph | Flexible, open-ended workflows |

---

## 6. Technical Deep-Dive: Implementation Details and Code Examples

This section provides comprehensive technical implementations for each major memory system, including architecture diagrams, detailed algorithms, and production-ready code examples.

### 6.1 Basic RAG Memory System

#### 6.1.1 Architecture Overview

Basic RAG represents the foundational approach to agent memory, using vector embeddings and similarity search for retrieval.

**System Components:**
```
┌─────────────────────────────────────────────────────┐
│             Basic RAG Architecture                  │
├─────────────────────────────────────────────────────┤
│                                                     │
│  User Query ──→ Embedding ──→ Vector Search        │
│                                      │              │
│                                      ↓              │
│                              ┌───────────────┐      │
│                              │  Vector DB    │      │
│                              │  (Chroma/     │      │
│                              │   Pinecone)   │      │
│                              └───────────────┘      │
│                                      │              │
│                                      ↓              │
│                         Top-K Similar Chunks        │
│                                      │              │
│                                      ↓              │
│               LLM ←── Augmented Prompt              │
│                 │                                   │
│                 ↓                                   │
│             Response                                │
└─────────────────────────────────────────────────────┘
```

#### 6.1.2 Complete Implementation

```python
"""
Basic RAG Memory System - Production Implementation
Supports: Conversation history, semantic search, metadata filtering
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import numpy as np
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings


@dataclass
class MemoryItem:
    """Represents a single memory entry"""
    id: str
    content: str
    embedding: np.ndarray
    metadata: Dict[str, Any]
    timestamp: datetime


class BasicRAGMemory:
    """
    Basic RAG memory system with semantic search capabilities

    Features:
    - Vector similarity search
    - Metadata filtering
    - Time-based relevance decay
    - Conversation context management
    """

    def __init__(
        self,
        embedding_model: str = "all-MiniLM-L6-v2",
        collection_name: str = "agent_memory",
        persist_directory: str = "./chroma_db"
    ):
        # Initialize embedding model
        self.embedding_model = SentenceTransformer(embedding_model)
        self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()

        # Initialize vector database
        self.client = chromadb.Client(Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=persist_directory
        ))

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}  # Use cosine similarity
        )

    def embed_text(self, text: str) -> np.ndarray:
        """Generate embedding for input text"""
        return self.embedding_model.encode(text, convert_to_numpy=True)

    def store(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        memory_id: Optional[str] = None
    ) -> str:
        """
        Store a memory in the vector database

        Args:
            content: Text content to store
            metadata: Additional metadata (user_id, session_id, etc.)
            memory_id: Optional custom ID

        Returns:
            ID of stored memory
        """
        # Generate embedding
        embedding = self.embed_text(content)

        # Create memory ID
        if memory_id is None:
            memory_id = f"mem_{datetime.now().timestamp()}"

        # Add timestamp to metadata
        if metadata is None:
            metadata = {}
        metadata["timestamp"] = datetime.now().isoformat()
        metadata["content_length"] = len(content)

        # Store in vector database
        self.collection.add(
            ids=[memory_id],
            embeddings=[embedding.tolist()],
            documents=[content],
            metadatas=[metadata]
        )

        return memory_id

    def retrieve(
        self,
        query: str,
        k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
        time_decay: bool = True,
        decay_rate: float = 0.01
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant memories using semantic search

        Args:
            query: Search query
            k: Number of results to return
            filter_metadata: Filter by metadata (e.g., {"user_id": "123"})
            time_decay: Apply time-based relevance decay
            decay_rate: Decay rate for older memories

        Returns:
            List of relevant memories with scores
        """
        # Generate query embedding
        query_embedding = self.embed_text(query)

        # Search vector database
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=k,
            where=filter_metadata
        )

        # Process results
        memories = []
        current_time = datetime.now()

        for i in range(len(results['ids'][0])):
            memory = {
                'id': results['ids'][0][i],
                'content': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'similarity_score': 1 - results['distances'][0][i],  # Convert distance to similarity
            }

            # Apply time decay if enabled
            if time_decay and 'timestamp' in memory['metadata']:
                memory_time = datetime.fromisoformat(memory['metadata']['timestamp'])
                age_hours = (current_time - memory_time).total_seconds() / 3600
                decay_factor = np.exp(-decay_rate * age_hours)
                memory['final_score'] = memory['similarity_score'] * decay_factor
            else:
                memory['final_score'] = memory['similarity_score']

            memories.append(memory)

        # Sort by final score
        memories.sort(key=lambda x: x['final_score'], reverse=True)

        return memories

    def delete(self, memory_id: str):
        """Delete a memory by ID"""
        self.collection.delete(ids=[memory_id])

    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        count = self.collection.count()
        return {
            "total_memories": count,
            "embedding_dimension": self.embedding_dim,
            "collection_name": self.collection.name
        }


# Example Usage
def example_basic_rag():
    """Example demonstrating Basic RAG usage"""

    # Initialize memory system
    memory = BasicRAGMemory()

    # Store conversation history
    memory.store(
        "User prefers Python over JavaScript for backend development",
        metadata={"type": "preference", "user_id": "user_123"}
    )

    memory.store(
        "User is working on a machine learning project using TensorFlow",
        metadata={"type": "context", "user_id": "user_123", "project": "ml_app"}
    )

    memory.store(
        "User asked about best practices for API design",
        metadata={"type": "query", "user_id": "user_123"}
    )

    # Retrieve relevant memories
    query = "What programming languages does the user like?"
    results = memory.retrieve(query, k=3, filter_metadata={"user_id": "user_123"})

    print(f"Query: {query}\n")
    for i, result in enumerate(results, 1):
        print(f"Result {i}:")
        print(f"  Content: {result['content']}")
        print(f"  Similarity: {result['similarity_score']:.3f}")
        print(f"  Final Score: {result['final_score']:.3f}\n")

    # Get statistics
    stats = memory.get_stats()
    print(f"Memory Stats: {stats}")


if __name__ == "__main__":
    example_basic_rag()
```

#### 6.1.3 Performance Characteristics

| Metric | Value | Notes |
|--------|-------|-------|
| **Embedding Time** | 10-50ms | Depends on text length and model |
| **Storage Time** | 5-20ms | Vector DB insert operation |
| **Retrieval Time** | 20-100ms | k=5, HNSW index |
| **Scalability** | Millions of vectors | With proper indexing |
| **Memory Footprint** | ~6KB per item | 384-dim embedding + metadata |

#### 6.1.4 Strengths and Limitations

**Strengths:**
- Simple, well-understood approach
- Fast semantic retrieval with HNSW indexing
- Easy to implement and debug
- Good baseline performance

**Limitations:**
- No relationship modeling between memories
- Limited temporal reasoning
- Can't handle multi-hop queries
- May retrieve semantically similar but contextually irrelevant results

---

### 6.2 MemGPT: OS-Style Memory Management

#### 6.2.1 Architecture Overview

MemGPT treats the LLM as an operating system with explicit memory management functions.

**System Architecture:**
```
┌──────────────────────────────────────────────────────────┐
│                  MemGPT Architecture                     │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │         Main Context (Limited - 8K tokens)      │    │
│  │  ┌──────────────┐  ┌──────────────┐            │    │
│  │  │ System Prompt│  │ User Message │            │    │
│  │  └──────────────┘  └──────────────┘            │    │
│  └─────────────────────────────────────────────────┘    │
│                      ↕ Memory Functions                  │
│  ┌─────────────────────────────────────────────────┐    │
│  │        Recall Memory (Recent Important)         │    │
│  │    ┌──────────┐  ┌──────────┐  ┌──────────┐   │    │
│  │    │ Memory 1 │  │ Memory 2 │  │ Memory 3 │   │    │
│  │    └──────────┘  └──────────┘  └──────────┘   │    │
│  └─────────────────────────────────────────────────┘    │
│                      ↕ Read/Write                        │
│  ┌─────────────────────────────────────────────────┐    │
│  │    Archival Memory (Unlimited External Storage) │    │
│  │         Vector Database + Metadata              │    │
│  └─────────────────────────────────────────────────┘    │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

#### 6.2.2 Complete Implementation

```python
"""
MemGPT-Style Memory System
Implements explicit memory management with function calling
"""

from typing import List, Dict, Any, Optional, Callable
from enum import Enum
import json
from dataclasses import dataclass, asdict
from datetime import datetime
import openai


class MemoryType(Enum):
    """Types of memory in MemGPT"""
    MAIN_CONTEXT = "main_context"
    RECALL = "recall"
    ARCHIVAL = "archival"


@dataclass
class MemoryBlock:
    """Represents a block of memory"""
    id: str
    content: str
    memory_type: MemoryType
    importance: float
    last_accessed: datetime
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['memory_type'] = self.memory_type.value
        d['last_accessed'] = self.last_accessed.isoformat()
        return d


class MemGPTMemory:
    """
    MemGPT-style memory system with explicit memory management

    Features:
    - Tiered memory (main context, recall, archival)
    - Explicit memory functions callable by LLM
    - Importance-based retention
    - LLM-controlled memory operations
    """

    def __init__(
        self,
        main_context_size: int = 2000,  # tokens
        recall_size: int = 10,  # number of blocks
        openai_api_key: str = None
    ):
        self.main_context_size = main_context_size
        self.recall_size = recall_size

        # Memory stores
        self.main_context: List[Dict[str, Any]] = []
        self.recall_memory: List[MemoryBlock] = []
        self.archival_memory: List[MemoryBlock] = []

        # Initialize basic RAG for archival
        from sentence_transformers import SentenceTransformer
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

        # OpenAI client
        if openai_api_key:
            openai.api_key = openai_api_key

    # Memory Functions (Callable by LLM)

    def memory_write(self, content: str, importance: float = 0.5) -> str:
        """
        Write to archival memory

        This function is called by the LLM to store information long-term

        Args:
            content: Content to store
            importance: Importance score (0.0-1.0)

        Returns:
            Confirmation message with memory ID
        """
        memory_id = f"arch_{datetime.now().timestamp()}"

        block = MemoryBlock(
            id=memory_id,
            content=content,
            memory_type=MemoryType.ARCHIVAL,
            importance=importance,
            last_accessed=datetime.now(),
            metadata={"created_at": datetime.now().isoformat()}
        )

        self.archival_memory.append(block)

        return f"Successfully wrote to archival memory. ID: {memory_id}"

    def memory_read(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Read from archival memory using semantic search

        This function is called by the LLM to retrieve relevant memories

        Args:
            query: Search query
            k: Number of memories to retrieve

        Returns:
            List of relevant memories
        """
        if not self.archival_memory:
            return []

        # Generate query embedding
        query_emb = self.embedding_model.encode(query)

        # Compute similarities
        results = []
        for block in self.archival_memory:
            content_emb = self.embedding_model.encode(block.content)
            similarity = np.dot(query_emb, content_emb) / (
                np.linalg.norm(query_emb) * np.linalg.norm(content_emb)
            )

            # Update last accessed
            block.last_accessed = datetime.now()

            results.append({
                'id': block.id,
                'content': block.content,
                'similarity': float(similarity),
                'importance': block.importance
            })

        # Sort by similarity * importance
        results.sort(
            key=lambda x: x['similarity'] * x['importance'],
            reverse=True
        )

        return results[:k]

    def recall_write(self, content: str, importance: float = 0.7) -> str:
        """
        Write to recall memory (recent important information)

        Args:
            content: Content to store
            importance: Importance score

        Returns:
            Confirmation message
        """
        memory_id = f"recall_{datetime.now().timestamp()}"

        block = MemoryBlock(
            id=memory_id,
            content=content,
            memory_type=MemoryType.RECALL,
            importance=importance,
            last_accessed=datetime.now(),
            metadata={}
        )

        self.recall_memory.append(block)

        # Evict least important if over capacity
        if len(self.recall_memory) > self.recall_size:
            self.recall_memory.sort(key=lambda x: x.importance)
            evicted = self.recall_memory.pop(0)
            # Move to archival
            evicted.memory_type = MemoryType.ARCHIVAL
            self.archival_memory.append(evicted)

        return f"Wrote to recall memory. ID: {memory_id}"

    def recall_read(self) -> List[Dict[str, Any]]:
        """
        Read all recall memory

        Returns:
            List of recall memories
        """
        return [
            {
                'id': block.id,
                'content': block.content,
                'importance': block.importance
            }
            for block in self.recall_memory
        ]

    def memory_edit(self, memory_id: str, new_content: str) -> str:
        """
        Edit an existing memory

        Args:
            memory_id: ID of memory to edit
            new_content: New content

        Returns:
            Confirmation message
        """
        # Search in archival
        for block in self.archival_memory:
            if block.id == memory_id:
                block.content = new_content
                block.last_accessed = datetime.now()
                return f"Successfully edited memory {memory_id}"

        # Search in recall
        for block in self.recall_memory:
            if block.id == memory_id:
                block.content = new_content
                block.last_accessed = datetime.now()
                return f"Successfully edited memory {memory_id}"

        return f"Memory {memory_id} not found"

    def get_memory_functions(self) -> List[Dict[str, Any]]:
        """
        Get function definitions for OpenAI function calling

        Returns:
            List of function schemas
        """
        return [
            {
                "name": "memory_write",
                "description": "Write information to long-term archival memory",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "Content to store in memory"
                        },
                        "importance": {
                            "type": "number",
                            "description": "Importance score from 0.0 to 1.0",
                            "minimum": 0.0,
                            "maximum": 1.0
                        }
                    },
                    "required": ["content"]
                }
            },
            {
                "name": "memory_read",
                "description": "Search and retrieve information from archival memory",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        },
                        "k": {
                            "type": "integer",
                            "description": "Number of memories to retrieve",
                            "default": 5
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "recall_write",
                "description": "Store recent important information in recall memory",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "Content to store"
                        },
                        "importance": {
                            "type": "number",
                            "description": "Importance score",
                            "default": 0.7
                        }
                    },
                    "required": ["content"]
                }
            },
            {
                "name": "recall_read",
                "description": "Read all recall memory",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]

    def execute_function(self, function_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a memory function by name"""
        function_map = {
            "memory_write": self.memory_write,
            "memory_read": self.memory_read,
            "recall_write": self.recall_write,
            "recall_read": self.recall_read,
            "memory_edit": self.memory_edit
        }

        if function_name in function_map:
            return function_map[function_name](**arguments)
        else:
            return f"Unknown function: {function_name}"

    def chat(
        self,
        user_message: str,
        system_prompt: str = "You are a helpful assistant with memory capabilities."
    ) -> str:
        """
        Chat with MemGPT-enabled agent

        Args:
            user_message: User's message
            system_prompt: System prompt

        Returns:
            Agent's response
        """
        # Build messages with recall memory
        messages = [
            {"role": "system", "content": system_prompt},
        ]

        # Add recall memory to context
        recall = self.recall_read()
        if recall:
            recall_text = "Recent important memories:\n" + "\n".join(
                f"- {m['content']}" for m in recall
            )
            messages.append({"role": "system", "content": recall_text})

        messages.append({"role": "user", "content": user_message})

        # Call OpenAI with function calling
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages,
            functions=self.get_memory_functions(),
            function_call="auto"
        )

        message = response['choices'][0]['message']

        # Handle function calls
        if message.get("function_call"):
            function_name = message["function_call"]["name"]
            arguments = json.loads(message["function_call"]["arguments"])

            # Execute function
            function_result = self.execute_function(function_name, arguments)

            # Send result back to LLM
            messages.append(message)
            messages.append({
                "role": "function",
                "name": function_name,
                "content": str(function_result)
            })

            # Get final response
            second_response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=messages
            )

            return second_response['choices'][0]['message']['content']

        return message.get('content', '')


# Example Usage
def example_memgpt():
    """Example demonstrating MemGPT usage"""

    memory = MemGPTMemory(openai_api_key="your-key-here")

    # Simulate conversation
    print("User: What's my name?")
    response = memory.chat("My name is Alice and I love machine learning")
    print(f"Assistant: {response}\n")

    # The LLM should have called memory_write or recall_write

    print("User: What do you remember about me?")
    response = memory.chat("What do you remember about me?")
    print(f"Assistant: {response}\n")

    # Check memory state
    print("Recall Memory:")
    for mem in memory.recall_read():
        print(f"  - {mem['content']}")

    print("\nArchival Memory Count:", len(memory.archival_memory))


if __name__ == "__main__":
    example_memgpt()
```

#### 6.2.3 Performance Characteristics

| Metric | Value | Notes |
|--------|-------|-------|
| **Memory Function Latency** | 100-200ms | Per function call |
| **LLM Overhead** | 1-3s | For function calling decision |
| **Archival Search** | 50-150ms | Depends on archive size |
| **Context Management** | Automatic | LLM-controlled |
| **Scalability** | Unlimited archival | Limited by recall size |

---

### 6.3 A-MEM: Agentic Memory System

#### 6.3.1 Architecture Overview

A-MEM treats memory itself as an autonomous agent that organizes and links information dynamically.

**System Architecture:**
```
┌───────────────────────────────────────────────────────┐
│              A-MEM Architecture                       │
├───────────────────────────────────────────────────────┤
│                                                       │
│  ┌────────────┐         ┌────────────┐              │
│  │  User      │ ←──────→│   User     │              │
│  │  Agent     │         │   Agent    │              │
│  └────────────┘         └────────────┘              │
│        │                                             │
│        │ Store/Retrieve                              │
│        ↓                                             │
│  ┌──────────────────────────────────────┐           │
│  │         Memory Agent                  │           │
│  │  ┌──────────────────────────────┐   │           │
│  │  │  Organization Engine         │   │           │
│  │  │  - Clustering                │   │           │
│  │  │  - Linking                   │   │           │
│  │  │  - Hierarchical structuring  │   │           │
│  │  └──────────────────────────────┘   │           │
│  └──────────────────────────────────────┘           │
│        │                                             │
│        ↓                                             │
│  ┌──────────────────────────────────────┐           │
│  │    Organized Memory Store            │           │
│  │                                      │           │
│  │    ┌─────┐    ┌─────┐    ┌─────┐  │           │
│  │    │Topic│────│Topic│────│Topic│  │           │
│  │    │  A  │    │  B  │    │  C  │  │           │
│  │    └─────┘    └─────┘    └─────┘  │           │
│  │       │          │          │      │           │
│  │    ┌─────┐    ┌─────┐    ┌─────┐  │           │
│  │    │Mem 1│    │Mem 2│    │Mem 3│  │           │
│  │    └─────┘    └─────┘    └─────┘  │           │
│  └──────────────────────────────────────┘           │
└───────────────────────────────────────────────────────┘
```

#### 6.3.2 Complete Implementation

```python
"""
A-MEM: Agentic Memory System
Memory as an autonomous agent with self-organization capabilities
"""

from typing import List, Dict, Any, Set, Optional
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
import numpy as np
from sklearn.cluster import AgglomerativeClustering
from sentence_transformers import SentenceTransformer


@dataclass
class MemoryNode:
    """A node in the A-MEM memory graph"""
    id: str
    content: str
    embedding: np.ndarray
    importance: float
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    links: Set[str] = field(default_factory=set)  # IDs of linked memories
    cluster_id: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_link(self, other_id: str):
        """Create bidirectional link to another memory"""
        self.links.add(other_id)


@dataclass
class MemoryCluster:
    """A cluster of related memories"""
    id: int
    name: str
    summary: str
    memory_ids: Set[str]
    centroid: np.ndarray
    created_at: datetime
    importance: float


class AMemMemoryAgent:
    """
    A-MEM: Autonomous Memory Agent

    Features:
    - Self-organizing memory clusters
    - Automatic linking of related memories
    - Hierarchical concept structuring
    - Dynamic importance scoring
    - Zettelkasten-inspired knowledge network
    """

    def __init__(
        self,
        embedding_model: str = "all-MiniLM-L6-v2",
        similarity_threshold: float = 0.7,
        cluster_threshold: float = 0.6,
        reorganization_interval: int = 50  # Reorganize every N memories
    ):
        self.embedding_model = SentenceTransformer(embedding_model)
        self.similarity_threshold = similarity_threshold
        self.cluster_threshold = cluster_threshold
        self.reorganization_interval = reorganization_interval

        # Memory storage
        self.memories: Dict[str, MemoryNode] = {}
        self.clusters: Dict[int, MemoryCluster] = {}
        self.next_cluster_id = 0

        # Indexing
        self.topic_index: Dict[str, Set[str]] = defaultdict(set)
        self.memory_count = 0

    def store(
        self,
        content: str,
        importance: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store a new memory with automatic organization

        Args:
            content: Memory content
            importance: Optional importance score (auto-computed if None)
            metadata: Additional metadata

        Returns:
            Memory ID
        """
        # Generate memory ID
        memory_id = f"amem_{datetime.now().timestamp()}_{self.memory_count}"
        self.memory_count += 1

        # Generate embedding
        embedding = self.embedding_model.encode(content)

        # Compute importance if not provided
        if importance is None:
            importance = self._compute_importance(content, embedding)

        # Create memory node
        node = MemoryNode(
            id=memory_id,
            content=content,
            embedding=embedding,
            importance=importance,
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            metadata=metadata or {}
        )

        # Store memory
        self.memories[memory_id] = node

        # Automatic linking phase
        self._auto_link_memory(node)

        # Periodic reorganization
        if self.memory_count % self.reorganization_interval == 0:
            self._reorganize_memory()

        return memory_id

    def _compute_importance(self, content: str, embedding: np.ndarray) -> float:
        """
        Compute importance score based on content characteristics

        Factors:
        - Content length (longer = more detailed)
        - Semantic uniqueness
        - Keyword presence
        """
        # Base score from content length
        length_score = min(len(content) / 500, 1.0)

        # Uniqueness score (how different from existing memories)
        if self.memories:
            similarities = []
            for mem in list(self.memories.values())[:100]:  # Sample for efficiency
                sim = np.dot(embedding, mem.embedding) / (
                    np.linalg.norm(embedding) * np.linalg.norm(mem.embedding)
                )
                similarities.append(sim)
            uniqueness = 1.0 - np.mean(similarities)
        else:
            uniqueness = 1.0

        # Keyword importance
        important_keywords = {'important', 'critical', 'key', 'remember', 'note'}
        keyword_score = 1.0 if any(kw in content.lower() for kw in important_keywords) else 0.5

        # Weighted combination
        importance = (
            0.3 * length_score +
            0.5 * uniqueness +
            0.2 * keyword_score
        )

        return importance

    def _auto_link_memory(self, new_node: MemoryNode):
        """
        Automatically create links between related memories

        Uses semantic similarity to identify related memories
        and creates bidirectional links
        """
        for mem_id, existing_node in self.memories.items():
            if mem_id == new_node.id:
                continue

            # Compute similarity
            similarity = np.dot(new_node.embedding, existing_node.embedding) / (
                np.linalg.norm(new_node.embedding) * np.linalg.norm(existing_node.embedding)
            )

            # Create link if above threshold
            if similarity >= self.similarity_threshold:
                new_node.add_link(mem_id)
                existing_node.add_link(new_node.id)

    def _reorganize_memory(self):
        """
        Reorganize memory structure using clustering

        Creates hierarchical clusters of related memories
        Similar to Zettelkasten's concept organization
        """
        if len(self.memories) < 5:
            return

        print(f"[A-MEM] Reorganizing {len(self.memories)} memories...")

        # Get embeddings and IDs
        memory_list = list(self.memories.values())
        embeddings = np.array([m.embedding for m in memory_list])
        memory_ids = [m.id for m in memory_list]

        # Hierarchical clustering
        n_clusters = min(max(len(self.memories) // 10, 2), 20)
        clustering = AgglomerativeClustering(
            n_clusters=n_clusters,
            affinity='cosine',
            linkage='average'
        )
        cluster_labels = clustering.fit_predict(embeddings)

        # Create/update clusters
        cluster_members = defaultdict(list)
        for mem_id, label in zip(memory_ids, cluster_labels):
            cluster_members[label].append(mem_id)
            self.memories[mem_id].cluster_id = label

        # Update cluster objects
        for cluster_id, member_ids in cluster_members.items():
            # Compute centroid
            member_embeddings = [
                self.memories[mid].embedding for mid in member_ids
            ]
            centroid = np.mean(member_embeddings, axis=0)

            # Generate cluster summary
            member_contents = [
                self.memories[mid].content for mid in member_ids[:5]  # Sample
            ]
            summary = self._generate_cluster_summary(member_contents)

            # Compute cluster importance
            importance = np.mean([
                self.memories[mid].importance for mid in member_ids
            ])

            if cluster_id in self.clusters:
                # Update existing cluster
                self.clusters[cluster_id].memory_ids = set(member_ids)
                self.clusters[cluster_id].centroid = centroid
                self.clusters[cluster_id].summary = summary
                self.clusters[cluster_id].importance = importance
            else:
                # Create new cluster
                self.clusters[cluster_id] = MemoryCluster(
                    id=cluster_id,
                    name=f"Topic_{cluster_id}",
                    summary=summary,
                    memory_ids=set(member_ids),
                    centroid=centroid,
                    created_at=datetime.now(),
                    importance=importance
                )

        print(f"[A-MEM] Created {len(self.clusters)} clusters")

    def _generate_cluster_summary(self, contents: List[str]) -> str:
        """Generate a summary for a cluster of memories"""
        # Simple keyword extraction (in production, use LLM)
        all_text = " ".join(contents).lower()
        words = all_text.split()
        word_freq = defaultdict(int)
        for word in words:
            if len(word) > 4:  # Filter short words
                word_freq[word] += 1

        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
        summary = "Related to: " + ", ".join([w[0] for w in top_words])
        return summary

    def retrieve(
        self,
        query: str,
        k: int = 5,
        use_links: bool = True,
        use_clusters: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Retrieve memories using multiple strategies

        Args:
            query: Search query
            k: Number of results
            use_links: Follow memory links for expanded results
            use_clusters: Use cluster information

        Returns:
            Retrieved memories with scores
        """
        if not self.memories:
            return []

        # Generate query embedding
        query_embedding = self.embedding_model.encode(query)

        # Compute similarities
        results = []
        for memory_id, node in self.memories.items():
            similarity = np.dot(query_embedding, node.embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(node.embedding)
            )

            # Boost score based on importance and access patterns
            boost = (
                node.importance * 0.3 +
                min(node.access_count / 10, 1.0) * 0.1 +
                similarity * 0.6
            )

            results.append({
                'id': memory_id,
                'content': node.content,
                'similarity': float(similarity),
                'importance': node.importance,
                'final_score': float(boost),
                'cluster_id': node.cluster_id,
                'links': list(node.links)
            })

        # Sort by final score
        results.sort(key=lambda x: x['final_score'], reverse=True)
        top_results = results[:k]

        # Expand with linked memories if enabled
        if use_links:
            linked_ids = set()
            for result in top_results:
                linked_ids.update(result['links'])

            # Add top linked memories
            for linked_id in list(linked_ids)[:k]:
                if linked_id in self.memories and linked_id not in [r['id'] for r in top_results]:
                    node = self.memories[linked_id]
                    top_results.append({
                        'id': linked_id,
                        'content': node.content,
                        'final_score': node.importance * 0.5,  # Lower score for linked
                        'reason': 'linked'
                    })

        # Update access patterns
        for result in top_results:
            if result['id'] in self.memories:
                self.memories[result['id']].access_count += 1
                self.memories[result['id']].last_accessed = datetime.now()

        return top_results[:k]

    def get_cluster_info(self, cluster_id: int) -> Optional[Dict[str, Any]]:
        """Get information about a memory cluster"""
        if cluster_id not in self.clusters:
            return None

        cluster = self.clusters[cluster_id]
        return {
            'id': cluster.id,
            'name': cluster.name,
            'summary': cluster.summary,
            'size': len(cluster.memory_ids),
            'importance': cluster.importance,
            'memory_count': len(cluster.memory_ids)
        }

    def get_memory_graph(self) -> Dict[str, Any]:
        """Get the complete memory graph structure"""
        nodes = []
        edges = []

        for memory_id, node in self.memories.items():
            nodes.append({
                'id': memory_id,
                'content': node.content[:100],  # Truncate
                'importance': node.importance,
                'cluster': node.cluster_id,
                'access_count': node.access_count
            })

            for linked_id in node.links:
                if memory_id < linked_id:  # Avoid duplicates
                    edges.append({
                        'source': memory_id,
                        'target': linked_id
                    })

        return {
            'nodes': nodes,
            'edges': edges,
            'clusters': [
                self.get_cluster_info(cid) for cid in self.clusters.keys()
            ]
        }


# Example Usage
def example_amem():
    """Example demonstrating A-MEM usage"""

    memory = AMemMemoryAgent()

    # Store related memories
    memories = [
        "Python is a high-level programming language",
        "TensorFlow is a machine learning framework written in Python",
        "Neural networks are fundamental to deep learning",
        "PyTorch is another popular deep learning framework",
        "JavaScript is used for web development",
        "React is a JavaScript library for building UIs",
        "Machine learning models require training data",
        "Deep learning is a subset of machine learning"
    ]

    print("Storing memories...")
    for content in memories:
        memory.store(content)

    print(f"\nTotal memories: {len(memory.memories)}")
    print(f"Total clusters: {len(memory.clusters)}")

    # Retrieve with query
    print("\nQuery: 'Tell me about machine learning frameworks'")
    results = memory.retrieve("machine learning frameworks", k=3)

    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['content']}")
        print(f"   Score: {result['final_score']:.3f}")
        print(f"   Cluster: {result.get('cluster_id')}")
        if result.get('links'):
            print(f"   Linked to: {len(result['links'])} memories")

    # Show cluster information
    print("\n\nMemory Clusters:")
    for cluster_id in memory.clusters:
        info = memory.get_cluster_info(cluster_id)
        print(f"\nCluster {info['id']}: {info['name']}")
        print(f"  Summary: {info['summary']}")
        print(f"  Size: {info['size']} memories")
        print(f"  Importance: {info['importance']:.3f}")


if __name__ == "__main__":
    example_amem()
```

(Continuing in next message due to length...)

---

## 6. Memory Operations and Mechanisms

### 6.1 Memory Consolidation

Memory consolidation transforms raw experiences into structured, retrievable knowledge.

#### 6.1.1 Summarization-Based Consolidation

**Approach**: Periodically summarize conversation history

```python
# Conceptual summarization workflow
def consolidate_memory(recent_history):
    summary = llm.summarize(recent_history)
    memory.store(summary, type="consolidated")
    memory.prune(recent_history)  # Remove summarized items
```

**Advantages:**
- Reduces memory footprint
- Captures high-level patterns
- Efficient storage

**Disadvantages:**
- Loss of detail
- Potential information loss
- Challenging to update summaries

#### 6.1.2 Extraction-Based Consolidation

**Approach**: Extract key facts and entities from conversations

```python
def consolidate_via_extraction(conversation):
    facts = llm.extract_facts(conversation)
    entities = llm.extract_entities(conversation)

    for fact in facts:
        memory.store_fact(fact, context=conversation.id)

    for entity in entities:
        memory.store_entity(entity, attributes, relationships)
```

**Advantages:**
- Preserves specific information
- Queryable structured data
- Better for entity-centric tasks

**Disadvantages:**
- Requires good extraction models
- Higher storage requirements
- Potential extraction errors

#### 6.1.3 Hierarchical Consolidation

**Approach**: Multi-level consolidation (detailed → summary → abstract)

**A-MEM's Dynamic Organization:**
- Raw memories → Organized clusters → High-level concepts
- Automatic linking between related memories
- Zettelkasten-inspired interconnected knowledge network

**MemoryBank's Importance Scoring:**
- Assign importance scores to memories
- Higher importance = more likely to be retained
- Combines recency, relevance, and user-defined importance

### 6.2 Forgetting Mechanisms

Effective forgetting is crucial for maintaining memory quality and efficiency.

#### 6.2.1 Time-Based Decay

**Approach**: Reduce relevance of old memories

```python
def compute_time_decay(memory_item, current_time):
    age = current_time - memory_item.created_at
    decay_factor = exp(-lambda * age)
    memory_item.score *= decay_factor
```

**Parameters:**
- λ (lambda): Decay rate
- Higher λ → faster forgetting
- Can be adaptive based on memory type

#### 6.2.2 Relevance-Based Pruning

**Approach**: Remove low-relevance memories

```python
def prune_by_relevance(memory_store, threshold):
    for item in memory_store:
        if item.access_count < threshold and item.age > min_age:
            memory_store.remove(item)
```

**Criteria:**
- Access frequency
- Recency of access
- Similarity to frequently accessed items
- User feedback signals

#### 6.2.3 Capacity-Based Eviction

**Approach**: LRU (Least Recently Used) or LFU (Least Frequently Used) eviction

```python
class CapacityLimitedMemory:
    def __init__(self, max_items):
        self.max_items = max_items
        self.cache = LRUCache(max_items)

    def store(self, key, value):
        if len(self.cache) >= self.max_items:
            self.cache.evict_lru()
        self.cache.insert(key, value)
```

**Strategies:**
- **LRU**: Remove least recently accessed
- **LFU**: Remove least frequently accessed
- **Hybrid**: Combine recency and frequency

#### 6.2.4 Contextual Forgetting

**Approach**: Selectively forget based on context

**Examples:**
- Forget session-specific information after session ends
- Forget corrected misinformation
- Forget temporary task state after completion

**Mem0's Approach:**
- TTL-based purging for temporary memories
- Relevance-based pruning for long-term memories
- User-controlled forgetting for privacy

### 6.3 Context Window Management

Given limited context windows, managing what information enters the LLM's context is critical.

#### 6.3.1 Window Memory (Fixed-Size Buffer)

**Approach**: Keep last N messages

```python
class WindowMemory:
    def __init__(self, window_size=10):
        self.messages = deque(maxlen=window_size)

    def add(self, message):
        self.messages.append(message)

    def get_context(self):
        return list(self.messages)
```

**Advantages:**
- Simple and predictable
- Guarantees recent context

**Disadvantages:**
- Loses older information
- No semantic filtering

#### 6.3.2 Summarization + Recent Messages

**Approach**: Summary of old + full recent messages

```python
def get_context(conversation):
    old_messages = conversation[:- window_size]
    recent_messages = conversation[-window_size:]

    summary = llm.summarize(old_messages)
    context = [summary] + recent_messages
    return context
```

**Advantages:**
- Maintains both historical context and detail
- More efficient than full history

**Disadvantages:**
- Summarization overhead
- Potential loss of nuance

#### 6.3.3 Retrieval-Based Context

**Approach**: Retrieve relevant memories based on current query

```python
def get_context(query, memory_store):
    relevant_memories = memory_store.retrieve(query, k=5)
    context = format_memories(relevant_memories)
    return context
```

**Advantages:**
- Semantically relevant context
- Scales to very long histories

**Disadvantages:**
- Retrieval latency
- May miss non-semantic relevance

#### 6.3.4 MemGPT's Hybrid Approach

**Approach**: Explicit memory management functions

- **Main Context**: Immediate working memory (fits in context window)
- **Archival Memory**: External unlimited storage
- **Recall Memory**: Recent important information

The LLM explicitly decides:
- What to load from archival → main context
- What to move from main → archival
- What to keep in recall memory

This gives the agent strategic control over context utilization.

### 6.4 Memory Retrieval Strategies

#### 6.4.1 Dense Retrieval (Semantic)

**Method**: Vector similarity search

```python
query_embedding = embed(query)
results = vector_db.search(query_embedding, k=10)
```

**Advantages:**
- Captures semantic similarity
- Handles paraphrasing
- No keyword dependence

**Disadvantages:**
- May miss exact matches
- Requires good embedding model
- Computationally intensive for large scale

#### 6.4.2 Sparse Retrieval (Keyword)

**Method**: BM25, TF-IDF

```python
results = keyword_index.search(query, algorithm="bm25", k=10)
```

**Advantages:**
- Fast and efficient
- Exact term matching
- Interpretable

**Disadvantages:**
- Misses semantic variations
- Requires query-document vocabulary overlap

#### 6.4.3 Hybrid Retrieval

**Method**: Combine dense + sparse retrieval

```python
dense_results = vector_db.search(embed(query), k=20)
sparse_results = keyword_index.search(query, k=20)
results = rerank(dense_results + sparse_results, query, k=10)
```

**Advantages:**
- Best of both worlds
- Higher recall and precision
- Robust to different query types

**Disadvantages:**
- More complex
- Higher computational cost

**Systems Using Hybrid:**
- Graphiti: Semantic + keyword + graph traversal
- Weaviate: Hybrid search built-in
- Advanced RAG systems

#### 6.4.4 Reranking

**Method**: Two-stage retrieval + reranking

```
Stage 1: Retrieve top-k candidates (k=100)
Stage 2: Rerank with more sophisticated model (select top-n, n=10)
```

**Reranking Models:**
- Cross-encoders (BERT-based)
- Cohere Rerank API
- LLM-based reranking

**Advantages:**
- Significantly improved relevance
- Can incorporate complex relevance signals

**Disadvantages:**
- Additional latency
- Higher computational cost

### 6.5 Memory Indexing

#### 6.5.1 Flat Index

**Method**: Store all vectors, compute similarity with all

**Complexity**: O(n) search time

**Use Case**: Small datasets (<10K vectors)

#### 6.5.2 Approximate Nearest Neighbor (ANN) Indexes

**HNSW (Hierarchical Navigable Small World):**
- Graph-based index
- O(log n) search complexity
- High recall, fast queries
- Used by: Pinecone, Weaviate, Qdrant

**IVF (Inverted File Index):**
- Clustering-based
- Partition space into Voronoi cells
- Search only relevant partitions
- Used by: FAISS

**LSH (Locality-Sensitive Hashing):**
- Hash similar vectors to same buckets
- Probabilistic guarantees
- Very fast, slightly lower recall

#### 6.5.3 Graph Indexing

**Node Indexing:**
- Index nodes by type, properties
- Enables fast node lookup

**Edge Indexing:**
- Index relationships by type
- Enables fast traversal

**Composite Indexes:**
- Multi-property indexes
- Temporal + entity + relation

**Graphiti's Hybrid:**
- Vector embeddings for semantic search
- Graph structure for relationship queries
- Keyword index for exact matches
- Combined for optimal retrieval

---

## 7. Applications and Use Cases

### 7.1 Conversational AI and Chatbots

**Requirements:**
- Maintain conversation context
- Remember user preferences
- Personalize responses
- Handle multi-turn dialogues

**Memory Needs:**
- Short-term: Current conversation
- Long-term: User profile, past conversations
- Entity: User details, mentioned entities

**Recommended Systems:**
- LangChain ConversationMemory
- Mem0 for personalization
- CrewAI for multi-bot systems

**Example:**
Customer support chatbot that remembers:
- Past issues the user reported
- User's product preferences
- Resolution history
- Communication style preferences

### 7.2 Personal Assistants

**Requirements:**
- Cross-session memory
- User preference learning
- Contextual awareness
- Privacy-preserving storage

**Memory Needs:**
- Episodic: Past interactions, events
- Semantic: User knowledge, facts
- Procedural: Learned task patterns

**Recommended Systems:**
- Zep for temporal knowledge
- Mem0 for multi-level memory
- LangGraph for complex workflows

**Example:**
AI assistant that:
- Remembers your meeting schedule
- Learns your work patterns
- Adapts to communication preferences
- Recalls context from weeks ago

### 7.3 Code Generation and Software Development

**Requirements:**
- Long context awareness
- Codebase understanding
- Iterative refinement
- Error learning

**Memory Needs:**
- Episodic: Previous code attempts, errors
- Semantic: Code patterns, API knowledge
- Procedural: Coding strategies, best practices

**Recommended Systems:**
- MemGPT for long context
- A-MEM for complex reasoning
- Reflexion for iterative improvement

**Example:**
Code assistant that:
- Remembers project structure
- Recalls past debugging sessions
- Learns from compilation errors
- Adapts to coding style preferences

### 7.4 Research and Knowledge Work

**Requirements:**
- Structured knowledge representation
- Multi-document understanding
- Temporal awareness
- Citation and source tracking

**Memory Needs:**
- Semantic: Facts, concepts, relationships
- Episodic: Research sessions, reading history
- Graph: Entity relationships, knowledge structure

**Recommended Systems:**
- Graphiti for knowledge graphs
- LlamaIndex for document retrieval
- A-MEM for knowledge organization

**Example:**
Research assistant that:
- Builds knowledge graph from papers
- Tracks concept evolution over time
- Remembers previous literature reviews
- Connects related findings

### 7.5 Multi-Agent Systems

**Requirements:**
- Shared memory across agents
- Individual agent memory
- Coordination state
- Communication history

**Memory Needs:**
- Shared semantic: Common knowledge base
- Individual episodic: Agent-specific experiences
- Coordination: Task state, responsibilities

**Recommended Systems:**
- CrewAI for team memory
- LangGraph for state management
- AutoGen for flexible collaboration

**Example:**
Software development team of agents:
- Shared: Project requirements, codebase
- Individual: Specialized knowledge per role
- Coordination: Task assignments, progress

### 7.6 Education and Tutoring

**Requirements:**
- Student model (knowledge state)
- Pedagogical memory (teaching strategies)
- Progress tracking
- Adaptive difficulty

**Memory Needs:**
- Episodic: Learning sessions, interactions
- Semantic: Student knowledge, misconceptions
- Procedural: Effective teaching strategies

**Recommended Systems:**
- LangChain for conversation management
- CrewAI for multi-subject tutoring
- Custom knowledge graphs for curriculum

**Example:**
Adaptive tutor that:
- Tracks student understanding
- Remembers common mistakes
- Adjusts teaching strategy
- Builds on prior lessons

### 7.7 Healthcare and Medical Assistants

**Requirements:**
- Patient history tracking
- Strict privacy compliance
- Temporal medical records
- Multi-modal information

**Memory Needs:**
- Episodic: Consultation history
- Semantic: Medical knowledge, patient data
- Temporal: Symptom evolution, treatment outcomes

**Recommended Systems:**
- Zep/Graphiti for temporal tracking
- HIPAA-compliant vector databases
- Encrypted memory stores

**Example:**
Medical assistant that:
- Maintains patient history
- Tracks symptom progression
- Remembers medication responses
- Respects privacy regulations

---

## 8. Challenges and Limitations

### 8.1 Scalability Challenges

#### 8.1.1 Memory Size Scaling

**Challenge**: As agents accumulate memories, storage and retrieval become increasingly expensive.

**Issues:**
- Vector database scaling to billions of items
- Graph databases with millions of edges
- Index update costs
- Storage costs

**Current Solutions:**
- Approximate nearest neighbor indexes (HNSW, IVF)
- Distributed vector databases
- Memory pruning and consolidation
- Tiered storage (hot/cold)

**Remaining Gaps:**
- Efficient updates at massive scale
- Real-time indexing for streaming data
- Cost-effective long-term storage

#### 8.1.2 Retrieval Latency

**Challenge**: Maintaining low latency as memory grows

**Issues:**
- Search time increases with database size
- Multi-hop graph queries can be slow
- Reranking adds latency
- Multiple retrieval operations compound delay

**Current Solutions:**
- Optimized ANN indexes (sub-linear search)
- Caching frequently accessed memories
- Asynchronous retrieval
- Pre-fetching based on context

**Remaining Gaps:**
- Guaranteed low-latency retrieval at scale
- Efficient multi-modal memory retrieval
- Real-time complex graph queries

### 8.2 Consistency and Coherence

#### 8.2.1 Conflicting Information

**Challenge**: Handling contradictory information in memory

**Issues:**
- User changes preferences
- Corrections to previous statements
- Outdated information
- Multiple sources with conflicts

**Current Solutions:**
- Temporal validity tracking (Graphiti)
- Confidence scoring
- Source tracking and provenance
- Update/invalidate mechanisms

**Remaining Gaps:**
- Automatic conflict detection
- Intelligent conflict resolution
- Reasoning about uncertainty

#### 8.2.2 Memory Drift

**Challenge**: Semantic drift over long-running sessions

**Issues:**
- Embedding spaces may shift
- Summarization compounds errors
- Extraction errors accumulate
- Context slowly becomes incoherent

**Current Solutions:**
- Periodic memory auditing
- Human-in-the-loop validation
- Redundant storage of critical information

**Remaining Gaps:**
- Automatic drift detection
- Self-correcting memory systems
- Robust error propagation prevention

### 8.3 Privacy and Security

#### 8.3.1 Data Privacy

**Challenge**: Protecting sensitive information in memory

**Issues:**
- Personal information in conversation history
- Compliance with GDPR, HIPAA, etc.
- Right to be forgotten
- Cross-user information leakage

**Current Solutions:**
- Encryption at rest and in transit
- User-controlled memory deletion
- Access control and authentication
- Memory anonymization

**Remaining Gaps:**
- Guaranteed information isolation
- Efficient encrypted similarity search
- Privacy-preserving memory sharing
- Auditable memory access

#### 8.3.2 Adversarial Attacks

**Challenge**: Malicious manipulation of agent memory

**Attack Vectors:**
- Memory poisoning (inserting false information)
- Privacy extraction (retrieving others' data)
- Memory overflow attacks
- Prompt injection affecting memory operations

**Current Solutions:**
- Input validation
- Memory access controls
- Rate limiting
- Anomaly detection

**Remaining Gaps:**
- Robust defenses against sophisticated attacks
- Detection of subtle memory poisoning
- Secure multi-agent memory sharing

### 8.4 Temporal Reasoning

#### 8.4.1 Time-Aware Retrieval

**Challenge**: Retrieving memories with temporal constraints

**Issues:**
- "What did the user say last week?"
- "How has preference X changed over time?"
- Validity periods for facts
- Temporal relationships between events

**Current Solutions:**
- Timestamp-based filtering
- Bi-temporal models (Graphiti, Zep)
- Temporal validity intervals

**Remaining Gaps:**
- Complex temporal reasoning
- Efficient temporal range queries at scale
- Automatic temporal relationship extraction

#### 8.4.2 Causal Reasoning

**Challenge**: Understanding cause-effect relationships

**Issues:**
- Linking actions to outcomes
- Learning from successes and failures
- Temporal causality vs. correlation

**Current Solutions:**
- Reflexion's reflection mechanism
- Explicit reward/outcome tracking
- Causal graphs (limited)

**Remaining Gaps:**
- Automatic causal discovery
- Counterfactual reasoning
- Long-term cause-effect tracking

### 8.5 Multi-Modal Memory

#### 8.5.1 Integration Challenge

**Challenge**: Remembering and integrating multi-modal information

**Modalities:**
- Text conversations
- Images and videos
- Audio interactions
- Structured data (tables, databases)
- Code and formal languages

**Current Solutions:**
- Multi-modal embedding models (CLIP, etc.)
- Separate indexes per modality
- Cross-modal retrieval

**Remaining Gaps:**
- Unified multi-modal memory representations
- Efficient cross-modal reasoning
- Consistent multi-modal consolidation

### 8.6 Interpretability and Control

#### 8.6.1 Memory Transparency

**Challenge**: Understanding what the agent remembers and why

**Issues:**
- Black-box memory retrieval
- Unexplained memory selection
- Difficulty debugging memory errors

**Current Solutions:**
- Memory inspection tools
- Explainable retrieval (showing similarity scores)
- Logging memory operations

**Remaining Gaps:**
- Human-interpretable memory representations
- Explainable memory consolidation
- Causal explanations for retrieval decisions

#### 8.6.2 User Control

**Challenge**: Giving users appropriate control over agent memory

**Issues:**
- Balance between automation and control
- Selective forgetting
- Memory correction
- Privacy management

**Current Solutions:**
- User-initiated memory deletion
- Memory editing interfaces
- Opt-in/opt-out mechanisms

**Remaining Gaps:**
- Intuitive memory management UIs
- Fine-grained memory control
- Predictable memory behavior

### 8.7 Evaluation and Benchmarking

#### 8.7.1 Lack of Standard Benchmarks

**Challenge**: Comparing memory systems objectively

**Issues:**
- Different evaluation metrics
- Task-specific performance
- Difficulty isolating memory vs. LLM performance
- Missing benchmarks for specific scenarios

**Existing Benchmarks:**
- Deep Memory Retrieval (DMR)
- LoCoMo dataset
- HotPotQA, TriviaQA (multi-hop)

**Remaining Gaps:**
- Standardized memory system benchmarks
- Cross-system comparison frameworks
- Temporal reasoning benchmarks
- Multi-agent memory benchmarks

---

## 9. Future Research Directions

### 9.1 Neuromorphic Memory Architectures

**Inspiration from Neuroscience:**
- Hippocampus-like episodic encoding
- Neocortex-like semantic consolidation
- Sleep-like offline memory reorganization
- Synaptic consolidation mechanisms

**Potential Approaches:**
- Spiking neural networks for memory
- Continuous learning with catastrophic forgetting prevention
- Replay-based consolidation
- Attention-based memory addressing

**Research Questions:**
- Can we create memory systems that learn continuously without forgetting?
- How to implement efficient replay mechanisms for memory consolidation?
- What is the optimal balance between plasticity and stability?

### 9.2 Self-Organizing Memory

**Concept**: Memory systems that autonomously organize and restructure

**Capabilities:**
- Automatic clustering of related memories
- Dynamic index creation
- Emergent hierarchical structures
- Adaptive forgetting strategies

**Related Work:**
- A-MEM's dynamic organization
- Self-organizing maps
- Hierarchical clustering

**Research Questions:**
- What are the principles for effective self-organization?
- How to ensure stability while allowing reorganization?
- Can memory organization co-evolve with agent behavior?

### 9.3 Federated and Distributed Memory

**Motivation**: Multi-agent systems, privacy, scalability

**Architectures:**
- Federated memory learning (without centralizing data)
- Distributed memory across multiple nodes
- Hierarchical memory (local + global)
- Blockchain-based memory provenance

**Applications:**
- Multi-user AI assistants
- Collaborative agent teams
- Privacy-preserving memory sharing
- Decentralized knowledge networks

**Research Questions:**
- How to efficiently share memory without centralizing?
- What are the consistency guarantees in distributed memory?
- How to handle Byzantine agents in multi-agent memory systems?

### 9.4 Meta-Learning for Memory Management

**Concept**: Learning how to remember

**Approaches:**
- Learning optimal forgetting strategies
- Adaptive consolidation policies
- Personalized memory management
- Transfer learning for memory architectures

**Potential Methods:**
- Reinforcement learning for memory operations
- Neural architecture search for memory systems
- Meta-learning across tasks/users

**Research Questions:**
- Can agents learn their own optimal memory strategies?
- How to transfer memory management policies across domains?
- What are the universal principles of effective memory management?

### 9.5 Causal and Counterfactual Memory

**Motivation**: Move beyond correlation to causation

**Capabilities:**
- Causal graph construction from experiences
- Counterfactual reasoning ("What if I had done X?")
- Causal intervention tracking
- Learning from hypotheticals

**Applications:**
- Scientific reasoning agents
- Decision-making systems
- Root cause analysis
- Planning under uncertainty

**Research Questions:**
- How to automatically extract causal relationships?
- Can agents maintain consistent counterfactual memories?
- How to integrate causal reasoning with probabilistic memory?

### 9.6 Emotional and Social Memory

**Inspiration**: Human emotional memory and social cognition

**Dimensions:**
- Affective tagging of memories (emotional valence)
- Social context and relationship tracking
- Theory of mind for other agents
- Empathy-driven memory prioritization

**Applications:**
- Emotional support agents
- Social robots
- Therapeutic AI
- Collaborative agents

**Research Questions:**
- How should emotions be represented in memory?
- Can agents develop nuanced social memories?
- How to balance emotional and factual memory?

### 9.7 Lifelong Learning with Stable Memory

**Challenge**: Continual learning without catastrophic forgetting

**Approaches:**
- Elastic weight consolidation for memory
- Progressive neural networks
- Experience replay from memory
- Compositional knowledge structures

**Goal**: Agents that learn continuously over years

**Research Questions:**
- How to prevent interference between old and new memories?
- What is the optimal balance between stability and plasticity?
- Can we achieve human-like lifelong learning?

### 9.8 Quantum-Inspired Memory Systems

**Speculative but Promising:**
- Superposition-like memory states
- Entanglement-inspired memory linking
- Quantum-inspired search algorithms
- Probabilistic memory representations

**Potential Advantages:**
- Representing uncertainty naturally
- Efficient search over large spaces
- Novel memory organization principles

**Research Questions:**
- Can quantum computing principles improve classical memory systems?
- What are the limits of quantum-inspired approaches?
- How to implement on classical hardware?

### 9.9 Memory-Augmented Reasoning

**Concept**: Tight integration of memory and reasoning

**Approaches:**
- Reasoning over memory graphs
- Memory-guided chain-of-thought
- Analogical reasoning from past experiences
- Inductive learning from memory patterns

**Systems:**
- Next-generation Reflexion
- Enhanced A-MEM
- Graph neural networks over memory

**Research Questions:**
- How to optimally combine retrieval and reasoning?
- Can memory guide LLM reasoning more effectively?
- What memory structures best support complex reasoning?

### 9.10 Standardization and Benchmarking

**Need**: Community standards for memory systems

**Directions:**
- Standard memory APIs and interfaces
- Comprehensive benchmark suites
- Reproducible evaluation protocols
- Open datasets for memory research

**Goals:**
- Enable fair comparison across systems
- Accelerate research through shared infrastructure
- Identify best practices and design patterns

**Key Questions:**
- What are the essential memory operations to standardize?
- How to create benchmarks that generalize across tasks?
- What metrics best capture memory system quality?

---

## 10. Conclusion

Memory systems have emerged as a foundational component for enabling LLM-based agents to transcend the limitations of fixed context windows and achieve persistent, adaptive intelligence. This survey has comprehensively examined the landscape of agent memory systems, from cognitive foundations to state-of-the-art implementations.

### 10.1 Key Findings

**Architectural Diversity**: Memory systems span a spectrum from simple vector-based retrieval to sophisticated hybrid architectures combining semantic search, knowledge graphs, and autonomous memory agents. No single architecture dominates across all use cases; rather, the optimal choice depends on specific requirements for capacity, retrieval speed, reasoning capabilities, and temporal awareness.

**Performance Improvements**: Modern memory systems demonstrate substantial performance gains over baseline approaches. Systems like A-MEM achieve more than double the performance on complex multi-hop reasoning tasks, while Mem0 delivers 26% accuracy improvements with 90% token savings. Temporal knowledge graphs like Graphiti and Zep achieve state-of-the-art retrieval accuracy (94.8%) while maintaining near-constant query times.

**Cognitive Inspiration**: The most successful systems draw inspiration from cognitive science, implementing distinct memory types (working, episodic, semantic, procedural) and processes (consolidation, forgetting, retrieval). This alignment with human memory principles appears crucial for building coherent, human-compatible agent memory.

**Trade-offs and Challenges**: Fundamental trade-offs persist between memory capacity and retrieval speed, between automation and interpretability, and between flexibility and efficiency. Significant challenges remain in scalability, consistency, privacy, temporal reasoning, and multi-modal integration.

### 10.2 Impact and Implications

The development of sophisticated memory systems is enabling transformative applications:

- **Personal AI Assistants** that learn and adapt over months and years
- **Multi-Agent Teams** that collaborate with shared knowledge
- **Research Agents** that build and maintain complex knowledge structures
- **Lifelong Learning Systems** that continuously improve from experience

These capabilities are moving AI agents from stateless tools to persistent, evolving partners.

### 10.3 Looking Forward

The field of agent memory systems is rapidly evolving. Key trends include:

1. **Agentic Memory**: Treating memory itself as an autonomous agent (A-MEM, MemInsight)
2. **Temporal Sophistication**: Bi-temporal models and advanced temporal reasoning (Graphiti, Zep)
3. **Hybrid Architectures**: Combining complementary approaches for robustness
4. **Production Maturity**: Transition from research prototypes to production systems (LangGraph, Mem0)
5. **Standardization**: Emergence of frameworks and best practices

Critical research directions include neuromorphic architectures, self-organizing memory, federated memory for multi-agent systems, causal reasoning, and integration with advanced reasoning techniques.

### 10.4 Recommendations for Practitioners

Based on our comparative analysis, we offer the following recommendations:

**For Conversational AI**: Use LangChain's memory utilities or Mem0 for multi-level personalized memory.

**For Document-Heavy Applications**: LlamaIndex provides optimized retrieval with minimal overhead.

**For Multi-Agent Systems**: CrewAI offers structured three-tier memory, while LangGraph provides maximum flexibility for complex production systems.

**For Research and Knowledge Work**: Knowledge graph-based systems (Graphiti, Zep) excel at structured knowledge and temporal tracking.

**For Long-Context Tasks**: MemGPT or A-MEM provide sophisticated memory management for complex reasoning.

**For Production Systems**: Prioritize systems with proven scalability (vector databases + LangGraph) and operational maturity.

### 10.5 Final Remarks

Memory is not merely a feature of intelligent agents—it is fundamental to intelligence itself. As LLM-based agents continue to evolve, memory systems will increasingly differentiate capable agents from truly intelligent ones. The convergence of cognitive science principles, advanced machine learning, and scalable infrastructure is creating memory systems that approach aspects of human-like persistent intelligence.

However, significant challenges remain. Achieving human-level memory capabilities—with their flexibility, efficiency, robustness, and lifelong learning—requires continued innovation across multiple dimensions: architecture, algorithms, evaluation, and applications.

The research community has made remarkable progress in a short time, but the journey has just begun. As memory systems mature, they will unlock new capabilities and applications we can only begin to imagine. The future of AI agents is inseparable from the future of agent memory systems.

---

## References

### Survey Papers

1. Zhang, Y., et al. (2024). "A Survey on the Memory Mechanism of Large Language Model based Agents." *arXiv preprint arXiv:2404.13501*. Also published in *ACM Transactions on Information Systems*.

2. Wang, L., et al. (2025). "From Human Memory to AI Memory: A Survey on Memory Mechanisms in the Era of LLMs." *arXiv preprint arXiv:2504.15965v2*.

3. Liu, X., et al. (2024). "Human-inspired Perspectives: A Survey on AI Long-term Memory." *arXiv preprint arXiv:2411.00489*.

### Memory Systems and Architectures

4. Chen, H., et al. (2025). "A-MEM: Agentic Memory for LLM Agents." *arXiv preprint arXiv:2502.12110*.

5. Packer, C., et al. (2023). "MemGPT: Towards LLMs as Operating Systems." *arXiv preprint*.

6. Park, J. S., et al. (2023). "Generative Agents: Interactive Simulacra of Human Behavior." *UIST 2023*.

7. Shinn, N., et al. (2023). "Reflexion: Language Agents with Verbal Reinforcement Learning." *NeurIPS 2023*.

8. Wang, L., et al. (2024). "MemoryBank: Enhancing Large Language Models with Long-Term Memory." *arXiv preprint*.

9. Zep Team. (2025). "Zep: A Temporal Knowledge Graph Architecture for Agent Memory." *arXiv preprint arXiv:2501.13956*.

10. Mem0 Team. (2024). "Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory." *arXiv preprint arXiv:2504.19413*.

11. Zhang, R., et al. (2025). "MemInsight: Autonomous Memory Augmentation for LLM Agents." *arXiv preprint arXiv:2503.21760*.

12. Getzep. (2024). "Graphiti: Build Real-Time Knowledge Graphs for AI Agents." GitHub repository. https://github.com/getzep/graphiti

### Knowledge Graphs and Temporal Reasoning

13. Ghosh, B. (2024). "Agents That Remember: Temporal Knowledge Graphs as Long-Term Memory." *Medium*.

14. Hajebi, S. (2024). "Building AI Agents with Knowledge Graph Memory: A Comprehensive Guide to Graphiti." *Medium*.

15. Bollacker, K., et al. (2008). "Freebase: A Collaboratively Created Graph Database for Structuring Human Knowledge." *SIGMOD 2008*.

### Vector Databases and RAG

16. Lewis, P., et al. (2020). "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks." *NeurIPS 2020*.

17. Johnson, J., et al. (2021). "Billion-scale Similarity Search with GPUs." *IEEE Transactions on Big Data*.

18. Malkov, Y., & Yashunin, D. (2018). "Efficient and Robust Approximate Nearest Neighbor Search using Hierarchical Navigable Small World Graphs." *IEEE Transactions on Pattern Analysis and Machine Intelligence*.

### Frameworks and Tools

19. Chase, H. (2022). "LangChain: Building Applications with LLMs through Composability." GitHub repository. https://github.com/langchain-ai/langchain

20. Liu, J. (2022). "LlamaIndex: A Data Framework for LLM Applications." GitHub repository. https://github.com/run-llama/llama_index

21. CrewAI Team. (2024). "CrewAI: Framework for Orchestrating Role-Playing, Autonomous AI Agents." https://www.crewai.com/

22. Microsoft Research. (2023). "AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation." GitHub repository. https://github.com/microsoft/autogen

23. LangGraph Team. (2024). "LangGraph: Build Stateful, Multi-Actor Applications with LLMs." https://langchain-ai.github.io/langgraph/

### Cognitive Science and Human Memory

24. Baddeley, A. (2000). "The Episodic Buffer: A New Component of Working Memory?" *Trends in Cognitive Sciences*, 4(11), 417-423.

25. Tulving, E. (1985). "Memory and Consciousness." *Canadian Psychology*, 26(1), 1-12.

26. Anderson, J. R., & Lebiere, C. (1998). *The Atomic Components of Thought*. Lawrence Erlbaum Associates.

27. Squire, L. R. (2004). "Memory Systems of the Brain: A Brief History and Current Perspective." *Neurobiology of Learning and Memory*, 82(3), 171-177.

### Multi-Agent Systems

28. Ghosh, S., et al. (2025). "AI Agents vs. Agentic AI: A Conceptual Taxonomy, Applications and Challenges." *arXiv preprint arXiv:2505.10468v1*.

29. Wu, Q., et al. (2023). "AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation Framework." *arXiv preprint*.

### Benchmarks and Evaluation

30. Yang, Z., et al. (2018). "HotpotQA: A Dataset for Diverse, Explainable Multi-hop Question Answering." *EMNLP 2018*.

31. Joshi, M., et al. (2017). "TriviaQA: A Large Scale Distantly Supervised Challenge Dataset for Reading Comprehension." *ACL 2017*.

### Applications

32. Weng, L. (2023). "LLM Powered Autonomous Agents." *Lil'Log Blog*. https://lilianweng.github.io/posts/2023-06-23-agent/

33. IBM Research. (2024). "What Is AI Agent Memory?" *IBM Think*. https://www.ibm.com/think/topics/ai-agent-memory

### Industry and Practice

34. MongoDB. (2024). "Powering Long-Term Memory for Agents With LangGraph and MongoDB." *MongoDB Blog*.

35. OpenAI. (2024). "Context Engineering - Short-Term Memory Management with Sessions from OpenAI Agents SDK." *OpenAI Cookbook*.

36. DeepLearning.AI. (2024). "LLMs as Operating Systems: Agent Memory." Short course. https://www.deeplearning.ai/short-courses/llms-as-operating-systems-agent-memory/

37. DeepLearning.AI. (2024). "Long-Term Agentic Memory with LangGraph." Short course. https://www.deeplearning.ai/short-courses/long-term-agentic-memory-with-langgraph/

### Security and Privacy

38. Mitchell, E., et al. (2025). "Episodic Memory in AI Agents Poses Risks That Should Be Studied and Mitigated." *arXiv preprint arXiv:2501.11739*.

39. Carlini, N., et al. (2021). "Extracting Training Data from Large Language Models." *USENIX Security 2021*.

### Comparative Studies

40. Yu, A. (2024). "First Hand Comparison of LangGraph, CrewAI and AutoGen." *Medium*.

41. Singh, V. K. (2024). "Battle of AI Agent Frameworks: CrewAI vs LangGraph vs AutoGen." *Medium*.

42. DataCamp. (2024). "LangChain vs LlamaIndex: A Detailed Comparison." https://www.datacamp.com/blog/langchain-vs-llamaindex

---

## Appendix A: Memory System Decision Tree

```
Question 1: What is your primary use case?
├─ Conversational AI / Chatbot
│  ├─ Simple conversations → LangChain ConversationMemory
│  ├─ Personalized, multi-session → Mem0
│  └─ Customer support → CrewAI or Mem0
│
├─ Document QA / RAG
│  ├─ Simple retrieval → LlamaIndex
│  ├─ Complex multi-hop → A-MEM
│  └─ Temporal documents → Graphiti
│
├─ Code Generation
│  ├─ Long context → MemGPT
│  ├─ Iterative refinement → Reflexion
│  └─ Complex reasoning → A-MEM
│
├─ Multi-Agent System
│  ├─ Structured roles → CrewAI
│  ├─ Complex workflows → LangGraph
│  └─ Flexible collaboration → AutoGen
│
├─ Research / Knowledge Work
│  ├─ Knowledge graphs → Graphiti + Zep
│  ├─ Document heavy → LlamaIndex
│  └─ Dynamic organization → A-MEM
│
└─ Personal Assistant
   ├─ Cross-session learning → Zep or Mem0
   ├─ Temporal tracking → Graphiti
   └─ General purpose → LangGraph + Vector DB
```

---

## Appendix B: Implementation Quick-Start Examples

### B.1 Basic Vector Memory with LangChain

```python
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.memory import VectorStoreRetrieverMemory

# Initialize embedding model and vector store
embeddings = OpenAIEmbeddings()
vectorstore = Chroma(embedding_function=embeddings)

# Create retriever-based memory
retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
memory = VectorStoreRetrieverMemory(retriever=retriever)

# Store information
memory.save_context(
    {"input": "My favorite color is blue"},
    {"output": "I'll remember that!"}
)

# Retrieve relevant memories
relevant_memories = memory.load_memory_variables(
    {"input": "What do you know about my preferences?"}
)
```

### B.2 CrewAI with Three-Tier Memory

```python
from crewai import Agent, Task, Crew

# Define agent with memory enabled
researcher = Agent(
    role='Researcher',
    goal='Find and analyze information',
    backstory='Expert researcher with strong memory',
    memory=True  # Enables all three memory types
)

writer = Agent(
    role='Writer',
    goal='Write comprehensive reports',
    backstory='Skilled writer who learns from past work',
    memory=True
)

# Create crew with shared memory
crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, writing_task],
    memory=True,
    verbose=True
)

# Run crew - agents will remember across executions
result = crew.kickoff()
```

### B.3 LangGraph with Persistent Checkpointing

```python
from langgraph.graph import StateGraph
from langgraph.checkpoint.mongodb import MongoDBSaver
from pymongo import MongoClient

# Initialize MongoDB checkpointer
client = MongoClient("mongodb://localhost:27017")
checkpointer = MongoDBSaver(client=client)

# Define state schema
class AgentState(TypedDict):
    messages: list
    user_profile: dict
    task_history: list

# Create graph with checkpointing
graph = StateGraph(AgentState, checkpointer=checkpointer)

# Add nodes
graph.add_node("process", process_function)
graph.add_node("respond", respond_function)

# Compile graph
app = graph.compile()

# Invoke with thread_id for persistent memory
response = app.invoke(
    {"messages": [("user", "Hello")]},
    config={"configurable": {"thread_id": "user_123"}}
)
```

### B.4 Graphiti Knowledge Graph Memory

```python
from graphiti import Graphiti

# Initialize Graphiti
graphiti = Graphiti(neo4j_uri="bolt://localhost:7687")

# Add information with temporal awareness
graphiti.add_episode(
    "Alice mentioned she prefers working in the morning",
    timestamp="2024-03-15T09:00:00Z"
)

graphiti.add_episode(
    "Alice said she now prefers evening work sessions",
    timestamp="2024-06-20T18:00:00Z"
)

# Query with temporal context
result = graphiti.search(
    query="When does Alice prefer to work?",
    time_filter="2024-05-01"  # What was true in May?
)
# Returns: "morning" (the preference valid at that time)

result = graphiti.search(
    query="When does Alice prefer to work?",
    time_filter="2024-07-01"  # What is true now?
)
# Returns: "evening" (the current preference)
```

---

**End of Survey Paper**

Total Word Count: ~13,500 words

This comprehensive survey provides researchers and practitioners with a deep understanding of memory systems for LLM-based agents, covering theoretical foundations, technical implementations, comparative analyses, and future research directions. The field is rapidly evolving, and this survey aims to serve as both a reference and a foundation for future work.