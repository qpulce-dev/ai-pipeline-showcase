"""
ETL Pipeline for data processing
"""
import asyncio
import logging
import os
from typing import Any, Dict, List, Optional

import duckdb
import pandas as pd

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define data paths
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "analytics.duckdb")

async def process_data(source: str = "sample") -> Dict[str, Any]:
    """
    Process data from the specified source and store in DuckDB

    Args:
        source: Data source identifier

    Returns:
        Dict with processing stats
    """
    logger.info(f"Starting ETL process for source: {source}")

    try:
        # Simulate data extraction (could be API call, CSV download, etc.)
        raw_data = await extract_data(source)

        # Transform the data
        transformed_data = transform_data(raw_data)

        # Load data into DuckDB
        stats = load_data(transformed_data)

        logger.info(f"ETL process completed successfully: {stats}")
        return {
            "status": "success",
            "source": source,
            "rows_processed": stats["rows_processed"],
            "timestamp": stats["timestamp"]
        }

    except Exception as e:
        logger.error(f"ETL process failed: {str(e)}")
        raise

async def extract_data(source: str) -> pd.DataFrame:
    """
    Extract data from specified source
    """
    logger.info(f"Extracting data from {source}")

    # For demo purposes, generate sample data if source is "sample"
    if source == "sample":
        await asyncio.sleep(1)  # Simulate API delay

        # Generate sample product data with reviews
        data = {
            "product_id": [f"P{i:03d}" for i in range(1, 101)],
            "product_name": [f"Product {i}" for i in range(1, 101)],
            "category": ["Electronics", "Clothing", "Home", "Books", "Food"] * 20,
            "price": [round(10 + i * 2.5, 2) for i in range(1, 101)],
            "review_text": [
                f"This product is {'great' if i % 5 == 0 else 'good' if i % 3 == 0 else 'average'}. " +
                f"{'Highly recommend!' if i % 4 == 0 else 'Would buy again.' if i % 3 == 0 else 'Decent value.'}"
                for i in range(1, 101)
            ],
            "rating": [(i % 5) + 1 for i in range(1, 101)]
        }

        return pd.DataFrame(data)
    else:
        # In a real application, this would fetch data from APIs, databases, etc.
        # For demo, we'll just raise an error for unknown sources
        raise ValueError(f"Unknown data source: {source}")

def transform_data(data: pd.DataFrame) -> pd.DataFrame:
    """
    Transform raw data for analysis
    """
    logger.info("Transforming data")

    # Demo transformations
    df = data.copy()

    # Add derived columns
    df["is_recommended"] = df["rating"] >= 4
    df["price_category"] = pd.cut(
        df["price"],
        bins=[0, 30, 60, 100, float("inf")],
        labels=["Budget", "Mid-range", "Premium", "Luxury"]
    )

    # Calculate sentiment score (simplified)
    df["sentiment_score"] = df["review_text"].apply(
        lambda x: len([w for w in ["great", "excellent", "amazing", "recommend"] if w in x.lower()]) -
                 len([w for w in ["bad", "poor", "terrible", "disappointing"] if w in x.lower()])
    )

    return df

# In etl/run_etl.py, modify the load_data function:
def load_data(data: pd.DataFrame) -> Dict[str, Any]:
    """
    Load transformed data into DuckDB
    """
    import datetime

    logger.info(f"Loading {len(data)} rows into DuckDB")

    # Connect to DuckDB
    conn = duckdb.connect(DB_PATH)

    # Create table if it doesn't exist
    conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            product_id VARCHAR,
            product_name VARCHAR,
            category VARCHAR,
            price DOUBLE,
            review_text VARCHAR,
            rating INTEGER,
            is_recommended BOOLEAN,
            price_category VARCHAR,
            sentiment_score INTEGER,
            processed_at TIMESTAMP
        )
    """)

    # Add processing timestamp
    data["processed_at"] = datetime.datetime.now()

    # Fix: Change how we insert data
    # Instead of using parameters, register the dataframe directly
    conn.register('data_df', data)
    conn.execute("INSERT INTO products SELECT * FROM data_df")

    # Get row count for reporting
    result = conn.execute("SELECT COUNT(*) FROM products").fetchone()
    total_rows = result[0] if result else 0

    conn.close()

    return {
        "rows_processed": len(data),
        "total_rows": total_rows,
        "timestamp": datetime.datetime.now().isoformat()
    }

if __name__ == "__main__":
    # For testing the ETL process directly
    import asyncio
    asyncio.run(process_data())
