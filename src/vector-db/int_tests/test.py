import requests
import unittest
import json

class TestLLMChatAPI(unittest.TestCase):
    def setUp(self):
        self.base_url = "http://localhost:9000"
        self.endpoint = f"{self.base_url}/llm/chats"
        self.headers = {
            "accept": "application/json",
            "X-Session-ID": "1234",
            "Content-Type": "application/json"
        }

    def test_successful_chat_request(self):
        """Test a successful chat request with valid input"""
        payload = {
            "content": "How is cheese made?"
        }

        # Make the POST request
        response = requests.post(
            self.endpoint,
            headers=self.headers,
            json=payload
        )

        # Assert status code
        self.assertEqual(response.status_code, 200)

        # Assert response headers
        self.assertEqual(response.headers["Content-Type"], "application/json")

        # Parse response body
        try:
            response_data = response.json()
            self.assertIsInstance(response_data, dict)
            # Add more specific assertions based on your API's response structure
        except json.JSONDecodeError:
            self.fail("Response is not valid JSON")

    def test_invalid_session_id(self):
        """Test request with missing session ID"""
        headers_without_session = self.headers.copy()
        del headers_without_session["X-Session-ID"]

        response = requests.post(
            self.endpoint,
            headers=headers_without_session,
            json={"content": "Test message"}
        )

        self.assertEqual(response.status_code, 400)

    def test_empty_content(self):
        """Test request with empty content"""
        response = requests.post(
            self.endpoint,
            headers=self.headers,
            json={"content": ""}
        )

        self.assertEqual(response.status_code, 400)

    def test_invalid_json(self):
        """Test request with malformed JSON"""
        response = requests.post(
            self.endpoint,
            headers=self.headers,
            data="invalid json"
        )

        self.assertEqual(response.status_code, 400)

if __name__ == "__main__":
    unittest.main(verbosity=2)