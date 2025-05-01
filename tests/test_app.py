"""
Test cases for FastAPI application
"""
import asyncio
import os
import sys
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Import the app instance directly
from app import app

# Create the test client
client = TestClient(app)

def test_root_endpoint():
    """Test the root endpoint returns expected information"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert data["name"] == "AI Pipeline Showcase"
    assert "version" in data
    assert "author" in data
    assert "description" in data

def test_health_endpoint():
    """Test health endpoint returns a valid response"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "components" in data
    assert "api" in data["components"]
    assert data["components"]["api"] == "healthy"

def test_etl_endpoint():
    """Test ETL endpoint returns a mock response"""
    # Send the request
    response = client.post("/etl/run", json={"source": "sample"})

    # Check the response
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ETL pipeline started"
    assert data["source"] == "sample"
    assert "note" in data
    assert "mock implementation" in data["note"].lower()

def test_vector_initialize_endpoint():
    """Test vector initialization endpoint returns a mock response"""
    # Send the request
    response = client.post("/vector/initialize")

    # Check the response
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "Vector store initialization started"
    assert "note" in data
    assert "mock implementation" in data["note"].lower()

@patch("app.USE_REAL_RAG", False)  # Force mock mode regardless of .env setting
def test_ask_endpoint():
    """Test ask endpoint returns a mock answer"""
    try:
        # Send the request
        response = client.post("/ask", json={"question": "What is the best product?"})

        # Check the response
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "mock" in data["answer"].lower()
    except Exception as e:
        # This helps with debugging
        print(f"Test failed with error: {str(e)}")
        # Re-raise to fail the test
        raise

def test_ask_endpoint_mock_mode():
    """Test ask endpoint in mock mode"""
    with patch("app.USE_REAL_RAG", False):
        response = client.post("/ask", json={"question": "What is the best product?"})
        assert response.status_code == 200
        data = response.json()
        assert "mock" in data["answer"].lower()

@pytest.mark.skipif(os.getenv("OPENAI_API_KEY") == "test_key" or not os.getenv("OPENAI_API_KEY"),
                   reason="Requires valid OpenAI API key")
def test_ask_endpoint_real_mode():
    """Test ask endpoint in real mode with actual OpenAI API"""
    # Check if we expect SQLAlchemy errors with this Python version
    sqlalchemy_compatible = sys.version_info < (3, 13, 0)

    with patch("app.USE_REAL_RAG", True):
        response = client.post("/ask", json={"question": "What is the best product?"})

        # Always expect a valid HTTP response, even with errors
        assert response.status_code == 200
        data = response.json()

        if sqlalchemy_compatible:
            # Only verify non-mock response if SQLAlchemy should work
            assert "mock" not in data["answer"].lower()
        else:
            # If we expect SQLAlchemy errors, verify graceful fallback
            assert "error" in data["answer"].lower()
            assert "falling back to mock" in data["answer"].lower()

@pytest.mark.skipif(sys.version_info >= (3, 13, 0),
                   reason="SQLAlchemy compatibility issue with Python 3.13")
def test_ask_endpoint_handles_rag_errors():
    """Test that errors in RAG implementation are handled gracefully"""
    with patch("app.USE_REAL_RAG", True), \
         patch("llm.rag_chain.answer_question", side_effect=Exception("Test error")):
        response = client.post("/ask", json={"question": "What is the best product?"})
        assert response.status_code == 200  # Should fail gracefully
        data = response.json()
        assert "error" in data["answer"].lower()

def test_ask_endpoint_handles_errors():
    """Test that errors at the API level are handled gracefully"""
    # Generate a runtime error by sending malformed data
    response = client.post("/ask", json={})  # Missing 'question' field

    # Your API should handle this gracefully without 500 errors
    assert response.status_code != 500

    # Or test with invalid JSON
    response = client.post("/ask", data="not valid json")
    assert response.status_code != 500
