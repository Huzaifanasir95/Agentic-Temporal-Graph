"""
Analyzer Agent
Extracts entities, events, and claims using LLM
"""

from typing import List, Dict, Any
from loguru import logger
from agents.state import AgentState
from models.llm_client import create_llm_client
import json
import time
import hashlib


class AnalyzerAgent:
    """
    Analyzer Agent - Extracts structured information from text
    Uses LLM to identify entities, events, and claims
    """
    
    ANALYSIS_PROMPT = """You are an expert OSINT analyst. Analyze the following article and extract:

1. **Entities**: People, organizations, locations mentioned
2. **Events**: Significant occurrences described
3. **Claims**: Factual statements that can be verified

Article:
{text}

Respond with valid JSON only:
{{
  "entities": [
    {{"name": "Entity Name", "type": "PERSON|ORGANIZATION|LOCATION|CONCEPT", "context": "brief context"}}
  ],
  "events": [
    {{"description": "What happened", "type": "ANNOUNCEMENT|CONFLICT|MEETING|POLICY", "timestamp": "when or null", "location": "where or null"}}
  ],
  "claims": [
    {{"text": "The claim", "context": "surrounding context", "confidence": 0.0-1.0}}
  ],
  "sentiment": {{"polarity": -1.0 to 1.0, "subjectivity": 0.0-1.0}},
  "summary": "Brief 2-sentence summary"
}}"""
    
    def __init__(self):
        """Initialize Analyzer Agent"""
        self.name = "AnalyzerAgent"
        self.llm = create_llm_client()
        logger.info(f"{self.name} initialized")
        
    def process(self, state: AgentState) -> AgentState:
        """
        Analyze text and extract structured information
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with extracted entities, events, claims
        """
        start_time = time.time()
        
        try:
            logger.info(f"[{self.name}] Analyzing...")
            
            full_text = state['raw_data'].get('full_text', '')
            
            if not full_text or len(full_text) < 50:
                logger.warning(f"[{self.name}] Text too short, skipping")
                state['next_agent'] = 'GraphBuilderAgent'
                return state
            
            # Truncate if too long (LLM token limits)
            if len(full_text) > 4000:
                full_text = full_text[:4000] + "..."
            
            # Use LLM to extract information
            analysis = self._analyze_with_llm(full_text)
            
            if analysis:
                # Process entities
                for entity_data in analysis.get('entities', []):
                    entity = self._create_entity(entity_data, state['raw_data'])
                    state['entities'].append(entity)
                
                # Process events
                for event_data in analysis.get('events', []):
                    event = self._create_event(event_data, state['raw_data'])
                    state['events'].append(event)
                
                # Process claims
                for claim_data in analysis.get('claims', []):
                    claim = self._create_claim(claim_data, state['raw_data'])
                    state['claims'].append(claim)
                
                # Store sentiment
                state['sentiment'] = analysis.get('sentiment')
                
                logger.info(f"[{self.name}] Extracted: {len(state['entities'])} entities, {len(state['events'])} events, {len(state['claims'])} claims")
            
            # Mark as processed
            state['processed_by'].append(self.name)
            
            # Route to next agent
            if state['claims']:
                state['next_agent'] = 'CrossReferenceAgent'
            else:
                state['next_agent'] = 'GraphBuilderAgent'
            
            elapsed = time.time() - start_time
            logger.debug(f"[{self.name}] Completed in {elapsed:.2f}s")
            
            return state
            
        except Exception as e:
            logger.error(f"[{self.name}] Error: {e}")
            state['errors'].append(f"{self.name}: {str(e)}")
            state['next_agent'] = 'GraphBuilderAgent'  # Skip to graph builder
            return state
            
    def _analyze_with_llm(self, text: str) -> Dict[str, Any]:
        """
        Use LLM to analyze text
        
        Args:
            text: Article text
            
        Returns:
            Extracted analysis dict
        """
        try:
            prompt = self.ANALYSIS_PROMPT.format(text=text)
            
            response = self.llm.generate_json(
                prompt=prompt,
                system_prompt="You are an expert OSINT analyst. Extract structured information from articles.",
                temperature=0.3,  # Lower temperature for structured output
                max_tokens=2000,
            )
            
            return response
            
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            return {}
            
    def _create_entity(self, entity_data: Dict[str, Any], source: Dict[str, Any]) -> Dict[str, Any]:
        """Create entity dict"""
        entity_id = self._generate_id(f"{entity_data['name']}_{entity_data['type']}")
        
        return {
            "id": entity_id,
            "name": entity_data['name'],
            "type": entity_data.get('type', 'UNKNOWN'),
            "confidence": 0.8,  # Default confidence
            "context": entity_data.get('context', ''),
            "mentions": 1,
            "source_id": source.get('id', ''),
        }
        
    def _create_event(self, event_data: Dict[str, Any], source: Dict[str, Any]) -> Dict[str, Any]:
        """Create event dict"""
        event_id = self._generate_id(event_data['description'][:100])
        
        return {
            "id": event_id,
            "description": event_data['description'],
            "type": event_data.get('type', 'UNKNOWN'),
            "timestamp": event_data.get('timestamp') or source.get('published_at'),
            "location": event_data.get('location'),
            "participants": [],
            "confidence": 0.75,
            "source_id": source.get('id', ''),
        }
        
    def _create_claim(self, claim_data: Dict[str, Any], source: Dict[str, Any]) -> Dict[str, Any]:
        """Create claim dict"""
        claim_id = self._generate_id(claim_data['text'])
        
        return {
            "id": claim_id,
            "text": claim_data['text'],
            "context": claim_data.get('context', ''),
            "stance": "NEUTRAL",
            "confidence": claim_data.get('confidence', 0.7),
            "about_entities": [],
            "about_events": [],
            "source_id": source.get('id', ''),
            "source_url": source.get('url', ''),
        }
        
    def _generate_id(self, text: str) -> str:
        """Generate unique ID from text"""
        return hashlib.md5(text.encode()).hexdigest()[:16]
        
    def __call__(self, state: AgentState) -> AgentState:
        """Allow agent to be called directly"""
        return self.process(state)


