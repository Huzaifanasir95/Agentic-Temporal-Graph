"""Quick test to check Neo4j data"""
from graph.neo4j_client import Neo4jClient

client = Neo4jClient()

# Check claims
result = client.execute_query("MATCH (c:Claim) RETURN count(c) as count")
print(f"Claims in database: {result[0]['count'] if result else 0}")

# Check entities
result = client.execute_query("MATCH (e:Entity) RETURN count(e) as count")
print(f"Entities in database: {result[0]['count'] if result else 0}")

# Check if claims have timestamps
result = client.execute_query("MATCH (c:Claim) WHERE c.timestamp IS NOT NULL RETURN count(c) as count")
print(f"Claims with timestamps: {result[0]['count'] if result else 0}")

# Sample a claim to see its properties
result = client.execute_query("MATCH (c:Claim) RETURN c LIMIT 1")
if result:
    print(f"\nSample claim properties: {dict(result[0]['c'])}")
