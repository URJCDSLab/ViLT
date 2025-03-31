# -*- coding: utf-8 -*-

from vilt.careermanager import CareersManager
import logging

path_to_docs = '../data-external/careers'
logging.basicConfig()
logging.root.setLevel(logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)
careersManager = CareersManager(path_docs=path_to_docs)
careersManager.process_from_csv()
careersManager.query_careers()
