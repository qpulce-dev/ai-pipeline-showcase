"""
RAG (Retrieval Augmented Generation) chain with production-grade fallbacks
"""
import asyncio
import logging
import os
import time
from functools import wraps
from typing import Any, Dict, List, Optional, Union

import duckdb
from langchain.prompts import PromptTemplate
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS

# Setup logging with more details
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define data paths
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
VECTOR_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "vectorstore")
DB_PATH = os.path.join(DATA_DIR, "analytics.duckdb")
VECTOR_PATH = os.path.join(VECTOR_DIR, "faiss_index")

os.makedirs(VECTOR_DIR, exist_ok=True)

# Configuration from environment with validation
MODEL_PROVIDER = os.getenv("MODEL_PROVIDER", "openai").lower()
if MODEL_PROVIDER not in ["openai", "huggingface", "mock"]:
    logger.warning(f"Invalid MODEL_PROVIDER: {MODEL_PROVIDER}. Falling back to 'openai'")
    MODEL_PROVIDER = "openai"

HF_EMBEDDING_MODEL = os.getenv("HF_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
HF_LLM_MODEL = os.getenv("HF_LLM_MODEL", "google/flan-t5-base")

# Check if required API keys are present
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
HUGGINGFACEHUB_API_TOKEN = os.getenv("HUGGINGFACEHUB_API_TOKEN")

if MODEL_PROVIDER == "openai" and not OPENAI_API_KEY:
    logger.warning("OpenAI selected but OPENAI_API_KEY not provided. Will try HuggingFace or fall back to mock.")
    MODEL_PROVIDER = "huggingface"

if MODEL_PROVIDER == "huggingface" and not HUGGINGFACEHUB_API_TOKEN:
    logger.warning("HuggingFace selected but HUGGINGFACEHUB_API_TOKEN not provided. Will fall back to mock.")
    MODEL_PROVIDER = "mock"

# Maximum retry attempts
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
# Retry backoff in seconds
RETRY_BACKOFF = int(os.getenv("RETRY_BACKOFF", "2"))

# Retry decorator for API calls
def retry_with_backoff(max_retries=MAX_RETRIES, backoff_in_seconds=RETRY_BACKOFF):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            retries = 0
            while retries <= max_retries:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries > max_retries:
                        logger.error(f"Maximum retries ({max_retries}) exceeded for {func.__name__}: {str(e)}")
                        raise
                    wait_time = backoff_in_seconds * (2 ** (retries - 1))  # Exponential backoff
                    logger.warning(f"Retry {retries}/{max_retries} for {func.__name__} after {wait_time}s. Error: {str(e)}")
                    await asyncio.sleep(wait_time)
        return wrapper
    return decorator

# Get embeddings with complete fallback chain
def get_embeddings():
    """Create embeddings with fallback chain: Provider -> OpenAI -> Mock"""
    # First try specified provider
    if MODEL_PROVIDER == "huggingface":
        logger.info(f"Attempting to use HuggingFace embeddings: {HF_EMBEDDING_MODEL}")
        try:
            from langchain_community.embeddings import HuggingFaceEmbeddings
            return HuggingFaceEmbeddings(model_name=HF_EMBEDDING_MODEL)
        except Exception as e:
            logger.warning(f"Failed to initialize HuggingFace embeddings: {str(e)}")

    # Next try OpenAI if not already attempted
    if MODEL_PROVIDER != "openai" and OPENAI_API_KEY:
        logger.info("Falling back to OpenAI embeddings")
        try:
            from langchain_openai import OpenAIEmbeddings
            return OpenAIEmbeddings(
                model="text-embedding-ada-002",
                openai_api_key=OPENAI_API_KEY
            )
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI embeddings: {str(e)}")

    # If specified provider is OpenAI, try it directly
    if MODEL_PROVIDER == "openai" and OPENAI_API_KEY:
        logger.info("Using OpenAI embeddings")
        try:
            from langchain_openai import OpenAIEmbeddings
            return OpenAIEmbeddings(
                model="text-embedding-ada-002",
                openai_api_key=OPENAI_API_KEY
            )
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI embeddings: {str(e)}")

    # Final fallback to mock embeddings
    logger.warning("All embedding options failed or not configured. Using mock embeddings.")
    class MockEmbeddings:
        """Mock embeddings for fallback"""
        def embed_documents(self, texts):
            return [[0.1] * 384 for _ in texts]

        def embed_query(self, text):
            return [0.1] * 384

    return MockEmbeddings()

# Get LLM with complete fallback chain
def get_llm():
    """Create LLM with fallback chain: Provider -> OpenAI -> Mock"""
    # First try specified provider
    if MODEL_PROVIDER == "huggingface":
        logger.info(f"Attempting to use HuggingFace LLM: {HF_LLM_MODEL}")
        try:
            # Try ChatHuggingFace if available (newer versions)
            try:
                from langchain_community.chat_models import ChatHuggingFace
                return ChatHuggingFace(
                    repo_id=HF_LLM_MODEL,
                    huggingfacehub_api_token=HUGGINGFACEHUB_API_TOKEN,
                    model_kwargs={"temperature": 0, "max_length": 512}
                )
            except (ImportError, Exception) as e:
                logger.info(f"ChatHuggingFace not available: {str(e)}. Trying HuggingFaceHub.")

                # Fall back to HuggingFaceHub
                from langchain_community.llms import HuggingFaceHub
                return HuggingFaceHub(
                    repo_id=HF_LLM_MODEL,
                    huggingfacehub_api_token=HUGGINGFACEHUB_API_TOKEN,
                    model_kwargs={"temperature": 0, "max_length": 512}
                )
        except Exception as e:
            logger.warning(f"Failed to initialize HuggingFace LLM: {str(e)}")

    # Next try OpenAI if not already attempted
    if MODEL_PROVIDER != "openai" and OPENAI_API_KEY:
        logger.info("Falling back to OpenAI LLM")
        try:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model_name="gpt-3.5-turbo",
                temperature=0,
                openai_api_key=OPENAI_API_KEY
            )
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI LLM: {str(e)}")

    # If specified provider is OpenAI, try it directly
    if MODEL_PROVIDER == "openai" and OPENAI_API_KEY:
        logger.info("Using OpenAI LLM")
        try:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model_name="gpt-3.5-turbo",
                temperature=0,
                openai_api_key=OPENAI_API_KEY
            )
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI LLM: {str(e)}")

    # Final fallback to mock LLM
    logger.warning("All LLM options failed or not configured. Using mock LLM.")
    from langchain.llms.fake import FakeListLLM
    return FakeListLLM(responses=["This is a mock response from the AI assistant. The system is running in demo mode."])

