# API Services

This container manages the API functions to initialize the BloodWise AI Chatbot via Google Gemini, route input questions and blood test data to the chatbot, and then output a response to be implemented into the frontend.

## Prerequisites
* Have Docker installed
* Cloned this repository to your local machine https://github.com/ghattisu/AC215_Bloodwise

## Run Container
- Make sure you are inside the `api-service` folder and open a terminal at this location
- Make sure that Docker Desktop is enabled and running
- Run `sh docker-shell.sh`

## This will:
* Launch the API endpoints via FastAPI, hosted on a local port. 
* Allow users to access the API endpoints for testing via their browser.

## Review Container Configuration
- Check `docker-shell.sh`: 
  - Port mapping: `-p 9000:9000`
  - Development mode: `-e DEV=1`
- Check `docker-entrypoint.sh`: Dev vs. Production settings

## Start the API Service

Run the following command within the docker shell: `uvicorn_server`

Verify service is running at `http://localhost:9000`

## View API Docs
Fast API gives us an interactive API documentation and exploration tool for free.
- Go to `http://localhost:9000/docs`
- You can test APIs from this tool

To test:
`pytest tests/test_chat_utils.py`
