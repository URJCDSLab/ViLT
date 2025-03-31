from vilt.careermanager import CareersManager
import logging

logging.basicConfig()
logging.root.setLevel(logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)
careersManager = CareersManager()
careersManager.delete_careers()
careersManager.query_careers()