def analyzer_node(state: AgentState) -> AgentState:
    """
    LangGraph node function for Analyzer Agent
    
    Args:
        state: Current state
        
    Returns:
        Updated state
    """
    agent = AnalyzerAgent()
    return agent.process(state)


if __name__ == "__main__":
    # Test Analyzer Agent
    from dotenv import load_dotenv
    from agents.state import create_initial_state
    from agents.collector import CollectorAgent
    
    load_dotenv()
    
    # Sample data
    sample_data = {
        "id": "test-002",
        "title": "UN Climate Summit Reaches Historic Agreement",
        "content": "Leaders from 195 countries gathered in Geneva today to sign the Paris Climate Accord 2.0. The agreement mandates a 50% reduction in global carbon emissions by 2030. UN Secretary-General António Guterres called it 'a turning point for humanity.' Scientists warn that without immediate action, global temperatures could rise by 2.5°C by 2050.",
        "source_type": "rss",
        "source_name": "Reuters",
        "published_at": "2026-01-04T10:00:00Z",
        "url": "https://example.com/article"
    }
    
    # Process with Collector first
    state = create_initial_state(sample_data)
    collector = CollectorAgent()
    state = collector.process(state)
    
    # Process with Analyzer
    analyzer = AnalyzerAgent()
    state = analyzer.process(state)
    
    print(f"\n✓ Analyzer Agent Test")
    print(f"  Entities: {len(state['entities'])}")
    for e in state['entities'][:3]:
        print(f"    - {e['name']} ({e['type']})")
    print(f"  Events: {len(state['events'])}")
    for ev in state['events'][:2]:
        print(f"    - {ev['description'][:60]}...")
    print(f"  Claims: {len(state['claims'])}")
    for c in state['claims'][:2]:
        print(f"    - {c['text'][:70]}...")
    print(f"  Next agent: {state['next_agent']}")
