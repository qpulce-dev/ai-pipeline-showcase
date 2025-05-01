#!/usr/bin/env python
"""
RAG Sanity Check - Direct test of the RAG system without using the API
"""
import asyncio
import os
import sys

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Check for OpenAI API key
if not os.getenv("OPENAI_API_KEY"):
    print("Error: OPENAI_API_KEY not found in environment variables")
    print("Please make sure you have set this in your .env file")
    sys.exit(1)

# Set USE_REAL_RAG to True for this test
os.environ["USE_REAL_RAG"] = "true"

# Path adjustments to make imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    # Import the RAG function
    from llm.rag_chain import (
        answer_question,
        create_or_load_vectorstore,
        get_documents_from_db,
    )

    # Create async test function
    async def test_rag():
        print("🔍 RAG System Sanity Check")
        print("==========================")

        print("\n1️⃣ Testing database connectivity...")
        try:
            docs = await get_documents_from_db()
            print(f"✅ Successfully retrieved {len(docs)} documents from database")
            print(f"📄 Sample document: {docs[0].page_content[:100]}..." if docs else "⚠️ No documents found")
        except Exception as e:
            print(f"❌ Database error: {str(e)}")
            return

        print("\n2️⃣ Testing vector store...")
        try:
            vectorstore = await create_or_load_vectorstore()
            print("✅ Vector store created/loaded successfully")
        except Exception as e:
            print(f"❌ Vector store error: {str(e)}")
            return

        print("\n3️⃣ Testing RAG question answering...")
        try:
            question = "What are the best rated electronics products?"
            print(f"🤔 Question: {question}")
            answer = await answer_question(question)
            print(f"🤖 Answer: {answer}")
            print("✅ RAG question answering successful")
        except Exception as e:
            print(f"❌ RAG error: {str(e)}")
            print(f"❌ Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            return

        print("\n✅ All RAG components are working correctly!")

    # Run the test
    asyncio.run(test_rag())

except ImportError as e:
    print(f"❌ Import error: {str(e)}")
    print("Please make sure your environment is set up correctly")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
