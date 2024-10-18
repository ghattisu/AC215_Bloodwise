## Milestone 2


#### Project Milestone 2 Organization


```
├── Readme.md
├── dvc
│   ├── .dvc
│   │   └── config
│   ├── .dvcignore
│   ├── datasets.dvc
│   ├── docker-entrypoint.sh
│   ├── docker-shell.sh
│   ├── Dockerfile
│   ├── Pipfile
│   ├── Readme.md
│   └── Pipfile.lock
├── fine-tuning-sg
│   ├── env.dev
│   ├── Readme.md
│   ├── dataset-creator
│   │   ├── cli.py
│   │   ├── docker-entrypoint.sh
│   │   ├── docker-shell.sh
│   │   ├── Dockerfile
│   │   ├── Pipfile
│   │   ├── Pipfile.lock
│   │   └── data
│   │       ├── .gitkeep
│   └── gemini-finetuner
│       ├── cli.py
│       ├── docker-entrypoint.sh
│       ├── docker-shell.sh
│       ├── Dockerfile
│       ├── Pipfile
│       └── Pipfile.lock
├── llm
│   ├── docker-volumes
│   ├── input-datasets
│   ├── biomarker_dictionary.csv
│   ├── chatbot_interface.py
│   ├── cli.py
│   ├── docker-compose.yml
│   ├── docker-entrypoint.sh
│   ├── docker-shell.sh
│   ├── Dockerfile
│   ├── Pipfile
│   ├── Pipfile.lock
│   ├── README.md
│   └── semantic_splitter.py
└── scraping
    ├── biomarkers_glossary
    ├── images
    │   └── containerimage.png
    ├── biomarkers_glossary.csv
    ├── Dockerfile
    ├── Pipfile
    ├── Pipfile.lock
    ├── docker-entrypoint.sh
    ├── docker-shell.sh
    ├── scrape_biomarkers.ipynb
    ├── README.md
    └── cli.py
```


# AC215 - Milestone2 - Bloodwise App


**Team Members**
Lucy Chen, Surabhi Ghatti, Siavash Raissi, Xingli Yu


**Group Name**
Bloodwise


**Project**
The goal of this project is to develop an application that provides users with easy explanations of lab test results based on the provided results and a symptom summary. The app will suggest what the results could mean, and if abnormal, suggest lifestyle changes, specifying to consult with a physician as well. The application will have a chatbot interface using a large language model (LLM) built on retrieval augmented generation (RAG) with accurate medical information.


### Milestone2 ###


In this milestone, we have the components for data management, including versioning, as well as the data scraping and cleaning needed to build out our RAG Pipeline. We have also attempted to fine-tune our LLM using dataset generation. Within the RAG container, we also launch our initial UI for our application.

**


**Data**
We scrapped several web pages from the Cleveland Clinic and Docus.AI that contain information about biomarkers and complete blood count (CBC). For each resource, we took the main glossary page to collect links to individual biomarker pages.


**Data Pipeline Containers**
1. Scraping: processes the scrapped webpages and saves them to a CSV file as well as individual text files to be used for the RAG pipeline.


	  **Input:** None
	
	
	  **Output:** CSV and txt files of scrapped webpages to be used for LLM


2. Fine-tuning: generates a question/answer dataset to be used to finetune the Gemini Model 


	  **Input:** Source and destination GCS locations, Vertex AI-service account
	
	
	  **Output:** Fine-tuned Gemini model deployed to an endpoint


3. LLM: this prepares the data generated from scraping for the RAG model, including tasks such as chunking, embedding, and populating the vector database. It then calls on the fine-tuned model and deploys the application interface.
 
	  **Input:** Scraped txt files and csv file, Vertex AI-service account
	
	
	  **Output:** Streamlit app with RAG fine-tuned LLM


4. DVC: sets-up and runs DVC to ensure proper version control of the data being used. 

   	  **Input:** The actual input datasets for LLM and Fine-tuning
	
	
	  **Output:** A small text files (`.dvc`) that contain: 
- Path to the actual data in the DVC cache, 
- MD5 hash of the data
- Information about how to reproduce the data





## Data Pipeline Overview


Here is a visual of our data pipeline: 

Since each section is containerized, please access the readme’s of each subfolder to run each container:
1. [Scraping](https://github.com/ghattisu/AC215_Bloodwise/tree/starter/scraping)
2. [Fine-Tuning](https://github.com/ghattisu/AC215_Bloodwise/tree/starter/fine-tuning-sg)
3. [LLM-RAG Deployment](https://github.com/ghattisu/AC215_Bloodwise/tree/starter/llm)
4. [DVC](https://github.com/ghattisu/AC215_Bloodwise/tree/starter/dvc)


## Container Preview
When run, each section's container and its respective Pipenv virtual environment should appear in the terminal and in DockerHub as:
![Container Image](https://github.com/ghattisu/AC215_Bloodwise/blob/starter/scraping/images/containerimage.png?raw=true)


### Resulting code options for each Container


**Scraping**
```
python cli.py

```


**Fine-tuning LLM**
```
*Dataset generation:*


python cli.py --generate
python cli.py --prepare
python cli.py --upload


*Gemini Finetuning:*


python cli.py --train
python cli.py --chat

```


**RAG and Deployment**
```
python cli.py --chunk
python cli.py --embed
python cli.py --load

```


**DVC**
```
# Current data version
dvc get https://github.com/ghattisu/AC215_Bloodwise.git dvc/datasets --rev starter

# Retrieve a different data version, let's try version 1
dvc get https://github.com/ghattisu/AC215_Bloodwise.git dvc/datasets --force --quiet --rev dataset_v1

```
