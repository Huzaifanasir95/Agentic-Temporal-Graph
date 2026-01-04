"""
System Health Check
Verify all services are running correctly
"""

import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
from models.llm_client import create_llm_client
from loguru import logger

load_dotenv()


def check_neo4j():
    """Check Neo4j connection"""
    try:
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        username = os.getenv("NEO4J_USERNAME", "neo4j")
        password = os.getenv("NEO4J_PASSWORD")
        
        driver = GraphDatabase.driver(uri, auth=(username, password))
        with driver.session() as session:
            result = session.run("RETURN 1 as test")
            _ = result.single()
        driver.close()
        
        logger.info("✓ Neo4j: Connected")
        return True
    except Exception as e:
        logger.error(f"✗ Neo4j: {e}")
        return False


def check_groq():
    """Check Groq API"""
    try:
        client = create_llm_client()
        response = client.generate(
            prompt="Say 'OK' if you can read this.",
            max_tokens=10
        )
        logger.info(f"✓ Groq API: Connected (response: {response[:50]}...)")
        return True
    except Exception as e:
        logger.error(f"✗ Groq API: {e}")
        return False


def check_redis():
    """Check Redis connection"""
    try:
        import redis
        r = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            decode_responses=True
        )
        r.ping()
        logger.info("✓ Redis: Connected")
        return True
    except Exception as e:
        logger.error(f"✗ Redis: {e}")
        return False


def check_kafka():
    """Check Kafka connection"""
    try:
        from kafka.admin import KafkaAdminClient
        client = KafkaAdminClient(
            bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:29092"),
            request_timeout_ms=5000
        )
        client.close()
        logger.info("✓ Kafka: Connected")
        return True
    except Exception as e:
        logger.error(f"✗ Kafka: {e}")
        return False


def main():
    """Run all health checks"""
    logger.info("=" * 50)
    logger.info("Agentic OSINT System - Health Check")
    logger.info("=" * 50)
    
    results = {
        "Neo4j": check_neo4j(),
        "Groq API": check_groq(),
        "Redis": check_redis(),
        "Kafka": check_kafka(),
    }
    
    logger.info("=" * 50)
    passed = sum(results.values())
    total = len(results)
    logger.info(f"Health Check: {passed}/{total} services OK")
    
    if passed == total:
        logger.info("🎉 All systems operational!")
    else:
        logger.warning("⚠️  Some services need attention")
    
    return passed == total


if __name__ == "__main__":
    main()
