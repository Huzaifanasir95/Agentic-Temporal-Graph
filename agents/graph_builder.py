"""
Graph Builder Agent
Updates Neo4j knowledge graph with entities, events, claims
"""

from typing import Dict, Any, List
from agents.state import AgentState, GraphOperation
from graph.neo4j_client import Neo4jClient
from loguru import logger
import time


class GraphBuilderAgent:
    """
    Builds and updates knowledge graph
    
    Responsibilities:
    - Create/update entity nodes
    - Create/update claim nodes
    - Create relationships
    - Update temporal information
    - Track provenance
    """
    
    def __init__(self):
        """Initialize graph builder"""
        self.neo4j = Neo4jClient()
        logger.info("GraphBuilderAgent initialized")
        
    def process(self, state: AgentState) -> AgentState:
        """
        Process state and update graph
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with graph operations
        """
        logger.info("[GraphBuilderAgent] Building graph...")
        start_time = time.time()
        
        operations = []
        
        # 1. Create source node
        if state.get('source'):
            self._create_source(state['source'])
            operations.append(
                GraphOperation(
                    operation_type='CREATE',
                    node_type='Source',
                    node_id=state['source'].get('url', ''),
                    properties={}
                )
            )
            
        # 2. Create entities
        for entity in state['entities']:
            self._create_entity(entity)
            operations.append(
                GraphOperation(
                    operation_type='CREATE',
                    node_type='Entity',
                    node_id=entity['id'],
                    properties={'name': entity['name'], 'type': entity['type']}
                )
            )
            
        # 3. Create claims
        for claim in state['claims']:
            self._create_claim(claim)
            operations.append(
                GraphOperation(
                    operation_type='CREATE',
                    node_type='Claim',
                    node_id=claim['id'],
                    properties={'text': claim['text']}
                )
            )
            
            # Link claim to entities mentioned
            for entity in claim.get('mentioned_entities', []):
                self._link_claim_to_entity(claim['id'], entity)
                operations.append(
                    GraphOperation(
                        operation_type='LINK',
                        node_type='Claim->Entity',
                        node_id=f"{claim['id']}->{entity}",
                        properties={'relationship': 'ABOUT'}
                    )
                )
                
            # Link contradictions
            for contradiction in claim.get('contradictions', []):
                self._link_contradiction(
                    claim['id'],
                    contradiction['claim_id'],
                    contradiction['confidence']
                )
                operations.append(
                    GraphOperation(
                        operation_type='LINK',
                        node_type='Claim->Claim',
                        node_id=f"{claim['id']}->{contradiction['claim_id']}",
                        properties={'relationship': 'CONTRADICTS'}
                    )
                )
                
        # 4. Create events
        for event in state['events']:
            self._create_event(event)
            operations.append(
                GraphOperation(
                    operation_type='CREATE',
                    node_type='Event',
                    node_id=event['id'],
                    properties={'description': event['description']}
                )
            )
            
        # Store operations in state
        state['graph_operations'] = operations
        
        # Update processing log
        state['processing_log'].append({
            'agent': 'GraphBuilderAgent',
            'action': 'updated_graph',
            'operations': len(operations),
            'timestamp': time.time()
        })
        
        # Mark as complete
        state['next_agent'] = 'COMPLETE'
        
        elapsed = time.time() - start_time
        logger.info(f"[GraphBuilderAgent] Created {len(operations)} graph operations in {elapsed:.2f}s")
        
        return state
        
    def _create_source(self, source: Dict[str, Any]) -> None:
        """Create source node"""
        try:
            self.neo4j.create_source(source)
            logger.debug(f"Created source: {source.get('source_name')}")
        except Exception as e:
            logger.error(f"Failed to create source: {e}")
            
    def _create_entity(self, entity: Dict[str, Any]) -> None:
        """Create entity node"""
        try:
            self.neo4j.create_entity(entity)
            logger.debug(f"Created entity: {entity['name']}")
        except Exception as e:
            logger.error(f"Failed to create entity: {e}")
            
    def _create_claim(self, claim: Dict[str, Any]) -> None:
        """Create claim node"""
        try:
            self.neo4j.create_claim(claim)
            logger.debug(f"Created claim: {claim['id']}")
        except Exception as e:
            logger.error(f"Failed to create claim: {e}")
            
    def _create_event(self, event: Dict[str, Any]) -> None:
        """Create event node"""
        # Note: Need to add create_event to Neo4jClient
        logger.debug(f"Event creation not yet implemented: {event['id']}")
        
    def _link_claim_to_entity(self, claim_id: str, entity_id: str) -> None:
        """Link claim to entity"""
        try:
            self.neo4j.link_claim_to_entity(claim_id, entity_id)
            logger.debug(f"Linked claim {claim_id} to entity {entity_id}")
        except Exception as e:
            logger.error(f"Failed to link claim to entity: {e}")
            
    def _link_contradiction(
        self,
        claim1_id: str,
        claim2_id: str,
        confidence: float
    ) -> None:
        """Link contradictory claims"""
        try:
            self.neo4j.link_claim_contradiction(claim1_id, claim2_id, confidence)
            logger.debug(f"Linked contradiction: {claim1_id} <-> {claim2_id}")
        except Exception as e:
            logger.error(f"Failed to link contradiction: {e}")
            
    def get_graph_stats(self) -> Dict[str, int]:
        """Get current graph statistics"""
        return self.neo4j.get_stats()
        
    def close(self):
        """Close connections"""
        self.neo4j.close()


if __name__ == "__main__":
    # Test graph builder
    from agents.state import create_initial_state
    
    # Create test state with full data
    state = create_initial_state("Test article about climate summit")
    
    state['source'] = {
        'url': 'https://test.com/article',
        'source_name': 'Test Source',
        'source_type': 'news',
        'title': 'Climate Summit Article'
    }
    
    state['entities'] = [
        {
            'id': 'entity_1',
            'name': 'UN',
            'type': 'ORGANIZATION',
            'confidence': 0.9
        },
        {
            'id': 'entity_2',
            'name': 'Geneva',
            'type': 'LOCATION',
            'confidence': 0.85
        }
    ]
    
    state['claims'] = [
        {
            'id': 'claim_1',
            'text': 'UN reaches historic climate agreement',
            'context': 'Summit announcement',
            'confidence': 0.8,
            'mentioned_entities': ['entity_1', 'entity_2']
        }
    ]
    
    state['events'] = [
        {
            'id': 'event_1',
            'description': 'Climate summit concludes',
            'timestamp': '2026-01-04',
            'location': 'Geneva'
        }
    ]
    
    agent = GraphBuilderAgent()
    
    try:
        result = agent.process(state)
        
        print(f"\n✓ Graph Builder Agent Test")
        print(f"  Graph operations: {len(result['graph_operations'])}")
        
        operation_types = {}
        for op in result['graph_operations']:
            op_type = f"{op['operation_type']}:{op['node_type']}"
            operation_types[op_type] = operation_types.get(op_type, 0) + 1
            
        print(f"\n  Operations by type:")
        for op_type, count in operation_types.items():
            print(f"    {op_type}: {count}")
            
        # Get graph stats
        stats = agent.get_graph_stats()
        print(f"\n  Graph statistics:")
        print(f"    Entities: {stats.get('entities', 0)}")
        print(f"    Claims: {stats.get('claims', 0)}")
        print(f"    Sources: {stats.get('sources', 0)}")
        print(f"    Events: {stats.get('events', 0)}")
        
        print(f"\n  Next agent: {result['next_agent']}")
        
    finally:
        agent.close()
