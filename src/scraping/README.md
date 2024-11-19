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

## Testing for this container
To run the pytests for this container, use the command `pytest tests/test_scrape.py` 

Initial setup:
- There are sample REAL_URLS, FAKE_URLS, and TEST_HTML responses to mock what should be present when accessing the web and what should be returned from scraping. The REAL_URLS consist of active URL's that we are currently using. FAKE_URLS and TEST_HTML are made up for the purposes of testing various functions functionalities.

Functions tested:
- get_mock_html(): mocks a real requests.get() function based on the chosen urls
- test_make_request(): uses get_mock_html() function to test various urls and the content and/or exceptions they return
- test_scrape_biomarkers_page(): tests the ability to pull down links from docus AI
- test_scrape_biomarkers_info(): accesses the links gotten from docus AI to check content (using mock HTML responses)
- test_scrape_cleveland_clinic(): tests the ability to pull down links from cleveland clinic
- test_save_to_file(): tests the ability to save scraped content into txt files
