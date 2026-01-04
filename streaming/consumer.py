"""
Kafka Consumer Client
Consumes messages from Kafka topics
"""

from kafka import KafkaConsumer
from typing import Optional, Callable, Dict, Any
from loguru import logger
import json
import os


class KafkaConsumerClient:
    """Kafka consumer for processing streaming data"""
    
    def __init__(
        self,
        topics: list[str],
        group_id: Optional[str] = None,
        bootstrap_servers: Optional[str] = None,
        auto_offset_reset: str = 'earliest',
        value_deserializer=None,
    ):
        """
        Initialize Kafka consumer
        
        Args:
            topics: List of topics to subscribe to
            group_id: Consumer group ID
            bootstrap_servers: Kafka server address
            auto_offset_reset: Where to start reading (earliest/latest)
            value_deserializer: Function to deserialize values
        """
        self.bootstrap_servers = bootstrap_servers or os.getenv(
            "KAFKA_BOOTSTRAP_SERVERS", "localhost:29092"
        )
        self.group_id = group_id or os.getenv(
            "KAFKA_CONSUMER_GROUP", "osint-processors"
        )
        
        # Default JSON deserializer
        if value_deserializer is None:
            value_deserializer = lambda v: json.loads(v.decode('utf-8'))
        
        self.consumer = KafkaConsumer(
            *topics,
            bootstrap_servers=self.bootstrap_servers,
            group_id=self.group_id,
            auto_offset_reset=auto_offset_reset,
            value_deserializer=value_deserializer,
            key_deserializer=lambda k: k.decode('utf-8') if k else None,
            enable_auto_commit=True,
            max_poll_records=500,
        )
        
        logger.info(f"Kafka consumer initialized: {topics} (group: {self.group_id})")
        
    def consume(
        self,
        callback: Callable[[Dict[str, Any]], None],
        max_messages: Optional[int] = None,
    ) -> int:
        """
        Consume messages and process with callback
        
        Args:
            callback: Function to process each message
            max_messages: Optional limit on messages to process
            
        Returns:
            Number of messages processed
        """
        count = 0
        
        try:
            for message in self.consumer:
                try:
                    # Process message
                    callback(message.value)
                    count += 1
                    
                    if max_messages and count >= max_messages:
                        break
                        
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    logger.debug(f"Message: {message.value}")
                    
            return count
            
        except KeyboardInterrupt:
            logger.info("Consumer interrupted by user")
            return count
        finally:
            logger.info(f"Processed {count} messages")
            
    def close(self):
        """Close consumer connection"""
        self.consumer.close()
        logger.info("Kafka consumer closed")


def create_consumer(topics: list[str]) -> KafkaConsumerClient:
    """Create consumer from environment config"""
    return KafkaConsumerClient(topics=topics)


if __name__ == "__main__":
    # Test consumer
    from dotenv import load_dotenv
    load_dotenv()
    
    def process_message(msg: Dict[str, Any]):
        """Sample message processor"""
        print(f"Received: {msg}")
    
    consumer = create_consumer(["raw-feeds"])
    
    # Consume up to 10 messages
    count = consumer.consume(process_message, max_messages=10)
    
    consumer.close()
    print(f"Consumed {count} messages")
