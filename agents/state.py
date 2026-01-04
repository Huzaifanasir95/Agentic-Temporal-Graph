"""
Agent State Schema
Shared state for multi-agent workflow
"""

from typing import TypedDict, List, Dict, Any, Optional, Annotated
from datetime import datetime
import operator


class AgentState(TypedDict):
    """
    Shared state passed between agents in the workflow
    """
    # Input data
    raw_data: Dict[str, Any]  # Original article/post from Kafka
    raw_text: str  # Combined text content
    source: Optional[Dict[str, Any]]  # Source information
    metadata: Dict[str, Any]  # Additional metadata
    
    # Extracted information
    entities: Annotated[List[Dict[str, Any]], operator.add]  # Entities found
    events: Annotated[List[Dict[str, Any]], operator.add]  # Events described
    claims: Annotated[List[Dict[str, Any]], operator.add]  # Claims made
    
    # Analysis results
    sentiment: Optional[Dict[str, Any]]  # Sentiment analysis
    bias_score: Optional[float]  # Bias detection score
    credibility_score: Optional[float]  # Source credibility
    
    # Cross-reference results
    similar_claims: Annotated[List[Dict[str, Any]], operator.add]  # Similar existing claims
    contradictions: Annotated[List[Dict[str, Any]], operator.add]  # Contradictory claims
    
    # Graph updates
    graph_operations: Annotated[List[Dict[str, Any]], operator.add]  # Neo4j operations to perform
    
    # Metadata
    processing_log: Annotated[List[Dict[str, Any]], operator.add]  # Processing history
    processed_by: Annotated[List[str], operator.add]  # Which agents processed this
    processing_time: Optional[float]  # Total processing time
    errors: Annotated[List[str], operator.add]  # Any errors encountered
    
    # Workflow control
    next_agent: Optional[str]  # Which agent should process next
    should_alert: bool  # Flag for high-priority items


# Entity schema
class Entity(TypedDict):
    """Extracted entity"""
    id: str
    name: str
    type: str  # PERSON, ORGANIZATION, LOCATION, CONCEPT, EVENT
    confidence: float
    context: str
    mentions: int


# Event schema
class Event(TypedDict):
    """Extracted event"""
    id: str
    description: str
    type: str  # ANNOUNCEMENT, CONFLICT, MEETING, POLICY_CHANGE, etc.
    timestamp: Optional[str]
    location: Optional[str]
    participants: List[str]  # Entity IDs
    confidence: float


# Claim schema
class Claim(TypedDict):
    """Extracted claim"""
    id: str
    text: str
    context: str
    stance: str  # SUPPORTS, REFUTES, NEUTRAL
    confidence: float
    about_entities: List[str]  # Entity IDs
    about_events: List[str]  # Event IDs
    source_id: str


# Graph operation schema
class GraphOperation(TypedDict):
    """Neo4j graph operation"""
    operation_type: str  # CREATE, MERGE, UPDATE, LINK
    node_type: Optional[str]  # Entity, Event, Claim, Source
    node_id: str  # ID of the node
    properties: Dict[str, Any]


def create_initial_state(raw_data: Dict[str, Any]) -> AgentState:
    """
    Create initial state from raw data
    
    Args:
        raw_data: Article/post data from Kafka
        
    Returns:
        Initial AgentState
    """
    return AgentState(
        raw_data=raw_data,
        raw_text='',
        source=raw_data.get('source', {}),
        metadata={},
        entities=[],
        events=[],
        claims=[],
        sentiment=None,
        bias_score=None,
        credibility_score=None,
        similar_claims=[],
        contradictions=[],
        graph_operations=[],
        processing_log=[],
        processed_by=[],
        processing_time=None,
        errors=[],
        next_agent=None,
        should_alert=False,
    )


def validate_state(state: AgentState) -> bool:
    """
    Validate state structure
    
    Args:
        state: Agent state to validate
        
    Returns:
        True if valid
    """
    required_keys = ['raw_data', 'entities', 'claims', 'processed_by']
    return all(key in state for key in required_keys)


if __name__ == "__main__":
    # Test state creation
    sample_data = {
        "id": "test-001",
        "title": "Test Article",
        "content": "Test content",
        "source_type": "rss",
    }
    
    state = create_initial_state(sample_data)
    
    print("Initial state created:")
    print(f"  Raw data: {state['raw_data']['title']}")
    print(f"  Entities: {len(state['entities'])}")
    print(f"  Claims: {len(state['claims'])}")
    print(f"  Valid: {validate_state(state)}")
