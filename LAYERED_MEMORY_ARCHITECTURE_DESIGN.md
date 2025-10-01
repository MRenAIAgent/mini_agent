# Layered Memory Architecture - Agent Memory Extensions + Learning System

## Executive Summary

This document specifies a **layered memory architecture** where different memory types are implemented as **agent memory layer extensions** that can be used independently or together. The learning system then **inherits and combines** these memory types along with graph memory to create a comprehensive learning experience.

**Core Architecture**:
- **Agent Memory Layer**: Core memory types as independent extensions of CoreMemoryManager
- **Learning System Layer**: Inherits from multiple memory types to create comprehensive learning capability

This design provides maximum flexibility - agents can use individual memory types as needed, while learning systems get the full memory suite.

## 1. Agent Memory Layer Architecture

### 1.1 Memory Type Hierarchy

```
CoreMemoryManager (Base)
├── EpisodicMemoryManager (Extension)
├── SemanticMemoryManager (Extension)
├── UserProfileMemoryManager (Extension)
├── InteractionMemoryManager (Extension)
└── LearningGraphMemory (Extension)

LearningMemorySystem (Inherits from multiple)
├── inherits EpisodicMemoryManager
├── inherits SemanticMemoryManager
├── inherits UserProfileMemoryManager
├── inherits InteractionMemoryManager
└── inherits LearningGraphMemory
```

### 1.2 Independent Memory Extensions

Each memory type is a standalone extension that can be used independently:

```python
# Individual memory managers - can be used standalone
episodic_memory = EpisodicMemoryManager()
semantic_memory = SemanticMemoryManager()
profile_memory = UserProfileMemoryManager()
interaction_memory = InteractionMemoryManager()
graph_memory = LearningGraphMemory()

# Or combined in learning system
learning_system = LearningMemorySystem()  # Inherits all memory types
```

## 2. Agent Memory Extensions

### 2.1 Episodic Memory Manager

```python
class EpisodicMemoryManager(CoreMemoryManager):
    """Agent memory extension for episodic experiences."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.episodes: Dict[str, Episode] = {}
        self.episode_index = EpisodeIndex()

    # === CORE EPISODIC MEMORY INTERFACE ===

    async def store_episode(
        self,
        user_id: str,
        episode: Episode
    ) -> str:
        """Store an episodic experience."""

        episode_id = f"ep_{datetime.now().timestamp()}_{user_id}"
        episode.episode_id = episode_id

        # Store as regular memory entry for base compatibility
        await super().store_memory(
            content=episode.get_narrative_description(),
            importance=episode.emotional_intensity,
            session_id=episode.session_id,
            metadata={
                "type": "episode",
                "episode_data": episode.to_dict(),
                "user_id": user_id,
                "temporal_markers": episode.get_temporal_markers(),
                "emotional_markers": episode.get_emotional_markers()
            }
        )

        # Store in episodic index
        self.episodes[episode_id] = episode
        await self.episode_index.add_episode(episode)

        return episode_id

    async def retrieve_similar_episodes(
        self,
        user_id: str,
        context: EpisodicContext,
        limit: int = 5
    ) -> List[Episode]:
        """Retrieve similar past episodes."""

        # Use episodic-specific similarity matching
        similar_episodes = await self.episode_index.find_similar(
            user_id=user_id,
            context=context,
            similarity_factors=[
                "emotional_state",
                "activity_type",
                "success_pattern",
                "temporal_context"
            ]
        )

        return similar_episodes[:limit]

    async def get_episodes_for_timeframe(
        self,
        user_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[Episode]:
        """Get episodes within specific timeframe."""

        return await self.episode_index.get_by_timeframe(
            user_id, start_time, end_time
        )

    async def analyze_episode_patterns(
        self,
        user_id: str
    ) -> EpisodePatternAnalysis:
        """Analyze patterns in user's episodes."""

        user_episodes = await self.episode_index.get_user_episodes(user_id)
        return EpisodePatternAnalyzer.analyze(user_episodes)

    # === EPISODIC-SPECIFIC QUERIES ===

    async def get_breakthrough_episodes(
        self,
        user_id: str,
        concept: str = None
    ) -> List[Episode]:
        """Get episodes where breakthroughs occurred."""

        return await self.episode_index.query({
            "user_id": user_id,
            "breakthrough_achieved": True,
            "concept": concept
        })

    async def get_struggle_episodes(
        self,
        user_id: str,
        concept: str = None
    ) -> List[Episode]:
        """Get episodes where user struggled."""

        return await self.episode_index.query({
            "user_id": user_id,
            "difficulty_experienced": "> 0.7",
            "success_level": "< 0.4",
            "concept": concept
        })

@dataclass
class Episode:
    """Represents a specific experiential episode."""

    episode_id: str = None
    user_id: str = None
    session_id: str = None
    timestamp: datetime = field(default_factory=datetime.now)

    # Episode content
    activity_type: str = None  # "learning", "practice", "assessment", "exploration"
    concepts_involved: List[str] = field(default_factory=list)
    narrative_description: str = None

    # Episode context
    environmental_context: Dict[str, Any] = field(default_factory=dict)
    social_context: str = None  # "individual", "group", "with_tutor"

    # Episode experience
    emotional_state: EmotionalState = None
    difficulty_experienced: float = 0.5  # 0.0-1.0
    effort_expended: float = 0.5  # 0.0-1.0
    engagement_level: float = 0.5  # 0.0-1.0

    # Episode outcomes
    success_level: float = 0.5  # 0.0-1.0
    learning_achieved: bool = False
    breakthrough_achieved: bool = False
    insights_gained: List[str] = field(default_factory=list)
    mistakes_made: List[str] = field(default_factory=list)

    # Episode reflection
    user_reflection: str = None
    satisfaction_level: float = 0.5  # 0.0-1.0

    def get_narrative_description(self) -> str:
        """Generate narrative description of episode."""
        if self.narrative_description:
            return self.narrative_description

        return f"User {self.activity_type} involving {', '.join(self.concepts_involved)} " \
               f"with {self.success_level:.1f} success level and {self.emotional_state.valence} emotional valence"

    def get_temporal_markers(self) -> List[str]:
        """Extract temporal context markers."""
        return [
            f"time_of_day:{self.timestamp.hour}",
            f"day_of_week:{self.timestamp.weekday()}",
            f"duration:{self.environmental_context.get('duration', 'unknown')}"
        ]

    def get_emotional_markers(self) -> List[str]:
        """Extract emotional context markers."""
        if not self.emotional_state:
            return []

        return [
            f"emotional_valence:{self.emotional_state.valence}",
            f"emotional_arousal:{self.emotional_state.arousal}",
            f"emotional_dominance:{self.emotional_state.dominance}"
        ]
```

