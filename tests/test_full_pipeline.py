"""
Full Pipeline Test
Integrates Kafka → Multi-Agent Pipeline → Neo4j
"""

from dotenv import load_dotenv
load_dotenv()

from agents.orchestrator import MultiAgentOrchestrator
from streaming.consumer import KafkaConsumerClient
from streaming.producer import KafkaProducerClient
from loguru import logger
import json
import time


def process_from_kafka():
    """
    Consume messages from Kafka and process through agent pipeline
    """
    orchestrator = MultiAgentOrchestrator()
    
    # Track processing stats
    stats = {
        'processed': 0,
        'succeeded': 0,
        'failed': 0,
        'start_time': time.time()
    }
    
    def handle_message(message):
        """Handle each Kafka message"""
        try:
            stats['processed'] += 1
            
            # Parse message
            article_data = json.loads(message.value.decode('utf-8'))
            
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing Article #{stats['processed']}")
            logger.info(f"Title: {article_data.get('title', 'Untitled')}")
            logger.info(f"{'='*60}\n")
            
            # Process through pipeline
            result = orchestrator.process_article(article_data)
            
            stats['succeeded'] += 1
            
            # Show summary
            logger.success(f"✓ Article #{stats['processed']} Complete")
            logger.info(f"  Entities: {len(result['entities'])}")
            logger.info(f"  Claims: {len(result['claims'])}")
            logger.info(f"  Graph Ops: {len(result['graph_operations'])}\n")
            
        except Exception as e:
            stats['failed'] += 1
            logger.error(f"✗ Failed to process article: {e}")
    
    # Create consumer
    consumer = KafkaConsumerClient(
        topics=['raw-feeds'],
        group_id='multi-agent-processor'
    )
    
    try:
        logger.info("🚀 Starting Multi-Agent Pipeline Consumer")
        logger.info("Listening to topic: raw-feeds")
        logger.info("Press Ctrl+C to stop\n")
        
        # Start consuming
        consumer.consume(
            callback=handle_message,
            max_messages=5  # Process 5 messages for testing
        )
        
    except KeyboardInterrupt:
        logger.info("\n⚠️  Stopping consumer...")
        
    finally:
        consumer.close()
        orchestrator.close()
        
        # Print final stats
        elapsed = time.time() - stats['start_time']
        logger.info(f"\n{'='*60}")
        logger.info(f"Pipeline Statistics")
        logger.info(f"{'='*60}")
        logger.info(f"Processed: {stats['processed']}")
        logger.info(f"Succeeded: {stats['succeeded']}")
        logger.info(f"Failed: {stats['failed']}")
        logger.info(f"Duration: {elapsed:.2f}s")
        if stats['succeeded'] > 0:
            logger.info(f"Avg Time: {elapsed/stats['succeeded']:.2f}s per article")
        logger.info(f"{'='*60}\n")


def send_test_article():
    """
    Send a test article to Kafka for processing
    """
    test_article = {
        'title': 'UN Security Council Votes on Climate Resolution',
        'content': '''
        The United Nations Security Council held an emergency session today to vote 
        on a landmark climate resolution. Secretary-General António Guterres urged 
        member states to support the measure, calling climate change "an existential 
        threat to humanity."
        
        The resolution proposes binding carbon emission targets for all member nations, 
        with penalties for non-compliance. China and Russia expressed reservations 
        about the enforcement mechanisms, while the European Union pledged full support.
        
        Environmental activists gathered outside UN headquarters in New York to demand 
        immediate action. "We cannot wait any longer," said climate activist Greta Thunberg. 
        "Every day of delay means more irreversible damage to our planet."
        
        The vote is expected to take place within 48 hours. If passed, the resolution 
        would require countries to reduce emissions by 45% by 2030 compared to 2020 levels.
        ''',
        'url': 'https://example.com/un-climate-vote',
        'source': {
            'source_name': 'UN News',
            'source_type': 'official',
            'url': 'https://example.com/un-climate-vote',
            'credibility_score': 0.95
        },
        'published_date': '2026-01-04T18:00:00Z',
        'author': 'UN News Service'
    }
    
    producer = KafkaProducerClient()
    
    try:
        logger.info("Sending test article to Kafka...")
        producer.send('raw-feeds', test_article)
        logger.success("✓ Test article sent to raw-feeds topic")
        
    finally:
        producer.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'send':
        # Send test article
        send_test_article()
    else:
        # Process from Kafka
        process_from_kafka()
