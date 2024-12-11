import pytest
import tempfile
from unittest.mock import patch, MagicMock, mock_open
import pandas as pd
import glob
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from cli import load

# Mock folders
INPUT_FOLDER = "test-input-datasets"
OUTPUT_FOLDER = "test-outputs"
CHROMADB_HOST = "mock-chromadb-host"
CHROMADB_PORT = 8000

@pytest.fixture
def mock_text_files():
    # Mock text files in the input directory
    return ["test1.txt", "test2.txt"]

@pytest.fixture
def mock_text_content():
    # Mock content of a text file
    return "Welcome to Bloodwise."

@pytest.fixture
def mock_embed_jsonl_files():
    # Mock the list of JSONL files
    return [os.path.join(OUTPUT_FOLDER, "embeddings-semantic-split-test1.jsonl")]

@pytest.fixture
def mock_embed_dataframe():
    # Mock DataFrame for the JSONL content
    data = {
        "id": ["id1", "id2"],
        "chunk": ["chunk 1 text", "chunk 2 text"],
        "embedding": [[0.1] * 256, [0.2] * 256],
        "book": ["book1", "book1"],
    }
    return pd.DataFrame(data)


@patch("glob.glob")
@patch("pandas.read_json")
@patch("chromadb.HttpClient")
def test_load_semantic_split(mock_chromadb_client, mock_read_json, mock_glob, mock_embed_jsonl_files, mock_embed_dataframe):
    # Arrange
    mock_glob.return_value = mock_embed_jsonl_files  # Mock the JSONL file list
    mock_read_json.return_value = mock_embed_dataframe  # Mock the DataFrame

    # Mock Chromadb client and collection
    mock_client = MagicMock()
    mock_chromadb_client.return_value = mock_client
    mock_collection = MagicMock()
    mock_client.create_collection.return_value = mock_collection

    load(method="semantic-split")

    # Assert
    # Verify that JSONL files were read
    mock_glob.assert_called_once()
    mock_read_json.assert_called_once_with(mock_embed_jsonl_files[0], lines=True)

    # Verify items were added to the collection
    mock_client.create_collection.assert_called_once_with(
        name="semantic-split-collection", metadata={"hnsw:space": "cosine"}
    )
    mock_collection.add.assert_called_once()  