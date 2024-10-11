import os
import argparse
import pandas as pd
import json
import time
import glob
from sklearn.model_selection import train_test_split
from google.cloud import storage
import vertexai

# Setup
GCP_PROJECT = os.environ["GCP_PROJECT"]
GCP_LOCATION = "us-central1"
OUTPUT_FOLDER = "finetuning-data"
GCS_BUCKET_NAME = os.environ["GCS_BUCKET_NAME"]


def prepare():
    print("prepare()")
    
    output_pairs_df = pd.read_json("hf://datasets/medalpaca/medical_meadow_medical_flashcards/medical_meadow_wikidoc_medical_flashcards.json")
    output_pairs_df = output_pairs_df[output_pairs_df["input"]!=""][["input", "output"]]
    output_pairs_df.rename(columns={"input":"question", "output":"answer"}, inplace=True)
    
    filename = os.path.join(OUTPUT_FOLDER, "instruct-dataset.csv")
    output_pairs_df.to_csv(filename, index=False)
    
    # output_pairs_df = pd.read_csv(filename)

    # Build training formats
    output_pairs_df['text'] = "human: " + output_pairs_df['question'] + "\n" + "bot: " + output_pairs_df['answer']
    output_pairs_df["contents"] = output_pairs_df.apply(lambda row: [{"role":"user","parts":[{"text": row["question"]}]},{"role":"model","parts":[{"text": row["answer"]}]}], axis=1)

    # Test train split
    df_train, df_test = train_test_split(output_pairs_df, test_size=0.1, random_state=42)
    df_train[["text"]].to_csv(os.path.join(OUTPUT_FOLDER, "train.csv"), index = False)
    df_test[["text"]].to_csv(os.path.join(OUTPUT_FOLDER, "test.csv"), index = False)

    # Gemini : Max numbers of examples in validation dataset: 256
    df_test = df_test[:256]

    # JSONL
    with open(os.path.join(OUTPUT_FOLDER, "train.jsonl"), "w") as json_file:
        json_file.write(df_train[["contents"]].to_json(orient='records', lines=True))
    with open(os.path.join(OUTPUT_FOLDER, "test.jsonl"), "w") as json_file:
        json_file.write(df_test[["contents"]].to_json(orient='records', lines=True))


def upload():
    print("upload()")

    storage_client = storage.Client()
    bucket = storage_client.bucket(GCS_BUCKET_NAME)
    timeout = 300

    data_files = glob.glob(os.path.join(OUTPUT_FOLDER, "*.jsonl")) + glob.glob(os.path.join(OUTPUT_FOLDER, "*.csv"))
    data_files.sort()
    
    # Upload
    for index, data_file in enumerate(data_files):
        filename = os.path.basename(data_file)
        destination_blob_name = os.path.join("llm-finetune-dataset-small", filename)
        blob = bucket.blob(destination_blob_name)
        print("Uploading file:", data_file, destination_blob_name)
        blob.upload_from_filename(data_file, timeout=timeout)
    

def main(args=None):
    print("CLI Arguments:", args)

    if args.prepare:
        prepare()
      
    if args.upload:
        upload()


if __name__ == "__main__":
    # Generate the inputs arguments parser
    # if you type into the terminal '--help', it will provide the description
    parser = argparse.ArgumentParser(description="CLI")

    parser.add_argument(
        "--prepare",
        action="store_true",
        help="Prepare data",
    )
    parser.add_argument(
        "--upload",
        action="store_true",
        help="Upload data to bucket",
    )

    args = parser.parse_args()

    main(args)