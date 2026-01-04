"""
Kafka Topics Management
Define and create topics
"""

from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError
from loguru import logger
import os


class KafkaTopics:
    """Manage Kafka topics"""
    
    # Topic definitions
    TOPICS = {
        "raw-feeds": {
            "partitions": 3,
            "replication": 1,
            "description": "Raw data from RSS/Twitter/Reddit/Web"
        },
        "processed-articles": {
            "partitions": 3,
            "replication": 1,
            "description": "Cleaned and normalized articles"
        },
        "extracted-claims": {
            "partitions": 2,
            "replication": 1,
            "description": "Extracted claims and entities"
        },
        "graph-updates": {
            "partitions": 2,
            "replication": 1,
            "description": "Updates to Neo4j graph"
        },
        "alerts": {
            "partitions": 1,
            "replication": 1,
            "description": "High-priority alerts and contradictions"
        }
    }
    
    def __init__(self, bootstrap_servers: str = None):
        """Initialize admin client"""
        self.bootstrap_servers = bootstrap_servers or os.getenv(
            "KAFKA_BOOTSTRAP_SERVERS", "localhost:29092"
        )
        
        self.admin = KafkaAdminClient(
            bootstrap_servers=self.bootstrap_servers,
            request_timeout_ms=10000,
        )
        
        logger.info("Kafka admin client initialized")
        
    def create_all_topics(self):
        """Create all defined topics"""
        topics_to_create = []
        
        for name, config in self.TOPICS.items():
            topics_to_create.append(
                NewTopic(
                    name=name,
                    num_partitions=config["partitions"],
                    replication_factor=config["replication"],
                )
            )
        
        try:
            self.admin.create_topics(
                new_topics=topics_to_create,
                validate_only=False
            )
            logger.info(f"Created {len(topics_to_create)} topics")
            
        except TopicAlreadyExistsError:
            logger.info("Topics already exist")
        except Exception as e:
            logger.error(f"Failed to create topics: {e}")
            raise
            
    def list_topics(self) -> list[str]:
        """List all topics"""
        topics = self.admin.list_topics()
        logger.info(f"Found {len(topics)} topics")
        return topics
        
    def delete_topic(self, topic_name: str):
        """Delete a topic"""
        try:
            self.admin.delete_topics([topic_name])
            logger.info(f"Deleted topic: {topic_name}")
        except Exception as e:
            logger.error(f"Failed to delete {topic_name}: {e}")
            raise
            
    def close(self):
        """Close admin connection"""
        self.admin.close()


if __name__ == "__main__":
    # Test topics management
    from dotenv import load_dotenv
    load_dotenv()
    
    manager = KafkaTopics()
    
    # Create all topics
    manager.create_all_topics()
    
    # List topics
    topics = manager.list_topics()
    print(f"Topics: {topics}")
    
    manager.close()
