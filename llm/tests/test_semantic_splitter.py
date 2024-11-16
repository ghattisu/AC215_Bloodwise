import pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from semantic_splitter import combine_sentences, calculate_cosine_distances, SemanticChunker


