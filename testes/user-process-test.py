# -*- coding: utf-8 -*-

from vilt.usermanager import User, UserManager, to_json
import logging


logging.basicConfig()
logging.root.setLevel(logging.INFO)
logging.basicConfig(level=logging.INFO)

userManager = UserManager()
test_user = User("Test", "One", "test@yahoo.com", "1234", "student")
userManager.add_user(to_json(test_user))
test_career = 'GCID'
test_subject = 'Estructuras de Datos y Programación Orientada a Objetos'

userManager.add_subject(test_user.email, test_career, test_subject)

test_text = '''El método de los k vecinos más cercanos (en inglés: k-nearest neighbors,
   abreviado k-nn)es un método de clasificación supervisada (Aprendizaje, estimación basada 
   en un conjunto de formación y prototipos) que sirve para estimar la función de densidad de 
   las predictoras por cada clase.'''

userManager.start_conversation(test_user.email, test_career, test_subject)
logging.info(f'Conversation started.')
pos, conv_pos = userManager.find_active_conversation_from_subject(test_user.email, test_career, test_subject)
logging.info(f'Close the conversation {pos} and {conv_pos} from user {test_user.email}')
userManager.update_feedback(test_user.email, pos, conv_pos, 1, 2, 3)
logging.info(f'Updating the feedback values related to the conversation.')
userManager.end_conversation(test_user.email, test_career, test_subject, test_text)
logging.info(f'Conversation finished.')

test_users = userManager.query_users_by_email(test_user.email)
for user in test_users:
    logging.info(f'Information stored in the user: {user}.')

userManager.delete_user(test_user.email, False)
