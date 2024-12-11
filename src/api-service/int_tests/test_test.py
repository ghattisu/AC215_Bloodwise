import unittest
import requests
import json

class TestLLMRAGChat(unittest.TestCase):
    def setUp(self):
        self.base_url = "http://localhost:9000"
        self.headers = {
            "accept": "application/json",
            "X-Session-ID": "1234",
            "Content-Type": "application/json"
        }

    # COMMENTED OUT: the test is checking for chatids that are already present
    # def test_get_chats(self):
    #     endpoint = f"{self.base_url}/chats"
    #     response = requests.get(endpoint, headers=self.headers)
    #     print(f"Request URL: {endpoint}")
    #     print(f"Response Status Code: {response.status_code}")
    #     print(f"Response Headers: {response.headers}")
    #     print(f"Response Content: {response.text}")
    #     self.assertEqual(response.status_code, 200)
    #     self.assertEqual(response.headers["Content-Type"], "application/json")
    #     try:
    #         response_data = response.json()
    #         self.assertIsInstance(response_data, list)
    #     except json.JSONDecodeError:
    #         self.fail("Response is not valid JSON")

    # def test_get_chat(self):
    #     chat_id = "some-chat-id"
    #     endpoint = f"{self.base_url}/chats/{chat_id}"
    #     response = requests.get(endpoint, headers=self.headers)
    #     if response.status_code == 200:
    #         self.assertEqual(response.headers["Content-Type"], "application/json")
    #         try:
    #             response_data = response.json()
    #             self.assertIsInstance(response_data, dict)
    #         except json.JSONDecodeError:
    #             self.fail("Response is not valid JSON")
    #     else:
    #         self.assertEqual(response.status_code, 404)

    def test_start_chat_with_llm(self):
        endpoint = f"{self.base_url}/llm-rag/chats"
        payload = {"content": "My blood test showed a glucose of 260. What does this mean?"}
        response = requests.post(endpoint, headers=self.headers, json=payload)
        print(f"Request URL: {endpoint}")
        print(f"Request Headers: {self.headers}")
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Headers: {response.headers}")
        print(f"Response Content: {response.text}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Content-Type"], "application/json")
        try:
            response_data = response.json()
            self.assertIsInstance(response_data, dict)
        except json.JSONDecodeError:
            self.fail("Response is not valid JSON")

    def test_continue_chat_with_llm(self):
        chat_id = "some-chat-id"
        endpoint = f"{self.base_url}/chats/{chat_id}"
        payload = {"content": "Tell me more about cheese."}
        response = requests.post(endpoint, headers=self.headers, json=payload)
        if response.status_code == 200:
            self.assertEqual(response.headers["Content-Type"], "application/json")
            try:
                response_data = response.json()
                self.assertIsInstance(response_data, dict)
            except json.JSONDecodeError:
                self.fail("Response is not valid JSON")
        else:
            self.assertEqual(response.status_code, 404)

    def test_get_chat_file(self):
        chat_id = "some-chat-id"
        message_id = "some-message-id"
        endpoint = f"{self.base_url}/files/{chat_id}/{message_id}.csv"
        response = requests.get(endpoint, headers=self.headers)
        if response.status_code == 200:
            self.assertEqual(response.headers["Content-Type"], "application/json")
            try:
                response_data = response.json()
                self.assertIsInstance(response_data, list)
            except json.JSONDecodeError:
                self.fail("Response is not valid JSON")
        else:
            self.assertIn(response.status_code, [403, 404])

if __name__ == "__main__":
    unittest.main(verbosity=2)