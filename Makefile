# -----------------------------------------
# Makefile for AI Pipeline Showcase
# -----------------------------------------

# Default environment settings
COMPOSE=docker compose
CLI=$(COMPOSE) run --rm airflow-cli
UP=$(COMPOSE) up -d
DOWN=$(COMPOSE) down
AIRFLOW_PORT=8081

#-----------------------------------------
# CORE COMMANDS
#-----------------------------------------

# Setup the entire project
setup:
	@echo "🛠️ Setting up AI Pipeline Showcase..."
	mkdir -p data vectorstore airflow/dags
	chmod -R 777 data vectorstore
	# Create .env file if it doesn't exist
	if [ ! -f .env ]; then \
		echo "# API Keys" > .env; \
		echo "OPENAI_API_KEY=your_openai_key_here" >> .env; \
		echo "HUGGINGFACEHUB_API_TOKEN=your_huggingface_token_here" >> .env; \
		echo "" >> .env; \
		echo "# Model Configuration" >> .env; \
		echo "MODEL_PROVIDER=openai" >> .env; \
		echo "HF_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2" >> .env; \
		echo "HF_LLM_MODEL=google/flan-t5-base" >> .env; \
		echo "" >> .env; \
		echo "AIRFLOW_UID=50000" >> .env; \
		echo "Created .env file. Please update with your API keys."; \
	fi
	@echo "✅ Project setup complete"
	@echo "Next steps:"
	@echo "1. Update your API keys in .env"
	@echo "2. Choose your model provider in .env (openai, huggingface, or mock)"
	@echo "3. Run 'make start' to start all services"

# Start everything
start:
	@echo "🚀 Starting AI Pipeline Showcase..."
	$(COMPOSE) up airflow-init
	$(UP)
	@echo "✅ Services started! Access:"
	@echo "  - Frontend: http://localhost:3000"
	@echo "  - API Docs: http://localhost:8000/docs"
	@echo "  - Airflow: http://localhost:$(AIRFLOW_PORT)"

# Stop everything
stop:
	@echo "🛑 Stopping all services..."
	$(DOWN)

# Restart everything (down + up)
restart:
	@echo "♻️ Restarting all services..."
	$(DOWN)
	$(COMPOSE) up airflow-init
	$(UP)

# Check service status
status:
	@echo "🔍 Checking service status..."
	$(COMPOSE) ps

# Health check
health:
	@echo "🩺 Checking API health..."
	curl -s http://localhost:8000/health | grep -q "healthy" && echo "API is healthy! ✅" || echo "API is not responding! ❌"
	@echo ""

#-----------------------------------------
# SERVICE MANAGEMENT
#-----------------------------------------

# Start just the API
start-api:
	@echo "🚀 Starting API only..."
	$(COMPOSE) up -d api
	@echo "✅ API started at http://localhost:8000/docs"

# Start just the frontend
start-frontend:
	@echo "🚀 Starting Frontend only..."
	$(COMPOSE) up -d api frontend
	@echo "✅ Frontend started at http://localhost:3000"

# Start just Airflow
start-airflow:
	@echo "🚀 Starting Airflow services..."
	$(COMPOSE) up airflow-init
	$(COMPOSE) up -d postgres redis airflow-apiserver airflow-scheduler airflow-worker airflow-triggerer
	@echo "✅ Airflow started at http://localhost:$(AIRFLOW_PORT)"

# View logs for a service
logs:
ifndef SERVICE
	@echo "⚠️  Error: Please provide SERVICE. Usage: make logs SERVICE=api"
	@exit 1
endif
	@echo "📜 Showing logs for service: $(SERVICE)"
	$(COMPOSE) logs -f $(SERVICE)

# Rebuild a specific service
rebuild:
ifndef SERVICE
	@echo "⚠️  Error: Please provide SERVICE. Usage: make rebuild SERVICE=frontend"
	@exit 1
