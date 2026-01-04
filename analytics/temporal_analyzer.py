"""
Temporal Analysis Module for OSINT Intelligence Platform

Tracks how entities, claims, and relationships evolve over time.
Detects trends, anomalies, and significant changes in the knowledge graph.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict
from dataclasses import dataclass, asdict
from loguru import logger

from graph.neo4j_client import Neo4jClient


@dataclass
class TemporalEvent:
    """Represents a temporal event in the knowledge graph"""
    timestamp: datetime
    event_type: str  # entity_created, claim_created, relationship_created, entity_updated
    entity_id: Optional[str] = None
    entity_name: Optional[str] = None
    entity_type: Optional[str] = None
    claim_id: Optional[str] = None
    claim_text: Optional[str] = None
    confidence: Optional[float] = None
    source: Optional[str] = None
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class TrendAnalysis:
    """Represents a detected trend"""
    entity_name: str
    entity_type: str
    trend_type: str  # increasing_mentions, decreasing_confidence, emerging, declining
    time_period: str  # "24h", "7d", "30d"
    mention_count: int
    confidence_avg: float
    confidence_trend: str  # increasing, decreasing, stable
    first_seen: datetime
    last_seen: datetime
    sources: List[str]
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['first_seen'] = self.first_seen.isoformat()
        data['last_seen'] = self.last_seen.isoformat()
        return data


@dataclass
class AnomalyDetection:
    """Represents a detected anomaly"""
    anomaly_type: str  # sudden_spike, confidence_drop, new_entity_cluster
    entity_name: str
    entity_type: str
    timestamp: datetime
    description: str
    severity: str  # low, medium, high, critical
    metrics: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


class TemporalAnalyzer:
    """
    Analyzes temporal patterns in the knowledge graph.
    
    Features:
    - Track entity/claim evolution over time
    - Detect trends (emerging entities, declining confidence)
    - Identify anomalies (sudden spikes, unusual patterns)
    - Generate timeline visualizations
    - Compute temporal statistics
    """
    
    def __init__(self, neo4j_client: Optional[Neo4jClient] = None):
        """Initialize temporal analyzer"""
        self.neo4j = neo4j_client or Neo4jClient()
        self.events: List[TemporalEvent] = []
        logger.info("Temporal Analyzer initialized")
    
    # ==================== Event Tracking ====================
    
    def record_event(self, event: TemporalEvent):
        """Record a temporal event"""
        self.events.append(event)
    
    def get_recent_events(self, hours: int = 24) -> List[TemporalEvent]:
        """Get events from the last N hours"""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [e for e in self.events if e.timestamp >= cutoff]
    
    # ==================== Trend Detection ====================
    
    def detect_trends(self, time_period: str = "24h") -> List[TrendAnalysis]:
        """
        Detect trends in entity mentions and confidence over time.
        
        Args:
            time_period: Time window ("24h", "7d", "30d")
        
        Returns:
            List of detected trends
        """
        hours = self._parse_time_period(time_period)
        cutoff = datetime.now() - timedelta(hours=hours)
        
        query = """
        MATCH (e:Entity)<-[:ABOUT]-(c:Claim)
        WHERE c.timestamp >= datetime($cutoff)
        WITH e, 
             count(c) as mention_count,
             avg(c.confidence_score) as avg_confidence,
             collect(c.confidence_score) as confidences,
             min(c.timestamp) as first_seen,
             max(c.timestamp) as last_seen
        WHERE mention_count > 0
        RETURN e.name as entity_name,
               e.type as entity_type,
               mention_count,
               avg_confidence,
               confidences,
               toString(first_seen) as first_seen,
               toString(last_seen) as last_seen
        ORDER BY mention_count DESC
        LIMIT 50
        """
        
        try:
            results = self.neo4j.execute_query(
                query,
                {"cutoff": cutoff.isoformat()}
            )
            
            trends = []
            for record in results:
                # Determine trend type
                trend_type = self._classify_trend(
                    record['mention_count'],
                    record['confidences']
                )
                
                # Determine confidence trend
                confidence_trend = self._analyze_confidence_trend(
                    record['confidences']
                )
                
                trend = TrendAnalysis(
                    entity_name=record['entity_name'],
                    entity_type=record['entity_type'],
                    trend_type=trend_type,
                    time_period=time_period,
                    mention_count=record['mention_count'],
                    confidence_avg=record['avg_confidence'],
                    confidence_trend=confidence_trend,
                    first_seen=datetime.fromisoformat(record['first_seen']),
                    last_seen=datetime.fromisoformat(record['last_seen']),
                    sources=['Neo4j']  # Placeholder since source not in schema
                )
                trends.append(trend)
            
            logger.info(f"Detected {len(trends)} trends in {time_period}")
            return trends
            
        except Exception as e:
            logger.error(f"Trend detection failed: {e}")
            return []
    
    def _classify_trend(self, mention_count: int, confidences: List[float]) -> str:
        """Classify trend based on metrics"""
        if mention_count >= 10:
            return "increasing_mentions"
        elif mention_count <= 2:
            return "declining"
        elif len(confidences) >= 5 and confidences[-1] < confidences[0] - 0.2:
            return "decreasing_confidence"
        else:
            return "emerging"
    
    def _analyze_confidence_trend(self, confidences: List[float]) -> str:
        """Analyze trend in confidence scores"""
        if len(confidences) < 2:
            return "stable"
        
        first_half = confidences[:len(confidences)//2]
        second_half = confidences[len(confidences)//2:]
        
        avg_first = sum(first_half) / len(first_half)
        avg_second = sum(second_half) / len(second_half)
        
        diff = avg_second - avg_first
        
        if diff > 0.1:
            return "increasing"
        elif diff < -0.1:
            return "decreasing"
        else:
            return "stable"
    
    # ==================== Anomaly Detection ====================
    
    def detect_anomalies(self, hours: int = 24) -> List[AnomalyDetection]:
        """
        Detect anomalies in temporal patterns.
        
        Looks for:
        - Sudden spikes in entity mentions
        - Confidence drops
        - New entity clusters
        
        Args:
            hours: Time window to analyze
        
        Returns:
            List of detected anomalies
        """
        anomalies = []
        cutoff = datetime.now() - timedelta(hours=hours)
        
        # Detect sudden spikes
        spike_anomalies = self._detect_mention_spikes(cutoff)
        anomalies.extend(spike_anomalies)
        
        # Detect confidence drops
        confidence_anomalies = self._detect_confidence_drops(cutoff)
        anomalies.extend(confidence_anomalies)
        
        # Detect new entity clusters
        cluster_anomalies = self._detect_entity_clusters(cutoff)
        anomalies.extend(cluster_anomalies)
        
        logger.info(f"Detected {len(anomalies)} anomalies in last {hours}h")
        return anomalies
    
    def _detect_mention_spikes(self, cutoff: datetime) -> List[AnomalyDetection]:
        """Detect sudden spikes in entity mentions"""
        query = """
        MATCH (e:Entity)<-[:ABOUT]-(c:Claim)
        WHERE c.timestamp >= datetime($cutoff)
        WITH e, count(c) as recent_count
        WHERE recent_count >= 5
        MATCH (e)<-[:ABOUT]-(c2:Claim)
        WHERE c2.timestamp < datetime($cutoff)
        WITH e, recent_count, count(c2) as historical_count
        WHERE historical_count > 0 AND recent_count > historical_count * 3
        RETURN e.name as entity_name,
               e.type as entity_type,
               recent_count,
               historical_count
        """
        
        try:
            results = self.neo4j.execute_query(
                query,
                {"cutoff": cutoff.isoformat()}
            )
            
            anomalies = []
            for record in results:
                spike_ratio = record['recent_count'] / record['historical_count']
                severity = "critical" if spike_ratio > 5 else "high"
                
                anomaly = AnomalyDetection(
                    anomaly_type="sudden_spike",
                    entity_name=record['entity_name'],
                    entity_type=record['entity_type'],
                    timestamp=datetime.now(),
                    description=f"Entity mentions spiked {spike_ratio:.1f}x above baseline",
                    severity=severity,
                    metrics={
                        "recent_count": record['recent_count'],
                        "historical_count": record['historical_count'],
                        "spike_ratio": spike_ratio
                    }
                )
                anomalies.append(anomaly)
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Spike detection failed: {e}")
            return []
    
    def _detect_confidence_drops(self, cutoff: datetime) -> List[AnomalyDetection]:
        """Detect sudden drops in confidence scores"""
        query = """
        MATCH (e:Entity)<-[:ABOUT]-(c:Claim)
        WHERE c.timestamp >= datetime($cutoff)
        WITH e, avg(c.confidence_score) as recent_confidence
        WHERE recent_confidence < 0.5
        MATCH (e)<-[:ABOUT]-(c2:Claim)
        WHERE c2.timestamp < datetime($cutoff)
        WITH e, recent_confidence, avg(c2.confidence_score) as historical_confidence
        WHERE historical_confidence > 0.7 AND recent_confidence < historical_confidence - 0.3
        RETURN e.name as entity_name,
               e.type as entity_type,
               recent_confidence,
               historical_confidence
        """
        
        try:
            results = self.neo4j.execute_query(
                query,
                {"cutoff": cutoff.isoformat()}
            )
            
            anomalies = []
            for record in results:
                drop = record['historical_confidence'] - record['recent_confidence']
                
                anomaly = AnomalyDetection(
                    anomaly_type="confidence_drop",
                    entity_name=record['entity_name'],
                    entity_type=record['entity_type'],
                    timestamp=datetime.now(),
                    description=f"Confidence dropped {drop:.2f} points",
                    severity="high",
                    metrics={
                        "recent_confidence": record['recent_confidence'],
                        "historical_confidence": record['historical_confidence'],
                        "drop": drop
                    }
                )
                anomalies.append(anomaly)
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Confidence drop detection failed: {e}")
            return []
    
    def _detect_entity_clusters(self, cutoff: datetime) -> List[AnomalyDetection]:
        """Detect new clusters of related entities"""
        query = """
        MATCH (e1:Entity)<-[:ABOUT]-(c:Claim)-[:ABOUT]->(e2:Entity)
        WHERE c.timestamp >= datetime($cutoff) AND e1 <> e2
        WITH e1, count(DISTINCT e2) as new_connections
        WHERE new_connections >= 3
        RETURN e1.name as entity_name,
               e1.type as entity_type,
               new_connections
        ORDER BY new_connections DESC
        LIMIT 10
        """
        
        try:
            results = self.neo4j.execute_query(
                query,
                {"cutoff": cutoff.isoformat()}
            )
            
            anomalies = []
            for record in results:
                severity = "high" if record['new_connections'] >= 10 else "medium"
                
                anomaly = AnomalyDetection(
                    anomaly_type="new_entity_cluster",
                    entity_name=record['entity_name'],
                    entity_type=record['entity_type'],
                    timestamp=datetime.now(),
                    description=f"Formed {record['new_connections']} new connections",
                    severity=severity,
                    metrics={
                        "new_connections": record['new_connections']
                    }
                )
                anomalies.append(anomaly)
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Cluster detection failed: {e}")
            return []
    
    # ==================== Timeline Analysis ====================
    
    def get_entity_timeline(self, entity_name: str, days: int = 30) -> Dict[str, Any]:
        """
        Get complete timeline of an entity's evolution.
        
        Args:
            entity_name: Name of entity to analyze
            days: Number of days to look back
        
        Returns:
            Timeline data with mentions, confidence evolution, relationships
        """
        cutoff = datetime.now() - timedelta(days=days)
        
        query = """
        MATCH (e:Entity {name: $entity_name})
        OPTIONAL MATCH (e)<-[:ABOUT]-(c:Claim)
        WHERE c.timestamp >= datetime($cutoff)
        WITH e, c
        ORDER BY c.timestamp
        RETURN e.name as entity_name,
               e.type as entity_type,
               toString(e.created_at) as created_at,
               collect({
                   timestamp: toString(c.timestamp),
                   claim_text: c.text,
                   confidence: c.confidence_score
               }) as mentions
        """
        
        try:
            results = self.neo4j.execute_query(
                query,
                {
                    "entity_name": entity_name,
                    "cutoff": cutoff.isoformat()
                }
            )
            
            if not results:
                return {}
            
            record = results[0]
            mentions = record['mentions']
            
            # Compute statistics
            confidence_history = [m['confidence'] for m in mentions if m.get('confidence')]
            sources = ['Neo4j']  # Placeholder since source not in schema
            
            timeline = {
                "entity_name": record['entity_name'],
                "entity_type": record['entity_type'],
                "created_at": record['created_at'],
                "total_mentions": len(mentions),
                "unique_sources": len(sources),
                "confidence_avg": sum(confidence_history) / len(confidence_history) if confidence_history else 0,
                "confidence_min": min(confidence_history) if confidence_history else 0,
                "confidence_max": max(confidence_history) if confidence_history else 0,
                "mentions": mentions,
                "sources": sources
            }
            
            return timeline
            
        except Exception as e:
            logger.error(f"Timeline analysis failed: {e}")
            return {}
    
    def get_global_timeline(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get global timeline of all activity.
        
        Args:
            hours: Time window
        
        Returns:
            Chronological list of all events
        """
        cutoff = datetime.now() - timedelta(hours=hours)
        
        query = """
        MATCH (c:Claim)
        WHERE c.timestamp >= datetime($cutoff)
        OPTIONAL MATCH (c)-[:ABOUT]->(e:Entity)
        RETURN toString(c.timestamp) as timestamp,
               c.text as claim_text,
               c.confidence_score as confidence,
               collect(e.name) as entities
        ORDER BY c.timestamp DESC
        """
        
        try:
            results = self.neo4j.execute_query(
                query,
                {"cutoff": cutoff.isoformat()}
            )
            
            timeline = []
            for record in results:
                timeline.append({
                    "timestamp": record['timestamp'],
                    "claim_text": record['claim_text'],
                    "confidence": record['confidence'],
                    "entities": record['entities']
                })
            
            return timeline
            
        except Exception as e:
            logger.error(f"Global timeline failed: {e}")
            return []
    
    # ==================== Statistics ====================
    
    def get_temporal_stats(self, time_period: str = "24h") -> Dict[str, Any]:
        """Get comprehensive temporal statistics"""
        hours = self._parse_time_period(time_period)
        cutoff = datetime.now() - timedelta(hours=hours)
        
        query = """
        MATCH (c:Claim)
        WHERE c.timestamp >= datetime($cutoff)
        WITH count(c) as total_claims
        MATCH (e:Entity)<-[:ABOUT]-(c2:Claim)
        WHERE c2.timestamp >= datetime($cutoff)
        RETURN total_claims,
               0 as new_entities,
               count(DISTINCT e) as active_entities
        """
        
        try:
            results = self.neo4j.execute_query(
                query,
                {"cutoff": cutoff.isoformat()}
            )
            
            if results:
                record = results[0]
                return {
                    "time_period": time_period,
                    "total_claims": record['total_claims'],
                    "new_entities": record['new_entities'],
                    "active_entities": record['active_entities'],
                    "claims_per_hour": record['total_claims'] / hours if hours > 0 else 0
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Temporal stats failed: {e}")
            return {}
    
    # ==================== Utilities ====================
    
    def _parse_time_period(self, time_period: str) -> int:
        """Convert time period string to hours"""
        if time_period == "24h":
            return 24
        elif time_period == "7d":
            return 24 * 7
        elif time_period == "30d":
            return 24 * 30
        else:
            return 24
    
    def export_trends(self, filepath: str, time_period: str = "24h"):
        """Export trend analysis to JSON file"""
        trends = self.detect_trends(time_period)
        data = {
            "time_period": time_period,
            "generated_at": datetime.now().isoformat(),
            "trend_count": len(trends),
            "trends": [t.to_dict() for t in trends]
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Exported {len(trends)} trends to {filepath}")
    
    def export_anomalies(self, filepath: str, hours: int = 24):
        """Export anomaly detection to JSON file"""
        anomalies = self.detect_anomalies(hours)
        data = {
            "time_window_hours": hours,
            "generated_at": datetime.now().isoformat(),
            "anomaly_count": len(anomalies),
            "anomalies": [a.to_dict() for a in anomalies]
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Exported {len(anomalies)} anomalies to {filepath}")
