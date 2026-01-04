// ============================================
// Neo4j Schema for Agentic OSINT System
// Temporal Knowledge Graph Schema
// ============================================

// ============================================
// 1. CONSTRAINTS - Unique Identifiers
// ============================================

// Entity Constraints
CREATE CONSTRAINT entity_id_unique IF NOT EXISTS
FOR (e:Entity) REQUIRE e.id IS UNIQUE;

CREATE CONSTRAINT entity_name_type_unique IF NOT EXISTS
FOR (e:Entity) REQUIRE (e.name, e.type) IS UNIQUE;

// Event Constraints
CREATE CONSTRAINT event_id_unique IF NOT EXISTS
FOR (ev:Event) REQUIRE ev.id IS UNIQUE;

// Claim Constraints
CREATE CONSTRAINT claim_id_unique IF NOT EXISTS
FOR (c:Claim) REQUIRE c.id IS UNIQUE;

// Source Constraints
CREATE CONSTRAINT source_url_unique IF NOT EXISTS
FOR (s:Source) REQUIRE s.url IS UNIQUE;

// Timestamp Constraints
CREATE CONSTRAINT timestamp_value_unique IF NOT EXISTS
FOR (t:Timestamp) REQUIRE t.value IS UNIQUE;

// ============================================
// 2. INDEXES - Performance Optimization
// ============================================

// Entity Indexes
CREATE INDEX entity_type_idx IF NOT EXISTS FOR (e:Entity) ON (e.type);
CREATE INDEX entity_name_idx IF NOT EXISTS FOR (e:Entity) ON (e.name);
CREATE INDEX entity_first_seen_idx IF NOT EXISTS FOR (e:Entity) ON (e.first_seen);

// Event Indexes
CREATE INDEX event_timestamp_idx IF NOT EXISTS FOR (ev:Event) ON (ev.timestamp);
CREATE INDEX event_type_idx IF NOT EXISTS FOR (ev:Event) ON (ev.type);

// Claim Indexes
CREATE INDEX claim_timestamp_idx IF NOT EXISTS FOR (c:Claim) ON (c.timestamp);
CREATE INDEX claim_stance_idx IF NOT EXISTS FOR (c:Claim) ON (c.stance);
CREATE INDEX claim_confidence_idx IF NOT EXISTS FOR (c:Claim) ON (c.confidence_score);

// Source Indexes
CREATE INDEX source_credibility_idx IF NOT EXISTS FOR (s:Source) ON (s.credibility_score);
CREATE INDEX source_domain_idx IF NOT EXISTS FOR (s:Source) ON (s.domain);
CREATE INDEX source_type_idx IF NOT EXISTS FOR (s:Source) ON (s.type);

// Full-Text Search Indexes
CREATE FULLTEXT INDEX entity_search_idx IF NOT EXISTS
FOR (e:Entity) ON EACH [e.name, e.description];

CREATE FULLTEXT INDEX claim_search_idx IF NOT EXISTS
FOR (c:Claim) ON EACH [c.text, c.context];

CREATE FULLTEXT INDEX event_search_idx IF NOT EXISTS
FOR (ev:Event) ON EACH [ev.description, ev.summary];

// ============================================
// 3. NODE LABELS & PROPERTIES
// ============================================

// Example Node Creation (for documentation)

// ENTITY Node
// (:Entity {
//   id: "uuid-v4",
//   name: "Entity Name",
//   type: "PERSON|ORGANIZATION|LOCATION|CONCEPT|EVENT",
//   description: "Optional description",
//   aliases: ["alias1", "alias2"],
//   first_seen: datetime(),
//   last_updated: datetime(),
//   mention_count: 0,
//   embedding: [float array]
// })

// EVENT Node
// (:Event {
//   id: "uuid-v4",
//   type: "ANNOUNCEMENT|CONFLICT|MEETING|POLICY_CHANGE|...",
//   description: "What happened",
//   summary: "Brief summary",
//   timestamp: datetime(),
//   location: "Where it happened",
//   confidence_score: 0.0-1.0,
//   created_at: datetime()
// })

// CLAIM Node
// (:Claim {
//   id: "uuid-v4",
//   text: "The actual claim text",
//   context: "Surrounding context",
//   stance: "SUPPORTS|REFUTES|NEUTRAL",
//   confidence_score: 0.0-1.0,
//   verification_status: "VERIFIED|REFUTED|UNVERIFIED",
//   timestamp: datetime(),
//   valid_from: datetime(),
//   valid_until: datetime() or null,
//   embedding: [float array]
// })