endif
	@echo "🔨 Rebuilding service: $(SERVICE)..."
	$(COMPOSE) build $(SERVICE)
	$(COMPOSE) up -d $(SERVICE)
	@echo "✅ Service $(SERVICE) rebuilt and restarted"

# Rebuild Airflow services
rebuild-airflow:
	@echo "🔨 Rebuilding Airflow services..."
	# Build the shared image first
	$(COMPOSE) build airflow-init
	# Restart all Airflow services
	$(COMPOSE) up -d --build airflow-apiserver airflow-scheduler airflow-worker airflow-triggerer
	@echo "✅ Airflow services rebuilt and restarted"

# Rebuild a specific Airflow service
rebuild-airflow-service:
ifndef SERVICE
	@echo "⚠️  Error: Please provide SERVICE. Usage: make rebuild-airflow-service SERVICE=airflow-scheduler"
	@exit 1
endif
	@echo "🔨 Rebuilding Airflow service: $(SERVICE)..."
	$(COMPOSE) build $(SERVICE)
	$(COMPOSE) up -d $(SERVICE)
	@echo "✅ Airflow service $(SERVICE) rebuilt and restarted"

# Rebuild everything
rebuild-all:
	@echo "🔄 Rebuilding all services..."
	$(COMPOSE) down
	$(COMPOSE) build
	$(COMPOSE) up airflow-init
	$(UP)
	@echo "✅ All services rebuilt and restarted"

#-----------------------------------------
# AI MODEL MANAGEMENT
#-----------------------------------------

# Switch model provider
switch-provider:
	@echo "Switching model provider..."
	@echo "Options: openai, huggingface, mock"
	@read -p "Enter provider: " provider; \
	sed -i.bak "s/MODEL_PROVIDER=.*/MODEL_PROVIDER=$$provider/" .env && \
	echo "✅ Switched to $$provider provider"

# Check current model configuration
check-models:
	@echo "📋 Current model configuration:"
	@grep -E "MODEL_PROVIDER|HF_EMBEDDING_MODEL|HF_LLM_MODEL" .env || echo "⚠️ Model configuration not found in .env"
	@echo ""
	@echo "🔍 Available model providers:"
	@echo "  - openai:      Requires OPENAI_API_KEY"
	@echo "  - huggingface: Requires HUGGINGFACEHUB_API_TOKEN"
	@echo "  - mock:        No API key required (demo mode)"

# Test with a specific provider
test-provider:
ifndef PROVIDER
	@echo "⚠️ Error: Please provide PROVIDER. Usage: make test-provider PROVIDER=huggingface"
	@exit 1
endif
ifndef QUESTION
	@echo "⚠️ Error: Please provide QUESTION. Usage: make test-provider PROVIDER=huggingface QUESTION=\"What are the best products?\""
	@exit 1
endif
	@echo "🧪 Testing with $(PROVIDER) provider..."
	@echo "🤔 Asking: $(QUESTION)"
	MODEL_PROVIDER=$(PROVIDER) python -c "import asyncio; from llm.rag_chain import answer_question; print(asyncio.run(answer_question('$(QUESTION)')))"

#-----------------------------------------
# API WORKFLOW OPERATIONS
#-----------------------------------------

# Run ETL process
run-etl:
	@echo "🔄 Running ETL process..."
	curl -X POST "http://localhost:8000/etl/run" -H "Content-Type: application/json" -d '{"source": "sample"}'
	@echo "\n✅ ETL process triggered"

# Run vector store initialization
init-vectors:
	@echo "🧠 Initializing vector store..."
	curl -X POST "http://localhost:8000/vector/initialize"
	@echo "\n✅ Vector store initialization triggered"

# Ask a question to the RAG system
ask:
ifndef QUESTION
	@echo "⚠️  Error: Please provide QUESTION. Usage: make ask QUESTION=\"What are the best products?\""
	@exit 1
endif
	@echo "🤔 Asking: $(QUESTION)"
	curl -X POST "http://localhost:8000/ask" -H "Content-Type: application/json" -d "{\"question\": \"$(QUESTION)\"}"
	@echo "\n"

