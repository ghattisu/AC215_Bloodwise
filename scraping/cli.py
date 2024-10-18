import os
import argparse
import requests
from bs4 import BeautifulSoup
from google.cloud import storage
import pandas as pd
import glob

# Setup
GCP_PROJECT = os.environ["GCP_PROJECT"]
GCP_LOCATION = "us-central1"
OUTPUT_FOLDER = "input-datasets"
GCS_BUCKET_NAME = "bloodwise-rag-knowledge-base"

def scrape():
    ## docus
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
        print(key)
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
    
    
def upload():
    print("Uploading")
    storage_client = storage.Client()
    bucket = storage_client.bucket(GCS_BUCKET_NAME)
    timeout = 300
    
    data_files = glob.glob(os.path.join(OUTPUT_FOLDER, "*.txt"))
    data_files.sort()
    print(data_files)
    
    # Upload
    for index, data_file in enumerate(data_files):
        filename = os.path.basename(data_file)
        destination_blob_name = os.path.join("text-documents", filename)
        blob = bucket.blob(destination_blob_name)
        print("Uploading file:", data_file, destination_blob_name)
        blob.upload_from_filename(data_file, timeout=timeout)
        
        

def main(args=None):
	print("CLI Arguments:", args)

	if args.scrape:
		scrape()

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
		"--upload",
		action="store_true",
		help="Upload data to GCP bucket",
	)

	args = parser.parse_args()
	main(args)
    