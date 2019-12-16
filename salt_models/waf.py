#!/usr/bin/env python
# encoding: utf-8

import subprocess
import os
import hashlib
import json
import base64

__virtualname__ = 'waf'


def run(data):
    result = {'success': False}
    waf_config = {"datas": [], "message": "", "code": 200, "hash": "", "version": "1.1"}
    try:

        ssl_dir = '/alidata1/conf/tengine/ssl/'
        site_dir = '/alidata1/conf/tengine/vhost/'
        waf_conf_path = '/alidata1/app/aegis_waf_iv/config.json'
        ngx_path = '/alidata1/app/tengine/sbin/nginx'

        if type(data) == str:
            data = json.loads(data)
        op = data["op"]

        ngx_conf_data = None
        ssl_key_data = None
        ssl_cert_data = None
        waf_conf_data = None

        ngx_conf_path = site_dir + 'bk.outer'
        ssl_key_path = ssl_dir + 'bk.key'
        ssl_cert_path = ssl_dir + 'bk.pem'

        if op in ['web_edit', 'web_add', 'web_stop', 'web_del']:
            if data.get('site_dir'):
                site_dir = data['site_dir']
            if data.get('waf_conf_path'):
                waf_conf_path = data['waf_conf_path']
            ngx_conf_path = site_dir + data['nid'] + '.outer'
            ngx_conf_data, ngx_conf_md5 = f_read(ngx_conf_path)

            if data['status'] == 1:
                ngx_conf_in = base64.b64decode(data["nginx_file"])

                if not ngx_conf_data:
                    f_write(ngx_conf_path, ngx_conf_in)
                elif ngx_conf_md5 != s_md5(ngx_conf_in):
                    f_write(ngx_conf_path, ngx_conf_in)

                if data.get('ssl_key_file') and data.get('ssl_cert_file'):
                    ssl_key_in = base64.b64decode(data["ssl_key_file"])
                    ssl_cert_in = base64.b64decode(data["ssl_cert_file"])
                    if data.get('ssl_dir'):
                        ssl_dir = data['ssl_dir']
                    ssl_key_path = ssl_dir + data['cert_nid'] + '.key'
                    ssl_cert_path = ssl_dir + data['cert_nid'] + '.pem'
                    ssl_key_data, ssl_key_md5 = f_read(ssl_key_path)
                    ssl_cert_data, ssl_cert_md5 = f_read(ssl_cert_path)

                    if not ssl_key_data:
                        f_write(ssl_key_path, ssl_key_in)
                    elif ssl_key_md5 != s_md5(ssl_key_in):
                        f_write(ssl_key_path, ssl_key_in)

                    if not ssl_cert_data:
                        f_write(ssl_cert_path, ssl_cert_in)
                    elif ssl_cert_md5 != s_md5(ssl_cert_in):
                        f_write(ssl_cert_path, ssl_cert_in)

                result['success'] = True

            if data['status'] == -1:
                if ngx_conf_data:
                    os.remove(ngx_conf_path)
                    result['success'] = True
                else:
                    result['info'] = "not found config file:" + str(ngx_conf_path)

        if op in ['waf_conf', 'rules', 'white_list', 'policy']:
            waf_conf_in = data["waf_file"]
            
            waf_conf_data, waf_conf_md5 = f_read(waf_conf_path)
            if waf_conf_data:
                if waf_conf_in.get('code') == 200:
                    f_write(waf_conf_path, json.dumps(waf_conf_in))
                    result['success'] = True
            '''
            if waf_conf_data:
                if waf_conf_in.get('code') == 200:
                    for w in waf_conf_in['datas']:
                        rule = []
                        for p in w['data']['filters']:
                            if p:
                                p_data = waf_conf_in['policy_data'].get(p)
                                if p_data:
                                    rule.extend(p_data)
                        w['data']['filters'] = rule
                        waf_config['datas'].append(w)
                    f_write(waf_conf_path, json.dumps(waf_config))
                    result['success'] = True
            '''
        if op == 'reload':
            if data.get('reload_time'):
                data['reload_time'] = None
            result['success'] = True

        if result['success']:
            if data.get('ngx_path'):
                ngx_path = data['ngx_path']
            (ngx_test_status, ngx_test) = subprocess.Popen(
                [ngx_path, "-t"],
                shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            ).communicate()
            if (ngx_test.find("test is successful") > -1) and (ngx_test.find("waf cfg is invalid") == -1):
                if data.get('reload_time'):
                    if data['reload_time'] > 0:
                        subprocess.Popen("sleep {0};{1} -s reload".format(str(data['reload_time']), ngx_path), shell=True)
                        ngx_reload = "will reload after {0}".format(str(data['reload_time']))
                    else:
                        ngx_reload = "will reload after {0}".format(str(-data['reload_time']))
                else:
                    (reload_status, ngx_reload) = subprocess.Popen(
                        [ngx_path, "-s", "reload"],
                        shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
                result['info'] = ngx_reload
            else:
                result['success'] = False
                result['info'] = ngx_test

        if not result['success']:
            if op in ['web_edit', 'web_add', 'web_stop', 'web_del']:
                if ngx_conf_data:
                    f_write(ngx_conf_path, ngx_conf_data)
                if ssl_key_data:
                    f_write(ssl_key_path, ssl_key_data)
                if ssl_cert_data:
                    f_write(ssl_cert_path, ssl_cert_data)

            if op in ['waf_conf', 'rules', 'white_list', 'policy']:
                if waf_conf_data:
                    f_write(waf_conf_path, waf_conf_data)

    except Exception as e:
        result['success'] = False
        result['info'] = str(e)

    return result


def s_md5(data):
    md5obj = hashlib.md5()
    md5obj.update(data)
    return md5obj.hexdigest()


def f_read(path):
    if os.path.exists(path):
        with open(path, 'r') as f1:
            data = f1.read()
            if data:
                file_md5 = s_md5(data)
            else:
                file_md5 = None
        return data, file_md5
    else:
        return None, None


def f_write(path, data):
    f_dir = os.path.dirname(path)
    if not os.path.exists(f_dir):
        os.makedirs(f_dir)
    with open(path, 'w') as f2:
        f2.write(data)
