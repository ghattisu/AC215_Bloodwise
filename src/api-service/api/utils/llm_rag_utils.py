import os
from typing import Dict, Any, List, Optional
from fastapi import HTTPException
import base64
import io
from PIL import Image
from pathlib import Path
import traceback
import chromadb
import vertexai
from vertexai.language_models import TextEmbeddingInput, TextEmbeddingModel
from vertexai.generative_models import GenerativeModel, SafetySetting, GenerationConfig, Content, Part, ToolConfig
from vertexai.generative_models import GenerativeModel, ChatSession, Part

# Setup
GCP_PROJECT = os.environ["GCP_PROJECT"]
GCP_LOCATION = "us-central1"
EMBEDDING_MODEL = "text-embedding-004"
EMBEDDING_DIMENSION = 256
GENERATIVE_MODEL = "gemini-1.5-flash-001"
CHROMADB_HOST = os.environ["CHROMADB_HOST"]
CHROMADB_PORT = os.environ["CHROMADB_PORT"]

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

# Initialize chat sessions
chat_sessions: Dict[str, ChatSession] = {}

# Connect to chroma DB
client = chromadb.HttpClient(host=CHROMADB_HOST, port=CHROMADB_PORT)
method = "semantic-split"
collection_name = f"{method}-collection"
# Get the collection
collection = client.get_collection(name=collection_name)

def generate_query_embedding(query):
	query_embedding_inputs = [TextEmbeddingInput(task_type='RETRIEVAL_DOCUMENT', text=query)]
	kwargs = dict(output_dimensionality=EMBEDDING_DIMENSION) if EMBEDDING_DIMENSION else {}
	embeddings = embedding_model.get_embeddings(query_embedding_inputs, **kwargs)
	return embeddings[0].values

def create_chat_session() -> ChatSession:
    """Create a new chat session with the model"""
    return generative_model.start_chat()

