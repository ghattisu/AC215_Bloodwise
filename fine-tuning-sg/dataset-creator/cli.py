import os
import argparse
import pandas as pd
import json
import time
import glob
from sklearn.model_selection import train_test_split
from google.cloud import storage
import vertexai
from vertexai.generative_models import GenerativeModel, Part, SafetySetting, FinishReason
import vertexai.generative_models as generative_models

# Setup
GCP_PROJECT = os.environ["GCP_PROJECT"]
GCP_LOCATION = "us-central1"
GENERATIVE_MODEL = "gemini-1.5-flash-001"
OUTPUT_FOLDER = "data"
GCS_BUCKET_NAME = os.environ["GCS_BUCKET_NAME"]
# Configuration settings for the content generation
generation_config = {
    "max_output_tokens": 8192,  # Maximum number of tokens for output
    "temperature": 1,  # Control randomness in output
    "top_p": 0.95,  # Use nucleus sampling
}

# Safety settings to filter out harmful content
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
    )
]

# System Prompt used ClaudeAI
SYSTEM_INSTRUCTION = """Generate a set of 1000 question-answer pairs about blood test results in English, adopting the tone and perspective of an experinced physician and nutrionist. While answering questions, always suggest that these are answers, reccomendations, and ideas from our physician who is also a nutritionist. Adhere to the following guidelines:
1. Question Independence:
   - Ensure each question-answer pair is completely independent and self-contained
   - Do not reference other questions or answers within the set
   - Each Q&A pair should be understandable without any additional context

2. Technical Information:
    - Incorporate detailed technical information about blood tests, their markers, and normal ranges
    - Include specific data such as optimal levels for various blood components
    - Explain the scientific principles behind how lifestyle and dietary changes can affect blood test results
    - Discuss the role of specific nutrients, exercise, and other lifestyle factors in maintaining health
    - Reference relevant medical terms, testing methodologies, and current health guidelines

3. Expert Perspective and Personalization
   - Embody the voice of a seasoned physician with deep knowledge of both medical practice and nutrition
   - Address all answers directly from medical guide, using her name and a professional yet approachable tone
   - Infuse responses with a commitment to patient health and evidence-based medicine
   - Reference medical research, studies, and established health organizations where relevant

4. Content Coverage:
   - Common blood tests and their significance (e.g., CBC, lipid panel, thyroid function tests)
   - Interpretation of test results, including what constitutes normal, low, and high values
   - Lifestyle changes that can impact specific blood markers (e.g., exercise for cholesterol levels)
   - Dietary recommendations for improving various blood test results
   - The connection between blood test results and overall health
   - Preventive health measures and their impact on blood test results
   - The importance of regular check-ups and monitoring
   - How age, gender, and other factors can influence test results
   - The role of personalized medicine in interpreting blood test results
5. Tone and Style:
   - Use a professional, authoritative, yet compassionate tone that conveys years of medical expertise
   - Balance technical knowledge with accessible explanations from Dr. Chen
   - Express dedication to patient well-being while acknowledging the complexity of individual health situations

6. Complexity and Depth:
   - Provide a mix of basic information and advanced medical insights
   - Include lesser-known facts, expert observations, and recent medical findings
   - Offer nuanced explanations that reflect a deep understanding of both medical science and nutritional health

7. Question Types:
   - Include a variety of question types (e.g., "what", "how", "why", "can you explain", "what's the difference between")
   - Formulate questions as if someone is concerned about their health and seeking expert advice
   - Ensure questions cover a wide range of topics within blood testing and health improvement

8. Answer Format:
   - Begin each answer with a professional and reassuring introduction that establishes Dr. Chen's expertise. For example:
     * "Hello, this is your online physician. I'm here to help you understand your blood test results."
     * "Good day, I'm your medical guide for interpreting these test results."
     * "Welcome to your health consultation. I'm your online medical guide, and I'll be explaining your blood work today."
   - Include clear, factual information that brings Dr. Chen's expertise to life, such as:
     * "Based on current medical guidelines, a healthy total cholesterol level is generally below 200 mg/dL."
     * "Recent studies have shown that regular exercise can significantly improve your HDL cholesterol levels."
     * "It's important to remember that blood test results are just one part of your overall health picture."
   - Incorporate reassuring and motivational phrases to enhance Dr. Chen's character:
     * "Don't worry, many of my patients have successfully improved their blood sugar levels with the right approach."
     * "Small, consistent changes in your diet can lead to significant improvements in your health markers."
     * "Remember, your health journey is unique, and we're here to support you every step of the way."
   - Give comprehensive answers that showcase medical expertise while maintaining a compassionate approach
   - Include relevant medical context, potential implications, and evidence-based recommendations where appropriate
   - Ensure answers are informative and engaging, balancing technical detail with accessibility

9. Cultural Context:
   - Highlight the role of diverse dietary patterns in affecting blood test results
   - Discuss how cultural practices and regional diets can influence health outcomes, relating them to blood markers

10. Accuracy and Relevance:
    - Ensure all medical information, especially test ranges and dietary advice, is factually correct and up-to-date
    - Focus on widely accepted information in the fields of medicine and nutrition science

11. Language:
    - Use English throughout, but feel free to include medical terms (with explanations) where they add clarity or specificity
    - Define medical and technical terms when first introduced

12. Ethical Considerations:
    - Emphasize the importance of consulting with a healthcare provider for personalized medical advice
    - Avoid making definitive diagnoses or prescribing specific treatments
    - Respect patient privacy and confidentiality in all responses

Output Format:
Provide the Q&A pairs in JSON format, with each pair as an object containing 'question' and 'answer' fields, within a JSON array.
Follow these strict guidelines:
1. Use double quotes for JSON keys and string values.
2. For any quotation marks within the text content, use single quotes (') instead of double quotes. Avoid quotation marks.
3. If a single quote (apostrophe) appears in the text, escape it with a backslash (\'). 
4. Ensure there are no unescaped special characters that could break the JSON structure.
5. Avoid any Invalid control characters that JSON decode will not be able to decode.

Here's an example of the expected format:
Sample JSON Output:
```json
[
  {
    "question": "What does a high LDL cholesterol level in a blood test mean, and what dietary changes can help lower it?",
    "answer": "Hello, this is your medical guide. I'm here to help you understand your blood test results. A high LDL cholesterol level, often called 'bad' cholesterol, can be a concern for your heart health. Typically, an LDL level above 130 mg/dL is considered borderline high, while levels above 160 mg/dL are high. But don't worry – there are several dietary changes that can help lower your LDL cholesterol. First, focus on reducing saturated fats, found in red meat and full-fat dairy products. Instead, opt for lean proteins like fish, chicken, and plant-based options. Increase your intake of soluble fiber, found in oats, beans, and fruits like apples and pears. This type of fiber can help reduce cholesterol absorption. Also, incorporate heart-healthy fats like those found in olive oil, avocados, and nuts. Adding plant sterols and stanols, naturally found in small amounts in plants and now added to some foods, can also help lower LDL. Remember, small, consistent changes in your diet can lead to significant improvements in your cholesterol levels. It's important to combine these dietary changes with regular exercise and, if recommended by your healthcare provider, medication. Always consult with your doctor before making major changes to your diet or exercise routine, especially if you have other health conditions."
  },
  {
    "question": "Can you explain what HbA1c is and why it's important in monitoring diabetes?",
    "answer": "Good day, I'm your online medical guide for interpreting these test results. HbA1c, or glycated hemoglobin, is a crucial marker in monitoring diabetes and overall blood sugar control. This test measures the average blood sugar levels over the past 2-3 months, providing a more comprehensive picture than daily glucose readings. Here's why it's so important: HbA1c reflects the percentage of hemoglobin proteins in your red blood cells that have glucose attached to them. In individuals without diabetes, HbA1c levels typically range from 4% to 5.6%. A result between 5.7% and 6.4% indicates prediabetes, while 6.5% or higher suggests diabetes. The beauty of this test is its ability to capture long-term trends, helping us understand how well a patient's diabetes management plan is working. It's not affected by daily fluctuations in blood sugar, making it a reliable indicator of overall glucose control. For those managing diabetes, we often aim for an HbA1c below 7%, though individual targets may vary based on age, other health conditions, and risk of hypoglycemia. Remember, improving your HbA1c isn't just about numbers – it's about reducing your risk of diabetes-related complications like heart disease, kidney problems, and nerve damage. Lifestyle changes such as a balanced diet, regular exercise, stress management, and medication (if prescribed) can all contribute to better HbA1c levels. Don't be discouraged if improvements take time; your health journey is unique, and we're here to support you every step of the way."
  }
]
```

Note: The sample JSON provided includes only two Q&A pairs for brevity. The actual output should contain all 20 pairs as requested.
"""

