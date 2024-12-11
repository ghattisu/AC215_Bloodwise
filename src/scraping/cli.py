import os
import argparse
import requests
from bs4 import BeautifulSoup
from google.cloud import storage
import pandas as pd
import glob

# Vertex AI
import vertexai
from vertexai.language_models import TextEmbeddingInput, TextEmbeddingModel
from vertexai.generative_models import GenerativeModel, SafetySetting, GenerationConfig, Content, Part, ToolConfig

# Langchain
from langchain.text_splitter import CharacterTextSplitter
from langchain.text_splitter import RecursiveCharacterTextSplitter
#from langchain_experimental.text_splitter import SemanticChunker
from semantic_splitter import SemanticChunker

# Setup
GCP_PROJECT = os.environ["GCP_PROJECT"]
GCP_LOCATION = "us-central1"
OUTPUT_FOLDER = "input-datasets"
DATASET_FOLDER = "outputs"
GCS_BUCKET_NAME = os.environ["GCS_BUCKET_NAME"]
EMBEDDING_MODEL = "text-embedding-004"
EMBEDDING_DIMENSION = 256


vertexai.init(project=GCP_PROJECT, location=GCP_LOCATION)
embedding_model = TextEmbeddingModel.from_pretrained(EMBEDDING_MODEL)
# Configuration settings for the content generation
generation_config = {
    "max_output_tokens": 8192,  # Maximum number of tokens for output
    "temperature": 0.25,  # Control randomness in output
    "top_p": 0.95,  # Use nucleus sampling
}

def scrape():
    # docus
    url = 'https://docus.ai/glossary/biomarkers'
    response = requests.get(url)
    
    content = response.text
    soup = BeautifulSoup(content, 'html.parser')
    cards = soup.find_all('div', class_='ant-col ant-col-xs-24 css-1drr2mu')
    links = []
    for card in cards:
        link = card.find('a')
        if(link):
            if not link.get('href').startswith('/tags'):
                links.append(link.get('href'))

    page = 1
    while True:
        url = f'https://docus.ai/glossary/biomarkers?page={page}'
        response = requests.get(url)
        content = response.text
        if 'No results found' in content:
            break
        
        soup = BeautifulSoup(content, 'html.parser')
        cards = soup.find_all('div', class_='ant-col ant-col-xs-24 css-1drr2mu')
        for card in cards:
            link = card.find('a')
            if(link):
                if not link.get('href').startswith('/tags'):
                    links.append(link.get('href'))
        page += 1

    biomarkers_glossary = {}
    for url in links: 
        response = requests.get(f"https://docus.ai/{url}")
        content = response.text
        soup = BeautifulSoup(content, 'html.parser')

        page_content = soup.find('section', class_='sc-5d4eaeca-0 htRsFi sc-fdf5dc80-0 gsFBbo')
        if page_content:
            content_div = page_content.find_all('div')

            text = ''
            for i in page_content.find_all('div', recursive=False)[2:]:
                text += i.get_text() + "\n"
        else:
            content_div = []
            text = ''

        title = soup.find("h1")
        if title:
            biomarkers_glossary[title.text] = text

    # make each entry into a txt file
    for key, value in biomarkers_glossary.items():
        with open(f'input-datasets/{key}.txt', 'w') as file:
            file.write(value)

    # CLEVELAND CLINIC
    url = "https://my.clevelandclinic.org/health/diagnostics/4053-complete-blood-count"
    response = requests.get(url)
    content = response.text

    soup = BeautifulSoup(content, 'html.parser')
    page_content = soup.find('div', {'data-identity': 'main-article-content'})

    cleveland_cbc_text = soup.find('h1').text + "\n"
    for i in page_content.find_all('div', recursive=False)[1:-1]:
        cleveland_cbc_text += i.get_text() + "\n"
    links = []
    for link in page_content.find_all('a'):
        if link.get('href').startswith('https://my.clevelandclinic.org/'):
            links.append(link.get('href'))

    import time
    for link in links: 
        try: 
            response = requests.get(link)
            content = response.text
            soup = BeautifulSoup(content, 'html.parser')

            page_content = soup.find('div', {'data-identity': 'main-article-content'})
            cleveland_cbc_text += soup.find('h1').text + "\n"
            print(soup.find('h1').text)

            for i in page_content.find_all('div', recursive=False)[1:-1]:
                cleveland_cbc_text += i.get_text() + "\n"

            for link in page_content.find_all('a'):
                if link.get('href').startswith('https://my.clevelandclinic.org/'):
                    if(link.get('href') not in links):
                        links.append(link.get('href'))
        except: 
            print(link)
            time.sleep(5)

    # export to a text file
    with open('input-datasets/cleveland_clinic.txt', 'w') as file:
        file.write(cleveland_cbc_text)

    print("Done!")
    
