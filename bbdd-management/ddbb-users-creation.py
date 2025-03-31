# -*- coding: utf-8 -*-

from vilt.usermanager import UserManager, to_json, User
import logging

logging.basicConfig()
logging.root.setLevel(logging.INFO)
logging.basicConfig(level=logging.INFO)


# Creación de administradores
admin1 = User('Fiutten', 'Admin', 'albertofer84@gmail.com', '1234', 'admin')
admin2 = User('Admin', 'Admin', 'admin@admin.com', 'admin')

# Creación de profesores
teacher1 = User('Alberto', 'Fernández Isabel', 'alberto.fernandez.isabel@urjc.es', '1234',
                'teacher')
teacher2 = User('Isaac', 'Martín de Diego', 'isaac.martin@urjc.es', '1234', 'teacher')
teacher3 = User('Carmen', 'Lancho Martín', 'carmen.lancho@urjc.es', '1234', 'teacher')

user_manager = UserManager()
user_manager.add_user(to_json(admin1))
user_manager.add_user(to_json(admin2))
user_manager.add_user(to_json(teacher1))
user_manager.add_user(to_json(teacher2))
user_manager.add_user(to_json(teacher3))

# Asignación de asignaturas a profesores
user_manager.add_subject(teacher1.email, 'GII', 'Arquitecturas Avanzadas de Computadores')
user_manager.add_subject(teacher2.email, 'GCID', 'Inferencia Estadística')
user_manager.add_subject(teacher3.email, 'GCID', 'Inferencia Estadística')
user_manager.add_subject(teacher2.email, 'GCID', 'Aprendizaje Automático I')
user_manager.add_subject(teacher3.email, 'GCID', 'Aprendizaje Automático I')
user_manager.add_subject(teacher2.email, 'GMAT', 'Minería de Datos')
user_manager.add_subject(teacher3.email, 'GMAT', 'Minería de Datos')
