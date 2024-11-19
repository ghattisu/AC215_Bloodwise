# API Services

This container manages the API functions to initialize the BloodWise AI Chatbot via Google Gemini, route input questions and blood test data to the chatbot, and then output a response to be implemented into the frontend.

## Prerequisites
* Have Docker installed
* Cloned this repository to your local machine https://github.com/ghattisu/AC215_Bloodwise
* Modify `env.dev` to represent your Bucket and Project Name.


## Run Container
- Make sure you are inside the `api-service` folder and open a terminal at this location
- Make sure that Docker Desktop is enabled and running
- Run `sh docker-shell.sh`

## This will:
* Launch the API endpoints via FastAPI, hosted on a local port. 
* Allow users to access the API endpoints for testing via their browser.

## Upload scraped text documents to GCP Bucket
`uvicorn_server`

To test:
`pytest tests/test_chat_utils.py`