# Initialize embeddings
embeddings = get_embeddings()

@retry_with_backoff()
async def get_documents_from_db() -> List[Document]:
    """
    Retrieve product data from DuckDB and convert to LangChain Documents
    """
    logger.info("Retrieving documents from DuckDB")

    try:
        # Connect to DuckDB
        conn = duckdb.connect(DB_PATH)

        # Query products
        result = conn.execute("""
            SELECT
                product_id,
                product_name,
                category,
                price,
                review_text,
                rating,
                price_category,
                sentiment_score
            FROM products
        """).fetchall()

        # Convert to Documents
        documents = []
        for row in result:
            product_id, name, category, price, review, rating, price_cat, sentiment = row

            # Create document text
            text = f"""Product: {name}
Category: {category}
Price:  ({price_cat})
Rating: {rating}/5
Review: {review}
Sentiment Score: {sentiment}
"""

            # Create metadata
            metadata = {
                "product_id": product_id,
                "name": name,
                "category": category,
                "price": price,
                "rating": rating
            }

            # Create document
            doc = Document(page_content=text, metadata=metadata)
            documents.append(doc)

        conn.close()
        logger.info(f"Retrieved {len(documents)} documents from database")
        return documents

    except Exception as e:
        logger.error(f"Error retrieving documents: {str(e)}")
        # Return empty list as a fallback
        return []

