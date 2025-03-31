# -*- coding: utf-8 -*-

from pymongo import MongoClient
from dotenv import load_dotenv
import logging
import os


class DBManager:
    """
    Manages database operations such as connecting, inserting, deleting, and querying data.
    """

    def __init__(self):
        """
        Initializes the database manager by loading environment variables for database credentials.
        """
        load_dotenv(override=True)
        self.mongo_host = os.getenv('MONGO_HOST')
        self.mongo_port = os.getenv('MONGO_PORT')
        self.mongo_user = os.getenv('MONGO_USER')
        self.mongo_pass = os.getenv('MONGO_PASS')
        self.mongo_db = None
        self.db = None
        self.client = None

    def connect_database(self, mongo_db):
        """
        Connects to the specified MongoDB database.

        Parameters
        ----------
        mongo_db : str
            The name of the database to connect to.
        """
        self.mongo_db = mongo_db
        connection_string = (f'mongodb://{self.mongo_user}:'
                             f'{self.mongo_pass}@{self.mongo_host}:{self.mongo_port}/'
                             f'{self.mongo_db}?authSource=admin&retryWrites=true&w=majority')
        self.client = MongoClient(connection_string)
        self.db = self.client[self.mongo_db]

    def disconnect_database(self):
        """
        Closes the database connection.
        """
        self.client.close()

    def collection_exists(self, collection_name):
        """
        Checks if a specific collection exists in the database.

        Parameters
        ----------
        collection_name : str
            The name of the collection to check.

        Returns
        -------
        bool
            True if the collection exists, False otherwise.
        """
        return collection_name in self.db.list_collection_names()

    def create_collection(self, collection_name):
        """
        Creates a new collection in the database if it does not already exist.

        Parameters
        ----------
        collection_name : str
            The name of the collection to create.

        Returns
        -------
        created: bool
            True if the collection was created, False if it already exists.
        """
        created = False
        if not self.collection_exists(collection_name):
            self.db.create_collection(collection_name)
            created = True
        else:
            logging.info(f"Collection '{collection_name}' already exists.")
        return created

    def delete_collection(self, collection_name):
        """
        Deletes a collection from the database if it exists.

        Parameters
        ----------
        collection_name : str
            The name of the collection to delete.
        """
        if self.collection_exists(collection_name):
            self.db.drop_collection(collection_name)
            logging.info(f"Deleted collection '{collection_name}'.")
        else:
            logging.info("Collection did not exist.")

    def insert_into_database(self, collection_name, info):
        """
        Inserts a document into the specified collection.

        Parameters
        ----------
        collection_name : str
            The name of the collection where the document will be inserted.
        info : dict
            The document to insert.
        """
        if not self.collection_exists(collection_name):
            logging.info(f"Creating a new collection '{collection_name}' in the database.")
            self.db.create_collection(collection_name)

        collection = self.db[collection_name]
        if not collection.find_one(info):
            collection.insert_one(info)
            logging.info("Document inserted successfully.")
        else:
            logging.info("Document already exists, skipping insertion.")

    def delete_entity(self, collection_name, condition, total=False):
        """
        Deletes documents from a collection based on a condition.

        Parameters
        ----------
        collection_name : str
            The name of the collection from which documents will be deleted.
        condition : dict
            The condition to match documents for deletion.
        total : bool, optional
            If True, deletes all matching documents; if False, deletes only the first match (default is False).
        """
        if not self.collection_exists(collection_name):
            logging.info(f"Collection '{collection_name}' does not exist in database.")
            return

        collection = self.db[collection_name]
        result = collection.delete_many(condition) if total else collection.delete_one(condition)
        logging.info(f"{result.deleted_count} documents deleted.")

    def query_database(self, collection_name, condition=None):
        """
        Queries documents from a specified collection.

        Parameters
        ----------
        collection_name : str
            The name of the collection to query.
        condition : dict, optional
            The query condition to filter documents (default is None, which retrieves all documents).

        Returns
        -------
        list
            A list of documents that match the query condition.
        """
        if not self.collection_exists(collection_name):
            logging.info(f"Collection '{collection_name}' does not exist in database.")
            return []

        collection = self.db[collection_name]
        return list(collection.find(condition or {}))

    def update_collection(self, collection_name, query, updating, many=True):
        """
        Updates documents in a specified collection based on a query condition.

        Parameters
        ----------
        collection_name : str
            The name of the collection where documents will be updated.
        query : dict
            The query condition to match documents.
        updating : dict
            The update operation to apply.
        many : bool, optional
            If True, updates all matching documents; if False, updates only the first match (default is True).

        Returns
        -------
        bool
            True if the update was performed successfully, False otherwise.
        """
        if not self.collection_exists(collection_name):
            logging.info(f"Collection '{collection_name}' does not exist in database.")
            return False

        collection = self.db[collection_name]
        if query and updating:
            if many:
                collection.update_many(query, updating)
            else:
                collection.update_one(query, updating)
            return True
        return False
