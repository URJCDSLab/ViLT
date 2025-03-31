# -*- coding: utf-8 -*-

from vilt.databasemanager import DBManager
from pathlib import Path
from os.path import isfile, join
from os import listdir
import pandas as pd
import unidecode
import logging


class CareersManager:
    """
    Manages career and subject data stored in a database, allowing insertion, deletion, and querying.
    """

    def __init__(self, db_careers=None, path_docs=None):
        """
        Initializes the CareersManager with a database connection and document path.

        Parameters
        ----------
        db_careers : str, optional
            The name of the database collection for careers (default is "careers").
        path_docs : str, optional
            Path to the directory containing career CSV files.
        """
        if path_docs is None:
            self.path_to_docs = Path(__file__).parent / "data-external/careers"
        else:
            self.path_to_docs = Path(__file__).parent / path_docs

        self.db_careers = db_careers if db_careers else "careers"
        self.dbmanager = DBManager()

    def store_careers(self, list_docs):
        """
        Reads career data from CSV files and stores it in the database.

        Parameters
        ----------
        list_docs : list
            List of CSV filenames containing career and subject data.
        """
        for doc in list_docs:
            df = pd.read_csv(self.path_to_docs / doc, sep=';', encoding='latin-1')
            df = df.iloc[:, 1].dropna()
            subject_list = df[-df.duplicated(keep=False)].tolist()
            clean_subject_list = []
            for subject in subject_list:
                clean_subject = unidecode.unidecode(subject.lower())
                if ('optativa' not in clean_subject and 'practicas externas' not in clean_subject and
                        'trabajo fin' not in clean_subject and 'reconocimiento academico' not in clean_subject):
                    subject = subject.strip()
                    logging.info(f'Processing subject: {subject}')
                    clean_subject_list.append(subject)

            init = doc.find('(')
            end = doc.find(')')
            career = doc[init + 1:end]
            json_data = {'career': career, 'subjects': clean_subject_list}

            self.dbmanager.connect_database(self.db_careers)
            self.dbmanager.insert_into_database(self.db_careers, json_data)
            self.dbmanager.disconnect_database()

    def process_from_csv(self):
        """
        Processes all CSV files in the document path and stores career data in the database.
        """
        careers = [f for f in listdir(self.path_to_docs) if isfile(join(self.path_to_docs, f)) and f.endswith('.csv')]
        logging.info(f"Processed {len(careers)} files")
        if not careers:
            logging.warning("No CSV files found")
        else:
            logging.info("Processing files")
        self.store_careers(careers)

    def delete_careers(self):
        """
        Deletes all career records from the database.
        """
        self.dbmanager.connect_database(self.db_careers)
        self.dbmanager.delete_collection(self.db_careers)
        self.dbmanager.disconnect_database()

    def query_careers(self):
        """
        Retrieves all career records from the database.

        Returns
        -------
        list
            A list of career documents from the database.
        """
        self.dbmanager.connect_database(self.db_careers)
        careers = self.dbmanager.query_database(self.db_careers)
        self.dbmanager.disconnect_database()
        return careers

    def query_subjects(self, career):
        """
        Retrieves all subjects associated with a given career.

        Parameters
        ----------
        career : str
            The name of the career to search for.

        Returns
        -------
        list
            A list of subjects related to the specified career.
        """
        subjects = []
        if career:
            condition = {'career': career}
            self.dbmanager.connect_database(self.db_careers)
            careers = self.dbmanager.query_database(self.db_careers, condition)
            if careers:
                subjects = careers[0]['subjects']
            self.dbmanager.disconnect_database()
        return subjects
