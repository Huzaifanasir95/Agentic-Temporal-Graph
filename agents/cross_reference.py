"""
Cross-Reference Agent
Queries Neo4j to find similar or contradictory claims
"""

from typing import Dict, Any
from agents.state import AgentState
from graph.neo4j_client import Neo4jClient
from loguru import logger
import time


class CrossReferenceAgent:
    """
    Cross-references claims against existing knowledge graph
    
    Responsibilities:
    - Query Neo4j for similar claims
    - Detect potential contradictions
    - Calculate confidence scores
    - Provide context from historical data
    """
    
    def __init__(self):
        """Initialize cross-reference agent"""
        self.neo4j = Neo4jClient()
        logger.info("CrossReferenceAgent initialized")
        
    def process(self, state: AgentState) -> AgentState:
        """
        Process state and cross-reference claims
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state
        """
        logger.info("[CrossReferenceAgent] Cross-referencing claims...")
        start_time = time.time()
        
        # Process each claim
        for claim in state['claims']:
            # Find similar existing claims
            similar = self._find_similar_claims(claim['text'])
            claim['similar_claims'] = similar
            
            # Check for contradictions
            if similar:
                contradictions = self._detect_contradictions(claim, similar)
                claim['contradictions'] = contradictions
                
                # Update confidence based on existing evidence
                claim['confidence'] = self._calculate_confidence(
                    claim,
                    similar,
                    contradictions
                )
                
        # Update processing log
        state['processing_log'].append({
            'agent': 'CrossReferenceAgent',
            'action': 'cross_referenced',
            'claims_processed': len(state['claims']),
            'timestamp': time.time()
        })
        
        # Determine next agent
        has_contradictions = any(c.get('contradictions') for c in state['claims'])
        state['next_agent'] = 'BiasDetectorAgent' if has_contradictions else 'GraphBuilderAgent'
        
        elapsed = time.time() - start_time
        logger.debug(f"[CrossReferenceAgent] Completed in {elapsed:.2f}s")
        
        return state
        
    def _find_similar_claims(self, claim_text: str) -> list:
        """
        Find similar claims in graph
        
        Args:
            claim_text: Claim text
            
        Returns:
            List of similar claims
        """
        try:
            similar = self.neo4j.find_similar_claims(claim_text, limit=5)
            logger.debug(f"Found {len(similar)} similar claims")
            return similar
        except Exception as e:
            logger.error(f"Error finding similar claims: {e}")
            return []
            
    def _detect_contradictions(
        self,
        current_claim: Dict[str, Any],
        similar_claims: list
    ) -> list:
        """
        Detect contradictions between claims
        
        Args:
            current_claim: Current claim
            similar_claims: Similar existing claims
            
        Returns:
            List of contradictory claims
        """
        contradictions = []
        
        current_text = current_claim['text'].lower()
        
        for similar in similar_claims:
            similar_text = similar['text'].lower()
            
            # Simple contradiction detection heuristics
            if self._are_contradictory(current_text, similar_text):
                contradictions.append({
                    'claim_id': similar['id'],
                    'text': similar['text'],
                    'confidence': 0.7,
                    'reason': 'semantic_contradiction'
                })
                
        return contradictions
        
    def _are_contradictory(self, text1: str, text2: str) -> bool:
        """
        Check if two texts are contradictory
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            True if contradictory
        """
        # Negation words
        negations = ['not', 'no', 'never', 'cannot', 'isn\'t', 'aren\'t', 'won\'t']
        
        # Check for negation patterns
        has_negation1 = any(neg in text1 for neg in negations)
        has_negation2 = any(neg in text2 for neg in negations)
        
        # Opposite negation status might indicate contradiction
        if has_negation1 != has_negation2:
            # Check for common keywords
            words1 = set(text1.split())
            words2 = set(text2.split())
            overlap = words1 & words2
            
            # If significant overlap but opposite negation, likely contradiction
            if len(overlap) > 3:
                return True
                
        return False
        
    def _calculate_confidence(
        self,
        claim: Dict[str, Any],
        similar_claims: list,
        contradictions: list
    ) -> float:
        """
        Calculate confidence score for claim
        
        Args:
            claim: Current claim
            similar_claims: Similar claims
            contradictions: Contradictory claims
            
        Returns:
            Confidence score (0-1)
        """
        base_confidence = claim.get('confidence', 0.5)
        
        # Boost confidence if similar verified claims exist
        verified = [c for c in similar_claims if c.get('status') == 'VERIFIED']
        if verified:
            base_confidence = min(1.0, base_confidence + 0.2)
            
        # Reduce confidence if contradictions found
        if contradictions:
            penalty = len(contradictions) * 0.15
            base_confidence = max(0.0, base_confidence - penalty)
            
        return round(base_confidence, 2)
        
    def close(self):
        """Close connections"""
        self.neo4j.close()


if __name__ == "__main__":
    # Test cross-reference agent
    from agents.state import create_initial_state
    
    # Create test state with claims
    state = create_initial_state("Test article about climate change")
    state['claims'] = [
        {
            'id': 'claim_1',
            'text': 'Global temperatures will rise by 2.5°C by 2050',
            'context': 'Climate report',
            'confidence': 0.7
        },
        {
            'id': 'claim_2',
            'text': 'Carbon emissions must be reduced by 50%',
            'context': 'Policy document',
            'confidence': 0.8
        }
    ]
    
    agent = CrossReferenceAgent()
    
    try:
        result = agent.process(state)
        
        print(f"\n✓ Cross-Reference Agent Test")
        print(f"  Claims processed: {len(result['claims'])}")
        
        for claim in result['claims']:
            print(f"\n  Claim: {claim['text'][:60]}...")
            print(f"    Confidence: {claim['confidence']}")
            print(f"    Similar claims: {len(claim.get('similar_claims', []))}")
            print(f"    Contradictions: {len(claim.get('contradictions', []))}")
            
        print(f"  Next agent: {result['next_agent']}")
        
    finally:
        agent.close()
