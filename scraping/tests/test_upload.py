from ../cli import upload
import pytest

import pytest
from unittest import mock
import os
import glob
from google.cloud import storage
from  cli import upload  # Replace 'your_module' with the actual module name

# Constants
GCS_BUCKET_NAME = os.environ["GCS_BUCKET_NAME"]
OUTPUT_FOLDER = "input-datasets"

@pytest.fixture
def mock_storage_client():
    # Mock the Google Cloud Storage Client
    with mock.patch('google.cloud.storage.Client') as mock_client:
        mock_bucket = mock.Mock()
        mock_client.return_value.bucket.return_value = mock_bucket
        yield mock_bucket

@pytest.fixture
def mock_glob():
    # Mock glob.glob to simulate file retrieval
    with mock.patch('glob.glob') as mock_glob:
        mock_glob.return_value = [
            'path-to-output-folder/file1.txt',
            'path-to-output-folder/file2.txt'
        ]
        yield mock_glob

@pytest.fixture
def mock_os_path():
    # Mock os.path.join and os.path.basename
    with mock.patch('os.path.join', side_effect=os.path.join) as mock_join, \
         mock.patch('os.path.basename', side_effect=os.path.basename) as mock_basename:
        yield mock_join, mock_basename

@pytest.fixture
def mock_blob():
    # Mock the Blob class' upload_from_filename method
    with mock.patch.object(storage.Blob, 'upload_from_filename') as mock_upload:
        yield mock_upload

def test_upload(mock_storage_client, mock_glob, mock_os_path, mock_blob):
    # Run the upload function
    upload()

    # Assert that glob.glob was called with the correct directory
    mock_glob.assert_called_once_with(os.path.join(OUTPUT_FOLDER, "*.txt"))
    
    # Assert that the correct files are retrieved
    assert mock_glob.return_value == ['path-to-output-folder/file1.txt', 'path-to-output-folder/file2.txt']
    
    # Check that storage.Client().bucket() was called with the correct bucket name
    mock_storage_client.bucket.assert_called_once_with(GCS_BUCKET_NAME)

    # Check that blob.upload_from_filename() was called twice (once for each file)
    mock_blob.assert_any_call('path-to-output-folder/file1.txt', timeout=300)
    mock_blob.assert_any_call('path-to-output-folder/file2.txt', timeout=300)

    # Assert the correct destination blob names
    mock_storage_client.bucket.return_value.blob.assert_any_call('text-documents/file1.txt')
    mock_storage_client.bucket.return_value.blob.assert_any_call('text-documents/file2.txt')

    # Assert that the upload function prints "Uploading"
    with mock.patch('builtins.print') as mock_print:
        upload()
        mock_print.assert_any_call("Uploading")
        mock_print.assert_any_call("Uploading file:", 'path-to-output-folder/file1.txt', 'text-documents/file1.txt')
        mock_print.assert_any_call("Uploading file:", 'path-to-output-folder/file2.txt', 'text-documents/file2.txt')