### 2.2 Semantic Memory Manager

```python
class SemanticMemoryManager(CoreMemoryManager):
    """Agent memory extension for semantic knowledge."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.knowledge_base = SemanticKnowledgeBase()
        self.concept_network = ConceptNetwork()

    # === CORE SEMANTIC MEMORY INTERFACE ===

    async def store_knowledge(
        self,
        user_id: str,
        knowledge: SemanticKnowledge
    ) -> str:
        """Store semantic knowledge."""

        knowledge_id = f"know_{datetime.now().timestamp()}_{user_id}"
        knowledge.knowledge_id = knowledge_id

        # Store as regular memory entry for base compatibility
        await super().store_memory(
            content=knowledge.get_knowledge_statement(),
            importance=knowledge.confidence_level,
            metadata={
                "type": "knowledge",
                "knowledge_data": knowledge.to_dict(),
                "user_id": user_id,
                "concepts": knowledge.related_concepts,
                "knowledge_type": knowledge.knowledge_type.value
            }
        )

        # Store in semantic knowledge base
        await self.knowledge_base.add_knowledge(knowledge)

        # Update concept network
        await self.concept_network.update_from_knowledge(knowledge)

        return knowledge_id

    async def retrieve_knowledge_about(
        self,
        user_id: str,
        concept: str,
        knowledge_types: List[KnowledgeType] = None
    ) -> List[SemanticKnowledge]:
        """Retrieve knowledge about a specific concept."""

        return await self.knowledge_base.query({
            "user_id": user_id,
            "concept": concept,
            "knowledge_types": knowledge_types
        })

    async def find_applicable_knowledge(
        self,
        user_id: str,
        situation_context: SituationContext
    ) -> List[SemanticKnowledge]:
        """Find knowledge applicable to a situation."""

        # Use semantic reasoning to find applicable knowledge
        applicable_knowledge = await self.knowledge_base.find_applicable(
            user_id=user_id,
            context=situation_context,
            reasoning_depth=2  # How many inference steps to make
        )

        return applicable_knowledge

    async def identify_knowledge_gaps(
        self,
        user_id: str,
        target_concept: str
    ) -> List[KnowledgeGap]:
        """Identify gaps in user's knowledge."""

        user_knowledge = await self.knowledge_base.get_user_knowledge(user_id)
        required_knowledge = await self.concept_network.get_required_knowledge(target_concept)

        gaps = []
        for required in required_knowledge:
            if not any(uk.covers_requirement(required) for uk in user_knowledge):
                gaps.append(KnowledgeGap(
                    missing_knowledge=required,
                    blocking_concept=target_concept,
                    suggested_sources=await self._suggest_knowledge_sources(required)
                ))

        return gaps

    # === SEMANTIC-SPECIFIC OPERATIONS ===

    async def consolidate_knowledge_from_experiences(
        self,
        user_id: str,
        episodes: List[Episode]
    ) -> List[SemanticKnowledge]:
        """Extract semantic knowledge from episodic experiences."""

        knowledge_extractor = KnowledgeExtractor()
        extracted_knowledge = []

        for episode in episodes:
            if episode.learning_achieved or episode.breakthrough_achieved:
                knowledge_items = await knowledge_extractor.extract_from_episode(episode)

                for knowledge in knowledge_items:
                    knowledge.user_id = user_id
                    knowledge.source_episodes = [episode.episode_id]

                    # Store extracted knowledge
                    await self.store_knowledge(user_id, knowledge)
                    extracted_knowledge.append(knowledge)

        return extracted_knowledge

    async def update_knowledge_confidence(
        self,
        user_id: str,
        knowledge_id: str,
        new_evidence: Evidence
    ) -> float:
        """Update knowledge confidence based on new evidence."""

        knowledge = await self.knowledge_base.get_knowledge(knowledge_id)
        if knowledge and knowledge.user_id == user_id:
            old_confidence = knowledge.confidence_level
            knowledge.confidence_level = await self._calculate_updated_confidence(
                knowledge, new_evidence
            )

            await self.knowledge_base.update_knowledge(knowledge)
            return knowledge.confidence_level

        return 0.0

@dataclass
class SemanticKnowledge:
    """Represents semantic knowledge."""

    knowledge_id: str = None
    user_id: str = None

    # Knowledge content
    knowledge_statement: str = None
    knowledge_type: KnowledgeType = None  # FACT, RULE, PROCEDURE, PRINCIPLE
    abstraction_level: float = 0.5  # 0.0 (concrete) to 1.0 (abstract)

    # Knowledge relationships
    related_concepts: List[str] = field(default_factory=list)
    prerequisite_knowledge: List[str] = field(default_factory=list)
    derived_knowledge: List[str] = field(default_factory=list)

    # Knowledge quality
    confidence_level: float = 0.5  # 0.0-1.0
    accuracy_estimate: float = 0.5  # 0.0-1.0
    scope_of_applicability: List[str] = field(default_factory=list)

    # Knowledge provenance
    source_episodes: List[str] = field(default_factory=list)
    source_type: SourceType = None  # INSTRUCTION, DISCOVERY, INFERENCE
    validation_episodes: List[str] = field(default_factory=list)

    # Knowledge evolution
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    access_count: int = 0

    def get_knowledge_statement(self) -> str:
        """Get natural language statement of knowledge."""
        return self.knowledge_statement or f"Knowledge about {', '.join(self.related_concepts)}"

    def covers_requirement(self, requirement: KnowledgeRequirement) -> bool:
        """Check if this knowledge covers a requirement."""
        return (
            requirement.concept in self.related_concepts and
            requirement.knowledge_type == self.knowledge_type and
            self.confidence_level >= requirement.minimum_confidence
        )

class KnowledgeType(Enum):
    FACT = "fact"                    # Declarative facts
    RULE = "rule"                    # If-then rules
    PROCEDURE = "procedure"          # Step-by-step procedures
    PRINCIPLE = "principle"          # Abstract principles
    EXAMPLE = "example"              # Concrete examples
    ANALOGY = "analogy"             # Analogical knowledge
```

