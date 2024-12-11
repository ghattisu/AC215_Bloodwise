import os
import argparse
import pandas as pd
import json
import time
import glob
import hashlib
import chromadb
import pandas as pd
from google.cloud import storage

# Langchain
from langchain.text_splitter import CharacterTextSplitter
from langchain.text_splitter import RecursiveCharacterTextSplitter
#from langchain_experimental.text_splitter import SemanticChunker

# Setup
GCP_PROJECT = os.environ["GCP_PROJECT"]
GCP_LOCATION = "us-central1"
GENERATIVE_MODEL = "gemini-1.5-flash-001"
INPUT_FOLDER = "input-datasets"
OUTPUT_FOLDER = "outputs"
CHROMADB_HOST = os.environ["CHROMADB_HOST"]
CHROMADB_PORT = 8000
GCS_BUCKET_NAME = "bloodwise-embeddings"

book_mappings = {
	"Albumin: Importance, Testing, and What Abnormal Levels Mean": {"author":"Docus", "year": 2024},
	"Blood Differential": {"author":"MedlinePlus", "year": 2022},
	"Hematocrit Test": {"author":"MedlinePlus", "year": 2022},
	"Hemoglobin Test": {"author":"MedlinePlus", "year": 2022},
	"Platelet Tests": {"author":"MedlinePlus", "year": 2022},
	"White Blood Count (WBC)": {"author":"MedlinePlus", "year": 2022},
	"Red Blood Cell (RBC) Count": {"author":"MedlinePlus", "year": 2022},
	"MCV (Mean Corpuscular Volume)": {"author":"MedlinePlus", "year": 2022},
	"cleveland_clinic": {"author":"Cleveland Clinic", "year": 2024},
	"cbc_test_dictionary": {"author":"Kaggle", "year": 2023},

}
def load_text_embeddings(df, collection, batch_size=500):

	# Generate ids
	df["id"] = df.index.astype(str)
	hashed_books = df["book"].apply(lambda x: hashlib.sha256(x.encode()).hexdigest()[:16])
	df["id"] = hashed_books + "-" + df["id"]

	metadata = {
		"book": df["book"].tolist()[0]
	}
	if metadata["book"] in book_mappings:
		book_mapping = book_mappings[metadata["book"]]
		metadata["author"] = book_mapping["author"]
		metadata["year"] = book_mapping["year"]
   
	# Process data in batches
	total_inserted = 0
	for i in range(0, df.shape[0], batch_size):
		# Create a copy of the batch and reset the index
		batch = df.iloc[i:i+batch_size].copy().reset_index(drop=True)

		ids = batch["id"].tolist()
		documents = batch["chunk"].tolist() 
		metadatas = [metadata for item in batch["book"].tolist()]
		embeddings = batch["embedding"].tolist()

		collection.add(
			ids=ids,
			documents=documents,
			metadatas=metadatas,
			embeddings=embeddings
		)
		total_inserted += len(batch)
		print(f"Inserted {total_inserted} items...")

	print(f"Finished inserting {total_inserted} items into collection '{collection.name}'")


def download_input_data():
    print("downloading")
    storage_client = storage.Client()
    bucket = storage_client.bucket(GCS_BUCKET_NAME)
    
    prefix = "embeddings/"
    blobs = bucket.list_blobs(prefix=prefix)
    for blob in blobs:
        # Create a local path for each blob
        local_path = os.path.join("input-datasets-embeddings", blob.name[len(prefix):])
        os.makedirs(os.path.dirname(local_path), exist_ok=True)

        # Download the blob to the local path
        blob.download_to_filename(local_path)

    print("downloaded")

def load(method="semantic-split"):
	print("load()")

	# Connect to chroma DB
	client = chromadb.HttpClient(host=CHROMADB_HOST, port=CHROMADB_PORT)

	# Get a collection object from an existing collection, by name. If it doesn't exist, create it.
	collection_name = f"{method}-collection"
	print("Creating collection:", collection_name)

	try:
		# Clear out any existing items in the collection
		client.delete_collection(name=collection_name)
		print(f"Deleted existing collection '{collection_name}'")
	except Exception:
		print(f"Collection '{collection_name}' did not exist. Creating new.")

	collection = client.create_collection(name=collection_name, metadata={"hnsw:space": "cosine"})
	print(f"Created new empty collection '{collection_name}'")
	print("Collection:", collection)

	# Get the list of embedding files
	jsonl_files = glob.glob(os.path.join("input-datasets-embeddings", f"embeddings-{method}-*.jsonl"))
	print("Number of files to process:", len(jsonl_files))

	# Process
	for jsonl_file in jsonl_files:
		print("Processing file:", jsonl_file)

		data_df = pd.read_json(jsonl_file, lines=True)
		print("Shape:", data_df.shape)
		print(data_df.head())

		# Load data
		load_text_embeddings(data_df, collection)


def main(args=None):
	print("CLI Arguments:", args)
 
	if args.download:
		download_input_data()

	if args.load:
		load()


if __name__ == "__main__":
	# Generate the inputs arguments parser
	# if you type into the terminal '--help', it will provide the description
	parser = argparse.ArgumentParser(description="CLI")

	parser.add_argument(
		"--download",
		action="store_true",
		help="Download knowledge base documents from GCS",
	)

	parser.add_argument(
		"--load",
		action="store_true",
		help="Load embeddings to vector db",
	)

	args = parser.parse_args()

	main(args)