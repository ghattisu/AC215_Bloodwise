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
EMBEDDING_MODEL = "text-embedding-004"
EMBEDDING_DIMENSION = 256
GENERATIVE_MODEL = "gemini-1.5-flash-001"
INPUT_FOLDER = "input-datasets"
OUTPUT_FOLDER = "outputs"
CHROMADB_HOST = "llm-rag-chromadb"
CHROMADB_PORT = 8000
GCS_BUCKET_NAME = "bloodwise-rag-knowledge-base"

vertexai.init(project=GCP_PROJECT, location=GCP_LOCATION)
embedding_model = TextEmbeddingModel.from_pretrained(EMBEDDING_MODEL)
# Configuration settings for the content generation
generation_config = {
    "max_output_tokens": 8192,  # Maximum number of tokens for output
    "temperature": 0.25,  # Control randomness in output
    "top_p": 0.95,  # Use nucleus sampling
}
# Initialize the GenerativeModel with specific system instructions
SYSTEM_INSTRUCTION = """
You are an AI assistant specialized in blood test knowledge. Your responses are based solely on the information provided in the text chunks given to you. Do not use any external knowledge or make assumptions beyond what is explicitly stated in these chunks.

When answering a query:
1. Carefully read all the text chunks provided.
2. Identify the most relevant information from these chunks to address the user's question.
3. Formulate your response using only the information found in the given chunks.
4. If the provided chunks do not contain sufficient information to answer the query, state that you don't have enough information to provide a complete answer.
5. Always maintain a professional and knowledgeable tone, befitting a blood test interpretation expert.
6. If there are contradictions in the provided chunks, mention this in your response and explain the different viewpoints presented.

Remember:
- You are an expert in blood test interpretation, but your knowledge is limited to the information in the provided chunks.
- Do not invent information or draw from knowledge outside of the given text chunks.
- If asked about topics unrelated to blood test, politely redirect the conversation back to blood-test-related subjects.
- Be concise in your responses while ensuring you cover all relevant information from the chunks.

Your goal is to provide accurate, helpful information about blood test interpretation based solely on the content of the text chunks you receive with each query.
"""
#MODEL_ENDPOINT = "projects/534883346897/locations/us-central1/endpoints/5135811116760301568"
MODEL_ENDPOINT = "projects/595664810090/locations/us-central1/endpoints/3140012794393395200"
generative_model = GenerativeModel(
	MODEL_ENDPOINT,
	system_instruction=[SYSTEM_INSTRUCTION]
)
safety_settings = [
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
        threshold=SafetySetting.HarmBlockThreshold.BLOCK_ONLY_HIGH
    ),
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        threshold=SafetySetting.HarmBlockThreshold.BLOCK_ONLY_HIGH
    ),
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
        threshold=SafetySetting.HarmBlockThreshold.BLOCK_ONLY_HIGH
    ),
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_HARASSMENT,
        threshold=SafetySetting.HarmBlockThreshold.BLOCK_ONLY_HIGH
    ),
]

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
    
    prefix = "text-documents/"
    blobs = bucket.list_blobs(prefix=prefix)
    for blob in blobs:
        # Create a local path for each blob
        local_path = os.path.join("input-datasets", blob.name[len(prefix):])
        os.makedirs(os.path.dirname(local_path), exist_ok=True)

        # Download the blob to the local path
        blob.download_to_filename(local_path)

    print("downloaded")


def chunk(method="semantic-split"):
	print("chunk()")

	# Make dataset folders
	os.makedirs(OUTPUT_FOLDER, exist_ok=True)

	# Get the list of text file
	text_files = glob.glob(os.path.join(INPUT_FOLDER, "*.txt"))
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

			jsonl_filename = os.path.join(OUTPUT_FOLDER, f"chunks-{method}-{book_name}.jsonl")
			with open(jsonl_filename, "w") as json_file:
				json_file.write(data_df.to_json(orient='records', lines=True))


def embed(method="semantic-split"):
	print("embed()")

	# Get the list of chunk files
	jsonl_files = glob.glob(os.path.join(OUTPUT_FOLDER, f"chunks-{method}-*.jsonl"))
	print("Number of files to process:", len(jsonl_files))

	# Process
	for jsonl_file in jsonl_files:
		print("Processing file:", jsonl_file)

		data_df = pd.read_json(jsonl_file, lines=True)
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
	jsonl_files = glob.glob(os.path.join(OUTPUT_FOLDER, f"embeddings-{method}-*.jsonl"))
	print("Number of files to process:", len(jsonl_files))

	# Process
	for jsonl_file in jsonl_files:
		print("Processing file:", jsonl_file)

		data_df = pd.read_json(jsonl_file, lines=True)
		print("Shape:", data_df.shape)
		print(data_df.head())

		# Load data
		load_text_embeddings(data_df, collection)

def get_model_response(prompt, method="semantic-split"):

   # Connect to chroma DB
	client = chromadb.HttpClient(host=CHROMADB_HOST, port=CHROMADB_PORT)
	# Get a collection object from an existing collection, by name. If it doesn't exist, create it.
	collection_name = f"{method}-collection"

	query_embedding = generate_query_embedding(prompt)
	# Get the collection
	collection = client.get_collection(name=collection_name)

	# Query based on embedding value 
	results = collection.query(
		query_embeddings=[query_embedding],
		n_results=10
	)

	INPUT_PROMPT = f"""
	{prompt}
	{"\n".join(results["documents"][0])}
	"""

	# print(INPUT_PROMPT)
	response = generative_model.generate_content(
		[INPUT_PROMPT],  # Input prompt
		generation_config=generation_config,  # Configuration settings
  		safety_settings=safety_settings,
		stream=False,  # Enable streaming for responses
	)
	response = response.text
	return response
    

def get_all_data(method="semantic-split"):
	# Connect to chroma DB
	client = chromadb.HttpClient(host=CHROMADB_HOST, port=CHROMADB_PORT)
	collection_name = f"{method}-collection"

	collection = client.get_collection(name=collection_name)
	content = collection.get(include=["metadatas", "documents"])
	df = pd.DataFrame({
		"ids": content["ids"],
		"metadata": content["metadatas"],
		"document": content["documents"]
	})
	return df


def main(args=None):
	print("CLI Arguments:", args)
 
	if args.download:
		download_input_data()

	if args.chunk:
		chunk()

	if args.embed:
		embed()

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
		"--load",
		action="store_true",
		help="Load embeddings to vector db",
	)

	# parser.add_argument("--chunk_type", default="semantic-split", help="char-split | recursive-split | semantic-split")

	args = parser.parse_args()

	main(args)