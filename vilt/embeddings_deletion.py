# -*- coding: utf-8 -*-

from vilt.embeddingmanager import EmbeddingManager, delete_but_pdfs
from pathlib import Path
import logging

if __name__ == "__main__":
    """
    Main script for deleting non-PDF embeddings from processed documents.
    
    This script initializes logging, sets up the project directory, and creates an instance of `EmbeddingManager` 
    to retrieve subject directories. It then deletes all files except PDFs from the specified directories.
    """
    logging.basicConfig()
    logging.root.setLevel(logging.INFO)
    logging.basicConfig(level=logging.INFO)
    project_folder = Path(__file__).parent / '..'
    path_to_docs = project_folder / 'processed_docs'
    embedding_manager = EmbeddingManager(path_to_docs)
    subject_dirs = embedding_manager.get_subject_dirs()
    delete_but_pdfs(subject_dirs)