### 2.3 User Profile Memory Manager

```python
class UserProfileMemoryManager(CoreMemoryManager):
    """Agent memory extension for user profiles and characteristics."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_profiles: Dict[str, UserProfile] = {}
        self.profile_tracker = ProfileTracker()

    # === CORE PROFILE MEMORY INTERFACE ===

    async def get_user_profile(
        self,
        user_id: str,
        create_if_missing: bool = True
    ) -> UserProfile:
        """Get or create user profile."""

        if user_id in self.user_profiles:
            return self.user_profiles[user_id]

        # Try to load from persistent storage
        profile_entry = await super().search_memory(
            query=f"user_profile user_id:{user_id}",
            filters={"type": "user_profile"}
        )

        if profile_entry:
            profile_data = profile_entry[0].metadata.get("profile_data", {})
            profile = UserProfile.from_dict(profile_data)
        elif create_if_missing:
            profile = UserProfile(user_id=user_id)
        else:
            return None

        self.user_profiles[user_id] = profile
        return profile

    async def update_profile_from_interaction(
        self,
        user_id: str,
        interaction: InteractionRecord
    ) -> ProfileUpdate:
        """Update user profile based on interaction."""

        profile = await self.get_user_profile(user_id)

        # Extract profile insights from interaction
        insights = await self.profile_tracker.extract_insights_from_interaction(interaction)

        # Update profile components
        updates = []

        if insights.learning_style_indicators:
            style_update = await self._update_learning_style(profile, insights.learning_style_indicators)
            updates.append(style_update)

        if insights.cognitive_indicators:
            cognitive_update = await self._update_cognitive_profile(profile, insights.cognitive_indicators)
            updates.append(cognitive_update)

        if insights.motivation_indicators:
            motivation_update = await self._update_motivation_profile(profile, insights.motivation_indicators)
            updates.append(motivation_update)

        # Save updated profile
        await self._save_profile(profile)

        return ProfileUpdate(
            user_id=user_id,
            updates=updates,
            confidence_change=sum(u.confidence_change for u in updates)
        )

    async def update_profile_from_episode(
        self,
        user_id: str,
        episode: Episode
    ) -> ProfileUpdate:
        """Update user profile based on learning episode."""

        profile = await self.get_user_profile(user_id)

        # Extract profile insights from episode
        insights = await self.profile_tracker.extract_insights_from_episode(episode)

        # Update performance patterns
        await self._update_performance_patterns(profile, episode)

        # Update emotional patterns
        await self._update_emotional_patterns(profile, episode)

        # Update learning velocity
        await self._update_learning_velocity(profile, episode)

        # Save updated profile
        await self._save_profile(profile)

        return ProfileUpdate(
            user_id=user_id,
            episode_id=episode.episode_id,
            profile_aspects_updated=["performance", "emotional", "velocity"]
        )

    # === PROFILE-SPECIFIC OPERATIONS ===

    async def predict_user_preference(
        self,
        user_id: str,
        situation: SituationContext
    ) -> UserPreferencePrediction:
        """Predict user preferences for a situation."""

        profile = await self.get_user_profile(user_id)

        return UserPreferencePrediction(
            preferred_content_type=profile.predict_content_preference(situation),
            preferred_difficulty_level=profile.predict_difficulty_preference(situation),
            preferred_interaction_style=profile.predict_interaction_preference(situation),
            confidence=profile.get_prediction_confidence()
        )

    async def get_personalization_parameters(
        self,
        user_id: str
    ) -> PersonalizationParameters:
        """Get parameters for personalizing user experience."""

        profile = await self.get_user_profile(user_id)

        return PersonalizationParameters(
            content_adaptation=profile.get_content_adaptation_settings(),
            pacing_adaptation=profile.get_pacing_adaptation_settings(),
            feedback_adaptation=profile.get_feedback_adaptation_settings(),
            motivation_adaptation=profile.get_motivation_adaptation_settings()
        )

@dataclass
class UserProfile:
    """Comprehensive user profile."""

    user_id: str
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)

    # Learning characteristics
    learning_style: LearningStyleProfile = field(default_factory=LearningStyleProfile)
    cognitive_profile: CognitiveProfile = field(default_factory=CognitiveProfile)
    motivation_profile: MotivationProfile = field(default_factory=MotivationProfile)
    emotional_profile: EmotionalLearningProfile = field(default_factory=EmotionalLearningProfile)

    # Performance patterns
    learning_velocity: Dict[str, float] = field(default_factory=dict)  # concept -> rate
    optimal_difficulty_levels: Dict[str, float] = field(default_factory=dict)  # domain -> difficulty
    attention_patterns: AttentionProfile = field(default_factory=AttentionProfile)
    error_patterns: ErrorProfile = field(default_factory=ErrorProfile)

    # Preferences and goals
    learning_goals: List[LearningGoal] = field(default_factory=list)
    content_preferences: ContentPreferences = field(default_factory=ContentPreferences)
    feedback_preferences: FeedbackPreferences = field(default_factory=FeedbackPreferences)

    # Meta-cognitive aspects
    self_awareness_level: float = 0.5  # How well they know their learning
    reflection_tendency: float = 0.5   # How much they reflect
    strategy_awareness: float = 0.5    # Awareness of learning strategies

    def predict_content_preference(self, situation: SituationContext) -> ContentType:
        """Predict preferred content type for situation."""
        # Implementation based on learning style and past preferences
        pass

    def predict_difficulty_preference(self, situation: SituationContext) -> float:
        """Predict optimal difficulty level for situation."""
        # Implementation based on cognitive profile and performance patterns
        pass

    def get_prediction_confidence(self) -> float:
        """Get confidence in profile-based predictions."""
        # Based on amount of data and consistency of patterns
        pass
```

