# Building a RAG System with Vector DB and LLM

In this container, we prepared a set of text documents for the RAG knowledge base. We will chunk the documents, create embeddings, store the embeddings in a vector database, and use them to enhance LLM responses to answer blood test interpreation questions. We fine-tuned a gemini model (in the fine-tuning-sg container) with sets of question-answer pairs related to blood test interpreations and used the fine-tuned model here. We also created a baseline dashboard for entering blood test results and chatting with the model.  

## Prerequisites
* Have Docker installed
* Cloned this repository to your local machine https://github.com/ghattisu/AC215_Bloodwise

### Setup GCP Service Account
- To set up a service account, go to the [GCP Console](https://console.cloud.google.com/home/dashboard), search for "Service accounts" in the top search box, or navigate to "IAM & Admin" > "Service accounts" from the top-left menu. 
- Create a new service account called "llm-service-account." 
- In "Grant this service account access to project" select:
    - Storage Admin
    - Vertex AI User
- This will create a service account.
- Click the service account and navigate to the tab "KEYS"
- Click the button "ADD Key (Create New Key)" and Select "JSON". This will download a private key JSON file to your computer. 
- Copy this JSON file into the **secrets** folder and rename it to `llm-service-account.json`.

Your folder structure should look like this:

```
    |-AC215_BLOODWISE
        |-llm
        |-fine-tuning-sg
        |-scraping
        |-dvc
        |-secrets
```

## Run LLM RAG Container
- Make sure you are inside the `llm` folder and open a terminal at this location
- Run `sh docker-shell.sh`

## Chunk Documents
`python cli.py --chunk`

This will:
* Read each text file in the input-datasets/books directory
* Split the text into chunks with semantic-splitting
* Save the chunks as JSONL files in the outputs directory

## Generate Embeddings
`python cli.py --embed`

This will:
* Reads the chunk files created in the previous section
* Uses Vertex AI's text embedding model to generate embeddings for each chunk
* Saves the chunks with their embeddings as new JSONL files
* We use Vertex AI `text-embedding-004` model to generate the embeddings

## Load Embeddings into Vector Database
`python cli.py --load`

This will:
* Connects to your ChromaDB instance
* Creates a new collection (or clears an existing one)
* Loads the embeddings and associated metadata into the collection

## (shortcut) chunking -> embedding -> loading the vector db
`python cli.py --chunk --embed --load`

## Open the chatbot interface
`streamlit run chatbot_interface.py`
Open http://localhost:8501/ in a web browser to view the chatbot_interface.

The dashboard contains two tabs: Vector Database, Chatbot
* The vector database tab contains a table displaying all records in the semantic-splitting-collection 
* The chatbot interface contains two elements: 
    * an empty table that allows users to enter blood test results (can leave elements blank). Click "save and begin chat" to
    ask the LLM to interpret the data entered.
    * a chat box to enter questions related to blood test
