"""
Source Credibility Scoring Module for OSINT Intelligence Platform

Evaluates source reliability based on:
- Historical accuracy
- Bias patterns
- Cross-validation with other sources
- Claim consistency
- Contradiction frequency
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
from loguru import logger

from graph.neo4j_client import Neo4jClient


@dataclass
class SourceCredibility:
    """Credibility score for a news source"""
    source_name: str
    overall_score: float  # 0-100
    accuracy_score: float  # 0-100
    consistency_score: float  # 0-100
    bias_score: float  # 0-100 (higher = less biased)
    reliability_score: float  # 0-100
    
    # Statistics
    total_claims: int
    contradicted_claims: int
    cross_validated_claims: int
    average_confidence: float
    
    # Trends
    score_trend: str  # improving, declining, stable
    last_updated: datetime
    
    # Details
    strengths: List[str]
    weaknesses: List[str]
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['last_updated'] = self.last_updated.isoformat()
        return data


@dataclass
class SourceComparison:
    """Comparison between multiple sources on the same topic"""
    topic: str
    sources: List[str]
    agreement_score: float  # 0-1, how much sources agree
    divergence_points: List[str]  # What they disagree on
    most_credible_source: str
    least_credible_source: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


class CredibilityScorer:
    """
    Evaluates and scores source credibility.
    
    Scoring Factors:
    1. Accuracy (40%): How often their claims are corroborated
    2. Consistency (25%): Internal consistency, no self-contradictions
    3. Bias (20%): Balanced reporting, diverse perspectives
    4. Reliability (15%): Regular updates, source diversity
    
    Score Ranges:
    - 90-100: Highly Credible
    - 75-89: Credible
    - 60-74: Moderately Credible
    - 40-59: Questionable
    - 0-39: Not Credible
    """
    
    def __init__(self, neo4j_client: Optional[Neo4jClient] = None):
        """Initialize credibility scorer"""
        self.neo4j = neo4j_client or Neo4jClient()
        self.source_cache: Dict[str, SourceCredibility] = {}
        logger.info("Credibility Scorer initialized")
    
    # ==================== Main Scoring ====================
    
    def score_source(self, source_name: str, days: int = 30) -> SourceCredibility:
        """
        Calculate comprehensive credibility score for a source.
        
        Args:
            source_name: Name of the source to evaluate
            days: Number of days of history to consider
        
        Returns:
            SourceCredibility object with detailed scores
        """
        logger.info(f"Scoring source: {source_name}")
        
        # Get source data
        source_data = self._get_source_data(source_name, days)
        
        if not source_data:
            logger.warning(f"No data found for source: {source_name}")
            return self._create_default_score(source_name)
        
        # Calculate individual scores
        accuracy_score = self._calculate_accuracy(source_data)
        consistency_score = self._calculate_consistency(source_data)
        bias_score = self._calculate_bias(source_data)
        reliability_score = self._calculate_reliability(source_data)
        
        # Calculate weighted overall score
        overall_score = (
            accuracy_score * 0.40 +
            consistency_score * 0.25 +
            bias_score * 0.20 +
            reliability_score * 0.15
        )
        
        # Determine trend
        score_trend = self._determine_trend(source_name, overall_score)
        
        # Identify strengths and weaknesses
        strengths, weaknesses = self._identify_strengths_weaknesses(
            accuracy_score, consistency_score, bias_score, reliability_score
        )
        
        # Create credibility object
        credibility = SourceCredibility(
            source_name=source_name,
            overall_score=round(overall_score, 2),
            accuracy_score=round(accuracy_score, 2),
            consistency_score=round(consistency_score, 2),
            bias_score=round(bias_score, 2),
            reliability_score=round(reliability_score, 2),
            total_claims=source_data['total_claims'],
            contradicted_claims=source_data['contradicted_claims'],
            cross_validated_claims=source_data['cross_validated_claims'],
            average_confidence=source_data['avg_confidence'],
            score_trend=score_trend,
            last_updated=datetime.now(),
            strengths=strengths,
            weaknesses=weaknesses
        )
        
        # Cache result
        self.source_cache[source_name] = credibility
        
        return credibility
    
    def score_all_sources(self, days: int = 30) -> Dict[str, SourceCredibility]:
        """Score all sources in the database"""
        sources = self._get_all_sources()
        
        credibility_scores = {}
        for source in sources:
            credibility_scores[source] = self.score_source(source, days)
        
        logger.info(f"Scored {len(credibility_scores)} sources")
        return credibility_scores
    
    # ==================== Data Retrieval ====================
    
    def _get_source_data(self, source_name: str, days: int) -> Optional[Dict]:
        """Get comprehensive data for an entity (treated as source)"""
        cutoff = datetime.now() - timedelta(days=days)
        
        query = """
        MATCH (e:Entity {name: $source_name})<-[:ABOUT]-(c:Claim)
        WHERE c.timestamp >= datetime($cutoff)
        WITH count(c) as total_claims,
             avg(c.confidence_score) as avg_confidence,
             collect(c) as claims
        
        // Find contradicted claims
        UNWIND claims as claim
        OPTIONAL MATCH (claim)-[:CONTRADICTS]-(other)
        WITH total_claims, avg_confidence, claims,
             count(DISTINCT other) as contradicted_claims
        
        // Count related entities (cross-validation proxy)
        UNWIND claims as c
        OPTIONAL MATCH (c)-[:ABOUT]->(e2:Entity)
        WHERE e2.name <> $source_name
        WITH total_claims, avg_confidence, contradicted_claims,
             count(DISTINCT e2) as cross_validated_claims
        
        RETURN total_claims,
               avg_confidence,
               contradicted_claims,
               cross_validated_claims
        """
        
        try:
            results = self.neo4j.execute_query(
                query,
                {
                    "source_name": source_name,
                    "cutoff": cutoff.isoformat()
                }
            )
            
            if results and results[0]['total_claims'] > 0:
                return results[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get source data: {e}")
            return None
    
    def _get_all_sources(self) -> List[str]:
        """Get list of all entities with claims (treating them as sources)"""
        query = """
        MATCH (e:Entity)<-[:ABOUT]-(c:Claim)
        WITH e.name as source, count(c) as claim_count
        WHERE claim_count > 0
        RETURN DISTINCT source
        ORDER BY claim_count DESC
        LIMIT 50
        """
        
        try:
            results = self.neo4j.execute_query(query, {})
            return [r['source'] for r in results if r['source']]
        except Exception as e:
            logger.error(f"Failed to get sources: {e}")
            return []
    
    # ==================== Score Calculation ====================
    
    def _calculate_accuracy(self, source_data: Dict) -> float:
        """
        Calculate accuracy score based on cross-validation.
        
        Accuracy = (cross_validated_claims / total_claims) * 100
        Penalty for contradictions: -5 points per contradiction
        """
        total = source_data['total_claims']
        validated = source_data['cross_validated_claims']
        contradicted = source_data['contradicted_claims']
        
        if total == 0:
            return 50.0  # Neutral score for no data
        
        # Base accuracy from cross-validation
        validation_rate = validated / total
        base_score = validation_rate * 100
        
        # Apply contradiction penalty
        contradiction_penalty = min(contradicted * 5, 30)  # Max 30 point penalty
        
        final_score = max(base_score - contradiction_penalty, 0)
        return min(final_score, 100)
    
    def _calculate_consistency(self, source_data: Dict) -> float:
        """
        Calculate consistency score.
        
        Consistency = 100 - (contradictions / total_claims * 100)
        Bonus for high confidence: +10 points if avg_confidence > 0.8
        """
        total = source_data['total_claims']
        contradicted = source_data['contradicted_claims']
        avg_confidence = source_data['avg_confidence']
        
        if total == 0:
            return 50.0
        
        # Base consistency (fewer contradictions = higher score)
        contradiction_rate = contradicted / total
        base_score = (1 - contradiction_rate) * 100
        
        # Confidence bonus
        confidence_bonus = 10 if avg_confidence > 0.8 else 0
        
        final_score = min(base_score + confidence_bonus, 100)
        return final_score
    
    def _calculate_bias(self, source_data: Dict) -> float:
        """
        Calculate bias score (higher = less biased).
        
        Uses cross-validation as proxy for balanced reporting.
        More cross-validation = more perspectives = less bias
        """
        total = source_data['total_claims']
        validated = source_data['cross_validated_claims']
        
        if total == 0:
            return 50.0
        
        # Sources with many cross-validated claims likely cover mainstream topics
        # objectively, reducing bias
        validation_rate = validated / total
        
        # Bias score: high validation = low bias
        bias_score = 50 + (validation_rate * 50)  # Scale from 50-100
        
        return min(bias_score, 100)
    
    def _calculate_reliability(self, source_data: Dict) -> float:
        """
        Calculate reliability score.
        
        Based on:
        - Volume of claims (regular reporting)
        - Average confidence
        """
        total = source_data['total_claims']
        avg_confidence = source_data['avg_confidence']
        
        # Volume score (more claims = more reliable)
        # Scale: 0-10 claims = 50-75, 10-50 = 75-90, 50+ = 90-100
        if total < 10:
            volume_score = 50 + (total * 2.5)
        elif total < 50:
            volume_score = 75 + ((total - 10) * 0.375)
        else:
            volume_score = 90 + min((total - 50) * 0.1, 10)
        
        # Confidence contribution
        confidence_score = avg_confidence * 100
        
        # Weighted average
        reliability = (volume_score * 0.6) + (confidence_score * 0.4)
        
        return min(reliability, 100)
    
    # ==================== Trend Analysis ====================
    
    def _determine_trend(self, source_name: str, current_score: float) -> str:
        """Determine if credibility is improving, declining, or stable"""
        
        # Check if we have cached historical score
        if source_name in self.source_cache:
            previous_score = self.source_cache[source_name].overall_score
            diff = current_score - previous_score
            
            if diff > 5:
                return "improving"
            elif diff < -5:
                return "declining"
            else:
                return "stable"
        
        # No historical data, assume stable
        return "stable"
    
    def _identify_strengths_weaknesses(
        self,
        accuracy: float,
        consistency: float,
        bias: float,
        reliability: float
    ) -> Tuple[List[str], List[str]]:
        """Identify source strengths and weaknesses"""
        
        scores = {
            "accuracy": accuracy,
            "consistency": consistency,
            "bias": bias,
            "reliability": reliability
        }
        
        strengths = []
        weaknesses = []
        
        for metric, score in scores.items():
            if score >= 80:
                strengths.append(f"High {metric} ({score:.1f}/100)")
            elif score < 60:
                weaknesses.append(f"Low {metric} ({score:.1f}/100)")
        
        # Add specific observations
        if consistency >= 90:
            strengths.append("Very consistent reporting")
        if accuracy >= 85:
            strengths.append("Well cross-validated claims")
        if bias >= 80:
            strengths.append("Balanced perspectives")
        
        if consistency < 60:
            weaknesses.append("Frequent self-contradictions")
        if accuracy < 50:
            weaknesses.append("Many claims lack corroboration")
        if reliability < 60:
            weaknesses.append("Limited reporting volume")
        
        return strengths, weaknesses
    
    def _create_default_score(self, source_name: str) -> SourceCredibility:
        """Create default score for sources with no data"""
        return SourceCredibility(
            source_name=source_name,
            overall_score=50.0,
            accuracy_score=50.0,
            consistency_score=50.0,
            bias_score=50.0,
            reliability_score=50.0,
            total_claims=0,
            contradicted_claims=0,
            cross_validated_claims=0,
            average_confidence=0.0,
            score_trend="stable",
            last_updated=datetime.now(),
            strengths=[],
            weaknesses=["Insufficient data for scoring"]
        )
    
    # ==================== Source Comparison ====================
    
    def compare_sources(self, entity_name: str, days: int = 30) -> Optional[SourceComparison]:
        """
        Compare how different sources report on the same entity.
        
        Args:
            entity_name: Entity to analyze
            days: Time window
        
        Returns:
            SourceComparison object
        """
        query = """
        MATCH (e:Entity {name: $entity_name})<-[:ABOUT]-(c:Claim)-[:ABOUT]->(e2:Entity)
        WHERE c.timestamp >= datetime($cutoff) AND e <> e2
        WITH e2.name as related_entity, collect(c.text) as claims, avg(c.confidence_score) as avg_conf
        WHERE related_entity IS NOT NULL
        RETURN related_entity as source, claims, avg_conf as confidence
        ORDER BY avg_conf DESC
        LIMIT 20
        """
        
        cutoff = datetime.now() - timedelta(days=days)
        
        try:
            results = self.neo4j.execute_query(
                query,
                {
                    "entity_name": entity_name,
                    "cutoff": cutoff.isoformat()
                }
            )
            
            if len(results) < 2:
                return None
            
            sources = [r['source'] for r in results]
            
            # Calculate agreement (simplified - would use NLI in production)
            # For now, just check if sources mention similar keywords
            all_claims = [claim for r in results for claim in r['claims']]
            agreement_score = self._calculate_agreement(all_claims)
            
            # Get credibility scores for ranking
            source_scores = {}
            for source in sources:
                if source not in self.source_cache:
                    self.score_source(source, days)
                source_scores[source] = self.source_cache[source].overall_score
            
            # Rank sources
            ranked_sources = sorted(source_scores.items(), key=lambda x: x[1], reverse=True)
            
            comparison = SourceComparison(
                topic=entity_name,
                sources=sources,
                agreement_score=agreement_score,
                divergence_points=["Requires detailed NLI analysis"],  # Placeholder
                most_credible_source=ranked_sources[0][0] if ranked_sources else "",
                least_credible_source=ranked_sources[-1][0] if ranked_sources else ""
            )
            
            return comparison
            
        except Exception as e:
            logger.error(f"Source comparison failed: {e}")
            return None
    
    def _calculate_agreement(self, claims: List[str]) -> float:
        """Calculate agreement score between claims"""
        # Simplified version - would use semantic similarity in production
        if len(claims) < 2:
            return 1.0
        
        # For now, return moderate agreement as placeholder
        return 0.7
    
    # ==================== Reporting ====================
    
    def generate_credibility_report(self, days: int = 30) -> Dict[str, Any]:
        """Generate comprehensive credibility report for all sources"""
        all_scores = self.score_all_sources(days)
        
        # Categorize sources
        highly_credible = []
        credible = []
        questionable = []
        not_credible = []
        
        for source, score in all_scores.items():
            if score.overall_score >= 90:
                highly_credible.append(source)
            elif score.overall_score >= 75:
                credible.append(source)
            elif score.overall_score >= 60:
                questionable.append(source)
            else:
                not_credible.append(source)
        
        # Calculate statistics
        scores_list = [s.overall_score for s in all_scores.values()]
        avg_score = sum(scores_list) / len(scores_list) if scores_list else 0
        
        report = {
            "generated_at": datetime.now().isoformat(),
            "time_period_days": days,
            "summary": {
                "total_sources": len(all_scores),
                "average_credibility": round(avg_score, 2),
                "highly_credible_count": len(highly_credible),
                "credible_count": len(credible),
                "questionable_count": len(questionable),
                "not_credible_count": len(not_credible)
            },
            "categories": {
                "highly_credible": highly_credible,
                "credible": credible,
                "questionable": questionable,
                "not_credible": not_credible
            },
            "detailed_scores": {
                source: score.to_dict() 
                for source, score in sorted(
                    all_scores.items(),
                    key=lambda x: x[1].overall_score,
                    reverse=True
                )
            }
        }
        
        return report
    
    def export_credibility_scores(self, filepath: str, days: int = 30):
        """Export credibility report to JSON file"""
        report = self.generate_credibility_report(days)
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Exported credibility report to {filepath}")
    
    # ==================== Integration ====================
    
    def store_credibility_in_graph(self, credibility: SourceCredibility):
        """Store credibility score in Neo4j"""
        query = """
        MERGE (s:Source {name: $source_name})
        SET s.credibility_score = $overall_score,
            s.accuracy_score = $accuracy_score,
            s.consistency_score = $consistency_score,
            s.bias_score = $bias_score,
            s.reliability_score = $reliability_score,
            s.total_claims = $total_claims,
            s.last_scored = $last_updated
        RETURN s
        """
        
        try:
            self.neo4j.execute_query(
                query,
                {
                    "source_name": credibility.source_name,
                    "overall_score": credibility.overall_score,
                    "accuracy_score": credibility.accuracy_score,
                    "consistency_score": credibility.consistency_score,
                    "bias_score": credibility.bias_score,
                    "reliability_score": credibility.reliability_score,
                    "total_claims": credibility.total_claims,
                    "last_updated": credibility.last_updated.isoformat()
                }
            )
            logger.debug(f"Stored credibility for {credibility.source_name}")
        except Exception as e:
            logger.error(f"Failed to store credibility: {e}")
    
    def get_credibility_rating(self, score: float) -> str:
        """Convert numerical score to rating"""
        if score >= 90:
            return "Highly Credible"
        elif score >= 75:
            return "Credible"
        elif score >= 60:
            return "Moderately Credible"
        elif score >= 40:
            return "Questionable"
        else:
            return "Not Credible"
