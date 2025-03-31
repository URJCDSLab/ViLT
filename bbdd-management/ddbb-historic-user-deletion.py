# -*- coding: utf-8 -*-

from vilt.usermanager import HistoryUserManager
import logging

logging.basicConfig()
logging.root.setLevel(logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)

user_manager = HistoryUserManager()
user_manager.delete_history_users()

historic_students = user_manager.query_users_by_role('student')
for historic_student in historic_students:
    logging.info(f'Historic students: {historic_student}')

historic_teachers = user_manager.query_users_by_role('teachers')
for historic_teacher in historic_teachers:
    logging.info(f'Historic teachers: {historic_teacher}')

historic_admins = user_manager.query_users_by_role('admin')
for historic_admin in historic_admins:
    logging.info(f'Historic admins: {historic_admin}')
