import json
import os
from typing import Dict, List, Optional
from datetime import datetime
import shutil
import glob
import base64
import traceback
import io
import pandas as pd
        
class ChatHistoryManager:
    def __init__(self, model, history_dir: str = "chat-history"):
        """Initialize the chat history manager with the specified directory"""
        self.model = model
        self.history_dir = os.path.join(history_dir, model)
        # self.images_dir = os.path.join(self.history_dir, "images")
        self.files_dir = os.path.join(self.history_dir, "files")
        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """Ensure the chat history directory exists"""
        os.makedirs(self.history_dir, exist_ok=True)
        os.makedirs(self.files_dir, exist_ok=True)
        # os.makedirs(self.images_dir, exist_ok=True)
    
    def _get_chat_filepath(self, chat_id: str, session_id: str) -> str:
        """Get the full file path for a chat JSON file"""
        return os.path.join(self.history_dir, session_id, f"{chat_id}.json")

    def _save_file(self, chat_id: str, message_id: str, csv_data: list) -> str:
        """
        Save csv data to a file and return the relative path.
        
        Args:
            chat_id: The chat ID
            message_id: The message ID
            csv_data: csv file
        
        Returns:
            str: Relative path to the saved image
        """
        # Create chat-specific image directory
        chat_files_dir = os.path.join(self.files_dir, chat_id)
        os.makedirs(chat_files_dir, exist_ok=True)
        
        # Save csv to file
        file_path = os.path.join(chat_files_dir, f"{message_id}.csv")
        try:
            pd.DataFrame(csv_data).to_csv(file_path, index=False)
            
            # Return relative path from chat history root
            return os.path.relpath(file_path, self.history_dir)
        except Exception as e:
            print(f"Error saving file: {str(e)}")
            traceback.print_exc()
            return ""
        
    def _load_file(self, relative_path: str) -> Optional[list]:
        """
        Load csv data from file and return as list.
        
        Args:
            relative_path: Relative path to the image from chat history root
        
        Returns:
            Optional[list]: csv data
        """
        full_path = os.path.join(self.history_dir, relative_path)
        try:
            if os.path.exists(full_path):
                return pd.read_csv(full_path).to_dict(orient='records')
                # with open(full_path, 'rb') as f:
                #     image_bytes = f.read()
                # return base64.b64encode(image_bytes).decode('utf-8')
        except Exception as e:
            print(f"Error loading file: {str(e)}")
            traceback.print_exc()
        return None

    
    def save_chat(self, chat_to_save: Dict, session_id: str) -> None:
        """Save a chat to both memory and file, handling files separately"""
        chat_dir = os.path.join(self.history_dir,session_id)
        os.makedirs(chat_dir, exist_ok=True)
        
        # Process messages to save files separately
        for message in chat_to_save["messages"]:
            if "file" in message and message["file"] is not None:
                #print("image:",message["image"])
                # Save image and replace with path
                file_path = self._save_file(
                    chat_to_save["chat_id"],
                    message["message_id"],
                    message["file"]
                )
                if file_path:
                    message["file_path"] = file_path
                del message["file"]
            # if "image" in message and message["image"] is not None:
            #     #print("image:",message["image"])
            #     # Save image and replace with path
            #     image_path = self._save_image(
            #         chat_to_save["chat_id"],
            #         message["message_id"],
            #         message["image"]
            #     )
            #     if image_path:
            #         message["image_path"] = image_path
            #     del message["image"]
        
        # Save chat data
        filepath = self._get_chat_filepath(chat_to_save["chat_id"], session_id)
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(chat_to_save, f, indent=2, ensure_ascii=False)    
        except Exception as e:
            print(f"Error saving chat {chat_to_save['chat_id']}: {str(e)}")
            traceback.print_exc()
            raise e

    def get_chat(self, chat_id: str, session_id: str) -> Optional[Dict]:
        """Get a specific chat by ID"""
        filepath = os.path.join(self.history_dir,session_id,f"{chat_id}.json")
        chat_data = {}
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                chat_data = json.load(f)        
        except Exception as e:
            print(f"Error loading chat history from {filepath}: {str(e)}")
            traceback.print_exc()
        return chat_data
    
    def get_recent_chats(self, session_id: str, limit: Optional[int] = None) -> List[Dict]:
        """Get recent chats, optionally limited to a specific number"""        
        chat_dir = os.path.join(self.history_dir,session_id)
        os.makedirs(chat_dir, exist_ok=True)
        recent_chats = []
        chat_files = glob.glob(os.path.join(chat_dir,"*.json"))
        for filepath in chat_files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    chat_data = json.load(f)        
                    recent_chats.append(chat_data)
            except Exception as e:
                print(f"Error loading chat history from {filepath}: {str(e)}")
                traceback.print_exc()

        # Sort by dts
        recent_chats.sort(key=lambda x: x.get('dts', 0), reverse=True)
        if limit:
            return recent_chats[:limit]

        return recent_chats
