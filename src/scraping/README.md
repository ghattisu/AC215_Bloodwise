# Scraping Web Documents for RAG

In this container, we prepared a script that performs web scraping to gather information about biomarkers and complete blood count (CBC) from two different sources: Docus.ai and Cleveland Clinic. For each resource, the script fetches the main glossary page and iterates to collect links to individual biomarker pages, stores the content of each biomarker page in a dictionary, and then saves the collected data into a CSV file and individual text files. These files are then chunked and embedded to be saved into a Google Cloud Bucket to serve as the bases for  serve as the basis for vectorization and retrieving of data via RAG.

## Prerequisites
* Have Docker installed
* Cloned this repository to your local machine https://github.com/ghattisu/AC215_Bloodwise
* Modify `env.dev` to represent your Bucket and Project Name.

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


## Run LLM RAG Container
- Make sure you are inside the `scraping` folder and open a terminal at this location
- Make sure that Docker Desktop is enabled and running
- Run `sh docker-shell.sh`

## Perform Scraping
`python cli.py --scrape`

This will:
* Scrape the Docus.ai and Cleveland Clinic web sources regarding metabolites
* Collect links via pagination
* Store each page in a dictionary
* Save the collected pages as .txt files in AC215_Bloodwise/scraping/input-datasets folder

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

## Upload sembeddings to GCP Bucket
`python cli.py --upload`

This will:
* Upload the embeddings in AC215_Bloodwise/scraping/outputs to a GCP bucket

Once finished, navigate to the AC215_Bloodwise/vector-db directory to download the embeddings and load them into a ChromaDB instance for RAG!

## Testing for this container
To run the pytests for this container, use the command `pytest tests/test_scrape.py` 

Initial setup:
- This test suite is designed to validate web scraping and data processing functions. It includes:
  - Predefined mock HTML content to simulate web responses
  - Fixtures for creating temporary directories and mocking environment variables
  - Sample URLs representing different sources (Docus.ai, Cleveland Clinic)

Functions tested:
- test_scrape(): mocks HTTP requests for different pages and tests scraping from Docus.ai biomarkers page
- test_chunk(): creates a sample input document and tests chunking method "semantic-split"
- test_embed(): prepares sample chunk files and tests embedding generation
- test_generate_embeddings(): tests generation of embeddings for both single query and multiple text chunks
