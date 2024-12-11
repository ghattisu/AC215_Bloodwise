import os
import sys
import pytest
import requests
import requests_mock
from bs4 import BeautifulSoup
import tempfile
#import pandas as pd
import json
#import glob
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from cli import scrape, generate_query_embedding, generate_text_embeddings, chunk, embed, upload

# Sample mock HTML content
MOCK_DOCUS_INITIAL_PAGE = """
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

MOCK_DOCUS_BIOMARKER_PAGE = """
<html>
    <h1>Ethyl Glucuronide</h1>
    <section class="sc-5d4eaeca-0 htRsFi sc-fdf5dc80-0 gsFBbo">
        <div>Header content</div>
        <div>Navigation content</div>
        <div>Some content about ethyl glucuronide.</div>
    </section>
</html>
"""

MOCK_CLEVELAND_CLINIC_PAGE = """
<html>
    <h1>Complete Blood Count</h1>
    <div data-identity="main-article-content">
        <div>Navigation</div>
        <div>Details on complete blood count.</div>
        <div>More information about CBC.</div>
        <div>Footer</div>
        <a href="https://my.clevelandclinic.org/health/diagnostics/4053-complete-blood-count">Complete Blood Count</a>
    </div>
</html>
"""

# Sample test data
REAL_URLS = [
    "https://docus.ai/glossary/biomarkers/ethyl-glucuronide",
    "https://my.clevelandclinic.org/health/diagnostics/4053-complete-blood-count"
]
# Fixtures to setup and teardown test environment
@pytest.fixture(scope='function')
def input_datasets_dir(tmp_path):
    """Create a temporary input datasets directory"""
    input_dir = tmp_path / "input-datasets"
    input_dir.mkdir()
    return input_dir

@pytest.fixture(scope='function')
def output_datasets_dir(tmp_path):
    """Create a temporary output datasets directory"""
    output_dir = tmp_path / "outputs"
    output_dir.mkdir()
    return output_dir

@pytest.fixture(scope='function')
def mock_env_vars(monkeypatch):
    """Mock environment variables"""
    monkeypatch.setenv("GCP_PROJECT", "test-project")
    monkeypatch.setenv("GCS_BUCKET_NAME", "test-bucket")
    return None

@pytest.fixture
def mock_requests(monkeypatch):
    """Create a fixture to mock requests and file operations"""
    # Ensure the input-datasets directory exists
    os.makedirs('input-datasets', exist_ok=True)

# Test for scrape function
def test_scrape(mock_requests, tmp_path):
    # Mock the necessary requests
    with requests_mock.Mocker() as m:
        # Mock the initial Docus.ai biomarkers page
        m.get('https://docus.ai/glossary/biomarkers', text="""
        <html>
            <body>
                <div class="ant-col ant-col-xs-24 css-1drr2mu">
                    <a href="/glossary/biomarkers/ethyl-glucuronide">Ethyl Glucuronide</a>
                </div>
            </body>
        </html>
        """)
        
        # Mock the first page of biomarkers results
        m.get('https://docus.ai/glossary/biomarkers?page=1', text="""
        <html>
            <body>
                <div class="ant-col ant-col-xs-24 css-1drr2mu">
                    <a href="/glossary/biomarkers/ets-urine-test">ETS Urine Test</a>
                </div>
            </body>
        </html>
        """)
        
        # Mock the "No results found" page to stop pagination
        m.get('https://docus.ai/glossary/biomarkers?page=2', text='No results found')
        
        # Mock individual biomarker pages
        m.get('https://docus.ai//glossary/biomarkers/ethyl-glucuronide', text="""
        <html>
            <h1>Ethyl Glucuronide</h1>
            <section class="sc-5d4eaeca-0 htRsFi sc-fdf5dc80-0 gsFBbo">
                <div>First div</div>
                <div>Second div</div>
                <div>Detailed information about Ethyl Glucuronide</div>
            </section>
        </html>
        """)
        
        m.get('https://docus.ai//glossary/biomarkers/ets-urine-test', text="""
        <html>
            <h1>ETS Urine Test</h1>
            <section class="sc-5d4eaeca-0 htRsFi sc-fdf5dc80-0 gsFBbo">
                <div>First div</div>
                <div>Second div</div>
                <div>Detailed information about ETS Urine Test</div>
            </section>
        </html>
        """)
        
        # Mock Cleveland Clinic pages
        m.get('https://my.clevelandclinic.org/health/diagnostics/4053-complete-blood-count', text="""
        <html>
            <h1>Complete Blood Count</h1>
            <div data-identity="main-article-content">
                <div>Navigation</div>
                <div>CBC Details</div>
                <div>More CBC Info</div>
                <a href="https://my.clevelandclinic.org/related-test">Related Test</a>
            </div>
        </html>
        """)
        
        # Mock related Cleveland Clinic page
        m.get('https://my.clevelandclinic.org/related-test', text="""
        <html>
            <h1>Related Test</h1>
            <div data-identity="main-article-content">
                <div>Related Test Details</div>
            </div>
        </html>
        """)
        
        # Run the scrape function
        scrape()
    
    # Assert that files were created
    assert os.path.exists('input-datasets/Ethyl Glucuronide.txt')
    assert os.path.exists('input-datasets/ETS Urine Test.txt')
    assert os.path.exists('input-datasets/cleveland_clinic.txt')
    
    # Optional: Check file contents
    with open('input-datasets/Ethyl Glucuronide.txt', 'r') as f:
        content = f.read()
        assert 'Detailed information about Ethyl Glucuronide' in content
    
    with open('input-datasets/cleveland_clinic.txt', 'r') as f:
        content = f.read()
        assert 'Complete Blood Count' in content

# Test for chunking
def test_chunk(monkeypatch, mock_env_vars, input_datasets_dir, output_datasets_dir):
    # Create a sample input text file
    test_file_path = input_datasets_dir / "test_document.txt"
    with open(test_file_path, 'w') as f:
        f.write("This is a test document with multiple sentences to demonstrate chunking.")
    
    # Monkeypatch the directories
    monkeypatch.setattr('cli.OUTPUT_FOLDER', str(input_datasets_dir))
    monkeypatch.setattr('cli.DATASET_FOLDER', str(output_datasets_dir))
    
    # Call the chunk function
    chunk(method="semantic-split")
    
    # Check if chunks were created
    chunk_files = list(output_datasets_dir.glob('*.jsonl'))
    assert len(chunk_files) > 0
    
    # Verify the content of the chunk file
    with open(chunk_files[0], 'r') as f:
        chunks = [json.loads(line) for line in f]
        assert len(chunks) > 0
        assert 'chunk' in chunks[0]
        assert 'book' in chunks[0]

# Test for embedding
def test_embed(monkeypatch, mock_env_vars, input_datasets_dir, output_datasets_dir):
    # Create a sample chunk file for testing
    chunk_file_path = output_datasets_dir / "chunks-semantic-split-test_document.jsonl"
    test_chunks = [
        {"chunk": "First test chunk", "book": "test_document"},
        {"chunk": "Second test chunk", "book": "test_document"}
    ]
    with open(chunk_file_path, 'w') as f:
        for chunk in test_chunks:
            f.write(json.dumps(chunk) + '\n')
    
    # Monkeypatch the directories
    monkeypatch.setattr('cli.DATASET_FOLDER', str(output_datasets_dir))
    
    # Call the embed function
    embed(method="semantic-split")
    
    # Check if embedding files were created
    embedding_files = list(output_datasets_dir.glob('embeddings-*.jsonl'))
    assert len(embedding_files) > 0
    
    # Verify the content of the embedding file
    with open(embedding_files[0], 'r') as f:
        embeddings = [json.loads(line) for line in f]
        assert len(embeddings) > 0
        assert 'embedding' in embeddings[0]

# Test for embedding generation
def test_generate_embeddings(mock_env_vars):
    # Test query embedding
    query = "test query"
    embedding = generate_query_embedding(query)
    assert isinstance(embedding, list)
    assert len(embedding) > 0

    # Test text embeddings
    chunks = ["first chunk", "second chunk"]
    embeddings = generate_text_embeddings(chunks)
    assert len(embeddings) == len(chunks)
    for emb in embeddings:
        assert isinstance(emb, list)
        assert len(emb) > 0