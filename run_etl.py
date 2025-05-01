#!/usr/bin/env python
"""
ETL Run Script - Creates and populates the products database
"""
import asyncio
import os

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def run_etl():
    print("📊 Running ETL Process")
    print("======================")

    try:
        from etl.run_etl import process_data

        print("Processing data...")
        result = await process_data(source="sample")

        print(f"✅ ETL process completed successfully")
        print(f"• Source: {result['source']}")
        print(f"• Rows processed: {result['rows_processed']}")
        print(f"• Timestamp: {result['timestamp']}")

        return True
    except Exception as e:
        print(f"❌ ETL process failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(run_etl())