### 2.4 Interaction Memory Manager

```python
class InteractionMemoryManager(CoreMemoryManager):
    """Agent memory extension for interaction and conversation history."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.conversations: Dict[str, Conversation] = {}
        self.interaction_analyzer = InteractionAnalyzer()

    # === CORE INTERACTION MEMORY INTERFACE ===

    async def store_interaction(
        self,
        interaction: InteractionRecord
    ) -> str:
        """Store an interaction record."""

        interaction_id = f"int_{datetime.now().timestamp()}_{interaction.session_id}"
        interaction.interaction_id = interaction_id

        # Store as regular memory entry for base compatibility
        await super().store_memory(
            content=f"User: {interaction.user_input}\nAgent: {interaction.agent_response}",
            importance=interaction.engagement_level,
            session_id=interaction.session_id,
            metadata={
                "type": "interaction",
                "interaction_data": interaction.to_dict(),
                "user_id": interaction.user_id,
                "concepts_discussed": interaction.concepts_discussed,
                "interaction_type": interaction.interaction_type.value
            }
        )

        # Add to conversation
        await self._add_to_conversation(interaction)

        return interaction_id

    async def get_conversation_context(
        self,
        session_id: str,
        context_window: int = 10
    ) -> ConversationContext:
        """Get recent conversation context."""

        if session_id not in self.conversations:
            await self._load_conversation(session_id)

        conversation = self.conversations.get(session_id)
        if not conversation:
            return ConversationContext(session_id=session_id, interactions=[])

        recent_interactions = conversation.get_recent_interactions(context_window)

        return ConversationContext(
            session_id=session_id,
            interactions=recent_interactions,
            conversation_summary=conversation.get_summary(),
            active_topics=conversation.get_active_topics(),
            user_engagement_trend=conversation.get_engagement_trend()
        )

    async def find_similar_interactions(
        self,
        user_id: str,
        current_interaction: InteractionRecord,
        limit: int = 5
    ) -> List[InteractionRecord]:
        """Find similar past interactions."""

        return await self.interaction_analyzer.find_similar(
            user_id=user_id,
            reference_interaction=current_interaction,
            similarity_factors=[
                "concepts_discussed",
                "interaction_type",
                "user_emotional_state",
                "difficulty_level"
            ],
            limit=limit
        )

    async def analyze_communication_patterns(
        self,
        user_id: str
    ) -> CommunicationPatternAnalysis:
        """Analyze user's communication patterns."""

        user_interactions = await self._get_user_interactions(user_id)
        return await self.interaction_analyzer.analyze_patterns(user_interactions)

    # === INTERACTION-SPECIFIC OPERATIONS ===

    async def track_conversation_flow(
        self,
        session_id: str
    ) -> ConversationFlow:
        """Track the flow and direction of conversation."""

        conversation = self.conversations.get(session_id)
        if not conversation:
            return ConversationFlow(session_id=session_id, flow_events=[])

        return await self.interaction_analyzer.analyze_conversation_flow(conversation)

    async def detect_conversation_breakdowns(
        self,
        session_id: str
    ) -> List[ConversationBreakdown]:
        """Detect when conversations break down."""

        conversation_flow = await self.track_conversation_flow(session_id)
        return await self.interaction_analyzer.detect_breakdowns(conversation_flow)

    async def predict_user_needs(
        self,
        session_id: str
    ) -> UserNeedsPrediction:
        """Predict what user might need next."""

        context = await self.get_conversation_context(session_id)
        return await self.interaction_analyzer.predict_needs(context)

@dataclass
class InteractionRecord:
    """Record of a single interaction."""

    interaction_id: str = None
    user_id: str = None
    session_id: str = None
    timestamp: datetime = field(default_factory=datetime.now)

    # Interaction content
    user_input: str = None
    agent_response: str = None
    interaction_type: InteractionType = None  # QUESTION, EXPLANATION, PRACTICE, ASSESSMENT

    # Interaction context
    concepts_discussed: List[str] = field(default_factory=list)
    learning_objectives: List[str] = field(default_factory=list)

    # User state during interaction
    user_emotional_state: EmotionalState = None
    user_engagement_level: float = 0.5  # 0.0-1.0
    user_confusion_level: float = 0.5   # 0.0-1.0
    user_confidence_level: float = 0.5  # 0.0-1.0

    # Interaction quality
    helpfulness_score: Optional[float] = None
    clarity_score: Optional[float] = None
    user_satisfaction: Optional[float] = None

    # Interaction outcomes
    learning_progress_made: bool = False
    new_questions_generated: List[str] = field(default_factory=list)
    concepts_clarified: List[str] = field(default_factory=list)
    misconceptions_addressed: List[str] = field(default_factory=list)

    def extract_concepts(self) -> List[str]:
        """Extract concepts discussed in this interaction."""
        # Implementation to extract concepts from text
        pass

    def calculate_interaction_value(self) -> float:
        """Calculate the learning value of this interaction."""
        # Implementation based on outcomes and quality scores
        pass
```