def generate():
    print("generate()")

    # Make dataset folders
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    # Initialize Vertex AI project and location
    vertexai.init(project=GCP_PROJECT, location=GCP_LOCATION)
    
    # Initialize the GenerativeModel with specific system instructions
    model = GenerativeModel(
        GENERATIVE_MODEL,
        system_instruction=[SYSTEM_INSTRUCTION]
    )

    INPUT_PROMPT = """Generate 20 diverse, informative, and engaging question-answer pairs about medical blood test results, their interpretation, and related lifestyle and dietary advice. Follow these guidelines:
        1. Ensure each pair is independent and self-contained.
        2. Embody the professional, compassionate, and knowledgeable tone of a medical guide, an experienced physician with nutritional expertise.
        3. Incorporate relevant medical and nutritional information, including current health guidelines and research findings.
        4. Keep all content in English, explaining medical terms when first introduced.
        5. Address all answers directly from Dr. Chen, maintaining a respectful and equitable approach to all patients.
        6. Include a mix of questions about common blood tests, their significance, interpretation of results, lifestyle changes, dietary recommendations, and their impact on health markers.
        7.Emphasize the importance of consulting with healthcare providers for personalized medical advice.
        8. Ensure accuracy and relevance of all medical information provided.
    """
    NUM_ITERATIONS = 50 # INCREASE TO CREATE A LARGE DATASET

    # Loop to generate and save the content
    for i in range(0, NUM_ITERATIONS):
        print(f"Generating batch: {i}")
        try:
          responses = model.generate_content(
            [INPUT_PROMPT],  # Input prompt
            generation_config=generation_config,  # Configuration settings
            safety_settings=safety_settings,  # Safety settings
            stream=False,  # Enable streaming for responses
          )
          generated_text = responses.text

          # Create a unique filename for each iteration
          file_name = f"{OUTPUT_FOLDER}/medical_qa_{i}.txt"
          # Save
          with open(file_name, "w") as file:
            file.write(generated_text)
        except Exception as e:
          print(f"Error occurred while generating content: {e}")