@retry_with_backoff()
async def create_or_load_vectorstore() -> FAISS:
    """
    Create or load FAISS vector store from documents
    """
    # Check if vector store exists
    if os.path.exists(VECTOR_PATH) and os.path.isdir(VECTOR_PATH) and len(os.listdir(VECTOR_PATH)) > 0:
        logger.info("Loading existing vector store")
        try:
            vectorstore = FAISS.load_local(VECTOR_PATH, embeddings)
            return vectorstore
        except Exception as e:
            logger.error(f"Error loading vector store: {str(e)}")
            # Fall through to recreation

    # Create new vector store
    logger.info("Creating new vector store")

    # Get documents
    documents = await get_documents_from_db()

    if not documents:
        logger.warning("No documents retrieved from database")
        # Create a minimal vector store with a placeholder document
        placeholder = Document(
            page_content="Placeholder document for empty vector store",
            metadata={"source": "placeholder"}
        )
        documents = [placeholder]

    # Split documents
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100
    )
    splits = text_splitter.split_documents(documents)

    # Create vector store
    vectorstore = FAISS.from_documents(splits, embeddings)

    # Save vector store
    try:
        vectorstore.save_local(VECTOR_PATH)
        logger.info(f"Created vector store with {len(splits)} chunks")
    except Exception as e:
        logger.error(f"Error saving vector store: {str(e)}")

    return vectorstore

@retry_with_backoff()
async def answer_question(question: str) -> str:
    """
    Answer a question using RAG with full fallback chain
    """
    logger.info(f"Answering question: {question}")

    try:
        # Get vector store
        vectorstore = await create_or_load_vectorstore()

        # Retrieve relevant documents
        relevant_docs = vectorstore.similarity_search(question, k=3)

        if not relevant_docs:
            logger.warning("No relevant documents found")
            return "I don't have enough information to answer that question based on the available data."

        # Combine relevant documents into context
        context = "\n\n".join([doc.page_content for doc in relevant_docs])

        # Create prompt template
        template = """
        You are a helpful product recommendation assistant. Use the following context to answer the question.
        If you don't know the answer based on the context, just say that you don't know.

        Context:
        {context}

        Question:
        {question}

        Answer:
        """

        # Format the prompt
        prompt = template.replace("{context}", context).replace("{question}", question)

        # Get the LLM
        llm = get_llm()

        # Get response from LLM
        response = llm.invoke(prompt)

        # Handle empty responses or unhelpful responses (like just "0")
        response_str = str(response).strip()
        if not response_str or response_str in ["0", "1", "None"]:
            # Debug information
            logger.info(f"Received unhelpful response from LLM: '{response_str}'")
            logger.info(f"Retrieved {len(relevant_docs)} documents, examining for best products")

            # For HuggingFace models that might give minimal responses
            # Generate a more helpful response based on the context
            best_products = []
            for i, doc in enumerate(relevant_docs):
                rating = doc.metadata.get("rating", 0)
                name = doc.metadata.get("name", "Unknown product")
                category = doc.metadata.get("category", "Unknown category")

                logger.info(f"Doc {i}: {name}, Rating: {rating}, Category: {category}")

                if isinstance(rating, (int, float)) and rating >= 4:  # Consider 4+ ratings as "best"
                    best_products.append({
                        "name": name,
                        "rating": rating,
                        "category": category
                    })

            logger.info(f"Found {len(best_products)} highly rated products")

            if best_products:
                best_products.sort(key=lambda x: x["rating"], reverse=True)
                products_text = ", ".join([f"{p['name']} (Rating: {p['rating']}/5)" for p in best_products[:3]])
                return f"Based on our product database, the best rated products are: {products_text}"
            else:
                # Let's check what ratings we actually have
                all_ratings = [doc.metadata.get("rating", 0) for doc in relevant_docs]
                logger.info(f"All ratings in retrieved documents: {all_ratings}")

                # If we have any ratings at all, return the highest ones
                if all_ratings:
                    highest_rating = max(all_ratings) if all_ratings else 0
                    highest_rated = [doc for doc in relevant_docs
                                    if doc.metadata.get("rating", 0) == highest_rating]

                    if highest_rated:
                        products_text = ", ".join([
                            f"{doc.metadata.get('name', 'Unknown product')} (Rating: {doc.metadata.get('rating', 0)}/5)"
                            for doc in highest_rated[:3]
                        ])
                        return f"The highest rated products in our database are: {products_text}"

                return "I don't have enough information about highly rated products to answer your question accurately."

        logger.info("Question answered successfully")
        return response_str

    except Exception as e:
        logger.error(f"Error answering question: {str(e)}")
        return "I'm currently experiencing technical difficulties. Please try again later or contact support if the problem persists."

if __name__ == "__main__":
    # For testing the RAG chain directly
    import asyncio

    async def test():
        # Test question
        question = "What are the best electronics products based on ratings?"
        answer = await answer_question(question)
        print(f"Q: {question}")
        print(f"A: {answer}")

    asyncio.run(test())
