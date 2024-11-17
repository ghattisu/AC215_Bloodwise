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
GCS_BUCKET_NAME = os.environ["GCS_BUCKET_NAME"]

def make_request(url):
    """Handles HTTP requests and returns the content of the page."""
    response = requests.get(url)
    response.raise_for_status()  # raises exception when not a 2xx response
    return response.text

def extract_links_from_cards(soup, class_name):
    """Extracts links from the cards in the BeautifulSoup object."""
    cards = soup.find_all('div', class_=class_name)
    links = []
    for card in cards:
        link = card.find('a')
        if link and not link.get('href').startswith('/tags'):
            links.append(link.get('href'))
    return links

def extract_text_from_page(soup, content_class):
    """Extracts the text content from a page."""
    page_content = soup.find('section', class_=content_class)
    text = ''
    if page_content:
        for i in page_content.find_all('div', recursive=False)[2:]:
            text += i.get_text() + "\n"
    return text

def save_to_file(filename, content):
    """Saves the scraped content to a file."""
    with open(filename, 'w') as file:
        file.write(content)

def scrape_biomarkers_page(start_url):
    """Scrape the Docus AI glossary biomarker pages."""
    page = 1
    links = []
    while True:
        url = f'{start_url}?page={page}'
        content = make_request(url)
        if 'No results found' in content:
            break
        soup = BeautifulSoup(content, 'html.parser')
        links += extract_links_from_cards(soup, 'ant-col ant-col-xs-24 css-1drr2mu')
        page += 1
    return links

def scrape_biomarkers_info(links):
    """Scrape details from the individual biomarkers pages."""
    biomarkers_glossary = {}
    for url in links:
        content = make_request(f"https://docus.ai/{url}")
        soup = BeautifulSoup(content, 'html.parser')
        title = soup.find("h1")
        text = extract_text_from_page(soup, 'sc-5d4eaeca-0 htRsFi sc-fdf5dc80-0 gsFBbo')
        if title:
            biomarkers_glossary[title.text] = text
    return biomarkers_glossary

def scrape_cleveland_clinic():
    """Scrape Cleveland Clinic page and linked articles."""
    url = "https://my.clevelandclinic.org/health/diagnostics/4053-complete-blood-count"
    content = make_request(url)
    soup = BeautifulSoup(content, 'html.parser')
    page_content = soup.find('div', {'data-identity': 'main-article-content'})
    cleveland_cbc_text = soup.find('h1').text + "\n"
    for i in page_content.find_all('div', recursive=False)[1:-1]:
        cleveland_cbc_text += i.get_text() + "\n"
    links = []
    for link in page_content.find_all('a'):
        if link.get('href').startswith('https://my.clevelandclinic.org/'):
            links.append(link.get('href'))
    return cleveland_cbc_text, links

def scrape():
    # Docus AI Biomarkers
    start_url = 'https://docus.ai/glossary/biomarkers'
    links = scrape_biomarkers_page(start_url)
    biomarkers_glossary = scrape_biomarkers_info(links)

    # Save biomarkers info to files
    for key, value in biomarkers_glossary.items():
        save_to_file(f'input-datasets/{key}.txt', value)

    # Cleveland Clinic
    cleveland_cbc_text, links = scrape_cleveland_clinic()

    # Process the Cleveland Clinic links and collect text
    while links:
        try:
            new_link = links.pop(0)
            content = make_request(new_link)
            soup = BeautifulSoup(content, 'html.parser')
            page_content = soup.find('div', {'data-identity': 'main-article-content'})
            cleveland_cbc_text += soup.find('h1').text + "\n"
            for i in page_content.find_all('div', recursive=False)[1:-1]:
                cleveland_cbc_text += i.get_text() + "\n"
            for link in page_content.find_all('a'):
                href = link.get('href')
                if href.startswith('https://my.clevelandclinic.org/') and href not in links:
                    links.append(href)
        except Exception as e:
            print(f"Error with link: {new_link}, error: {e}")

    save_to_file('input-datasets/cleveland_clinic.txt', cleveland_cbc_text)
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
    