#-----------------------------------------
# AIRFLOW DAG MANAGEMENT
#-----------------------------------------

# List all DAGs
list-dags:
	@echo "📄 Listing all available DAGs..."
	$(CLI) airflow dags list

# List DAG import errors
list-errors:
	@echo "❌ Listing DAG import errors..."
	$(CLI) airflow dags list-import-errors

# Trigger a DAG by ID
trigger-dag:
ifndef DAG_ID
	@echo "⚠️  Error: Please provide DAG_ID. Usage: make trigger-dag DAG_ID=your_dag_id"
	@exit 1
endif
	@echo "🎯 Triggering DAG: $(DAG_ID)"
	$(CLI) airflow dags trigger $(DAG_ID)

# View DAG runs
dag-runs:
ifndef DAG_ID
	@echo "⚠️  Error: Please provide DAG_ID. Usage: make dag-runs DAG_ID=your_dag_id"
	@exit 1
endif
	@echo "🔎 Listing runs for DAG: $(DAG_ID)"
	$(CLI) airflow dags list-runs --dag-id $(DAG_ID)

#-----------------------------------------
# TROUBLESHOOTING
#-----------------------------------------

# Full clean (bring down containers + clean up volumes)
clean:
	@echo "🧹 Cleaning Docker environment..."
	$(COMPOSE) down -v
	@echo "✅ Environment cleaned"

# Debug connections
debug:
	@echo "🔍 Debugging connections..."
	# Check if debug.sh exists, if not create it
	if [ ! -f debug.sh ]; then \
		echo '#!/bin/bash\necho "=== AI Pipeline Debugging Script ==="\necho ""\necho "=== 1. Checking container status ==="\ndocker ps -a\necho ""\necho "=== 2. Checking API container logs ==="\ndocker compose logs api --tail 30\necho ""\necho "=== 3. Checking if API container is exposing the port correctly ==="\ndocker inspect -f "{{range \$$p, \$$conf := .NetworkSettings.Ports}}{{$p}} -> {{if \$$conf}}{{range \$$conf}}{{.HostIp}}:{{.HostPort}}{{end}}{{else}}not exposed{{end}}{{println}}{{end}}" $$(docker compose ps -q api)\necho ""\necho "=== 4. Checking network connectivity to API container ==="\nAPI_CONTAINER_IP=$$(docker inspect -f "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}" $$(docker compose ps -q api))\nif [ ! -z "$$API_CONTAINER_IP" ]; then\n  echo "API container IP: $$API_CONTAINER_IP"\n  docker run --rm busybox ping -c 3 $$API_CONTAINER_IP\nelse\n  echo "Could not determine API container IP!"\nfi\necho ""\necho "=== 5. Checking frontend container logs ==="\ndocker compose logs frontend --tail 30\necho ""\necho "=== 6. Checking environment variables ==="\necho "API container environment:"\ndocker exec $$(docker compose ps -q api) env | grep -E "PORT|HOST"\necho ""\necho "Frontend container environment:"\ndocker exec $$(docker compose ps -q frontend) env | grep -E "PORT|HOST|REACT"\necho ""\necho "=== 7. Checking if the API is actually running inside the container ==="\ndocker exec $$(docker compose ps -q api) ps aux | grep uvicorn\necho ""\necho "=== 8. Checking Docker network configuration ==="\necho "Networks:"\ndocker network ls\necho ""\necho "AI Pipeline network details:"\ndocker network inspect ai-pipeline-showcase_ai_pipeline_network\necho ""\necho "=== Debugging complete ==="\necho "To fix connection issues, try:"\necho "1. Restart the containers: docker compose restart api frontend"\necho "2. Rebuild the containers: docker compose up -d --build api frontend"\necho "3. Check for errors in the application code"\necho "4. If everything seems correct, try accessing the API with curl from inside the frontend container:"\necho "   docker exec -it $$(docker compose ps -q frontend) curl http://api:8000/health"' > debug.sh; \
		chmod +x debug.sh; \
	fi
	./debug.sh
