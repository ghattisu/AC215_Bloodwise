import os
import argparse
import pandas as pd
import json
import time
import glob
import sys
from google.cloud import storage
import vertexai
from vertexai.preview.tuning import sft
from vertexai.generative_models import GenerativeModel, GenerationConfig

# Setup
GCP_PROJECT = os.environ["GCP_PROJECT"]
TRAIN_DATASET = "gs://llm-fine-tune-generation-sg/llm-finetune-dataset-small/train.jsonl" # Replace with your dataset
VALIDATION_DATASET = "gs://llm-fine-tune-generation-sg/llm-finetune-dataset-small/test.jsonl" # Replace with your dataset
GCP_LOCATION = "us-central1"
GENERATIVE_SOURCE_MODEL = "gemini-1.5-flash-002" # gemini-1.5-pro-002
# Configuration settings for the content generation
generation_config = {
    "max_output_tokens": 3000,  # Maximum number of tokens for output
    "temperature": 0.75,  # Control randomness in output
    "top_p": 0.95,  # Use nucleus sampling
}

vertexai.init(project=GCP_PROJECT, location=GCP_LOCATION)

def train(wait_for_job=False):
    print("train()")

    # Supervised Fine Tuning
    sft_tuning_job = sft.train(
        source_model=GENERATIVE_SOURCE_MODEL,
        train_dataset=TRAIN_DATASET,
        validation_dataset=VALIDATION_DATASET,
        epochs=1, # change to 2-3
        adapter_size=4,
        learning_rate_multiplier=1.0,
        tuned_model_display_name="bloodwise-tuned-model-v3",
    )
    print("Training job started. Monitoring progress...\n\n")

    # Wait and refresh
    time.sleep(60)
    sft_tuning_job.refresh()
    
    if wait_for_job:
        print("Check status of tuning job:")
        print(sft_tuning_job)
        while not sft_tuning_job.has_ended:
            time.sleep(60)
            sft_tuning_job.refresh()
            print("Job in progress...")

    print(f"Tuned model name: {sft_tuning_job.tuned_model_name}")
    print(f"Tuned model endpoint name: {sft_tuning_job.tuned_model_endpoint_name}")
    print(f"Experiment: {sft_tuning_job.experiment}")


def chat():
    print("chat()")
    # Get the model endpoint from Vertex AI: https://console.cloud.google.com/vertex-ai/studio/tuning?project=ac215-project
    #MODEL_ENDPOINT = "projects/129349313346/locations/us-central1/endpoints/810191635601162240"
    #MODEL_ENDPOINT = "projects/129349313346/locations/us-central1/endpoints/5584851665544019968"
    #MODEL_ENDPOINT = "projects/945056213921/locations/us-central1/endpoints/1077223427569352704" # Finetuned model
    MODEL_ENDPOINT = "projects/945056213921/locations/us-central1/endpoints/8860991696037478400"
    
    generative_model = GenerativeModel(MODEL_ENDPOINT)

    query = "Hi, I just got my blood test results back and I'm a bit worried. My total cholesterol is 240 mg/dL, LDL is 160 mg/dL, HDL is 45 mg/dL, and triglycerides are 180 mg/dL. My fasting blood glucose is 110 mg/dL. I'm a 45-year-old man, slightly overweight, and I don't exercise much. What do these results mean, and what changes should I make to improve my health? "
    print("query: ",query)
    response = generative_model.generate_content(
        [query],  # Input prompt
        generation_config=generation_config,  # Configuration settings
        stream=False,  # Enable streaming for responses
    )
    generated_text = response.text
    print("Fine-tuned LLM Response:", generated_text)
     

def main(args=None):
    print("CLI Arguments:", args)

    if args.train:
        train()
    
    if args.chat:
        chat()


if __name__ == "__main__":
    # Generate the inputs arguments parser
    # if you type into the terminal '--help', it will provide the description
    parser = argparse.ArgumentParser(description="CLI")

    parser.add_argument(
        "--train",
        action="store_true",
        help="Train model",
    )
    parser.add_argument(
        "--chat",
        action="store_true",
        help="Chat with model",
    )

    args = parser.parse_args()

    main(args)