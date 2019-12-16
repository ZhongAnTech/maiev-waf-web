# -*- coding: utf-8 -*-
import json
from urllib import urlencode
from urllib2 import urlopen
from functools import wraps
from urlparse import urlparse, parse_qs
from flask import redirect, request, session, jsonify, abort
from modules import Admin, Cluster, Msg


def logout(uesr):
    session.pop('user', None)
    return redirect('/Login')


def require_login(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect('/Login')
        user = session['user']
        user_data = Admin.get(nid=user['nid'], status=1)
        user['msg'] = []
        user['cluster'] = []
        clusters_data = Cluster.get_all(status=1)
        msg = Msg.get_all(status=1, msg_status=1, user=user['nid'])
        for a in clusters_data:
            if a.status == 1:
                # 按创建时间排序
                clusters = {'name': a.name, 'id': a.id, 'nid': a.nid, 'gmt_created': a.gmt_created}
                user['cluster'].append(clusters)
        user['cluster'].sort(key=lambda x: x['gmt_created'], reverse=False)
        user['msg_num'] = len(msg)
        for m in msg[0:3]:
            try:
                user['msg'].append({
                    'nid': m.nid,
                    'time': m.gmt_created,
                    'content': json.loads(m.content),
                    'genre': m.genre
                })
            except Exception as e:
                str(e)
        kwargs['user'] = user
        return f(*args, **kwargs)

    return decorated_function
