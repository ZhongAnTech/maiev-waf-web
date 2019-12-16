# -*- coding: utf-8 -*-
from functools import wraps


def handle_user(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        user = args[1]
        print '-----------------', user
        if user.get('orgin') != 'aegis_waf':
            user['name'] = user.get('username')
        return func(*args, **kwargs)
    return wrapper