// SOURCE Node
// (:Source {
//   id: "uuid-v4",
//   url: "https://...",
//   domain: "example.com",
//   type: "NEWS|SOCIAL_MEDIA|ACADEMIC|GOVERNMENT|...",
//   title: "Article/Post title",
//   author: "Author name",
//   published_at: datetime(),
//   scraped_at: datetime(),
//   credibility_score: 0.0-1.0,
//   bias_score: -1.0 to 1.0 (left to right),
//   language: "en",
//   metadata: {json object}
// })

// TIMESTAMP Node (for temporal queries)
// (:Timestamp {
//   value: datetime(),
//   year: 2026,
//   month: 1,
//   day: 4,
//   hour: 12
// })

// ============================================
// 4. RELATIONSHIP TYPES
// ============================================

// Entity Relationships
// (:Entity)-[:MENTIONS {timestamp, context, source_id}]->(:Entity)
// (:Entity)-[:PARTICIPATES_IN {role, timestamp}]->(:Event)
// (:Entity)-[:LOCATED_IN {since, until}]->(:Entity)
// (:Entity)-[:AFFILIATED_WITH {role, since, until}]->(:Entity)
// (:Entity)-[:SIMILAR_TO {similarity_score}]->(:Entity)

// Claim Relationships
// (:Claim)-[:ABOUT]->(:Entity)
// (:Claim)-[:ABOUT]->(:Event)
// (:Claim)-[:SUPPORTS {confidence}]->(:Claim)
// (:Claim)-[:CONTRADICTS {confidence}]->(:Claim)
// (:Claim)-[:EVOLVES_TO]->(:Claim)
// (:Claim)-[:CITED_BY]->(:Source)
// (:Claim)-[:MADE_BY]->(:Entity)

// Source Relationships
// (:Source)-[:PUBLISHED]->(:Claim)
// (:Source)-[:REPORTS_ON]->(:Event)
// (:Source)-[:MENTIONS]->(:Entity)
// (:Source)-[:REFERENCES]->(:Source)

// Temporal Relationships
// (:Event)-[:PRECEDES {interval_days}]->(:Event)
// (:Event)-[:CAUSED_BY]->(:Event)
// (:Claim)-[:VALID_AT]->(:Timestamp)

// ============================================
// 5. INITIALIZATION - Sample Data (Optional)
// ============================================

// Create initial source credibility baseline
MERGE (s:Source {domain: "reuters.com"})
SET s.credibility_score = 0.95,
    s.bias_score = 0.05,
    s.type = "NEWS";

MERGE (s:Source {domain: "apnews.com"})
SET s.credibility_score = 0.94,
    s.bias_score = 0.0,
    s.type = "NEWS";

MERGE (s:Source {domain: "bbc.com"})
SET s.credibility_score = 0.92,
    s.bias_score = -0.1,
    s.type = "NEWS";

// Create system metadata node
CREATE (sys:SystemMetadata {
  schema_version: "1.0.0",
  created_at: datetime(),
  last_updated: datetime(),
  total_entities: 0,
  total_claims: 0,
  total_events: 0,
  total_sources: 0
});

// ============================================
// 6. UTILITY QUERIES (for reference)
// ============================================

// Get all nodes and relationship counts
// MATCH (n)
// RETURN labels(n) as label, count(n) as count
// ORDER BY count DESC;

// Find contradictory claims about same entity
// MATCH (e:Entity {name: "Target Name"})
// MATCH (e)<-[:ABOUT]-(c1:Claim)-[r:CONTRADICTS]-(c2:Claim)
// WHERE c1.timestamp < c2.timestamp
// RETURN c1.text, c2.text, c1.timestamp, c2.timestamp, r.confidence;

// Temporal evolution of claims
// MATCH path = (c1:Claim)-[:EVOLVES_TO*]->(c2:Claim)
// WHERE c1.about = "Topic"
// RETURN path;

// Find trending entities in last 7 days
// MATCH (e:Entity)<-[r:MENTIONS]-(s:Source)
// WHERE r.timestamp > datetime() - duration('P7D')
// RETURN e.name, e.type, count(r) as mentions
// ORDER BY mentions DESC
// LIMIT 20;

// Source credibility analysis
// MATCH (s:Source)-[:PUBLISHED]->(c:Claim)-[r:CONTRADICTS]->()
// RETURN s.domain, s.credibility_score, count(r) as contradictions
// ORDER BY contradictions DESC;
