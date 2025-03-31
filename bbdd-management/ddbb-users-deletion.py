# -*- coding: utf-8 -*-

from vilt.usermanager import UserManager
import logging

logging.basicConfig()
logging.root.setLevel(logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)

user_manager = UserManager()
# Borrado de estudiantes
user_manager.delete_users_by_role('student')
# Borrado de profesores
user_manager.delete_users_by_role('teacher')
# Borrado de administradores
user_manager.delete_users_by_role('admin')
