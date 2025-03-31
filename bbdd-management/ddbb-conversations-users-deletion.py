# -*- coding: utf-8 -*-

from vilt.usermanager import UserManager, to_json

user_manager = UserManager()

users = user_manager.query_users_by_role('student')
for user in users:
    for enrolled in user['subjects']:
        enrolled['conversations'] = []
    user_manager.delete_user(user['email'], False)
    user_manager.add_user(to_json(user))
    print(user)
