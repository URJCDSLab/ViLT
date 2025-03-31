# -*- coding: utf-8 -*-

from vilt.databasemanager import DBManager
import logging

dbname = "test_documents"
logging.basicConfig()
logging.root.setLevel(logging.INFO)
logging.basicConfig(level=logging.INFO)
dbmanager = DBManager()
dbmanager.connect_database(dbname)
dbmanager.create_collection(dbname)
data = {'titulo': 'pepito', 'edad': 100}
dbmanager.insert_into_database(dbname, data)
dbmanager.query_database(dbname)
data = {'titulo': 'pepito'}
dbmanager.delete_entity(dbname, data)
dbmanager.query_database(dbname)
dbmanager.delete_collection(dbname)
dbmanager.query_database(dbname)
