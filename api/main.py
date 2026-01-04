"""
REST API for OSINT Knowledge Graph
Query entities, claims, sources, and relationships
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from dotenv import load_dotenv
load_dotenv()

from graph.neo4j_client import Neo4jClient
from analytics.temporal_analyzer import TemporalAnalyzer
from analytics.contradiction_detector import ContradictionDetector
from analytics.credibility_scorer import CredibilityScorer
from loguru import logger

app = FastAPI(
    title="OSINT Knowledge Graph API",
    description="Query and explore the temporal OSINT knowledge graph",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Neo4j client
neo4j_client = Neo4jClient()

# Analytics components (Phase 4B)
temporal_analyzer = TemporalAnalyzer(neo4j_client)
contradiction_detector = ContradictionDetector(neo4j_client)
credibility_scorer = CredibilityScorer(neo4j_client)


# Response models
class Entity(BaseModel):
    id: str
    name: str
    type: str
    confidence: float

class Claim(BaseModel):
    id: str
    text: str
    confidence: float
    
class Source(BaseModel):
    domain: str
    credibility: float
    url: Optional[str]

class GraphStats(BaseModel):
    entities: int
    claims: int
    sources: int
    events: int


@app.get("/", tags=["Status"])
async def root():
    """API status"""
    return {
        "status": "operational",
        "service": "OSINT Knowledge Graph API",
        "version": "1.0.0"
    }


@app.get("/stats", response_model=GraphStats, tags=["Analytics"])
async def get_stats():
    """Get knowledge graph statistics"""
    try:
        stats = neo4j_client.get_stats()
        return GraphStats(**stats)
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/entities", response_model=List[Entity], tags=["Entities"])
async def search_entities(
    name: Optional[str] = Query(None, description="Search by name"),
    type: Optional[str] = Query(None, description="Filter by type"),
    limit: int = Query(50, ge=1, le=500)
):
    """Search entities in knowledge graph"""
    try:
        query = "MATCH (e:Entity) "
        params = {}
        
        conditions = []
        if name:
            conditions.append("toLower(e.name) CONTAINS toLower($name)")
            params['name'] = name
        if type:
            conditions.append("e.type = $type")
            params['type'] = type
            
        if conditions:
            query += "WHERE " + " AND ".join(conditions) + " "
            
        query += "RETURN e.id as id, e.name as name, e.type as type, e.confidence as confidence "
        query += "ORDER BY e.confidence DESC LIMIT $limit"
        params['limit'] = limit
        
        with neo4j_client.driver.session() as session:
            result = session.run(query, **params)
            return [Entity(**dict(r)) for r in result]
            
    except Exception as e:
        logger.error(f"Entity search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/claims", response_model=List[Claim], tags=["Claims"])
async def search_claims(
    text: Optional[str] = Query(None, description="Search claim text"),
    min_confidence: float = Query(0.0, ge=0.0, le=1.0),
    limit: int = Query(50, ge=1, le=500)
):
    """Search claims in knowledge graph"""
    try:
        query = "MATCH (c:Claim) "
        params = {'min_confidence': min_confidence, 'limit': limit}
        
        if text:
            query += "WHERE toLower(c.text) CONTAINS toLower($text) AND c.confidence_score >= $min_confidence "
            params['text'] = text
        else:
            query += "WHERE c.confidence_score >= $min_confidence "
            
        query += "RETURN c.id as id, c.text as text, c.confidence_score as confidence "
        query += "ORDER BY c.confidence_score DESC LIMIT $limit"
        
        with neo4j_client.driver.session() as session:
            result = session.run(query, **params)
            return [Claim(**dict(r)) for r in result]
            
    except Exception as e:
        logger.error(f"Claim search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/entity/{entity_id}/claims", tags=["Relationships"])
async def get_entity_claims(entity_id: str):
    """Get all claims about an entity"""
    try:
        query = """
        MATCH (e:Entity {id: $entity_id})<-[:ABOUT|MENTIONS]-(c:Claim)
        RETURN c.id as id, c.text as text, c.confidence_score as confidence
        ORDER BY c.confidence_score DESC
        """
        
        with neo4j_client.driver.session() as session:
            result = session.run(query, entity_id=entity_id)
            claims = [dict(r) for r in result]
            
            if not claims:
                raise HTTPException(status_code=404, detail="Entity not found or no claims")
                
            return {"entity_id": entity_id, "claims": claims}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Entity claims error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/claim/{claim_id}/entities", tags=["Relationships"])
async def get_claim_entities(claim_id: str):
    """Get all entities mentioned in a claim"""
    try:
        query = """
        MATCH (c:Claim {id: $claim_id})-[:ABOUT|MENTIONS]->(e:Entity)
        RETURN e.id as id, e.name as name, e.type as type, e.confidence as confidence
        """
        
        with neo4j_client.driver.session() as session:
            result = session.run(query, claim_id=claim_id)
            entities = [dict(r) for r in result]
            
            if not entities:
                raise HTTPException(status_code=404, detail="Claim not found or no entities")
                
            return {"claim_id": claim_id, "entities": entities}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Claim entities error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sources", response_model=List[Dict[str, Any]], tags=["Sources"])
async def get_sources(limit: int = Query(50, ge=1, le=500)):
    """Get all sources"""
    try:
        query = """
        MATCH (s:Source)
        RETURN s.domain as domain, s.credibility_score as credibility, 
               s.url as url, s.title as title
        ORDER BY s.credibility_score DESC
        LIMIT $limit
        """
        
        with neo4j_client.driver.session() as session:
            result = session.run(query, limit=limit)
            return [dict(r) for r in result]
            
    except Exception as e:
        logger.error(f"Sources error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/network/{entity_name}", tags=["Analytics"])
async def get_entity_network(entity_name: str, depth: int = Query(2, ge=1, le=3)):
    """Get entity network (related entities through claims)"""
    try:
        query = """
        MATCH path = (e1:Entity)-[:ABOUT|MENTIONS*1..{depth}]-(e2:Entity)
        WHERE toLower(e1.name) CONTAINS toLower($name)
        RETURN DISTINCT e2.id as id, e2.name as name, e2.type as type
        LIMIT 20
        """.replace("{depth}", str(depth * 2))
        
        with neo4j_client.driver.session() as session:
            result = session.run(query, name=entity_name)
            return [dict(r) for r in result]
            
    except Exception as e:
        logger.error(f"Network error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    neo4j_client.close()


# ==================== Phase 4B: Enhanced Analytics Endpoints ====================

@app.get("/analytics/trends", tags=["Analytics"])
async def get_trends(time_period: str = Query("24h", regex="^(24h|7d|30d)$")):
    """
    Get temporal trends for entities
    
    Args:
        time_period: Time window (24h, 7d, 30d)
    
    Returns:
        List of detected trends with metrics
    """
    try:
        trends = temporal_analyzer.detect_trends(time_period=time_period)
        return {
            "time_period": time_period,
            "trend_count": len(trends),
            "trends": [t.to_dict() for t in trends]
        }
    except Exception as e:
        logger.error(f"Trends endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/anomalies", tags=["Analytics"])
async def get_anomalies(hours: int = Query(24, ge=1, le=168)):
    """
    Get detected anomalies in temporal patterns
    
    Args:
        hours: Time window in hours (1-168)
    
    Returns:
        List of detected anomalies
    """
    try:
        anomalies = temporal_analyzer.detect_anomalies(hours=hours)
        return {
            "time_window_hours": hours,
            "anomaly_count": len(anomalies),
            "anomalies": [a.to_dict() for a in anomalies]
        }
    except Exception as e:
        logger.error(f"Anomalies endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/entity-timeline/{entity_name}", tags=["Analytics"])
async def get_entity_timeline(entity_name: str, days: int = Query(30, ge=1, le=365)):
    """
    Get complete timeline of an entity's evolution
    
    Args:
        entity_name: Name of entity
        days: Number of days to look back
    
    Returns:
        Timeline data with mentions and metrics
    """
    try:
        timeline = temporal_analyzer.get_entity_timeline(entity_name, days)
        if not timeline:
            raise HTTPException(status_code=404, detail="Entity not found or no timeline data")
        return timeline
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Entity timeline endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/contradictions", tags=["Analytics"])
async def get_contradictions(
    entity_name: Optional[str] = None,
    days: int = Query(7, ge=1, le=90)
):
    """
    Get detected contradictions between claims
    
    Args:
        entity_name: Optional - filter by entity
        days: Number of days to analyze
    
    Returns:
        List of contradictions with severity scores
    """
    try:
        contradictions = contradiction_detector.detect_contradictions(
            entity_name=entity_name,
            days=days
        )
        return {
            "days_analyzed": days,
            "entity_filter": entity_name,
            "contradiction_count": len(contradictions),
            "contradictions": [c.to_dict() for c in contradictions[:50]]  # Limit to 50
        }
    except Exception as e:
        logger.error(f"Contradictions endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/contradiction-report", tags=["Analytics"])
async def get_contradiction_report(days: int = Query(7, ge=1, le=90)):
    """
    Get comprehensive contradiction report with clustering
    
    Args:
        days: Number of days to analyze
    
    Returns:
        Detailed contradiction report with clusters
    """
    try:
        report = contradiction_detector.generate_contradiction_report(days)
        return report
    except Exception as e:
        logger.error(f"Contradiction report endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/credibility", tags=["Analytics"])
async def get_source_credibility(
    source_name: Optional[str] = None,
    days: int = Query(30, ge=1, le=365)
):
    """
    Get source credibility scores
    
    Args:
        source_name: Optional - specific source to score
        days: Number of days of history to consider
    
    Returns:
        Credibility scores for source(s)
    """
    try:
        if source_name:
            # Single source
            score = credibility_scorer.score_source(source_name, days)
            return {
                "source": source_name,
                "score": score.to_dict()
            }
        else:
            # All sources
            scores = credibility_scorer.score_all_sources(days)
            return {
                "days_analyzed": days,
                "source_count": len(scores),
                "sources": {name: score.to_dict() for name, score in scores.items()}
            }
    except Exception as e:
        logger.error(f"Credibility endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/credibility-report", tags=["Analytics"])
async def get_credibility_report(days: int = Query(30, ge=1, le=365)):
    """
    Get comprehensive source credibility report
    
    Args:
        days: Number of days to analyze
    
    Returns:
        Detailed credibility report with categorization
    """
    try:
        report = credibility_scorer.generate_credibility_report(days)
        return report
    except Exception as e:
        logger.error(f"Credibility report endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/temporal-stats", tags=["Analytics"])
async def get_temporal_stats(time_period: str = Query("24h", regex="^(24h|7d|30d)$")):
    """
    Get temporal statistics for the knowledge graph
    
    Args:
        time_period: Time window (24h, 7d, 30d)
    
    Returns:
        Comprehensive temporal statistics
    """
    try:
        stats = temporal_analyzer.get_temporal_stats(time_period)
        return stats
    except Exception as e:
        logger.error(f"Temporal stats endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/source-comparison/{entity_name}", tags=["Analytics"])
async def compare_sources_on_entity(
    entity_name: str,
    days: int = Query(30, ge=1, le=365)
):
    """
    Compare how different sources report on the same entity
    
    Args:
        entity_name: Entity to analyze
        days: Time window
    
    Returns:
        Source comparison with agreement scores
    """
    try:
        comparison = credibility_scorer.compare_sources(entity_name, days)
        if not comparison:
            raise HTTPException(
                status_code=404,
                detail="Not enough sources found for comparison"
            )
        return comparison.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Source comparison endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
