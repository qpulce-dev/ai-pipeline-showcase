# test_hf.py
import os

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.llms import HuggingFaceHub

# Test embeddings (doesn't need API key)
print("Testing HuggingFace Embeddings...")
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
result = embeddings.embed_query("Hello world")
print(f"Embedding dimensions: {len(result)}")  # Should be 384

# Test LLM (needs API key)
print("\nTesting HuggingFace Hub LLM...")
llm = HuggingFaceHub(
    repo_id="google/flan-t5-base",
    huggingfacehub_api_token=os.getenv("HUGGINGFACEHUB_API_TOKEN"),
    model_kwargs={"temperature": 0.7, "max_length": 64}
)
result = llm.invoke("What is machine learning?")
print(f"LLM response: {result}")
