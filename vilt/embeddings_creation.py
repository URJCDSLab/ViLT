# -*- coding: utf-8 -*-

from vilt.embeddingmanager import EmbeddingManager
from pathlib import Path
import logging

if __name__ == "__main__":
    """
    Main script for generating embeddings from processed documents.

    This script initializes logging, sets up the project directory, and creates an instance of `EmbeddingManager` 
    to generate embeddings from the documents stored in the `processed_docs` directory.
    """
    logging.basicConfig()
    logging.root.setLevel(logging.INFO)
    logging.basicConfig(level=logging.INFO)
    project_folder = Path(__file__).parent / '..'
    path_to_docs = project_folder/'processed_docs'
    embedding_manager = EmbeddingManager(path_to_docs)
    embedding_manager.generate_embeddings()
