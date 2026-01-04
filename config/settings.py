"""
Configuration Management
Load settings from YAML and environment variables
"""

from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import List, Dict, Optional
from functools import lru_cache
import yaml
from pathlib import Path


class Neo4jSettings(BaseSettings):
    """Neo4j database configuration"""
    uri: str = Field(default="bolt://localhost:7687", env="NEO4J_URI")
    username: str = Field(default="neo4j", env="NEO4J_USERNAME")
    password: str = Field(default="osint_password_2026", env="NEO4J_PASSWORD")
    database: str = Field(default="neo4j", env="NEO4J_DATABASE")
    max_connections: int = 50
    

class KafkaSettings(BaseSettings):
    """Kafka streaming configuration"""
    bootstrap_servers: str = Field(default="localhost:29092", env="KAFKA_BOOTSTRAP_SERVERS")
    consumer_group: str = "osint-processors"
    auto_offset_reset: str = "earliest"
    
    # Topics
    topic_raw_feeds: str = "raw-feeds"
    topic_processed_articles: str = "processed-articles"
    topic_extracted_claims: str = "extracted-claims"
    topic_graph_updates: str = "graph-updates"
    

class OllamaSettings(BaseSettings):
    """Ollama LLM configuration"""
    base_url: str = Field(default="http://localhost:11434", env="OLLAMA_BASE_URL")
    model: str = Field(default="deepseek-v3", env="OLLAMA_MODEL")
    timeout: int = 120
    temperature: float = 0.7
    max_tokens: int = 2048
    

class ModelSettings(BaseSettings):
    """ML model configurations"""
    nli_model_name: str = "microsoft/deberta-v3-base"
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    spacy_model: str = "en_core_web_sm"
    device: str = "cuda"  # cuda or cpu
    

class APISettings(BaseSettings):
    """API server configuration"""
    host: str = Field(default="0.0.0.0", env="API_HOST")
    port: int = Field(default=8000, env="API_PORT")
    workers: int = 4
    reload: bool = True
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    

class ProcessingSettings(BaseSettings):
    """Processing and threshold configuration"""
    min_claim_confidence: float = 0.6
    min_entity_confidence: float = 0.7
    min_nli_confidence: float = 0.75
    min_source_credibility: float = 0.4
    max_concurrent_tasks: int = 10
    

class Settings(BaseSettings):
    """Main application settings"""
    
    # Application
    app_name: str = "Agentic OSINT Analyst"
    app_version: str = "0.1.0"
    environment: str = Field(default="development", env="ENVIRONMENT")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Component settings
    neo4j: Neo4jSettings = Neo4jSettings()
    kafka: KafkaSettings = KafkaSettings()
    ollama: OllamaSettings = OllamaSettings()
    models: ModelSettings = ModelSettings()
    api: APISettings = APISettings()
    processing: ProcessingSettings = ProcessingSettings()
    
    # Cache
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    
    # Feature flags
    enable_twitter_crawler: bool = False
    enable_reddit_crawler: bool = True
    enable_rss_crawler: bool = True
    enable_bias_detection: bool = True
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
    @classmethod
    def load_from_yaml(cls, yaml_path: str = "config/settings.yaml"):
        """Load settings from YAML file"""
        config_path = Path(yaml_path)
        
        if not config_path.exists():
            return cls()
            
        with open(config_path, 'r') as f:
            yaml_config = yaml.safe_load(f)
            
        return cls(**cls._flatten_dict(yaml_config))
    
    @staticmethod
    def _flatten_dict(d: Dict, parent_key: str = '', sep: str = '_') -> Dict:
        """Flatten nested dictionary for Pydantic"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(Settings._flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    try:
        return Settings.load_from_yaml()
    except Exception:
        return Settings()


if __name__ == "__main__":
    # Test configuration loading
    settings = get_settings()
    print(f"App: {settings.app_name} v{settings.app_version}")
    print(f"Environment: {settings.environment}")
    print(f"Neo4j URI: {settings.neo4j.uri}")
    print(f"Kafka: {settings.kafka.bootstrap_servers}")
    print(f"Ollama: {settings.ollama.base_url} ({settings.ollama.model})")