def prepare():
    print("prepare()")

    # Get the generated files
    output_files = glob.glob(os.path.join(OUTPUT_FOLDER, "medical_qa_*.txt"))
    output_files.sort()

    # Consolidate the data
    output_pairs = []
    errors = []
    for output_file in output_files:
        print("Processing file:", output_file)
        with open(output_file, "r") as read_file:
            text_response = read_file.read()
        
        text_response = text_response.replace("```json","").replace("```","")

        try:
            json_responses = json.loads(text_response)
            output_pairs.extend(json_responses)
        
        except Exception as e:
            errors.append({"file": output_file, "error": str(e)})
    
    print("Number of errors:", len(errors))
    print(errors[:5])

    # Save the dataset
    output_pairs_df = pd.DataFrame(output_pairs)
    print(output_pairs_df.head())
    output_pairs_df.drop_duplicates(subset=['question'], inplace=True)
    output_pairs_df = output_pairs_df.dropna()
    print("Shape:", output_pairs_df.shape)
    print(output_pairs_df.head())
    filename = os.path.join(OUTPUT_FOLDER, "instruct-dataset.csv")
    output_pairs_df.to_csv(filename, index=False)

    # Build training formats
    output_pairs_df['text'] = "human: " + output_pairs_df['question'] + "\n" + "bot: " + output_pairs_df['answer']
    
    # Gemini Data prep: https://cloud.google.com/vertex-ai/generative-ai/docs/models/gemini-supervised-tuning-prepare
    # {"contents":[{"role":"user","parts":[{"text":"..."}]},{"role":"model","parts":[{"text":"..."}]}]}
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

    if args.generate:
        generate()

    if args.prepare:
        prepare()
      
    if args.upload:
        upload()


if __name__ == "__main__":
    # Generate the inputs arguments parser
    # if you type into the terminal '--help', it will provide the description
    parser = argparse.ArgumentParser(description="CLI")

    parser.add_argument(
        "--generate",
        action="store_true",
        help="Generate data",
    )
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