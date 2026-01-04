"""
Kafka Producer Client
Publishes messages to Kafka topics
"""

from kafka import KafkaProducer
from typing import Dict, Any, Optional
from loguru import logger
import json
import os


class KafkaProducerClient:
    """Kafka producer for streaming data"""
    
    def __init__(
        self,
        bootstrap_servers: Optional[str] = None,
        value_serializer=None,
    ):
        """
        Initialize Kafka producer
        
        Args:
            bootstrap_servers: Kafka server address
            value_serializer: Function to serialize values
        """
        self.bootstrap_servers = bootstrap_servers or os.getenv(
            "KAFKA_BOOTSTRAP_SERVERS", "localhost:29092"
        )
        
        # Default JSON serializer
        if value_serializer is None:
            value_serializer = lambda v: json.dumps(v).encode('utf-8')
        
        self.producer = KafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=value_serializer,
            key_serializer=lambda k: k.encode('utf-8') if k else None,
            compression_type='gzip',
            max_request_size=10485760,  # 10MB
            retries=3,
        )
        
        logger.info(f"Kafka producer initialized: {self.bootstrap_servers}")
        
    def send(
        self,
        topic: str,
        value: Dict[str, Any],
        key: Optional[str] = None,
    ) -> None:
        """
        Send message to Kafka topic
        
        Args:
            topic: Topic name
            value: Message value (will be JSON serialized)
            key: Optional message key
        """
        try:
            future = self.producer.send(topic, key=key, value=value)
            future.get(timeout=10)  # Wait for confirmation
            logger.debug(f"Sent message to {topic}")
        except Exception as e:
            logger.error(f"Failed to send to {topic}: {e}")
            raise
            
    def send_batch(
        self,
        topic: str,
        messages: list[Dict[str, Any]],
    ) -> None:
        """
        Send batch of messages
        
        Args:
            topic: Topic name
            messages: List of message dicts
        """
        try:
            for msg in messages:
                key = msg.get('id') or msg.get('url')
                self.producer.send(topic, key=key, value=msg)
            
            self.producer.flush()
            logger.info(f"Sent {len(messages)} messages to {topic}")
            
        except Exception as e:
            logger.error(f"Batch send failed: {e}")
            raise
            
    def close(self):
        """Close producer connection"""
        self.producer.close()
        logger.info("Kafka producer closed")


def create_producer() -> KafkaProducerClient:
    """Create producer from environment config"""
    return KafkaProducerClient()


if __name__ == "__main__":
    # Test producer
    from dotenv import load_dotenv
    load_dotenv()
    
    producer = create_producer()
    
    # Send test message
    test_msg = {
        "id": "test-001",
        "type": "test",
        "content": "Hello from producer",
        "timestamp": "2026-01-04T12:00:00Z"
    }
    
    producer.send("raw-feeds", test_msg)
    producer.close()
    
    print("Test message sent successfully!")
