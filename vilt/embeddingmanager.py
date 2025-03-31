# -*- coding: utf-8 -*-
from langchain_community.document_loaders import DirectoryLoader, JSONLoader
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from vilt.careermanager import CareersManager
from dotenv import load_dotenv
import logging
import shutil
import PyPDF2
import json
import os

def create_json_files(db_path):
    """
    Converts all PDF files in the specified directory to JSON format.

    Parameters
    ----------
    db_path : str
        Path to the directory containing PDF files.

    Returns
    -------
    bool
        True if at least one PDF was converted, False otherwise.
    """
    correct = False
    for file in os.listdir(db_path):
        if file.endswith(".pdf"):
            correct = True
            file_path = os.path.join(db_path, file)
            parse_pdf_to_json(file_path)
    return correct


def parse_pdf_to_json(file_path):
    """
    Extracts text from a PDF file and saves it as a JSON file.

    Parameters
    ----------
    file_path : str
        Path to the PDF file.
    """
    destination = file_path.replace(".pdf", ".json")
    pdf_file = open(file_path, 'rb')
    reader = PyPDF2.PdfReader(pdf_file)
    content = ""
    for page in reader.pages:
        content += page.extract_text().replace("\n", " ")
    with open(destination, 'w', encoding='utf8') as json_file:
        json.dump(content, json_file, ensure_ascii=False, indent=4)


def delete_but_pdfs(subject_dirs):
    """
    Deletes all non-PDF files and subdirectories from the given subject directories.

    Parameters
    ----------
    subject_dirs : list
        List of directories to clean.
    """
    for subject_dir in subject_dirs:
        logging.info(f'Subject directory {subject_dir}')
        for doc in os.listdir(subject_dir):
            d_file = os.path.join(subject_dir, doc)
            if os.path.isfile(d_file):
                if not doc.endswith(".pdf"):
                    os.unlink(d_file)
                    logging.info('Deleting non-PDF documents.')
            elif os.path.isdir(d_file):
                shutil.rmtree(d_file)
                logging.info('Deleting directory.')


def create_vector_db(db_path):
    """
    Generates vector embeddings from JSON files in the specified directory and stores them in a database.

    Parameters
    ----------
    db_path : str
        Path to the directory containing JSON documents.
    """
    texts = []
    try:
        loader_dir = DirectoryLoader(db_path, glob='*.json', loader_cls=JSONLoader,
                                     loader_kwargs={'jq_schema': '.', 'text_content': False})
        documents = loader_dir.load_and_split()
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1024, chunk_overlap=80, length_function=len, is_separator_regex=False
        )
        texts += text_splitter.split_documents(documents)
        embeddings = FastEmbedEmbeddings()
        Chroma.from_documents(documents=texts, embedding=embeddings, persist_directory=db_path)
        logging.info(f'The {db_path} folder has been successfully created with embeddings inside.')
    except Exception as e:
        logging.error(f'An error occurred while processing file: {e}')


def create_vectors(subject_dirs):
    """
    Processes subject directories, converting PDFs to JSON and generating embeddings.

    Parameters
    ----------
    subject_dirs : list
        List of subject directories to process.
    """
    for subject_dir in subject_dirs:
        if create_json_files(subject_dir):
            create_vector_db(subject_dir)


class EmbeddingManager:
    """
    Manages embedding generation and subject directory retrieval.
    """

    def __init__(self, process_docs):
        """
        Initializes the EmbeddingManager with the path to processed documents.

        Parameters
        ----------
        process_docs : str
            Path to the directory containing processed documents.
        """
        load_dotenv(override=True)
        os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_KEY")
        self.process_docs = process_docs

    def get_subject_dirs(self):
        """
        Retrieves subject directories from the processed documents folder.

        Returns
        -------
        list
            A list of valid subject directories.
        """
        subject_dirs = []
        listdir = os.listdir(self.process_docs)
        career_manager = CareersManager()
        careers = career_manager.query_careers()
        name_careers = [career['career'] for career in careers]
        for c_file in listdir:
            career_dir = os.path.join(self.process_docs, c_file)
            if os.path.isdir(career_dir) and c_file in name_careers:
                s_dirs = os.listdir(career_dir)
                for s_file in s_dirs:
                    subjects = career_manager.query_subjects(c_file)
                    subject_dir = os.path.join(career_dir, s_file)
                    if os.path.isdir(subject_dir) and s_file in subjects:
                        subject_dirs.append(subject_dir)
        return subject_dirs

    def generate_embeddings(self):
        """
        Generates embeddings for all subject directories, removing non-PDF files before processing.
        """
        subject_dirs = self.get_subject_dirs()
        delete_but_pdfs(subject_dirs)
        create_vectors(subject_dirs)