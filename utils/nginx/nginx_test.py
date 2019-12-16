#!/usr/bin/env python
# encoding: utf-8
import re
import subprocess
import os
import hashlib
from modules import Cert
from utils.log import log_setting
from utils.nginx.redis_lock import deco, RedisLock

logger = log_setting(app_name="aegis_waf_4.0")


# def test_ngx(web):
#     result = {'success': True, 'info': ''}
#     return result


@deco(RedisLock("112255"))
def test_ngx(web):
    result = {'success': False, 'info': ''}
    try:
        ssl_dir = '/alidata1/app/aegis-waf3/utils/nginx/conf/ssl/'
        site_dir = '/alidata1/app/aegis-waf3/utils/nginx/conf/vhost/'
        # site_dir = '/usr/local/nginx/conf.d/'
        # waf_conf_path = '/alidata1/app/aegis_waf_iii/config.json'
        ngx_path = '/alidata1/app/tengine/sbin/nginx'
        # ngx_path = '/alidata1/app/tengine/nginx/sbin/nginx'

        # 本地同步所有证书
        certs = Cert.get_all(status=1)
        for cert_ in certs:
            ssl_key_in = cert_.keys
            ssl_cert_in = cert_.cert
            if ssl_key_in and ssl_cert_in:
                ssl_key_path = ssl_dir + cert_.nid + '.key'
                ssl_cert_path = ssl_dir + cert_.nid + '.pem'
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

        # 写入本地域名配置文件
        # ngx_conf_in = web_dict['conf_file']
        ngx_conf_in = web.conf_file
        #ngx_conf_in = re.sub(r'listen 443 ssl http2 spdy;',
        #                     'listen 443 default_server ssl http2;',
        #                     ngx_conf_in)
        # ngx_conf_path = site_dir + web_dict['nid'] + '.outer'
        ngx_conf_path = site_dir + web.nid + '.outer'
        ngx_conf_data, ngx_conf_md5 = f_read(ngx_conf_path)
        if not ngx_conf_data:
            f_write(ngx_conf_path, ngx_conf_in)
        elif ngx_conf_md5 != s_md5(ngx_conf_in):
            f_write(ngx_conf_path, ngx_conf_in)

        log_path = "/alidata1/logs/"
        error_log_path = '/alidata1/logs/'
        mk_dir(log_path)
        mk_dir(error_log_path)

        nginx_conf = "/alidata1/app/aegis-waf3/utils/nginx/conf/nginx.conf"
        # cmd = [ngx_path, "-t"]
        cmd = [ngx_path, "-t", "-c", nginx_conf]
        (ngx_test_status, ngx_test) = subprocess.Popen(
            cmd, shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        ).communicate()

        # 移除配置文件
        f_remove(ngx_conf_path)
        # time.sleep(0.5)

        info = 'called.--', str(os.getpid()), str(os.getppid())
        logger.info(info)
        logger.info('user-id: ', web.user)
        print info
        print 'user-id: ', web.user, ngx_test

        if (ngx_test.find("test is successful") > -1) and \
                (ngx_test.find("waf cfg is invalid") == -1):
            result['success'] = True
        else:
            raise Exception('ngx_test: ', ngx_test)
    except Exception as e:
        result['info'] = 'Nginx test fail: ', str(e)
        logger.info(result['info'])
    return result


def mk_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)


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


def f_remove(path):
    if os.path.exists(path):
        return os.remove(path)
