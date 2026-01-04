# Quick Setup Guide

## 1. Prerequisites Check

```powershell
# Check Python version (need 3.10+)
python --version

# Check Docker
docker --version
docker-compose --version
```

## 2. Initial Setup (5 minutes)

```powershell
# 1. Create virtual environment
python -m venv venv
.\venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Download Spacy model
python -m spacy download en_core_web_sm

# 4. Copy environment file
copy .env.example .env
```

## 3. Start Infrastructure (10 minutes)

```powershell
# Start all services
docker-compose up -d

# Wait for services to start (30-60 seconds)
Start-Sleep -Seconds 60

# Check service status
docker-compose ps
```

## 4. Initialize Database

```powershell
# Initialize Neo4j schema
python graph/init_schema.py

# Verify in browser: http://localhost:7474
# Username: neo4j
# Password: osint_password_2026
```

## 5. Download LLM Model

```powershell
# Pull DeepSeek-V3 (or use llama3:70b)
docker exec -it osint-ollama ollama pull deepseek-v3

# This may take 10-30 minutes depending on your internet speed
```

## 6. Verify Everything Works

```powershell
# Test Neo4j connection
docker exec osint-neo4j cypher-shell -u neo4j -p osint_password_2026 "RETURN 1"

# Test Kafka
docker exec osint-kafka kafka-topics --bootstrap-server localhost:9092 --list

# Test Ollama
curl http://localhost:11434/api/tags
```

## 7. Access Points

- **Neo4j Browser**: http://localhost:7474 (neo4j / osint_password_2026)
- **Kafka UI**: http://localhost:8080
- **Ollama API**: http://localhost:11434

## Troubleshooting

### Services won't start
```powershell
# Check logs
docker-compose logs neo4j
docker-compose logs kafka
docker-compose logs ollama

# Restart specific service
docker-compose restart neo4j
```

### Port conflicts
```powershell
# Check what's using a port
netstat -ano | findstr :7474
netstat -ano | findstr :9092
```

### Out of memory
- Increase Docker memory in Docker Desktop settings
- Minimum: 8GB RAM
- Recommended: 16GB+ RAM

## Next Steps

Once Phase 1 is complete and verified:
- Phase 2: Implement data crawlers
- Phase 3: Build LangGraph agents
- Phase 4: Train NLI model
- Phase 5: Create API endpoints

## Quick Test Commands

```powershell
# Test Python imports
python -c "import neo4j, kafka, transformers; print('All imports OK')"

# Test configuration loading
python config/settings.py

# List Docker volumes
docker volume ls
```
