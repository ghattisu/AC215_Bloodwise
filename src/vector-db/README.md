# Instantiating Vector DB for RAG

In this container, we prepared a set of text documents for the RAG knowledge base. We will chunk the documents, create embeddings, store the embeddings in a vector database, and use them to enhance LLM responses to answer blood test interpreation questions.  

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
├── Readme.md
├── src
│   ├── api-service
│   ├── dvc
│   ├── deployment
│   ├── frontend-react
│   ├── scraping
│   ├── vector-db
├── .github/workflows
├── .flake8
├── .gitignore
├── secrets

```

## Run LLM RAG Container
- Make sure you are inside the `vector-db` folder and open a terminal at this location
- Run `sh docker-shell.sh`

## Download Documents
`python cli.py --download`

This will:
* Download embeddings from GCS bucket


## Load Embeddings into Vector Database
`python cli.py --load`

This will:
* Connects to your ChromaDB instance
* Creates a new collection (or clears an existing one)
* Loads the embeddings and associated metadata into the collection

## (shortcut) chunking -> embedding -> loading the vector db
`python cli.py --download --load`

**Make sure to keep this container running as you launch your API and Frontend Components!**

## Testing in this container
To run the pytests for this container, use the command `pytest tests/test_db.py` 

Functions tested: 
- load(): mocks embedded jsonl file and chromadb client and collection, verify the jsonl file were read and items were added to the collection.
