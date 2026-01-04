"""
Neo4j Client
Database operations for graph management
"""

from neo4j import GraphDatabase
from typing import List, Dict, Any, Optional
from loguru import logger
import os


class Neo4jClient:
    """Neo4j database client"""
    
    def __init__(
        self,
        uri: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        """Initialize Neo4j client"""
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.username = username or os.getenv("NEO4J_USERNAME", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD")
        
        self.driver = GraphDatabase.driver(
            self.uri,
            auth=(self.username, self.password)
        )
        
        logger.info(f"Neo4j client connected: {self.uri}")
        
    def close(self):
        """Close connection"""
        self.driver.close()
        
    def find_similar_claims(
        self,
        claim_text: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find similar existing claims
        
        Args:
            claim_text: Claim to search for
            limit: Max results
            
        Returns:
            List of similar claims
        """
        query = """
        MATCH (c:Claim)
        WHERE c.text CONTAINS $keyword
        RETURN c.id as id, c.text as text, c.confidence_score as confidence, 
               c.timestamp as timestamp
        LIMIT $limit
        """
        
        # Extract keywords (simple approach)
        keywords = claim_text.split()[:3]  # First 3 words
        keyword = " ".join(keywords)
        
        with self.driver.session() as session:
            result = session.run(query, keyword=keyword, limit=limit)
            return [dict(record) for record in result]
            
    def find_contradictory_claims(
        self,
        claim_id: str
    ) -> List[Dict[str, Any]]:
        """
        Find claims that contradict given claim
        
        Args:
            claim_id: Claim ID
            
        Returns:
            List of contradictory claims
        """
        query = """
        MATCH (c1:Claim {id: $claim_id})-[r:CONTRADICTS]-(c2:Claim)
        RETURN c2.id as id, c2.text as text, r.confidence as confidence
        """
        
        with self.driver.session() as session:
            result = session.run(query, claim_id=claim_id)
            return [dict(record) for record in result]
            
    def create_entity(self, entity: Dict[str, Any]) -> None:
        """
        Create or update entity node
        
        Args:
            entity: Entity dict
        """
        query = """
        MERGE (e:Entity {id: $id})
        SET e.name = $name,
            e.type = $type,
            e.confidence = $confidence,
            e.last_updated = datetime()
        RETURN e.id as id
        """
        
        with self.driver.session() as session:
            session.run(
                query,
                id=entity['id'],
                name=entity['name'],
                type=entity['type'],
                confidence=entity.get('confidence', 0.8)
            )
            
    def create_claim(self, claim: Dict[str, Any]) -> None:
        """
        Create claim node
        
        Args:
            claim: Claim dict
        """
        query = """
        MERGE (c:Claim {id: $id})
        SET c.text = $text,
            c.context = $context,
            c.confidence_score = $confidence,
            c.timestamp = datetime(),
            c.verification_status = 'UNVERIFIED'
        RETURN c.id as id
        """
        
        with self.driver.session() as session:
            session.run(
                query,
                id=claim['id'],
                text=claim['text'],
                context=claim.get('context', ''),
                confidence=claim.get('confidence', 0.7)
            )
            
    def create_source(self, source: Dict[str, Any]) -> None:
        """
        Create source node
        
        Args:
            source: Source dict
        """
        query = """
        MERGE (s:Source {url: $url})
        SET s.domain = $domain,
            s.type = $type,
            s.credibility_score = $credibility,
            s.title = $title
        RETURN s.url as url
        """
        
        with self.driver.session() as session:
            session.run(
                query,
                url=source.get('url', ''),
                domain=source.get('source_name', ''),
                type=source.get('source_type', 'unknown'),
                credibility=source.get('credibility_score', 0.5),
                title=source.get('title', '')
            )
            
    def link_claim_to_entity(self, claim_id: str, entity_id: str) -> None:
        """Link claim to entity"""
        query = """
        MATCH (c:Claim {id: $claim_id})
        MATCH (e:Entity {id: $entity_id})
        MERGE (c)-[:ABOUT]->(e)
        """
        
        with self.driver.session() as session:
            session.run(query, claim_id=claim_id, entity_id=entity_id)
            
    def link_claim_contradiction(
        self,
        claim1_id: str,
        claim2_id: str,
        confidence: float
    ) -> None:
        """Link two contradictory claims"""
        query = """
        MATCH (c1:Claim {id: $claim1_id})
        MATCH (c2:Claim {id: $claim2_id})
        MERGE (c1)-[r:CONTRADICTS]-(c2)
        SET r.confidence = $confidence,
            r.detected_at = datetime()
        """
        
        with self.driver.session() as session:
            session.run(
                query,
                claim1_id=claim1_id,
                claim2_id=claim2_id,
                confidence=confidence
            )
            
    def get_stats(self) -> Dict[str, int]:
        """Get database statistics"""
        query = """
        OPTIONAL MATCH (e:Entity)
        WITH count(e) as entities
        OPTIONAL MATCH (c:Claim)
        WITH entities, count(c) as claims
        OPTIONAL MATCH (s:Source)
        WITH entities, claims, count(s) as sources
        OPTIONAL MATCH (ev:Event)
        WITH entities, claims, sources, count(ev) as events
        RETURN entities, claims, sources, events
        """
        
        with self.driver.session() as session:
            result = session.run(query)
            record = result.single()
            return dict(record) if record else {}


if __name__ == "__main__":
    # Test Neo4j client
    from dotenv import load_dotenv
    load_dotenv()
    
    client = Neo4jClient()
    
    try:
        stats = client.get_stats()
        print(f"\n✓ Neo4j Connection Test")
        print(f"  Entities: {stats.get('entities', 0)}")
        print(f"  Claims: {stats.get('claims', 0)}")
        print(f"  Sources: {stats.get('sources', 0)}")
        print(f"  Events: {stats.get('events', 0)}")
        
    finally:
        client.close()
