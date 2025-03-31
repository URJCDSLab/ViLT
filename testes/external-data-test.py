# -*- coding: utf-8 -*-

from vilt.docmanager import process_students_excel
from vilt.usermanager import UserManager
import logging

logging.basicConfig()
logging.root.setLevel(logging.INFO)
logging.basicConfig(level=logging.INFO)
usermanager = UserManager()
process_students_excel('data-external/student-lists/bigdata_24-25.xls', 'GCID',
                       'Estructuras de Datos y Programación Orientada a Objetos')
