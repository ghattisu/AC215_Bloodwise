import os
import sys
import pytest
import requests
import requests_mock
from io import StringIO
from bs4 import BeautifulSoup
import tempfile
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from cli import scrape, make_request, extract_links_from_cards, extract_text_from_page, scrape_biomarkers_page, scrape_biomarkers_info, scrape_cleveland_clinic

# Sample test data
REAL_URLS = [
    "https://docus.ai/glossary/biomarkers/ethyl-glucuronide",
    "https://my.clevelandclinic.org/health/diagnostics/4053-complete-blood-count"
]

FAKE_URLS = [
    "https://docus.ai/glossary/biomarkers/does-not-exist",
    "https://my.clevelandclinic.org/health/diagnostics/does-not-exist"
]

TEST_HTML =  """
    <html>
        <body>
            <div class="ant-col ant-col-xs-24 css-1drr2mu">
                <a href="/glossary/biomarkers/ethyl-glucuronide">Ethyl Glucuronide</a>
            </div>
            <div class="ant-col ant-col-xs-24 css-1drr2mu">
                <a href="/glossary/biomarkers/ets-urine-test">ETS Urine Test</a>
            </div>
        </body>
    </html>
    """


# Helper function to generate mock HTML content for each URL
def get_mock_html(url,empty=False):
    if empty: 
        return "<html><body><h1>Empty Page</h1><div>No content available.</div></body></html>"
    elif "ethyl-glucuronide" in url:
        return "<html><body><h1>Ethyl Glucuronide</h1><div>Some content about ethyl glucuronide.</div></body></html>"
    elif "complete-blood-count" in url:
        return "<html><body><h1>Complete Blood Count</h1><div>Details on complete blood count.</div></body></html>"
    return "<html><body><h1>Unknown Page</h1><div>Content not found.</div></body></html>"

# Use a temporary directory for the output files
@pytest.fixture(scope='module')
def temp_directory():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

# Test for the make_request function (mocking HTTP requests)
def test_make_request():
    url= REAL_URLS[0]
    with requests_mock.Mocker() as m:
        m.get(url, text=get_mock_html(url))
        content = make_request(url)
        assert "Ethyl Glucuronide" in content

    # Test real URL with no content
    with requests_mock.Mocker() as m:
        m.get(url, text=get_mock_html(url, empty=True)) 
        content = make_request(url)
        assert "No content available" in content  # We check for a placeholder in an empty page
    
    # Test fake URL
    fake_url = FAKE_URLS[0]  # Fake URL
    with pytest.raises(requests.exceptions.RequestException):
        make_request(fake_url)

# Test for extract_link_from_cards
def test_extract_link_from_cards():
    html = TEST_HTML
    with requests_mock.Mocker() as m:
        m.get("https://docus.ai/glossary/biomarkers", text=html)
        soup = requests.get("https://docus.ai/glossary/biomarkers").text
        soup = BeautifulSoup(soup, 'html.parser')
        links = extract_links_from_cards(soup, 'ant-col ant-col-xs-24 css-1drr2mu')
        assert len(links) == 2
        assert '/glossary/biomarkers/ethyl-glucuronide' in links
        assert '/glossary/biomarkers/ets-urine-test' in links

# Test biomarker pages
def test_scrape_biomarkers_page():
    url='https://docus.ai/glossary/biomarkers'
    with requests_mock.Mocker() as m:
        m.get(url, text=TEST_HTML)
        soup = BeautifulSoup(TEST_HTML, 'html.parser')
        links = extract_links_from_cards(soup, 'ant-col ant-col-xs-24 css-1drr2mu')
        assert len(links) == 2
        assert '/glossary/biomarkers/ethyl-glucuronide' in links
        assert '/glossary/biomarkers/ets-urine-test' in links
    
    # Test fake site
    fake_url = FAKE_URLS[0]
    with pytest.raises(requests.exceptions.RequestException):
        make_request(fake_url)