# -*- coding: utf-8 -*-

from vilt.embeddingmanager import EmbeddingManager
import logging

logging.basicConfig()
logging.root.setLevel(logging.INFO)
logging.basicConfig(level=logging.INFO)
path_to_docs = "processed_docs"
embedding_manager = EmbeddingManager(path_to_docs)
embedding_manager.generate_embeddings()
