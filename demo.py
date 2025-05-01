#!/usr/bin/env python
"""
Demo script to showcase the AI Pipeline
"""
import asyncio
import os
import sys
import argparse
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import components
try:
    from etl.run_etl import process_data
    from llm.rag_chain import answer_question
    from vectorstore.index_faiss import initialize_vector_store
except ImportError as e:
    logger.error(f"Import error: {e}")
    logger.error("Make sure you're running this script from the project root")
    sys.exit(1)

async def run_demo(run_etl: bool = True, question: str = None):
    """Run the demo pipeline"""
    print("📊 AI Pipeline Demo")
    print("===================")
    
    if run_etl:
        print("\n🔄 Step 1: Running ETL Process...")
        try:
            etl_result = await process_data()
            print(f"✅ ETL completed: {etl_result['rows_processed']} rows processed")
        except Exception as e:
            print(f"❌ ETL failed: {str(e)}")
            return
    
    print("\n🔧 Step 2: Initializing Vector Store...")
    try:
        await initialize_vector_store()
        print("✅ Vector store ready")
    except Exception as e:
        print(f"❌ Vector store initialization failed: {str(e)}")
        return
    
    # Get question from args or prompt user
    if not question:
        print("\n🤖 Step 3: Ask a question about the data")
        question = input("Enter your question: ")
    else:
        print(f"\n🤖 Step 3: Answering question: {question}")
    
    try:
        print("\n💭 Thinking...")
        answer = await answer_question(question)
        print("\n📝 Answer:")
        print(answer)
        print("\n✨ Demo completed successfully!")
    except Exception as e:
        print(f"❌ Error answering question: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the AI Pipeline demo")
    parser.add_argument("--skip-etl", action="store_true", help="Skip the ETL step")
    parser.add_argument("--question", type=str, help="Question to ask the system")
    
    args = parser.parse_args()
    
    asyncio.run(run_demo(
        run_etl=not args.skip_etl,
        question=args.question
    ))
