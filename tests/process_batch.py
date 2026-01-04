"""
Process Existing Kafka Messages
Process all RSS articles through the multi-agent pipeline
"""

from dotenv import load_dotenv
load_dotenv()

from agents.orchestrator import MultiAgentOrchestrator
from streaming.consumer import KafkaConsumerClient
from loguru import logger
import json
import time


def process_all_articles(max_articles=20):
    """
    Process articles from Kafka through pipeline
    
    Args:
        max_articles: Maximum number of articles to process
    """
    orchestrator = MultiAgentOrchestrator()
    
    stats = {
        'processed': 0,
        'succeeded': 0,
        'failed': 0,
        'total_entities': 0,
        'total_claims': 0,
        'start_time': time.time()
    }
    
    def handle_message(message_value):
        """Handle each article"""
        try:
            stats['processed'] += 1
            article = message_value
            
            title = article.get('title', 'Untitled')[:60]
            logger.info(f"\n[{stats['processed']}/{max_articles}] {title}...")
            
            # Process through pipeline
            result = orchestrator.process_article(article)
            
            stats['succeeded'] += 1
            stats['total_entities'] += len(result['entities'])
            stats['total_claims'] += len(result['claims'])
            
            logger.success(f"✓ Entities: {len(result['entities'])}, Claims: {len(result['claims'])}")
            
        except Exception as e:
            stats['failed'] += 1
            logger.error(f"✗ Failed: {e}")
    
    consumer = KafkaConsumerClient(
        topics=['raw-feeds'],
        group_id='batch-processor'
    )
    
    try:
        logger.info("="*60)
        logger.info("🚀 Processing RSS Articles Through Multi-Agent Pipeline")
        logger.info("="*60)
        logger.info(f"Max articles: {max_articles}\n")
        
        consumer.consume(
            callback=handle_message,
            max_messages=max_articles
        )
        
    except KeyboardInterrupt:
        logger.warning("\n⚠️  Interrupted by user")
        
    finally:
        consumer.close()
        orchestrator.close()
        
        # Final stats
        elapsed = time.time() - stats['start_time']
        
        print(f"\n{'='*60}")
        print(f"Processing Complete")
        print(f"{'='*60}")
        print(f"Articles Processed: {stats['processed']}")
        print(f"Succeeded: {stats['succeeded']}")
        print(f"Failed: {stats['failed']}")
        print(f"Total Entities: {stats['total_entities']}")
        print(f"Total Claims: {stats['total_claims']}")
        print(f"Duration: {elapsed:.1f}s")
        if stats['succeeded'] > 0:
            print(f"Avg Time: {elapsed/stats['succeeded']:.1f}s per article")
        print(f"{'='*60}\n")
        
        # Show graph stats
        from graph.neo4j_client import Neo4jClient
        client = Neo4jClient()
        try:
            graph_stats = client.get_stats()
            print(f"Neo4j Knowledge Graph:")
            print(f"  Entities: {graph_stats.get('entities', 0)}")
            print(f"  Claims: {graph_stats.get('claims', 0)}")
            print(f"  Sources: {graph_stats.get('sources', 0)}")
            print(f"  Events: {graph_stats.get('events', 0)}")
        finally:
            client.close()


if __name__ == "__main__":
    import sys
    
    # Get max articles from command line
    max_articles = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    
    process_all_articles(max_articles)
