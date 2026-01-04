"""
Contradiction Detection Module for OSINT Intelligence Platform

Uses Natural Language Inference (NLI) to detect contradictory claims.
Employs cross-encoder models for accurate semantic contradiction detection.
"""

import json
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from loguru import logger

try:
    from sentence_transformers import CrossEncoder
    CROSS_ENCODER_AVAILABLE = True
except ImportError:
    CROSS_ENCODER_AVAILABLE = False
    logger.warning("sentence-transformers not available - using fallback detection")

from graph.neo4j_client import Neo4jClient


@dataclass
class Contradiction:
    """Represents a detected contradiction between two claims"""
    claim1_id: str
    claim1_text: str
    claim1_confidence: float
    claim1_source: str = "Unknown"
    claim1_timestamp: str = ""
    
    claim2_id: str
    claim2_text: str
    claim2_confidence: float
    claim2_source: str = "Unknown"
    claim2_timestamp: str = ""
    
    contradiction_score: float  # 0-1, higher = more contradictory
    contradiction_type: str  # factual, temporal, numerical, semantic
    entities_involved: List[str]
    severity: str  # low, medium, high, critical
    detected_at: datetime
    
    explanation: Optional[str] = None
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['detected_at'] = self.detected_at.isoformat()
        return data


@dataclass
class ContradictionCluster:
    """Group of related contradictions"""
    cluster_id: str
    entities: List[str]
    contradictions: List[Contradiction]
    cluster_score: float
    impact: str  # low, medium, high, critical
    sources_involved: List[str]
    time_span: str  # days between first and last contradiction
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['contradictions'] = [c.to_dict() for c in self.contradictions]
        return data


