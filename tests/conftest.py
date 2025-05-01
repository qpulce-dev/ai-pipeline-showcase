"""
Pytest configuration for AI Pipeline Showcase
"""
import asyncio
import os
import sys
from unittest.mock import patch

import pytest

# Add the parent directory to sys.path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Create fixture for mocking OpenAI API calls
@pytest.fixture
def mock_openai():
    """Mock OpenAI API calls to prevent actual API usage during tests"""
    with patch('langchain.embeddings.openai.OpenAIEmbeddings.__call__') as mock_embeddings:
        # Mock embeddings to return predictable vectors
        mock_embeddings.return_value = [[0.1] * 1536]  # OpenAI embeddings are 1536 dimensions
        yield mock_embeddings

@pytest.fixture
def mock_llm():
    """Mock LLM calls to prevent actual API usage during tests"""
    with patch('langchain.chat_models.ChatOpenAI.invoke') as mock_chat:
        # Mock chat completion to return a simple response
        mock_chat.return_value = "This is a mocked response from the LLM."
        yield mock_chat

@pytest.fixture
def mock_db():
    """Mock DuckDB to prevent database operations during tests"""
    with patch('duckdb.connect') as mock_connect:
        # Create a mock cursor that returns empty results
        mock_cursor = mock_connect.return_value
        mock_cursor.execute.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []
        mock_cursor.fetchone.return_value = [0]
        yield mock_connect

@pytest.fixture
def mock_vector_store():
    """Mock FAISS vector store"""
    with patch('langchain.vectorstores.FAISS.from_documents') as mock_from_docs, \
         patch('langchain.vectorstores.FAISS.load_local') as mock_load_local, \
         patch('langchain.vectorstores.FAISS.save_local') as mock_save_local:

        # Create a mock vector store
        mock_vectorstore = mock_from_docs.return_value
        mock_load_local.return_value = mock_vectorstore

        # Mock similarity search to return empty results
        mock_vectorstore.similarity_search.return_value = []
        mock_vectorstore.as_retriever.return_value.get_relevant_documents.return_value = []

        yield {
            'from_documents': mock_from_docs,
            'load_local': mock_load_local,
            'save_local': mock_save_local,
            'instance': mock_vectorstore
        }

@pytest.fixture
def mock_async_openai():
    """Mock async OpenAI API calls"""
    async def mock_aembedding(*args, **kwargs):
        return [[0.1] * 1536]

    with patch('langchain.embeddings.openai.OpenAIEmbeddings.aembed_documents', new=mock_aembedding), \
         patch('langchain.embeddings.openai.OpenAIEmbeddings.aembed_query', new=mock_aembedding):
        yield
