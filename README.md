# 🕵️ Agentic OSINT Analyst

**Multi-Agent Open Source Intelligence Analysis System**

A sophisticated defense-grade OSINT system that combines real-time intelligence gathering, multi-agent orchestration with LangGraph, and temporal knowledge graphs to analyze, cross-reference, and verify information from multiple sources.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Neo4j](https://img.shields.io/badge/Neo4j-5.16-green.svg)](https://neo4j.com/)
[![Kafka](https://img.shields.io/badge/Kafka-7.5-red.svg)](https://kafka.apache.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🎯 **Project Overview**

This system is designed for the **Adarga/Defense Intelligence** target market and demonstrates:

- ✅ **Real-time Data Ingestion** from news feeds, social media, and web sources
- ✅ **Multi-Agent Orchestration** using LangGraph for intelligent workflow management
- ✅ **Temporal Knowledge Graph** in Neo4j for tracking claim evolution and contradictions
- ✅ **Fact Verification** using NLI (Natural Language Inference) models
- ✅ **Bias Detection** and source credibility scoring
- ✅ **Scalable Architecture** with Kafka streaming and local LLMs (Ollama)

---

## 🏗️ **Architecture**

```
┌─────────────────────────────────────────────┐
│         Data Sources                         │
│  RSS | Twitter | Reddit | News Sites        │
└──────────────────┬──────────────────────────┘
                   │
         ┌─────────▼─────────┐
         │   Kafka Cluster   │
         │   (Data Stream)   │
         └─────────┬─────────┘
                   │
    ┌──────────────▼──────────────┐
    │   LangGraph Orchestration   │
    │                             │
    │  ┌────────────────────┐    │
    │  │  Collector Agent   │────┤
    │  │  Analyzer Agent    │────┤
    │  │  Cross-Ref Agent   │────┤
    │  │  Bias Detector     │────┤
    │  │  Graph Builder     │────┤
    │  └────────────────────┘    │
    └─────────────┬──────────────┘
                  │
         ┌────────▼────────┐
         │   Neo4j Graph   │
         │   Database      │
         └─────────────────┘
```

---

## 🚀 **Quick Start**

### **Prerequisites**

- **Python 3.10+**
- **Docker & Docker Compose**
- **NVIDIA GPU** (optional, for faster model inference)
- **16GB+ RAM** recommended

### **1. Clone the Repository**

```bash
git clone https://github.com/yourusername/Agentic-Temporal-Graph.git
cd Agentic-Temporal-Graph
```

### **2. Set Up Environment**

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys (Twitter, Reddit, etc.)
# Note: RSS and web scraping work without API keys
```

### **3. Start Infrastructure with Docker**

```bash
# Start Neo4j, Kafka, Ollama, Redis, PostgreSQL
docker-compose up -d

# Wait for services to be healthy (30-60 seconds)
docker-compose ps
```

### **4. Install Python Dependencies**

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download Spacy model
python -m spacy download en_core_web_sm
```

### **5. Initialize Neo4j Schema**

```bash
# Initialize graph database schema
python graph/init_schema.py
```

### **6. Pull Ollama Model**

```bash
# Download DeepSeek-V3 (or Llama-3)
docker exec -it osint-ollama ollama pull deepseek-v3

# Verify model is loaded
curl http://localhost:11434/api/tags
```

### **7. Run the System**

```bash
# Start the main orchestration (coming in Phase 2)
python main.py

# Or start API server
uvicorn api.main:app --reload
```

---

## 📁 **Project Structure**

```
Agentic-Temporal-Graph/
├── agents/                    # Multi-Agent System
│   ├── collector.py          # Data collection agent
│   ├── analyzer.py           # Entity & claim extraction
│   ├── cross_reference.py    # Fact cross-referencing
│   ├── bias_detector.py      # Bias & credibility analysis
│   └── graph_builder.py      # Neo4j graph updates
│
├── crawlers/                  # Data Ingestion
│   ├── rss_crawler.py        # RSS feed parser
│   ├── twitter_crawler.py    # Twitter/X API
│   ├── reddit_crawler.py     # Reddit API (PRAW)
│   └── web_scraper.py        # BeautifulSoup/Playwright
│
├── graph/                     # Graph Database
│   ├── schema.cypher         # Neo4j schema definition
│   ├── init_schema.py        # Schema initializer
│   ├── neo4j_client.py       # Database client
│   └── queries.py            # Pre-built Cypher queries
│
├── models/                    # ML Models
│   ├── nli_model.py          # Natural Language Inference
│   ├── embeddings.py         # Sentence embeddings
│   └── llm_client.py         # Ollama LLM client
│
├── kafka/                     # Streaming Components
│   ├── producer.py           # Kafka producers
│   ├── consumer.py           # Kafka consumers
│   └── topics.py             # Topic management
│
├── api/                       # REST API
│   ├── main.py               # FastAPI app
│   ├── routes.py             # API endpoints
│   └── schemas.py            # Pydantic models
│
├── config/                    # Configuration
│   ├── settings.yaml         # Main config
│   └── settings.py           # Config loader
│
├── tests/                     # Test suite
│
├── docker-compose.yml         # Infrastructure setup
├── requirements.txt           # Python dependencies
├── .env.example              # Environment template
└── README.md                 # This file
```

---

## 🔧 **Configuration**

### **Key Configuration Files**

1. **`.env`** - Environment variables (API keys, passwords)
2. **`config/settings.yaml`** - Application settings
3. **`docker-compose.yml`** - Infrastructure services

### **Important Settings**

| Setting | Description | Default |
|---------|-------------|---------|
| `OLLAMA_MODEL` | LLM model to use | `deepseek-v3` |
| `NEO4J_PASSWORD` | Neo4j database password | `osint_password_2026` |
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka connection | `localhost:29092` |
| `MIN_CLAIM_CONFIDENCE` | Claim extraction threshold | `0.6` |
| `ENABLE_BIAS_DETECTION` | Enable/disable bias checking | `true` |

---

## 📊 **Graph Schema**

### **Node Types**

- **Entity**: People, Organizations, Locations, Concepts
- **Event**: Time-stamped occurrences
- **Claim**: Statements with confidence scores
- **Source**: News articles, posts, documents
- **Timestamp**: For temporal queries

### **Relationship Types**

- `(:Entity)-[:MENTIONS]->(:Entity)`
- `(:Claim)-[:CONTRADICTS]->(:Claim)`
- `(:Claim)-[:SUPPORTS]->(:Claim)`
- `(:Source)-[:PUBLISHED]->(:Claim)`
- `(:Event)-[:PRECEDES]->(:Event)`

### **Example Query**

```cypher
// Find contradictory claims about an entity
MATCH (e:Entity {name: "Target Name"})
MATCH (e)<-[:ABOUT]-(c1:Claim)-[r:CONTRADICTS]-(c2:Claim)
WHERE c1.timestamp < c2.timestamp
RETURN c1.text, c2.text, c1.timestamp, c2.timestamp
```

---

## 🤖 **Multi-Agent Workflow**

### **Agent Pipeline**

1. **Collector Agent** → Fetches raw data from sources
2. **Analyzer Agent** → Extracts entities, events, claims
3. **Cross-Reference Agent** → Compares with existing data
4. **Bias Detector Agent** → Analyzes credibility & bias
5. **Graph Builder Agent** → Updates Neo4j graph

### **LangGraph State Machine**

```python
from langgraph.graph import StateGraph

# Define state schema
state = {
    "raw_data": dict,
    "entities": list,
    "claims": list,
    "relationships": list,
    "next_agent": str
}

# Build agent graph
graph = StateGraph(state)
graph.add_node("collector", collector_agent)
graph.add_node("analyzer", analyzer_agent)
# ... more nodes
```

---

## 🔬 **Fact Verification Pipeline**

### **NLI Model Training**

Train on datasets:
- **FEVER** (Fact Extraction and VERification)
- **MultiNLI** (Multi-Genre NLI)
- **LIAR** (Political claims)

### **Verification Process**

1. Extract claim from new article
2. Query Neo4j for similar claims
3. Run NLI model: Entailment / Contradiction / Neutral
4. Aggregate confidence scores
5. Update graph with verdict

---

## 🌐 **API Endpoints**

Once running, access the API at `http://localhost:8000`

### **Available Endpoints**

```
GET  /api/health              # Health check
POST /api/query               # Natural language query
GET  /api/entity/{id}         # Entity timeline
POST /api/claims/verify       # Fact-check a claim
GET  /api/graph/export        # Export subgraph
GET  /api/sources/credibility # Source reliability scores
```

### **API Documentation**

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## 📈 **Monitoring & Dashboards**

### **Access Points**

- **Neo4j Browser**: http://localhost:7474
- **Kafka UI**: http://localhost:8080
- **API Docs**: http://localhost:8000/docs
- **Ollama API**: http://localhost:11434

### **Monitoring Commands**

```bash
# Check service health
docker-compose ps

# View Neo4j logs
docker logs osint-neo4j

# View Kafka topics
docker exec osint-kafka kafka-topics --bootstrap-server localhost:9092 --list

# Check Ollama models
curl http://localhost:11434/api/tags
```

---

## 🧪 **Testing**

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test module
pytest tests/test_agents.py -v
```

---

## 🔐 **Security Considerations**

### **For Production Deployment:**

1. **Change default passwords** in `.env`
2. **Enable authentication** on all services
3. **Use SSL/TLS** for external connections
4. **Implement rate limiting** on API endpoints
5. **Secure API keys** using secrets management
6. **Enable audit logging**
7. **Set up firewalls** and network policies

---

## 🛠️ **Troubleshooting**

### **Common Issues**

**1. Ollama won't start**
```bash
# Check GPU availability
docker logs osint-ollama

# Fall back to CPU-only
# Remove GPU section from docker-compose.yml
```

**2. Neo4j connection refused**
```bash
# Wait for Neo4j to fully start (can take 30-60s)
docker logs osint-neo4j

# Verify connection
docker exec osint-neo4j cypher-shell -u neo4j -p osint_password_2026 "RETURN 1"
```

**3. Kafka consumer lag**
```bash
# Check consumer groups
docker exec osint-kafka kafka-consumer-groups --bootstrap-server localhost:9092 --list

# Reset offsets if needed
docker exec osint-kafka kafka-consumer-groups --bootstrap-server localhost:9092 --group osint-processors --reset-offsets --to-earliest --all-topics --execute
```

---

## 🎓 **Learning Resources**

- **LangGraph**: https://python.langchain.com/docs/langgraph
- **Neo4j Cypher**: https://neo4j.com/docs/cypher-manual/
- **Kafka Streams**: https://kafka.apache.org/documentation/streams/
- **Ollama**: https://ollama.ai/docs
- **NLI Models**: https://huggingface.co/tasks/text-classification

---

## 📋 **Development Roadmap**

### **Phase 1: Infrastructure** ✅
- [x] Project structure
- [x] Docker setup
- [x] Neo4j schema
- [x] Configuration management

### **Phase 2: Data Ingestion** (Next)
- [ ] RSS crawler
- [ ] Reddit crawler
- [ ] Web scraper
- [ ] Kafka producers

### **Phase 3: Multi-Agent System**
- [ ] LangGraph orchestration
- [ ] Agent implementations
- [ ] State management

### **Phase 4: NLI & Verification**
- [ ] Train NLI model
- [ ] Implement fact-checking
- [ ] Bias detection

### **Phase 5: API & Frontend**
- [ ] REST API
- [ ] Graph visualization
- [ ] Dashboard

---

## 🤝 **Contributing**

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 **Acknowledgments**

- **LangChain/LangGraph** - Multi-agent orchestration framework
- **Neo4j** - Graph database platform
- **Apache Kafka** - Streaming platform
- **Ollama** - Local LLM deployment
- **Hugging Face** - Pre-trained models

---

## 📧 **Contact**

**Project Maintainer**: Your Name  
**Email**: your.email@example.com  
**LinkedIn**: [Your Profile](https://linkedin.com/in/yourprofile)

**Target Market**: Defense Intelligence / OSINT / National Security

---

## ⚠️ **Disclaimer**

This system is designed for **legal and ethical OSINT analysis only**. Users are responsible for:
- Complying with all applicable laws and regulations
- Respecting data privacy and terms of service
- Using the system for legitimate intelligence purposes only

---

**Built with ❤️ for Defense Intelligence Applications**

*Showcasing real-time intelligence analysis, multi-agent AI, and temporal knowledge graphs at scale.*
