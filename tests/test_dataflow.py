"""
Test Data Flow
Verify data is flowing through Kafka correctly
"""

from streaming.consumer import KafkaConsumerClient
from loguru import logger
import json


def test_kafka_consumer():
    """Test consuming messages from raw-feeds topic"""
    logger.info("=" * 60)
    logger.info("Testing Kafka Consumer - Reading raw-feeds")
    logger.info("=" * 60)
    
    message_count = 0
    sample_messages = []
    
    def process_message(msg):
        nonlocal message_count, sample_messages
        message_count += 1
        
        # Store first 3 messages as samples
        if len(sample_messages) < 3:
            sample_messages.append(msg)
        
        # Print progress
        if message_count % 10 == 0:
            logger.info(f"Processed {message_count} messages...")
    
    # Create consumer
    consumer = KafkaConsumerClient(
        topics=["raw-feeds"],
        auto_offset_reset='earliest'  # Read from beginning
    )
    
    try:
        # Consume messages
        consumer.consume(process_message, max_messages=100)
        
    finally:
        consumer.close()
    
    # Print results
    logger.info("=" * 60)
    logger.info(f"✓ Consumed {message_count} messages from raw-feeds")
    logger.info("=" * 60)
    
    if sample_messages:
        logger.info("\nSample messages:")
        for i, msg in enumerate(sample_messages, 1):
            logger.info(f"\n[{i}] {msg.get('source_type', 'unknown').upper()}")
            logger.info(f"    Title: {msg.get('title', 'N/A')[:80]}")
            logger.info(f"    Source: {msg.get('source_name', 'N/A')}")
            logger.info(f"    URL: {msg.get('url', 'N/A')}")
            logger.info(f"    Published: {msg.get('published_at', 'N/A')}")
    
    return message_count


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    count = test_kafka_consumer()
    
    if count > 0:
        print(f"\n✅ SUCCESS: Data pipeline is working!")
        print(f"   {count} messages flowing through Kafka")
    else:
        print(f"\n⚠️  No messages found in Kafka")
        print(f"   Run: python ingestion.py first")
