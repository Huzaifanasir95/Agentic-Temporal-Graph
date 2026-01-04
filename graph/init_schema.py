"""
Neo4j Schema Initializer
Executes schema.cypher and sets up initial graph structure
"""

from neo4j import GraphDatabase
from loguru import logger
import os
from pathlib import Path


class SchemaInitializer:
    """Initialize Neo4j graph database schema"""
    
    def __init__(self, uri: str, username: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
        self.schema_path = Path(__file__).parent / "schema.cypher"
        
    def close(self):
        """Close database connection"""
        self.driver.close()
        
    def execute_cypher_file(self, file_path: Path) -> None:
        """Execute a Cypher file line by line"""
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        # Split by semicolon and filter out comments
        statements = []
        current_statement = []
        
        for line in content.split('\n'):
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('//'):
                continue
                
            current_statement.append(line)
            
            # Execute when we hit a semicolon
            if line.endswith(';'):
                statement = ' '.join(current_statement)
                statements.append(statement)
                current_statement = []
        
        # Execute each statement
        with self.driver.session() as session:
            for statement in statements:
                try:
                    session.run(statement)
                    logger.debug(f"Executed: {statement[:100]}...")
                except Exception as e:
                    logger.warning(f"Statement failed (may already exist): {str(e)[:100]}")
                    
    def initialize_schema(self) -> None:
        """Initialize the complete schema"""
        logger.info("Initializing Neo4j schema...")
        
        try:
            # Execute schema file
            self.execute_cypher_file(self.schema_path)
            
            logger.info("✓ Schema initialization complete")
            
            # Verify schema
            self.verify_schema()
            
        except Exception as e:
            logger.error(f"Schema initialization failed: {e}")
            raise
            
    def verify_schema(self) -> None:
        """Verify that schema was created correctly"""
        with self.driver.session() as session:
            # Check constraints
            result = session.run("SHOW CONSTRAINTS")
            constraints = [record["name"] for record in result]
            logger.info(f"Created {len(constraints)} constraints")
            
            # Check indexes
            result = session.run("SHOW INDEXES")
            indexes = [record["name"] for record in result]
            logger.info(f"Created {len(indexes)} indexes")
            
            # Check if system metadata exists
            result = session.run("MATCH (sys:SystemMetadata) RETURN count(sys) as count")
            count = result.single()["count"]
            logger.info(f"System metadata nodes: {count}")


if __name__ == "__main__":
    # Initialize from environment variables
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    username = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "osint_password_2026")
    
    initializer = SchemaInitializer(uri, username, password)
    
    try:
        initializer.initialize_schema()
    finally:
        initializer.close()
