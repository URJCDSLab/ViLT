# -*- coding: utf-8 -*-

from vilt.careermanager import CareersManager
import logging

logging.root.setLevel(logging.INFO)
logging.basicConfig(level=logging.INFO)
careersManager = CareersManager('test_careers', 'data-external/careers')
careersManager.process_from_csv()
careers = careersManager.query_careers()
for career in careers:
    logging.info(career)
careersManager.delete_careers()