def generate_query_embedding(query):
    query_embedding_inputs = [TextEmbeddingInput(task_type='RETRIEVAL_DOCUMENT', text=query)]
    kwargs = dict(output_dimensionality=EMBEDDING_DIMENSION) if EMBEDDING_DIMENSION else {}
    embeddings = embedding_model.get_embeddings(query_embedding_inputs, **kwargs)
    return embeddings[0].values


def generate_text_embeddings(chunks, dimensionality: int = 256, batch_size=250):
    # Max batch size is 250 for Vertex AI
    all_embeddings = []
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        inputs = [TextEmbeddingInput(text, "RETRIEVAL_DOCUMENT") for text in batch]
        kwargs = dict(output_dimensionality=dimensionality) if dimensionality else {}
        embeddings = embedding_model.get_embeddings(inputs, **kwargs)
        all_embeddings.extend([embedding.values for embedding in embeddings])
    return all_embeddings

def chunk(method="semantic-split"):
    print("chunk()")

    # Make dataset folders
    os.makedirs(DATASET_FOLDER, exist_ok=True)

    # Get the list of text file
    text_files = glob.glob(os.path.join(OUTPUT_FOLDER, "*.txt"))
    print("Number of files to process:", len(text_files))

    # Process
    for text_file in text_files:
        print("Processing file:", text_file)
        filename = os.path.basename(text_file)
        book_name = filename.split(".")[0]

        with open(text_file) as f:
            input_text = f.read()
        
        text_chunks = None

        if method == "semantic-split":
            # Init the splitter
            text_splitter = SemanticChunker(embedding_function=generate_text_embeddings)
            # Perform the splitting
            text_chunks = text_splitter.create_documents([input_text])
            
            text_chunks = [doc.page_content for doc in text_chunks]
            print("Number of chunks:", len(text_chunks))

        if text_chunks is not None:
            # Save the chunks
            data_df = pd.DataFrame(text_chunks,columns=["chunk"])
            data_df["book"] = book_name
            print("Shape:", data_df.shape)
            print(data_df.head())

            jsonl_filename = os.path.join(DATASET_FOLDER, f"chunks-{method}-{book_name}.jsonl")
            with open(jsonl_filename, "w") as json_file:
                json_file.write(data_df.to_json(orient='records', lines=True))


def embed(method="semantic-split"):
    print("embed()")

    # Get the list of chunk files
    jsonl_files = glob.glob(os.path.join(DATASET_FOLDER, f"chunks-{method}-*.jsonl"))
    print("Number of files to process:", len(jsonl_files))

    # Process
    for jsonl_file in jsonl_files:
        print("Processing file:", jsonl_file)

        data_df = pd.read_json(jsonl_file, lines=True)

        #remove where text chunk is empty becaue it won't process the text embedding
        data_df = data_df[data_df["chunk"] != ""]
        print("Shape:", data_df.shape)
        print(data_df.head())

        chunks = data_df["chunk"].values
        if method == "semantic-split":
            embeddings = generate_text_embeddings(chunks,EMBEDDING_DIMENSION, batch_size=15)
        else:
            embeddings = generate_text_embeddings(chunks,EMBEDDING_DIMENSION, batch_size=100)
        data_df["embedding"] = embeddings

        # Save 
        print("Shape:", data_df.shape)
        print(data_df.head())

        jsonl_filename = jsonl_file.replace("chunks-","embeddings-")
        with open(jsonl_filename, "w") as json_file:
            json_file.write(data_df.to_json(orient='records', lines=True))
   
def upload(method="semantic-split"):
    print("Uploading")
    storage_client = storage.Client()
    bucket = storage_client.bucket(GCS_BUCKET_NAME)
    timeout = 300

    #read in embeddings
    jsonl_files = glob.glob(os.path.join(DATASET_FOLDER, f"embeddings-{method}-*.jsonl"))
    jsonl_files.sort()
    print(jsonl_files)

    #Upload embeddings
    for index, data_file in enumerate(jsonl_files):
        filename = os.path.basename(data_file)
        destination_blob_name = os.path.join("embeddings", filename)
        blob = bucket.blob(destination_blob_name)
        print("Uploading file:", data_file, destination_blob_name)
        blob.upload_from_filename(data_file, timeout=timeout)
        
        

def main(args=None):
    print("CLI Arguments:", args)
    
    if args.scrape:
      scrape()
    
    if args.chunk:
      chunk()

    if args.embed:
      embed()
    
    if args.upload:
      upload()

if __name__ == "__main__":
    # Generate the inputs arguments parser
    # if you type into the terminal '--help', it will provide the description
    parser = argparse.ArgumentParser(description="CLI")

    parser.add_argument(
        "--scrape",
        action="store_true",
        help="Scrape data from docus and cleveland clinic",
    )
    parser.add_argument(
        "--chunk",
        action="store_true",
        help="Chunk text",
    )
    parser.add_argument(
        "--embed",
        action="store_true",
        help="Generate embeddings",
    )
    parser.add_argument(
        "--upload",
        action="store_true",
        help="Upload data to GCP bucket",
    )
    args = parser.parse_args()
    main(args)
    