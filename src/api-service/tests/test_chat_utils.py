import os
import sys
import pytest
# import requests
import shutil
# import requests_mock
from io import StringIO
# from bs4 import BeautifulSoup
import tempfile
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from api.utils.chat_utils import ChatHistoryManager
# from cli import scrape, make_request, extract_links_from_cards, extract_text_from_page, scrape_biomarkers_page, scrape_biomarkers_info, scrape_cleveland_clinic, save_to_file

@pytest.fixture
def chat_manager():
    return ChatHistoryManager(model="test_model", history_dir="test_chat_history")

@pytest.fixture
def sample_chat():
    return {
        "chat_id": "123",
        "messages": [
            {"message_id": "1", "text": "Hello", "file": None},
            {"message_id": "2", "text": "World", "file": [{"col1": "data1", "col2": "data2"}]}
        ],
        "dts": 1234567890
    }

def test_ensure_directories(chat_manager):
    assert os.path.exists(chat_manager.history_dir)
    assert os.path.exists(chat_manager.files_dir)

def test_save_chat(chat_manager, sample_chat):
    session_id = "session_1"
    chat_manager.save_chat(sample_chat, session_id)
    chat_filepath = chat_manager._get_chat_filepath(sample_chat["chat_id"], session_id)
    assert os.path.exists(chat_filepath)

def test_get_chat(chat_manager, sample_chat):
    session_id = "session_1"
    chat_manager.save_chat(sample_chat, session_id)
    loaded_chat = chat_manager.get_chat(sample_chat["chat_id"], session_id)
    assert loaded_chat == sample_chat

def test_get_recent_chats(chat_manager, sample_chat):
    session_id = "session_1"
    chat_manager.save_chat(sample_chat, session_id)
    recent_chats = chat_manager.get_recent_chats(session_id)
    assert len(recent_chats) == 1
    assert recent_chats[0] == sample_chat

def test_save_file(chat_manager):
    chat_id = "123"
    message_id = "1"
    csv_data = [{"col1": "data1", "col2": "data2"}]
    file_path = chat_manager._save_file(chat_id, message_id, csv_data)
    full_path = os.path.join(chat_manager.history_dir, file_path)
    assert os.path.exists(full_path)

def test_load_file(chat_manager):
    chat_id = "123"
    message_id = "1"
    csv_data = [{"col1": "data1", "col2": "data2"}]
    file_path = chat_manager._save_file(chat_id, message_id, csv_data)
    loaded_data = chat_manager._load_file(file_path)
    assert loaded_data == csv_data

@pytest.fixture(scope="module", autouse=True)
def cleanup():
    yield
    shutil.rmtree("test_chat_history", ignore_errors=True)