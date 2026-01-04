"""
Collector Agent
Consumes messages from Kafka and initializes agent state
"""

from typing import Dict, Any, Optional
from loguru import logger
from agents.state import AgentState, create_initial_state
import time


class CollectorAgent:
    """
    Collector Agent - Entry point for data processing
    Retrieves raw data and initializes the agent workflow
    """
    
    def __init__(self):
        """Initialize Collector Agent"""
        self.name = "CollectorAgent"
        logger.info(f"{self.name} initialized")
        
    def process(self, state: AgentState) -> AgentState:
        """
        Process raw data and prepare for analysis
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with cleaned data
        """
        start_time = time.time()
        
        try:
            logger.info(f"[{self.name}] Processing: {state['raw_data'].get('title', 'Untitled')[:50]}...")
            
            # Clean and normalize raw data
            raw = state['raw_data']
            
            # Validate required fields
            if not raw.get('content') and not raw.get('title'):
                raise ValueError("No content or title found")
            
            # Combine title and content
            full_text = self._prepare_text(raw)
            
            # Update state
            state['raw_data']['full_text'] = full_text
            state['raw_data']['word_count'] = len(full_text.split())
            
            # Mark as processed
            state['processed_by'].append(self.name)
            
            # Route to next agent
            state['next_agent'] = 'AnalyzerAgent'
            
            elapsed = time.time() - start_time
            logger.debug(f"[{self.name}] Completed in {elapsed:.2f}s")
            
            return state
            
        except Exception as e:
            logger.error(f"[{self.name}] Error: {e}")
            state['errors'].append(f"{self.name}: {str(e)}")
            state['next_agent'] = None  # Stop workflow
            return state
            
    def _prepare_text(self, raw_data: Dict[str, Any]) -> str:
        """
        Combine title, content, and metadata into full text
        
        Args:
            raw_data: Raw article/post data
            
        Returns:
            Combined text
        """
        parts = []
        
        # Title
        if raw_data.get('title'):
            parts.append(raw_data['title'])
        
        # Content
        if raw_data.get('content'):
            parts.append(raw_data['content'])
        elif raw_data.get('full_content'):
            parts.append(raw_data['full_content'])
        
        # Author context
        if raw_data.get('author'):
            parts.append(f"Author: {raw_data['author']}")
        
        return "\n\n".join(parts)
        
    def __call__(self, state: AgentState) -> AgentState:
        """Allow agent to be called directly"""
        return self.process(state)


def collector_node(state: AgentState) -> AgentState:
    """
    LangGraph node function for Collector Agent
    
    Args:
        state: Current state
        
    Returns:
        Updated state
    """
    agent = CollectorAgent()
    return agent.process(state)


if __name__ == "__main__":
    # Test Collector Agent
    from dotenv import load_dotenv
    load_dotenv()
    
    # Sample raw data
    sample_data = {
        "id": "test-001",
        "title": "Breaking: New Climate Agreement Signed",
        "content": "World leaders gathered today to sign a historic climate agreement. The treaty commits all major economies to reduce carbon emissions by 50% by 2030.",
        "source_type": "rss",
        "source_name": "BBC World News",
        "author": "Jane Doe",
        "published_at": "2026-01-04T12:00:00Z",
    }
    
    # Create initial state
    state = create_initial_state(sample_data)
    
    # Process with Collector Agent
    agent = CollectorAgent()
    updated_state = agent.process(state)
    
    print(f"\n✓ Collector Agent Test")
    print(f"  Processed by: {updated_state['processed_by']}")
    print(f"  Word count: {updated_state['raw_data'].get('word_count', 0)}")
    print(f"  Next agent: {updated_state['next_agent']}")
    print(f"  Errors: {len(updated_state['errors'])}")
