"""
Bias Detection Agent
Uses NLI models to detect bias and verify claims
"""

from typing import Dict, Any, List
from agents.state import AgentState
from models.llm_client import create_llm_client
from loguru import logger
import time


class BiasDetectorAgent:
    """
    Detects bias and verifies claims using NLI
    
    Responsibilities:
    - Detect political/ideological bias
    - Analyze sentiment and framing
    - Verify claims against evidence
    - Flag potentially misleading content
    """
    
    # Bias detection patterns
    BIAS_INDICATORS = {
        'loaded_language': [
            'radical', 'extreme', 'dangerous', 'shocking', 'outrageous',
            'devastating', 'slam', 'destroy', 'demolish'
        ],
        'absolute_terms': [
            'always', 'never', 'all', 'none', 'every', 'completely',
            'totally', 'absolutely', 'entirely'
        ],
        'emotional_appeals': [
            'feel', 'believe', 'fear', 'hope', 'worry', 'concerned',
            'alarmed', 'excited', 'angry'
        ]
    }
    
    def __init__(self):
        """Initialize bias detector"""
        self.llm = create_llm_client()
        logger.info("BiasDetectorAgent initialized")
        
    def process(self, state: AgentState) -> AgentState:
        """
        Process state and detect bias
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state
        """
        logger.info("[BiasDetectorAgent] Analyzing bias...")
        start_time = time.time()
        
        # Analyze full article for bias
        article_text = state['raw_text']
        bias_analysis = self._analyze_bias(article_text)
        
        # Store in metadata
        state['metadata']['bias_analysis'] = bias_analysis
        
        # Verify individual claims
        for claim in state['claims']:
            verification = self._verify_claim(claim, article_text)
            claim['verification'] = verification
            
            # Update confidence based on bias and verification
            claim['confidence'] = self._adjust_confidence(
                claim['confidence'],
                bias_analysis,
                verification
            )
            
        # Update processing log
        state['processing_log'].append({
            'agent': 'BiasDetectorAgent',
            'action': 'analyzed_bias',
            'bias_score': bias_analysis['overall_bias_score'],
            'timestamp': time.time()
        })
        
        # Always go to Graph Builder after bias detection
        state['next_agent'] = 'GraphBuilderAgent'
        
        elapsed = time.time() - start_time
        logger.debug(f"[BiasDetectorAgent] Completed in {elapsed:.2f}s")
        
        return state
        
    def _analyze_bias(self, text: str) -> Dict[str, Any]:
        """
        Analyze text for bias
        
        Args:
            text: Article text
            
        Returns:
            Bias analysis results
        """
        # Pattern-based detection
        patterns = self._detect_bias_patterns(text)
        
        # LLM-based analysis
        llm_analysis = self._analyze_with_llm(text)
        
        # Combine results
        overall_score = (patterns['score'] + llm_analysis.get('bias_score', 0.5)) / 2
        
        return {
            'overall_bias_score': round(overall_score, 2),
            'bias_types': llm_analysis.get('bias_types', []),
            'pattern_matches': patterns['matches'],
            'framing': llm_analysis.get('framing', 'neutral'),
            'recommendation': self._get_recommendation(overall_score)
        }
        
    def _detect_bias_patterns(self, text: str) -> Dict[str, Any]:
        """
        Detect bias using pattern matching
        
        Args:
            text: Text to analyze
            
        Returns:
            Pattern detection results
        """
        text_lower = text.lower()
        matches = {}
        total_indicators = 0
        
        for category, indicators in self.BIAS_INDICATORS.items():
            found = [ind for ind in indicators if ind in text_lower]
            if found:
                matches[category] = found
                total_indicators += len(found)
                
        # Calculate bias score (0-1)
        word_count = len(text.split())
        bias_ratio = total_indicators / max(word_count, 1)
        bias_score = min(1.0, bias_ratio * 100)  # Scale up
        
        return {
            'score': bias_score,
            'matches': matches
        }
        
    def _analyze_with_llm(self, text: str) -> Dict[str, Any]:
        """
        Use LLM for bias analysis
        
        Args:
            text: Text to analyze
            
        Returns:
            LLM analysis results
        """
        prompt = f"""Analyze this article for bias and provide:
1. Bias score (0.0 = no bias, 1.0 = extreme bias)
2. Types of bias detected (political, emotional, sensational, etc.)
3. Framing (neutral, positive, negative)

Article: {text[:1000]}...

Respond with valid JSON only:
{{"bias_score": 0.0, "bias_types": [], "framing": "neutral"}}"""
        
        try:
            response = self.llm.generate_json(
                prompt=prompt,
                system_prompt="You are an expert media bias analyst.",
                temperature=0.2,
                max_tokens=500
            )
            return response
        except Exception as e:
            logger.error(f"LLM bias analysis failed: {e}")
            return {'bias_score': 0.5, 'bias_types': [], 'framing': 'unknown'}
            
    def _verify_claim(
        self,
        claim: Dict[str, Any],
        context: str
    ) -> Dict[str, Any]:
        """
        Verify claim against context
        
        Args:
            claim: Claim to verify
            context: Article context
            
        Returns:
            Verification results
        """
        # Check if claim is supported by context
        claim_text = claim['text'].lower()
        context_lower = context.lower()
        
        # Simple keyword overlap
        claim_words = set(claim_text.split())
        context_words = set(context_lower.split())
        overlap = claim_words & context_words
        
        support_ratio = len(overlap) / len(claim_words) if claim_words else 0
        
        # Determine verification status
        if support_ratio > 0.7:
            status = 'SUPPORTED'
        elif support_ratio > 0.4:
            status = 'PARTIALLY_SUPPORTED'
        else:
            status = 'UNSUPPORTED'
            
        return {
            'status': status,
            'support_ratio': round(support_ratio, 2),
            'method': 'keyword_overlap'
        }
        
    def _adjust_confidence(
        self,
        original_confidence: float,
        bias_analysis: Dict[str, Any],
        verification: Dict[str, Any]
    ) -> float:
        """
        Adjust claim confidence based on bias and verification
        
        Args:
            original_confidence: Original confidence score
            bias_analysis: Bias analysis results
            verification: Verification results
            
        Returns:
            Adjusted confidence score
        """
        confidence = original_confidence
        
        # Penalize high bias
        bias_penalty = bias_analysis['overall_bias_score'] * 0.2
        confidence -= bias_penalty
        
        # Adjust based on verification
        if verification['status'] == 'SUPPORTED':
            confidence += 0.1
        elif verification['status'] == 'UNSUPPORTED':
            confidence -= 0.2
            
        return max(0.0, min(1.0, round(confidence, 2)))
        
    def _get_recommendation(self, bias_score: float) -> str:
        """Get recommendation based on bias score"""
        if bias_score < 0.3:
            return 'LOW_BIAS'
        elif bias_score < 0.6:
            return 'MODERATE_BIAS'
        else:
            return 'HIGH_BIAS'