class ContradictionDetector:
    """
    Detects contradictions between claims using NLI models.
    
    Features:
    - Cross-encoder NLI for semantic contradiction detection
    - Numerical contradiction detection (different numbers for same fact)
    - Temporal contradiction detection (conflicting timelines)
    - Factual contradiction detection (opposite statements)
    - Contradiction clustering and severity scoring
    """
    
    def __init__(self, neo4j_client: Optional[Neo4jClient] = None, model_name: str = "cross-encoder/nli-deberta-v3-base"):
        """
        Initialize contradiction detector.
        
        Args:
            neo4j_client: Neo4j database client
            model_name: Cross-encoder model for NLI
        """
        self.neo4j = neo4j_client or Neo4jClient()
        self.model_name = model_name
        self.model = None
        
        # Try to load model
        if CROSS_ENCODER_AVAILABLE:
            try:
                self.model = CrossEncoder(model_name)
                logger.info(f"Loaded NLI model: {model_name}")
            except Exception as e:
                logger.warning(f"Could not load NLI model: {e}")
                self.model = None
        
        self.contradiction_cache: List[Contradiction] = []
        logger.info("Contradiction Detector initialized")
    
    # ==================== Main Detection ====================
    
    def detect_contradictions(self, entity_name: Optional[str] = None, days: int = 30) -> List[Contradiction]:
        """
        Detect contradictions in claims.
        
        Args:
            entity_name: Optional - focus on specific entity
            days: Number of days to look back
        
        Returns:
            List of detected contradictions
        """
        # Get claims to analyze
        claims = self._get_claims(entity_name, days)
        
        if len(claims) < 2:
            logger.info("Not enough claims to detect contradictions")
            return []
        
        logger.info(f"Analyzing {len(claims)} claims for contradictions...")
        
        contradictions = []
        
        # Compare all pairs of claims
        for i in range(len(claims)):
            for j in range(i + 1, len(claims)):
                claim1 = claims[i]
                claim2 = claims[j]
                
                # Check if claims involve similar entities
                common_entities = set(claim1['entities']) & set(claim2['entities'])
                if not common_entities:
                    continue
                
                # Detect contradiction using multiple methods
                contradiction = self._analyze_claim_pair(claim1, claim2, common_entities)
                
                if contradiction:
                    contradictions.append(contradiction)
        
        # Sort by contradiction score
        contradictions.sort(key=lambda x: x.contradiction_score, reverse=True)
        
        # Cache results
        self.contradiction_cache.extend(contradictions)
        
        logger.info(f"Detected {len(contradictions)} contradictions")
        return contradictions
    
    def _get_claims(self, entity_name: Optional[str], days: int) -> List[Dict]:
        """Retrieve claims from Neo4j"""
        if entity_name:
            query = """
            MATCH (e:Entity {name: $entity_name})<-[:ABOUT]-(c:Claim)
            WHERE c.timestamp >= datetime() - duration({days: $days})
            WITH c, collect(e.name) as entities
            RETURN c.id as id,
                   c.text as text,
                   c.confidence_score as confidence,
                   toString(c.timestamp) as timestamp,
                   entities
            ORDER BY c.timestamp DESC
            LIMIT 100
            """
            params = {"entity_name": entity_name, "days": days}
        else:
            query = """
            MATCH (c:Claim)
            WHERE c.timestamp >= datetime() - duration({days: $days})
            OPTIONAL MATCH (c)-[:ABOUT]->(e:Entity)
            WITH c, collect(e.name) as entities
            WHERE size(entities) > 0
            RETURN c.id as id,
                   c.text as text,
                   c.confidence_score as confidence,
                   toString(c.timestamp) as timestamp,
                   entities
            ORDER BY c.timestamp DESC
            LIMIT 200
            """
            params = {"days": days}
        
        try:
            results = self.neo4j.execute_query(query, params)
            return results
        except Exception as e:
            logger.error(f"Failed to retrieve claims: {e}")
            return []
    
    def _analyze_claim_pair(self, claim1: Dict, claim2: Dict, common_entities: set) -> Optional[Contradiction]:
        """Analyze a pair of claims for contradictions"""
        
        # Skip if same claim or same source at same time
        if claim1['id'] == claim2['id']:
            return None
        
        text1 = claim1['text']
        text2 = claim2['text']
        
        # Method 1: NLI-based detection (most accurate)
        if self.model:
            nli_score = self._detect_nli_contradiction(text1, text2)
            if nli_score > 0.7:  # High confidence contradiction
                return self._create_contradiction(
                    claim1, claim2, nli_score, "semantic", list(common_entities)
                )
        
        # Method 2: Numerical contradiction
        num_contradiction = self._detect_numerical_contradiction(text1, text2)
        if num_contradiction:
            score, explanation = num_contradiction
            contradiction = self._create_contradiction(
                claim1, claim2, score, "numerical", list(common_entities)
            )
            contradiction.explanation = explanation
            return contradiction
        
        # Method 3: Temporal contradiction
        temp_contradiction = self._detect_temporal_contradiction(text1, text2)
        if temp_contradiction:
            score, explanation = temp_contradiction
            contradiction = self._create_contradiction(
                claim1, claim2, score, "temporal", list(common_entities)
            )
            contradiction.explanation = explanation
            return contradiction
        
        # Method 4: Factual contradiction (keywords)
        fact_contradiction = self._detect_factual_contradiction(text1, text2)
        if fact_contradiction:
            score, explanation = fact_contradiction
            contradiction = self._create_contradiction(
                claim1, claim2, score, "factual", list(common_entities)
            )
            contradiction.explanation = explanation
            return contradiction
        
        return None
    
    # ==================== Detection Methods ====================
    
    def _detect_nli_contradiction(self, text1: str, text2: str) -> float:
        """
        Use NLI model to detect contradiction.
        
        Returns:
            Contradiction score (0-1)
        """
        if not self.model:
            return 0.0
        
        try:
            # Cross-encoder returns scores for [contradiction, entailment, neutral]
            scores = self.model.predict([(text1, text2)])
            
            # Convert logits to probabilities
            import torch
            probs = torch.softmax(torch.tensor(scores), dim=0)
            contradiction_prob = probs[0].item()
            
            return contradiction_prob
            
        except Exception as e:
            logger.error(f"NLI detection failed: {e}")
            return 0.0
    
    def _detect_numerical_contradiction(self, text1: str, text2: str) -> Optional[Tuple[float, str]]:
        """Detect contradictions in numerical values"""
        import re
        
        # Extract numbers from both texts
        numbers1 = re.findall(r'\b\d+(?:,\d{3})*(?:\.\d+)?\b', text1)
        numbers2 = re.findall(r'\b\d+(?:,\d{3})*(?:\.\d+)?\b', text2)
        
        if not numbers1 or not numbers2:
            return None
        
        # Convert to floats
        try:
            nums1 = [float(n.replace(',', '')) for n in numbers1]
            nums2 = [float(n.replace(',', '')) for n in numbers2]
        except:
            return None
        
        # Check for significant differences
        for n1 in nums1:
            for n2 in nums2:
                if n1 != n2 and abs(n1 - n2) / max(n1, n2) > 0.2:  # 20% difference
                    return (
                        0.8,
                        f"Numerical discrepancy: {n1} vs {n2}"
                    )
        
        return None
    
    def _detect_temporal_contradiction(self, text1: str, text2: str) -> Optional[Tuple[float, str]]:
        """Detect contradictions in temporal statements"""
        # Keywords indicating temporal contradictions
        before_after_pairs = [
            ('before', 'after'),
            ('earlier', 'later'),
            ('first', 'last'),
            ('previous', 'next'),
            ('past', 'future')
        ]
        
        text1_lower = text1.lower()
        text2_lower = text2.lower()
        
        for word1, word2 in before_after_pairs:
            if word1 in text1_lower and word2 in text2_lower:
                return (
                    0.75,
                    f"Temporal contradiction: '{word1}' vs '{word2}'"
                )
            if word2 in text1_lower and word1 in text2_lower:
                return (
                    0.75,
                    f"Temporal contradiction: '{word2}' vs '{word1}'"
                )
        
        return None
    
    def _detect_factual_contradiction(self, text1: str, text2: str) -> Optional[Tuple[float, str]]:
        """Detect factual contradictions using keywords"""
        # Negation patterns
        negation_indicators = [
            ('is', 'is not'),
            ('was', 'was not'),
            ('has', 'has not'),
            ('did', 'did not'),
            ('will', 'will not'),
            ('can', 'cannot'),
            ('confirmed', 'denied'),
            ('approved', 'rejected'),
            ('agreed', 'disagreed'),
            ('yes', 'no'),
            ('true', 'false')
        ]
        
        text1_lower = text1.lower()
        text2_lower = text2.lower()
        
        for positive, negative in negation_indicators:
            if positive in text1_lower and negative in text2_lower:
                return (
                    0.7,
                    f"Factual contradiction: '{positive}' vs '{negative}'"
                )
            if negative in text1_lower and positive in text2_lower:
                return (
                    0.7,
                    f"Factual contradiction: '{negative}' vs '{positive}'"
                )
        
        return None
    
    # ==================== Contradiction Construction ====================
    
    def _create_contradiction(
        self,
        claim1: Dict,
        claim2: Dict,
        score: float,
        contradiction_type: str,
        entities: List[str]
    ) -> Contradiction:
        """Create a Contradiction object"""
        
        # Determine severity based on score and claim confidence
        avg_confidence = (claim1['confidence'] + claim2['confidence']) / 2
        
        if score > 0.9 and avg_confidence > 0.8:
            severity = "critical"
        elif score > 0.8 or avg_confidence > 0.7:
            severity = "high"
        elif score > 0.7:
            severity = "medium"
        else:
            severity = "low"
        
        return Contradiction(
            claim1_id=claim1['id'],
            claim1_text=claim1['text'],
            claim1_confidence=claim1['confidence'],
            claim1_source="Neo4j",
            claim1_timestamp=claim1['timestamp'],
            claim2_id=claim2['id'],
            claim2_text=claim2['text'],
            claim2_confidence=claim2['confidence'],
            claim2_source="Neo4j",
            claim2_timestamp=claim2['timestamp'],
            contradiction_score=score,
            contradiction_type=contradiction_type,
            entities_involved=entities,
            severity=severity,
            detected_at=datetime.now()
        )
    
    # ==================== Clustering ====================
    
    def cluster_contradictions(self, contradictions: List[Contradiction]) -> List[ContradictionCluster]:
        """
        Group related contradictions into clusters.
        
        Args:
            contradictions: List of contradictions to cluster
        
        Returns:
            List of contradiction clusters
        """
        if not contradictions:
            return []
        
        # Group by common entities
        entity_groups = {}
        for contradiction in contradictions:
            for entity in contradiction.entities_involved:
                if entity not in entity_groups:
                    entity_groups[entity] = []
                entity_groups[entity].append(contradiction)
        
        # Create clusters
        clusters = []
        for entity, entity_contradictions in entity_groups.items():
            if len(entity_contradictions) < 2:
                continue
            
            # Calculate cluster metrics
            cluster_score = sum(c.contradiction_score for c in entity_contradictions) / len(entity_contradictions)
            
            sources = ["Neo4j"]  # Placeholder since claims don't have source property
            
            # Determine impact
            if cluster_score > 0.85 and len(entity_contradictions) >= 3:
                impact = "critical"
            elif cluster_score > 0.75 or len(entity_contradictions) >= 5:
                impact = "high"
            elif cluster_score > 0.65:
                impact = "medium"
            else:
                impact = "low"
            
            cluster = ContradictionCluster(
                cluster_id=f"cluster_{entity}_{datetime.now().strftime('%Y%m%d')}",
                entities=[entity],
                contradictions=entity_contradictions,
                cluster_score=cluster_score,
                impact=impact,
                sources_involved=list(sources),
                time_span=self._calculate_time_span(entity_contradictions)
            )
            clusters.append(cluster)
        
        clusters.sort(key=lambda x: x.cluster_score, reverse=True)
        logger.info(f"Created {len(clusters)} contradiction clusters")
        return clusters
    
    def _calculate_time_span(self, contradictions: List[Contradiction]) -> str:
        """Calculate time span of contradictions"""
        timestamps = []
        for c in contradictions:
            try:
                timestamps.append(datetime.fromisoformat(c.claim1_timestamp))
                timestamps.append(datetime.fromisoformat(c.claim2_timestamp))
            except:
                pass
        
        if len(timestamps) < 2:
            return "unknown"
        
        span = max(timestamps) - min(timestamps)
        days = span.days
        
        if days < 1:
            return "< 1 day"
        elif days == 1:
            return "1 day"
        else:
            return f"{days} days"
    
    # ==================== Reporting ====================
    
    def generate_contradiction_report(self, days: int = 7) -> Dict[str, Any]:
        """Generate comprehensive contradiction report"""
        contradictions = self.detect_contradictions(days=days)
        clusters = self.cluster_contradictions(contradictions)
        
        # Calculate statistics
        severity_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        type_counts = {}
        
        for c in contradictions:
            severity_counts[c.severity] += 1
            type_counts[c.contradiction_type] = type_counts.get(c.contradiction_type, 0) + 1
        
        report = {
            "generated_at": datetime.now().isoformat(),
            "time_period_days": days,
            "summary": {
                "total_contradictions": len(contradictions),
                "total_clusters": len(clusters),
                "critical_contradictions": severity_counts["critical"],
                "high_severity": severity_counts["high"],
                "by_type": type_counts
            },
            "clusters": [c.to_dict() for c in clusters[:10]],  # Top 10 clusters
            "recent_contradictions": [c.to_dict() for c in contradictions[:20]]  # Top 20
        }
        
        return report
    
    def export_contradictions(self, filepath: str, days: int = 7):
        """Export contradictions to JSON file"""
        report = self.generate_contradiction_report(days)
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Exported contradiction report to {filepath}")
    
    # ==================== Integration ====================
    
    def store_contradiction_in_graph(self, contradiction: Contradiction):
        """Store detected contradiction as a relationship in Neo4j"""
        query = """
        MATCH (c1:Claim {id: $claim1_id})
        MATCH (c2:Claim {id: $claim2_id})
        MERGE (c1)-[r:CONTRADICTS]->(c2)
        SET r.score = $score,
            r.type = $type,
            r.severity = $severity,
            r.detected_at = $detected_at
        RETURN r
        """
        
        try:
            self.neo4j.execute_query(
                query,
                {
                    "claim1_id": contradiction.claim1_id,
                    "claim2_id": contradiction.claim2_id,
                    "score": contradiction.contradiction_score,
                    "type": contradiction.contradiction_type,
                    "severity": contradiction.severity,
                    "detected_at": contradiction.detected_at.isoformat()
                }
            )
            logger.debug(f"Stored contradiction in graph: {contradiction.claim1_id} <-> {contradiction.claim2_id}")
        except Exception as e:
            logger.error(f"Failed to store contradiction: {e}")
