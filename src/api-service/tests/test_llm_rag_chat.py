import pytest
import sys 
import os
from fastapi.testclient import TestClient
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from api.routers.llm_rag_chat import router

from unittest.mock import patch

client = TestClient(router)

@pytest.fixture
def session_id():
    return "test-session-id"

@patch('api.utils.llm_rag_utils.create_chat_session')
@patch('api.utils.llm_rag_utils.generate_chat_response')
def test_get_chats(mock_create_chat_session, mock_generate_chat_response, session_id):
    mock_create_chat_session.return_value = {}
    mock_generate_chat_response.return_value = "Mock response"
    response = client.get("/chats", headers={"X-Session-ID": session_id})
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@patch('api.utils.llm_rag_utils.create_chat_session')
@patch('api.utils.llm_rag_utils.generate_chat_response')
def test_get_chat(mock_create_chat_session, mock_generate_chat_response, session_id):
    mock_create_chat_session.return_value = {}
    mock_generate_chat_response.return_value = "Mock response"
    chat_id = "test-chat-id"
    response = client.get(f"/chats/{chat_id}", headers={"X-Session-ID": session_id})
    if response.status_code == 200:
        assert "chat_id" in response.json()
    else:
        assert response.status_code == 404

@patch('api.utils.llm_rag_utils.create_chat_session')
@patch('api.utils.llm_rag_utils.generate_chat_response')
def test_start_chat_with_llm(mock_create_chat_session, mock_generate_chat_response, session_id):
    mock_create_chat_session.return_value = {}
    mock_generate_chat_response.return_value = "Mock response"
    message = {"content": "Hello, how are you?"}
    response = client.post("/chats", json=message, headers={"X-Session-ID": session_id})
    assert response.status_code == 200
    assert "chat_id" in response.json()
    assert "messages" in response.json()

@patch('api.utils.llm_rag_utils.create_chat_session')
@patch('api.utils.llm_rag_utils.generate_chat_response')
def test_continue_chat_with_llm(mock_create_chat_session, mock_generate_chat_response, session_id):
    mock_create_chat_session.return_value = {}
    mock_generate_chat_response.return_value = "Mock response"
    chat_id = "test-chat-id"
    message = {"content": "Can you tell me more?"}
    response = client.post(f"/chats/{chat_id}", json=message, headers={"X-Session-ID": session_id})
    if response.status_code == 200:
        assert "chat_id" in response.json()
        assert "messages" in response.json()
    else:
        assert response.status_code == 404

@patch('api.utils.llm_rag_utils.create_chat_session')
@patch('api.utils.llm_rag_utils.generate_chat_response')
def test_get_chat_file(mock_create_chat_session, mock_generate_chat_response, session_id):
    mock_create_chat_session.return_value = {}
    mock_generate_chat_response.return_value = "Mock response"
    chat_id = "test-chat-id"
    message_id = "test-message-id"
    response = client.get(f"/files/{chat_id}/{message_id}.csv")
    if response.status_code == 200:
        assert response.headers["content-type"] == "text/csv"
    else:
        assert response.status_code in [403, 404]