## 3. Learning Memory System - Inheriting All Memory Types

### 3.1 Learning System with Multiple Inheritance

```python
class LearningMemorySystem(
    EpisodicMemoryManager,
    SemanticMemoryManager,
    UserProfileMemoryManager,
    InteractionMemoryManager,
    LearningGraphMemory
):
    """Complete learning system inheriting all memory types."""

    def __init__(self, config: LearningSystemConfig):
        # Initialize all parent classes
        EpisodicMemoryManager.__init__(self, **config.episodic_config)
        SemanticMemoryManager.__init__(self, **config.semantic_config)
        UserProfileMemoryManager.__init__(self, **config.profile_config)
        InteractionMemoryManager.__init__(self, **config.interaction_config)
        LearningGraphMemory.__init__(self, **config.graph_config)

        # Learning system coordination
        self.memory_coordinator = MemoryCoordinator(self)
        self.learning_analytics = LearningAnalytics(self)

    # === UNIFIED LEARNING INTERFACE ===

    async def process_learning_interaction(
        self,
        user_id: str,
        user_input: str,
        session_id: str
    ) -> ComprehensiveLearningResponse:
        """Process learning interaction using all memory types."""

        # Create interaction record
        interaction = InteractionRecord(
            user_id=user_id,
            session_id=session_id,
            user_input=user_input,
            timestamp=datetime.now()
        )

        # Get comprehensive context from all memory types

        # 1. Get similar episodes (EpisodicMemoryManager)
        episodic_context = await self.retrieve_similar_episodes(
            user_id, EpisodicContext.from_interaction(interaction)
        )

        # 2. Get relevant knowledge (SemanticMemoryManager)
        concepts = interaction.extract_concepts()
        semantic_context = []
        for concept in concepts:
            knowledge = await self.retrieve_knowledge_about(user_id, concept)
            semantic_context.extend(knowledge)

        # 3. Get user profile (UserProfileMemoryManager)
        user_profile = await self.get_user_profile(user_id)

        # 4. Get conversation context (InteractionMemoryManager)
        conversation_context = await self.get_conversation_context(session_id)

        # 5. Get learning graph context (LearningGraphMemory)
        next_concepts = await self.get_next_concepts(user_id)

        # Generate comprehensive response using all contexts
        response = await self.memory_coordinator.generate_contextualized_response(
            interaction=interaction,
            episodic_context=episodic_context,
            semantic_context=semantic_context,
            user_profile=user_profile,
            conversation_context=conversation_context,
            learning_recommendations=next_concepts
        )

        # Store interaction (InteractionMemoryManager)
        interaction.agent_response = response.text
        interaction_id = await self.store_interaction(interaction)

        return ComprehensiveLearningResponse(
            response_text=response.text,
            episodic_insights=response.episodic_insights,
            semantic_knowledge_used=response.semantic_knowledge_used,
            personalization_applied=response.personalization_applied,
            next_recommendations=next_concepts,
            interaction_id=interaction_id
        )

    async def complete_learning_session(
        self,
        user_id: str,
        session_id: str,
        session_outcome: SessionOutcome
    ) -> SessionConsolidationResult:
        """Complete learning session and consolidate across all memory types."""

        # Get all interactions from session
        conversation_context = await self.get_conversation_context(session_id, context_window=100)

        # Create learning episode (EpisodicMemoryManager)
        episode = Episode.from_session(conversation_context, session_outcome)
        episode_id = await self.store_episode(user_id, episode)

        # Extract semantic knowledge (SemanticMemoryManager)
        extracted_knowledge = await self.consolidate_knowledge_from_experiences(
            user_id, [episode]
        )

        # Update user profile (UserProfileMemoryManager)
        profile_update = await self.update_profile_from_episode(user_id, episode)

        # Update learning graph (LearningGraphMemory)
        graph_updates = []
        if episode.learning_achieved:
            for concept in episode.concepts_involved:
                success = await self.mark_concept_learned(
                    user_id, concept, episode.success_level
                )
                graph_updates.append(success)

        return SessionConsolidationResult(
            episode_id=episode_id,
            knowledge_extracted=len(extracted_knowledge),
            profile_updated=profile_update.confidence_change > 0,
            graph_concepts_updated=len(graph_updates),
            session_summary=await self._generate_session_summary(
                episode, extracted_knowledge, profile_update
            )
        )

    # === CROSS-MEMORY ANALYTICS ===

    async def get_comprehensive_learning_insights(
        self,
        user_id: str
    ) -> ComprehensiveLearningInsights:
        """Get insights using all memory types."""

        return await self.learning_analytics.generate_comprehensive_insights(user_id)

    async def predict_learning_success(
        self,
        user_id: str,
        planned_activity: PlannedActivity
    ) -> LearningSuccessPrediction:
        """Predict success using all memory types."""

        # Use episodic patterns
        similar_episodes = await self.retrieve_similar_episodes(
            user_id, EpisodicContext.from_planned_activity(planned_activity)
        )

        # Use semantic knowledge
        relevant_knowledge = await self.find_applicable_knowledge(
            user_id, SituationContext.from_planned_activity(planned_activity)
        )

        # Use user profile
        user_profile = await self.get_user_profile(user_id)
        preferences = await self.predict_user_preference(
            user_id, SituationContext.from_planned_activity(planned_activity)
        )

        # Use learning graph
        readiness = await self.can_learn_concept(user_id, planned_activity.target_concept)

        return await self.memory_coordinator.predict_success(
            planned_activity, similar_episodes, relevant_knowledge,
            user_profile, preferences, readiness
        )

class MemoryCoordinator:
    """Coordinates between different memory types."""

    def __init__(self, learning_system: LearningMemorySystem):
        self.episodic = learning_system  # Access to episodic methods
        self.semantic = learning_system  # Access to semantic methods
        self.profile = learning_system   # Access to profile methods
        self.interaction = learning_system  # Access to interaction methods
        self.graph = learning_system     # Access to graph methods

    async def generate_contextualized_response(
        self,
        interaction: InteractionRecord,
        episodic_context: List[Episode],
        semantic_context: List[SemanticKnowledge],
        user_profile: UserProfile,
        conversation_context: ConversationContext,
        learning_recommendations: List[ConceptRecommendation]
    ) -> ContextualizedResponse:
        """Generate response using insights from all memory types."""

        # Analyze context from each memory type
        episodic_insights = self._analyze_episodic_context(episodic_context, interaction)
        semantic_insights = self._analyze_semantic_context(semantic_context, interaction)
        profile_insights = self._analyze_profile_context(user_profile, interaction)
        conversation_insights = self._analyze_conversation_context(conversation_context, interaction)

        # Generate personalized response
        response_text = await self._generate_integrated_response(
            interaction, episodic_insights, semantic_insights,
            profile_insights, conversation_insights, learning_recommendations
        )

        return ContextualizedResponse(
            text=response_text,
            episodic_insights=episodic_insights,
            semantic_knowledge_used=semantic_insights,
            personalization_applied=profile_insights,
            conversation_continuity=conversation_insights
        )
```

