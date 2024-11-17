# Scraping Web Documents for RAG

In this container, we prepared a script that performs web scraping to gather information about biomarkers and complete blood count (CBC) from two different sources: Docus.ai and Cleveland Clinic. For each resource, the script fetches the main glossary page and iterates to collect links to individual biomarker pages, stores the content of each biomarker page in a dictionary, and then saves the collected data into a CSV file and individual text files. These files serve as the basis for subsequent chunking, embedding, vectorization, and retrieving of data via RAG.

## Prerequisites
* Have Docker installed
* Cloned this repository to your local machine https://github.com/ghattisu/AC215_Bloodwise
* Modify `env.dev` to represent your Bucket and Project Name.


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


## Upload scraped text documents to GCP Bucket
`python cli.py --upload`

This will:
* Upload the .txt files in AC215_Bloodwise/scraping/input-datasets to a GCP bucket

Once finished, navigate to the AC215_Bloodwise/llm directory to begin chunking and vectorizing the collected resources as a means to enhance LLM responses.