if __name__ == "__main__":
    # Test bias detector
    from agents.state import create_initial_state
    
    # Create test state
    state = create_initial_state("""
    SHOCKING: Government COMPLETELY DESTROYS opposition with RADICAL new policy!
    Everyone is OUTRAGED by this DEVASTATING decision that will TOTALLY change everything.
    """)
    
    state['claims'] = [
        {
            'id': 'claim_1',
            'text': 'Government introduces radical new policy',
            'confidence': 0.7
        }
    ]
    
    agent = BiasDetectorAgent()
    result = agent.process(state)
    
    print(f"\n✓ Bias Detector Agent Test")
    bias = result['metadata']['bias_analysis']
    print(f"  Bias score: {bias['overall_bias_score']}")
    print(f"  Framing: {bias['framing']}")
    print(f"  Recommendation: {bias['recommendation']}")
    
    if bias['pattern_matches']:
        print(f"  Pattern matches:")
        for category, matches in bias['pattern_matches'].items():
            print(f"    {category}: {matches[:3]}")
            
    print(f"\n  Claims:")
    for claim in result['claims']:
        print(f"    {claim['text'][:50]}...")
        print(f"      Confidence: {claim['confidence']}")
        print(f"      Verification: {claim['verification']['status']}")
        
    print(f"  Next agent: {result['next_agent']}")
