import pytest
import tempfile
from unittest.mock import patch, MagicMock, mock_open
import pandas as pd
import glob
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from cli import chunk, embed, load

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
def mock_chunk_jsonl_files():
    # Mock the list of JSONL files
    return [os.path.join(OUTPUT_FOLDER, f"chunks-semantic-split-test1.jsonl")]

@pytest.fixture
def mock_chunk_dataframe():
    # Mock DataFrame for the JSONL content
    data = {
        "chunk": ["chunk 1 text", "chunk 2 text"],
    }
    return pd.DataFrame(data)

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

@patch("os.makedirs")
@patch("glob.glob")
@patch("builtins.open", new_callable=mock_open)
@patch("pandas.DataFrame.to_json")
def test_chunk(mock_to_json, mock_open_file, mock_glob, mock_makedirs, mock_text_files, mock_text_content):
    # Arrange
    mock_glob.return_value = [os.path.join(INPUT_FOLDER, file) for file in mock_text_files]
    mock_open_file.return_value.read.return_value = mock_text_content

    # Mock the SemanticChunker and generate_text_embeddings
    mock_semantic_chunker = MagicMock()
    mock_semantic_chunker.return_value.create_documents.return_value = [
        MagicMock(page_content="chunk 1"),
        MagicMock(page_content="chunk 2"),
    ]

    with patch("semantic_splitter.SemanticChunker", mock_semantic_chunker):
        # Act
        chunk(method="semantic-split")

    # Assert
    # Verify files were read
    mock_open_file.assert_called()  
    # Verify chunks were saved
    mock_to_json.assert_called()  

    # Verify the chunking
    assert len(mock_semantic_chunker.return_value.create_documents()) == 2


@patch("glob.glob")
@patch("pandas.read_json")
@patch("builtins.open")
def test_embed(mock_open_file, mock_read_json, mock_glob, mock_chunk_jsonl_files, mock_chunk_dataframe):
    # Arrange
    mock_glob.return_value = mock_chunk_jsonl_files  # Mock JSONL files
    mock_read_json.return_value = mock_chunk_dataframe  # Mock the DataFrame

    # Mock generate_text_embeddings
    mock_generate_text_embeddings = MagicMock(return_value=[[0.1] * 256, [0.2] * 256])

    with patch("cli.generate_text_embeddings", mock_generate_text_embeddings):
        embed(method="semantic-split")

    # Assert
    mock_read_json.assert_called_once_with(mock_chunk_jsonl_files[0], lines=True)

    # Check embeddings were generated
    mock_generate_text_embeddings.assert_called()

    # Verify the file was saved
    assert mock_open_file.called
    file_path = mock_open_file.call_args[0][0]
    assert file_path.startswith(OUTPUT_FOLDER)
    assert file_path.endswith("embeddings-semantic-split-test1.jsonl")

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

    
