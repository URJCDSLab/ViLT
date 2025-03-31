# -*- coding: utf-8 -*-

from vilt.usermanager import UserManager, to_json

user_manager = UserManager()

users = user_manager.query_users_by_email('vangaf@yahoo.com')
if len(users) > 0:
    user = users[0]
    for enrolled in user['subjects']:
        enrolled['info_values']['conversations'] = []
    user_manager.delete_user(user['email'], False)
    user_manager.add_user(to_json(user))
    print(user)