### 3.2 Application Usage Examples

```python
async def learning_system_usage_example():
    """Example of using the complete learning system."""

    # Initialize learning system with all memory types
    config = LearningSystemConfig(
        episodic_config={"storage_backend": "postgresql"},
        semantic_config={"knowledge_base": "vector_db"},
        profile_config={"profile_tracker": "advanced"},
        interaction_config={"conversation_analyzer": "nlp_enhanced"},
        graph_config={"graph_backend": "neo4j"}
    )

    learning_system = LearningMemorySystem(config)

    user_id = "student_alice"
    session_id = "algebra_session_1"

    # === LEARNING INTERACTION ===

    # Process learning interaction using all memory types
    response = await learning_system.process_learning_interaction(
        user_id=user_id,
        user_input="I'm struggling with quadratic equations",
        session_id=session_id
    )

    print(f"Response: {response.response_text}")
    print(f"Episodic insights: {response.episodic_insights}")
    print(f"Personalization: {response.personalization_applied}")
    print(f"Next concepts: {response.next_recommendations}")

    # === SESSION COMPLETION ===

    # Complete session with consolidation across all memory types
    session_outcome = SessionOutcome(
        overall_success=0.75,
        learning_objectives_met=["understanding_discriminant"],
        breakthroughs_achieved=True,
        user_satisfaction=0.8
    )

    consolidation = await learning_system.complete_learning_session(
        user_id, session_id, session_outcome
    )

    print(f"Consolidation: {consolidation.session_summary}")

    # === LEARNING INSIGHTS ===

    # Get comprehensive insights from all memory types
    insights = await learning_system.get_comprehensive_learning_insights(user_id)

    print(f"Learning patterns: {insights.episodic_patterns}")
    print(f"Knowledge gaps: {insights.semantic_gaps}")
    print(f"Profile insights: {insights.profile_insights}")
    print(f"Communication patterns: {insights.interaction_patterns}")

async def individual_memory_usage_example():
    """Example of using individual memory types independently."""

    # Can use individual memory types independently

    # Just episodic memory for experience tracking
    episodic_memory = EpisodicMemoryManager()
    episode = Episode(
        user_id="student_bob",
        activity_type="practice",
        concepts_involved=["linear_equations"],
        success_level=0.8
    )
    await episodic_memory.store_episode("student_bob", episode)

    # Just semantic memory for knowledge management
    semantic_memory = SemanticMemoryManager()
    knowledge = SemanticKnowledge(
        knowledge_statement="Linear equations have the form ax + b = 0",
        knowledge_type=KnowledgeType.FACT,
        related_concepts=["linear_equations"]
    )
    await semantic_memory.store_knowledge("student_bob", knowledge)

    # Just profile memory for personalization
    profile_memory = UserProfileMemoryManager()
    profile = await profile_memory.get_user_profile("student_bob")
    print(f"Learning style: {profile.learning_style}")

    # Just interaction memory for conversation
    interaction_memory = InteractionMemoryManager()
    interaction = InteractionRecord(
        user_id="student_bob",
        session_id="session_1",
        user_input="What is a linear equation?",
        agent_response="A linear equation is an equation of the form ax + b = 0..."
    )
    await interaction_memory.store_interaction(interaction)
```

<function_calls>
<invoke name="TodoWrite">
<parameter name="todos">[{"content": "Move memory types to agent memory layer", "status": "completed", "activeForm": "Moving memory types to agent memory layer"}, {"content": "Design episodic memory as agent memory extension", "status": "completed", "activeForm": "Designing episodic memory as agent memory extension"}, {"content": "Design semantic memory as agent memory extension", "status": "completed", "activeForm": "Designing semantic memory as agent memory extension"}, {"content": "Design user profile memory as agent memory extension", "status": "completed", "activeForm": "Designing user profile memory as agent memory extension"}, {"content": "Design interaction memory as agent memory extension", "status": "completed", "activeForm": "Designing interaction memory as agent memory extension"}, {"content": "Create learning system that inherits all memory types", "status": "completed", "activeForm": "Creating learning system that inherits all memory types"}]