def generate_chat_response(chat_session: ChatSession, message: Dict) -> str:
    """
    Generate a response using the chat session to maintain history.
    Handles both text and image inputs.

    Args:
        chat_session: The Vertex AI chat session
        message: Dict containing 'content' (text) and optionally 'csv'

    Returns:
        str: The model's response
    """
    try:
        # Initialize parts list for the message
        message_parts = []

        # Process csv if present
        if message.get("file"):
            # print("file:", message.get("file"))

            try:
                # Get blood test biomarkers definitions
                biomarker_dictionary = {
                    "definition": {
                        "WBC": "White Blood Cell",
                        "LYMp": "Lymphocytes percentage, which is a type of white blood cell",
                        "MIDp": "Indicates the percentage combined value of the other types of white blood cells not classified as lymphocytes or granulocytes",
                        "NEUTp": "Neutrophils are a type of white blood cell (leukocytes); neutrophils percentage",
                        "LYMn": "Lymphocytes number are a type of white blood cell",
                        "MIDn": "Indicates the combined number of other white blood cells not classified as lymphocytes or granulocytes",
                        "NEUTn": "Neutrophils Number",
                        "RBC": "Red Blood Cell",
                        "HGB": "Hemoglobin",
                        "HCT": "Hematocrit is the proportion, by volume, of the Blood that consists of red blood cells",
                        "MCV": "Mean Corpuscular Volume",
                        "MCH": "Mean Corpuscular Hemoglobin is the average amount of haemoglobin in the average red cell",
                        "MCHC": "Mean Corpuscular Hemoglobin Concentration",
                        "RDWSD": "Red Blood Cell Distribution Width",
                        "RDWCV": "Red blood cell distribution width",
                        "PLT": "Platelet Count",
                        "MPV": "Mean Platelet Volume",
                        "PDW": "Red Cell Distribution Width",
                        "PCT": "The level of Procalcitonin in the Blood",
                        "PLCR": "Platelet Large Cell Ratio",
                    },
                    "normal_range": {
                        "WBC": "4.0 to 10.0",
                        "LYMp": "20.0 to 40.0",
                        "MIDp": "1.0 to 15.0",
                        "NEUTp": "50.0 to 70.0",
                        "LYMn": "0.6 to 4.1",
                        "MIDn": "0.1 to 1.8",
                        "NEUTn": "2.0 to 7.8",
                        "RBC": "3.50 to 5.50",
                        "HGB": "11.0 to 16.0",
                        "HCT": "36.0 to 48.0",
                        "MCV": "80.0 to 99.0",
                        "MCH": "26.0 to 32.0",
                        "MCHC": "32.0 to 36.0",
                        "RDWSD": "37.0 to 54.0",
                        "RDWCV": "11.5 to 14.5",
                        "PLT": "100 to 400",
                        "MPV": "7.4 to 10.4",
                        "PDW": "10.0 to 17.0",
                        "PCT": "0.10 to 0.28",
                        "PLCR": "13.0 to 43.0",
                    },
                    "unit": {
                        "WBC": "10^9/L.",
                        "LYMp": "%",
                        "MIDp": "%",
                        "NEUTp": "%",
                        "LYMn": "10^9/L.",
                        "MIDn": "10^9/L.",
                        "NEUTn": "10^9/L.",
                        "RBC": "10^12/L",
                        "HGB": "g/dL",
                        "HCT": "%",
                        "MCV": "fL",
                        "MCH": "pg",
                        "MCHC": "g/dL",
                        "RDWSD": "fL",
                        "RDWCV": "%",
                        "PLT": "10^9/L",
                        "MPV": "fL",
                        "PDW": "%",
                        "PCT": "%",
                        "PLCR": "%",
                    },
                }

                uploaded_data = message.get("file")[0]
                blood_test_input_prompt = ""
                for biomarker in uploaded_data:
                    if biomarker != "ID":
                        blood_test_input_prompt += f"{biomarker} is {biomarker_dictionary['definition'][biomarker]}, the normal range for it is {biomarker_dictionary['normal_range'][biomarker]}, and the patient has a value of {uploaded_data[biomarker]}.\n "

                message_parts.append(blood_test_input_prompt)
                # Add text content if present
                if message.get("content"):
                    message_parts.append(message["content"])
                else:
                    message_parts.append("Interpret the blood test result.")
            except ValueError as e:
                print(f"Error processing uploaded file: {str(e)}")
                raise HTTPException(
                    status_code=400, detail=f"Failed to process the uploaded file."
                )
        elif message.get("file_path"):
            # Read the file
            file_path = os.path.join(
                "chat-history", "llm-rag", message.get("file_path")
            )
            file = pd.read_csv(file_path)
            message_parts.append(file)

            # Add text content if present
            if message.get("content"):
                message_parts.append(message["content"])
            else:
                message_parts.append("Interpret the blood test result.")

        # # Process image if present
        # if message.get("image"):
        #     try:
        #         # Extract the actual base64 data and mime type
        #         base64_string = message.get("image")
        #         if ',' in base64_string:
        #             header, base64_data = base64_string.split(',', 1)
        #             mime_type = header.split(':')[1].split(';')[0]
        #         else:
        #             base64_data = base64_string
        #             mime_type = 'image/jpeg'  # default to JPEG if no header

        #         # Decode base64 to bytes
        #         image_bytes = base64.b64decode(base64_data)

        #         # Create an image Part using FileData
        #         image_part = Part.from_data(image_bytes, mime_type=mime_type)
        #         message_parts.append(image_part)

        #         # Add text content if present
        #         if message.get("content"):
        #             message_parts.append(message["content"])
        #         else:
        #             message_parts.append("Name the cheese in the image, no descriptions needed")
        #     except ValueError as e:
        #         print(f"Error processing image: {str(e)}")
        #         raise HTTPException(
        #             status_code=400,
        #             detail=f"Image processing failed: {str(e)}"
        #         )
        # elif message.get("image_path"):
        #     # Read the image file
        #     image_path = os.path.join("chat-history","llm-rag",message.get("image_path"))
        #     with Path(image_path).open('rb') as f:
        #         image_bytes = f.read()

        #     # Determine MIME type based on file extension
        #     mime_type = {
        #         '.jpg': 'image/jpeg',
        #         '.jpeg': 'image/jpeg',
        #         '.png': 'image/png',
        #         '.gif': 'image/gif'
        #     }.get(Path(image_path).suffix.lower(), 'image/jpeg')

        #     # Create an image Part using FileData
        #     image_part = Part.from_data(image_bytes, mime_type=mime_type)
        #     message_parts.append(image_part)

        #     # Add text content if present
        #     if message.get("content"):
        #         message_parts.append(message["content"])
        #     else:
        #         message_parts.append("Name the cheese in the image, no descriptions needed")
        else:
            # Add text content if present
            if message.get("content"):
                # Create embeddings for the message content
                query_embedding = generate_query_embedding(message["content"])
                # Retrieve chunks based on embedding value
                results = collection.query(
                    query_embeddings=[query_embedding], n_results=5
                )
                INPUT_PROMPT = f"""
                {message["content"]}
                {"\n".join(results["documents"][0])}
                """
                message_parts.append(INPUT_PROMPT)

        if not message_parts:
            raise ValueError("Message must contain either text content or image")

        # Send message with all parts to the model
        response = chat_session.send_message(
            message_parts, generation_config=generation_config
        )

        return response.text

    except Exception as e:
        print(f"Error generating response: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail=f"Failed to generate response: {str(e)}"
        )


def rebuild_chat_session(chat_history: List[Dict]) -> ChatSession:
    """Rebuild a chat session with complete context"""
    new_session = create_chat_session()

    for message in chat_history:
        if message["role"] == "user":
            generate_chat_response(new_session, message)

    return new_session
