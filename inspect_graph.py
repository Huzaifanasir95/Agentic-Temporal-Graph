"""
Neo4j Graph Inspection Tool
View what's stored in the knowledge graph
"""

from dotenv import load_dotenv
load_dotenv()

from graph.neo4j_client import Neo4jClient
from loguru import logger


def inspect_graph():
    """Inspect and display graph contents"""
    client = Neo4jClient()
    
    try:
        # Get overall stats
        stats = client.get_stats()
        print(f"\n{'='*60}")
        print(f"Neo4j Knowledge Graph Statistics")
        print(f"{'='*60}")
        print(f"  Entities: {stats.get('entities', 0)}")
        print(f"  Claims: {stats.get('claims', 0)}")
        print(f"  Sources: {stats.get('sources', 0)}")
        print(f"  Events: {stats.get('events', 0)}")
        
        # Show entities
        if stats.get('entities', 0) > 0:
            print(f"\n{'='*60}")
            print(f"Entities")
            print(f"{'='*60}")
            
            query = """
            MATCH (e:Entity)
            RETURN e.id as id, e.name as name, e.type as type, e.confidence as confidence
            ORDER BY e.confidence DESC
            LIMIT 20
            """
            
            with client.driver.session() as session:
                result = session.run(query)
                for i, record in enumerate(result, 1):
                    print(f"  {i}. {record['name']} ({record['type']}) - confidence: {record['confidence']:.2f}")
                    print(f"     ID: {record['id']}")
        
        # Show claims
        if stats.get('claims', 0) > 0:
            print(f"\n{'='*60}")
            print(f"Claims")
            print(f"{'='*60}")
            
            query = """
            MATCH (c:Claim)
            RETURN c.id as id, c.text as text, c.confidence_score as confidence
            ORDER BY c.confidence_score DESC
            LIMIT 10
            """
            
            with client.driver.session() as session:
                result = session.run(query)
                for i, record in enumerate(result, 1):
                    print(f"  {i}. {record['text'][:80]}...")
                    print(f"     Confidence: {record['confidence']:.2f}")
                    print(f"     ID: {record['id']}\n")
        
        # Show sources
        if stats.get('sources', 0) > 0:
            print(f"\n{'='*60}")
            print(f"Sources")
            print(f"{'='*60}")
            
            query = """
            MATCH (s:Source)
            RETURN s.url as url, s.domain as domain, s.credibility_score as credibility, s.title as title
            LIMIT 10
            """
            
            with client.driver.session() as session:
                result = session.run(query)
                for i, record in enumerate(result, 1):
                    print(f"  {i}. {record['title'] or 'Untitled'}")
                    print(f"     Domain: {record['domain']}")
                    print(f"     Credibility: {record['credibility']:.2f}")
                    print(f"     URL: {record['url']}\n")
        
        # Show relationships
        print(f"\n{'='*60}")
        print(f"Relationships")
        print(f"{'='*60}")
        
        query = """
        MATCH ()-[r]->()
        RETURN type(r) as rel_type, count(r) as count
        ORDER BY count DESC
        """
        
        with client.driver.session() as session:
            result = session.run(query)
            relationships = list(result)
            if relationships:
                for record in relationships:
                    print(f"  {record['rel_type']}: {record['count']}")
            else:
                print(f"  No relationships found")
        
        print(f"\n{'='*60}\n")
        
    finally:
        client.close()


if __name__ == "__main__":
    inspect_graph()
