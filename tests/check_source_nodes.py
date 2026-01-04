"""Check if Source nodes exist in Neo4j"""
from graph.neo4j_client import Neo4jClient

client = Neo4jClient()

# Check for Source nodes
query1 = """
MATCH (s:Source)
RETURN count(s) as source_count
"""
result = client.execute_query(query1, {})
print(f"Source nodes: {result[0]['source_count']}")

# Check relationships between Source and Claim
query2 = """
MATCH (s:Source)-[r]->(c:Claim)
RETURN type(r) as relationship_type, count(*) as count
LIMIT 5
"""
result = client.execute_query(query2, {})
print("\nSource->Claim relationships:")
for r in result:
    print(f"  {r['relationship_type']}: {r['count']}")

# Check reverse direction
query3 = """
MATCH (c:Claim)-[r]->(s:Source)
RETURN type(r) as relationship_type, count(*) as count
LIMIT 5
"""
result = client.execute_query(query3, {})
print("\nClaim->Source relationships:")
for r in result:
    print(f"  {r['relationship_type']}: {r['count']}")

# Sample Source node
query4 = """
MATCH (s:Source)
RETURN s.name as name, s.type as type
LIMIT 3
"""
result = client.execute_query(query4, {})
print("\nSample Source nodes:")
for r in result:
    print(f"  {r['name']} ({r['type']})")

client.close()
