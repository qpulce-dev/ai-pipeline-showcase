"""
AI Pipeline Showcase - Main Application (Simplified Version)
"""
import logging
import os
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Make sure this is at the top of your file if not already there
load_dotenv()

# Default to mock mode unless specifically enabled
USE_REAL_RAG = os.getenv("USE_REAL_RAG", "false").lower() == "true"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="AI Pipeline Showcase",
    description="Demonstration of ETL + LLM RAG pipeline for technical interviews",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class Query(BaseModel):
    question: str

class ETLRequest(BaseModel):
    source: str = "sample"  # Default to sample data

class HealthResponse(BaseModel):
    status: str
    components: Dict[str, str]

@app.get("/", tags=["General"])
async def root():
    """Root endpoint with basic information"""
    return {
        "name": "AI Pipeline Showcase",
        "version": "0.1.0",
        "author": "Queanu Pulce",
        "description": "Full-stack AI data pipeline demonstration"
    }

@app.post("/ask", tags=["RAG"])
async def ask_question(query: Query):
    """Ask a question to the RAG system"""
    logger.info(f"Received question: {query.question}")
    try:
        if USE_REAL_RAG:
            # Use the actual RAG implementation
            try:
                from llm.rag_chain import answer_question
                answer = await answer_question(query.question)
                return {
                    "answer": answer,
                    "sources": []  # You could populate this with actual sources
                }
            except Exception as e:
                logger.error(f"Error in RAG implementation: {str(e)}")
                # Fall back to mock mode if there's an error
                return {
                    "answer": f"Error in RAG system. Falling back to mock: '{query.question}'",
                    "sources": []
                }
        else:
            # Use mock response in demo mode
            return {
                "answer": f"This is a mock answer to: '{query.question}'. The RAG system is currently in demo mode.",
                "sources": []
            }
    except Exception as e:
        logger.error(f"Error processing question: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")

@app.post("/etl/run", tags=["ETL"])
async def run_etl_pipeline(request: ETLRequest, background_tasks: BackgroundTasks):
    """Trigger ETL pipeline run"""
    logger.info(f"Triggering ETL pipeline for source: {request.source}")

    # Instead of calling the real ETL process, return a mock response
    return {
        "status": "ETL pipeline started",
        "source": request.source,
        "note": "This is a mock implementation."
    }

@app.post("/vector/initialize", tags=["Vector Store"])
async def initialize_vectors(background_tasks: BackgroundTasks):
    """Initialize or update vector store"""
    logger.info("Triggering vector store initialization")

    # Mock vector store initialization
    return {
        "status": "Vector store initialization started",
        "note": "This is a mock implementation."
    }

@app.get("/health", response_model=HealthResponse, tags=["Monitoring"])
async def health_check():
    """Health check endpoint to verify all components are operational"""
    # Basic health check
    components = {
        "api": "healthy",
        "database": "mock",
        "vector_store": "mock"
    }

    # Create data directory if it doesn't exist
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(data_dir, exist_ok=True)
    components["database"] = "initialized"

    # Create vector store directory if it doesn't exist
    vector_dir = os.path.join(os.path.dirname(__file__), "vectorstore")
    os.makedirs(vector_dir, exist_ok=True)
    components["vector_store"] = "initialized"

    return {"status": "healthy", "components": components}

if __name__ == "__main__":
    import os

    import uvicorn

    # Create list of directories to watch (only watch directories that exist)
    reload_dirs = ["."]
    for dir_path in ["./airflow/dags"]:  # Use the correct path
        if os.path.exists(dir_path):
            reload_dirs.append(dir_path)

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True, reload_dirs=reload_dirs)
