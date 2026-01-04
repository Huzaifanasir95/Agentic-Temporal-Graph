"""
Quick Pipeline Test
Tests Kafka → Multi-Agent → Neo4j without long-running consumer
"""

from dotenv import load_dotenv
load_dotenv()

from agents.orchestrator import MultiAgentOrchestrator
from streaming.consumer import KafkaConsumerClient
from loguru import logger
import json


def test_pipeline():
    """Process one message from Kafka"""
    orchestrator = MultiAgentOrchestrator()
    consumer = KafkaConsumerClient(
        topics=['raw-feeds'],
        group_id='test-processor'
    )
    
    try:
        logger.info("🚀 Fetching message from Kafka...")
        
        # Process one message using the consume method with callback
        processed_count = [0]  # Use list for mutable counter
        
        def process_message(message_value):
            article = message_value  # Already deserialized as JSON
            logger.info(f"Processing: {article.get('title', 'Untitled')[:60]}...")
            
            # Process through pipeline
            result = orchestrator.process_article(article)
            
            logger.success("\n✓ Pipeline Complete!")
            logger.info(f"  Entities: {len(result['entities'])}")
            logger.info(f"  Claims: {len(result['claims'])}")
            logger.info(f"  Graph Ops: {len(result['graph_operations'])}")
            
            processed_count[0] += 1
        
        # Consume just 1 message
        consumer.consume(callback=process_message, max_messages=1)
        
        if processed_count[0] == 0:
            logger.warning("No messages found in Kafka")
            
    finally:
        consumer.close()
        orchestrator.close()


if __name__ == "__main__":
    test_pipeline()
