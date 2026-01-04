"""Check Neo4j database structure"""
from graph.neo4j_client import Neo4jClient

client = Neo4jClient()

# Check relationship types
print("=== Relationship Types ===")
result = client.execute_query("""
MATCH ()-[r]->()
RETURN DISTINCT type(r) as rel_type, count(*) as count
ORDER BY count DESC
""")
for r in result:
    print(f"{r['rel_type']}: {r['count']}")

print("\n=== Entity->Claim Relationships ===")
result = client.execute_query("""
MATCH (e:Entity)-[r]->(c:Claim)
RETURN type(r) as rel_type, count(*) as count
LIMIT 5
""")
for r in result:
    print(f"{r['rel_type']}: {r['count']}")

print("\n=== Sample Claim Properties ===")
result = client.execute_query("""
MATCH (c:Claim)
RETURN c.id, c.text, c.timestamp, c.source, c.confidence_score
LIMIT 3
""")
for r in result:
    print(f"ID: {r['c.id']}")
    print(f"  Text: {r['c.text'][:50]}...")
    print(f"  Timestamp: {r['c.timestamp']}")
    print(f"  Source: {r['c.source']}")
    print(f"  Confidence: {r['c.confidence_score']}")
    print()

print("=== Check Entity APPEARS_IN Claim ===")
result = client.execute_query("""
MATCH (e:Entity)-[:APPEARS_IN]->(c:Claim)
RETURN count(*) as count
""")
print(f"Entity APPEARS_IN Claim relationships: {result[0]['count'] if result else 0}")

print("\n=== Check if claims have 'source' property ===")
result = client.execute_query("""
MATCH (c:Claim)
WHERE c.source IS NOT NULL
RETURN count(*) as count
""")
print(f"Claims with source property: {result[0]['count'] if result else 0}")
