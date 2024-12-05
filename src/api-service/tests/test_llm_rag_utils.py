import os
import sys
import pytest
# import requests
import shutil
# import requests_mock
from io import StringIO
# from bs4 import BeautifulSoup
import tempfile
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from vertexai.generative_models import ChatSession
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from api.utils.llm_rag_utils import (
    generate_query_embedding,
    create_chat_session,
    generate_chat_response,
    rebuild_chat_session,
)

# Mock environment variables
@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    monkeypatch.setenv("GCP_PROJECT", "test_project")
    monkeypatch.setenv("CHROMADB_HOST", "localhost")
    monkeypatch.setenv("CHROMADB_PORT", "8000")

# Mock Vertex AI initialization
@pytest.fixture(autouse=True)
def mock_vertexai_init():
    with patch("vertexai.init") as mock_init:
        yield mock_init

# Mock TextEmbeddingModel
@pytest.fixture
def mock_text_embedding_model():
    with patch("vertexai.language_models.TextEmbeddingModel.from_pretrained") as mock_model:
        mock_instance = MagicMock()
        mock_model.return_value = mock_instance
        yield mock_instance

# Mock GenerativeModel
@pytest.fixture
def mock_generative_model():
    with patch("vertexai.generative_models.GenerativeModel") as mock_model:
        mock_instance = MagicMock()
        mock_model.return_value = mock_instance
        yield mock_instance

# Mock ChromaDB client
@pytest.fixture
def mock_chromadb_client():
    with patch("chromadb.HttpClient") as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        yield mock_instance

def test_generate_query_embedding(mock_text_embedding_model):
    mock_text_embedding_model.get_embeddings.return_value = [MagicMock(values=[0.1, 0.2, 0.3])]
    query = "test query"
    embedding = generate_query_embedding(query)
    assert embedding == [0.1, 0.2, 0.3]
    mock_text_embedding_model.get_embeddings.assert_called_once()

def test_create_chat_session(mock_generative_model):
    session = create_chat_session()
    assert isinstance(session, ChatSession)
    mock_generative_model.start_chat.assert_called_once()

def test_generate_chat_response_text(mock_generative_model, mock_chromadb_client):
    chat_session = MagicMock()
    message = {"content": "test message"}
    mock_chromadb_client.get_collection.return_value.query.return_value = {
        "documents": [["chunk1", "chunk2", "chunk3"]]
    }
    response = MagicMock()
    response.text = "response text"
    chat_session.send_message.return_value = response

    result = generate_chat_response(chat_session, message)
    assert result == "response text"
    chat_session.send_message.assert_called_once()

def test_generate_chat_response_file(mock_generative_model):
    chat_session = MagicMock()
    message = {"file": [{"WBC": "5.0", "HGB": "13.0"}]}
    response = MagicMock()
    response.text = "response text"
    chat_session.send_message.return_value = response

    result = generate_chat_response(chat_session, message)
    assert result == "response text"
    chat_session.send_message.assert_called_once()

def test_generate_chat_response_error(mock_generative_model):
    chat_session = MagicMock()
    message = {"content": "test message"}
    chat_session.send_message.side_effect = Exception("Test error")

    with pytest.raises(HTTPException):
        generate_chat_response(chat_session, message)

def test_rebuild_chat_session(mock_generative_model):
    chat_history = [{"role": "user", "content": "test message"}]
    new_session = rebuild_chat_session(chat_history)
    assert isinstance(new_session, ChatSession)
    mock_generative_model.start_chat.assert_called_once()