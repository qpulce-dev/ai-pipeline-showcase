"""
Test cases for ETL functionality
"""
import asyncio
import os
import sys
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from etl.run_etl import extract_data, load_data, process_data, transform_data


@pytest.mark.etl
@pytest.mark.unit
def test_transform_data():
    """Test data transformation logic"""
    # Create sample input data
    input_data = pd.DataFrame({
        "product_id": ["P001", "P002", "P003"],
        "product_name": ["Test Product 1", "Test Product 2", "Test Product 3"],
        "category": ["Electronics", "Clothing", "Home"],
        "price": [25.99, 45.50, 75.00],
        "review_text": [
            "This product is great. Highly recommend!",
            "Good product but a bit expensive.",
            "Average product. Decent value."
        ],
        "rating": [5, 3, 2]
    })

    # Transform the data
    result = transform_data(input_data)

    # Verify the transformation
    assert "is_recommended" in result.columns
    assert "price_category" in result.columns
    assert "sentiment_score" in result.columns

    # Check is_recommended logic
    assert result.loc[0, "is_recommended"] == True  # Rating 5
    assert result.loc[1, "is_recommended"] == False  # Rating 3
    assert result.loc[2, "is_recommended"] == False  # Rating 2

    # Check price categorization
    assert result.loc[0, "price_category"] == "Budget"
    assert result.loc[1, "price_category"] == "Mid-range"
    assert result.loc[2, "price_category"] == "Premium"

    # Check sentiment score calculation
    assert result.loc[0, "sentiment_score"] > 0  # Positive review
    assert result.loc[2, "sentiment_score"] <= 0  # Negative/neutral review

@pytest.mark.etl
@pytest.mark.asyncio
async def test_extract_data_sample():
    """Test data extraction for sample data"""
    # Extract sample data
    result = await extract_data("sample")

    # Verify the result
    assert isinstance(result, pd.DataFrame)
    assert len(result) > 0
    assert "product_id" in result.columns
    assert "product_name" in result.columns
    assert "category" in result.columns
    assert "price" in result.columns
    assert "review_text" in result.columns
    assert "rating" in result.columns

@pytest.mark.etl
@pytest.mark.asyncio
async def test_extract_data_invalid_source():
    """Test data extraction with invalid source"""
    # Try to extract data from an invalid source
    with pytest.raises(ValueError):
        await extract_data("invalid_source")

@pytest.mark.etl
@pytest.mark.unit
def test_load_data(mock_db):
    """Test data loading into DuckDB"""
    # Create sample data
    data = pd.DataFrame({
        "product_id": ["P001", "P002"],
        "product_name": ["Test Product 1", "Test Product 2"],
        "category": ["Electronics", "Clothing"],
        "price": [25.99, 45.50],
        "review_text": ["Great", "Good"],
        "rating": [5, 3],
        "is_recommended": [True, False],
        "price_category": ["Budget", "Mid-range"],
        "sentiment_score": [2, 0]
    })

    # Load the data
    result = load_data(data)

    # Verify the result
    assert "rows_processed" in result
    assert result["rows_processed"] == 2
    assert "total_rows" in result
    assert "timestamp" in result

    # Verify that DuckDB connect was called
    mock_db.assert_called_once()

    # Verify that execute was called to create table and insert data
    mock_cursor = mock_db.return_value
    assert mock_cursor.execute.call_count >= 2

@pytest.mark.etl
@pytest.mark.asyncio
async def test_process_data():
    """Test the entire ETL process"""
    with patch('etl.run_etl.extract_data') as mock_extract, \
         patch('etl.run_etl.transform_data') as mock_transform, \
         patch('etl.run_etl.load_data') as mock_load:

        # Mock the extract_data function
        mock_extract_df = pd.DataFrame({
            "product_id": ["P001", "P002"],
            "product_name": ["Test Product 1", "Test Product 2"],
            "category": ["Electronics", "Clothing"],
            "price": [25.99, 45.50],
            "review_text": ["Great", "Good"],
            "rating": [5, 3]
        })
        mock_extract.return_value = mock_extract_df

        # Mock the transform_data function
        mock_transform_df = mock_extract_df.copy()
        mock_transform_df["is_recommended"] = [True, False]
        mock_transform_df["price_category"] = ["Budget", "Mid-range"]
        mock_transform_df["sentiment_score"] = [2, 0]
        mock_transform.return_value = mock_transform_df

        # Mock the load_data function
        mock_load.return_value = {
            "rows_processed": 2,
            "total_rows": 2,
            "timestamp": "2025-04-29T12:00:00"
        }

        # Process the data
        result = await process_data(source="test")

        # Verify the mocks were called
        mock_extract.assert_called_once_with("test")
        mock_transform.assert_called_once_with(mock_extract_df)
        mock_load.assert_called_once_with(mock_transform_df)

        # Verify the result
        assert result["status"] == "success"
        assert result["source"] == "test"
        assert result["rows_processed"] == 2
        assert "timestamp" in result
