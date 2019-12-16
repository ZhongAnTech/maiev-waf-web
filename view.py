# -*- coding: utf-8 -*-
import time
import urllib2
import os

from models.audit import Recored
from utils import sso
from utils.nginx.nginx_test import test_ngx
from utils.sync_cert import CertHandler
from utils.tools import get_ip, geoip, parser_ssl, get_address
from app import app
from modules import *
from datetime import timedelta
from utils.templet import Assemble
from flask import render_template, request, jsonify, session, redirect, url_for
from elasticsearch import Elasticsearch
from utils.salt import asyn_salt, SaltClient
from urllib import urlencode, unquote
logger = log_setting(app_name="aegis_waf_4.0")


@app.route('/waf/api/WebConfig', methods=['GET', 'POST'])
@sso.require_login
def web_add(user):
    result = {'success': False}
    try:
        if request.method == 'GET':
            cluster = request.values.get('cluster', default=user['cluster'][0]['nid'])
            page = request.values.get('page', type=int, default=1)
            size = request.values.get('size', type=int, default=10)
            start = request.values.get('start', type=int, default=0)
            draw = request.values.get('draw', type=int, default=1)
            search = request.values.get('search')
            data = []
            certs = []
            policy = []
            clu = Cluster.get(status=1, nid=cluster)
            if clu:
                if start:
                    page = start/size + 1
                web = Web.get_page(page, size, search, clu.nid, user['role'], user['nid'])
                if web:
                    for d in web.items:
                        i = 1
                        info = {'backup': False}
                        server_data = []
                        backup = BackUp.get_by_web(web=d.nid)
                        servers = Server.get_all(status=1, web=d.nid)
                        for s in servers:
                            if backup and (i == 1):
                                info['backup'] = True
                                info['proxy_service'] = get_address(backup.file_data)
                                i += 1
                            elif i == 1:
                                info['proxy_service'] = s.proxy_service.split(',')
                            info['location_url'] = s.location_url
                            server_data.append(info)
                        name_host = get_ip(d.name)
                        cname = d.cname if d.cname else clu.cname
                        temp_data = {
                            'nid': d.nid,
                            'cluster': d.cluster,
                            'name': d.name,
                            'name_host': name_host,
                            'http': d.http,
                            'https': d.https,
                            'https_trans': d.https_trans,
                            'status': d.web_status,
                            'defend_web': d.defend_web,
                            'defend_cc': d.defend_cc,
                            'defend_blacklist': d.defend_blacklist,
                            'cname': cname,
                            'server': server_data
                        }
                        if user['role'] == 1 and name_host != cname:
                            temp_data['name_host'] = ''
                        data.append(temp_data)

                cert_data = Cert.get_all(status=1)
                for c in cert_data:
                    certs.append({'nid': c.nid, 'name': c.name})
                for pp in Policy.get_all_clu(nid=clu.nid):
                    policy.append({"nid": pp.uuid, "name": pp.name, "kind": pp.kind})
                result['data'] = {
                    'webs': data,
                    'policy': policy,
                    'certs': certs,
                    'pages': {'total': web.total if web else 0, 'page': page, 'size': size, 'draw': draw},
                    'clusters': {'name': clu.name, 'nid': clu.nid}
                }
                # 记录
                Recored.record_web_manage(user, clu)
                result['success'] = True
            else:
                result['info'] = '集群环境不存在'
        if request.method == 'POST':
            request_data = request.get_json()
            cluster = request_data.get('cluster', user['cluster'][0]['nid'])
            https_port = 443
            http_port = 80
            cert_nid = None
            clu = Cluster.get(nid=cluster, status=1)
            if clu:
                # 删除测试配置文件
                # CertHandler.delete_test_conf(clu.nid, user)

                if request_data.get('https_port'):
                    https_port = ','.join(request_data['https_port'])
                if request_data.get('http_port'):
                    http_port = ','.join(request_data['http_port'])
                if int(request_data.get('https', 0)) == 1:
                    cert_nid = request_data.get('cert_nid')
                web = Web(
                    cluster_id=clu.id,
                    cluster=clu.nid,
                    conf_type=request_data['conf_type'],
                    https_trans=int(request_data.get('https_trans', 0)),
                    https_port=https_port,
                    http_port=http_port,
                    https=int(request_data.get('https', 0)),
                    http=int(request_data.get('http', 0)),
                    name=request_data['name'],
                    user=user['nid'],
                    mark=request_data.get('mark'),
                    conf_file=request_data.get('conf_file'),
                    cert=cert_nid
                ).create()
                if web:
                    ser = request_data['server']
                    if ser and (type(ser) == list):
                        for s in ser:
                            Server(
                                cluster=clu.nid,
                                web=web.nid,
                                web_id=web.id,
                                site_name=web.name,
                                user=user['nid'],
                                seq=int(s.get('order', 0)),
                                proxy_service=','.join(s['proxy_service']),
                                location_pattern=s.get('location_pattern', '/'),
                                location_url=s.get('location_url'),
                                rewrite_flag=s.get('rewrite_flag', 'nowrite'),
                                rewrite_matches=s.get('rewrite_matches'),
                                rewrite_pattern=s.get('rewrite_pattern'),
                                websocket=int(s.get('websocket', 0)),
                                slb_alg=int(s.get('slb_alg', 0)),
                                http_back=int(s.get('http_back', 1))
                            ).create()
                    conf_text = Assemble(web.nid).ngx_file()
                    web = Web.get(cluster=clu.nid, nid=web.nid)
                    if conf_text['success']:
                        # 测试配置文件
                        # test_result = test_ngx(web)
                        test_result = {'success': True}

                        # test_result = zmq_send(web)
                        if test_result['success']:
                            # 测试成功下发
                            asyn_salt(clu_nid=clu.nid, op='web_add',
                                      nid=web.nid, user=user['nid'])
                            result['data'] = {'nid': web.nid}
                            result['success'] = True
                        else:
                            # 测试不成功, 删除入库信息
                            servers = Server.get_all(web=web.nid)
                            for s_ in servers:
                                s_.delete()
                            web.delete()
                            result['info'] = test_result['info']
                        # 记录
                        Recored.record_web_config(user, clu, web, test_result['success'])
                    else:
                        result['info'] = conf_text.get('info')
                else:
                    result['info'] = '站点域名记录已经存在'
            else:
                result['info'] = '集群环境不存在'
    except Exception as e:
        logger.error(str(e))
        result['info'] = str(e)
    return jsonify(result)


@app.route('/waf/api/clusters', methods=['GET'])
def web_clusters():
    result = {'success': False, 'data': []}
    try:
        clusters = Cluster.get_all(status=1)
        for clu_temp in clusters:
            temp_clu = {
                'id': clu_temp.id,
                'nid': clu_temp.nid,
                'name': clu_temp.name
            }
            result['data'].append(temp_clu)
        result['success'] = True
    except Exception as e:
        logger.error(str(e))
        result['info'] = str(e)
    return jsonify(result)


@app.route('/waf/api/WebName', methods=['POST'])
def web_name():
    result = {'success': False, 'info': []}
    try:
        request_data = request.get_json()
        web_name = request_data.get('web_name', '')
        cluster_nid = request_data.get('cluster_nid', '')
        if not (web_name and cluster_nid):
            raise Exception('loss web name or cluster nid.')
        if Web.get(status=1, name=web_name, cluster=cluster_nid):
            raise Exception('Web name already exists on the cluster: ',
                            web_name)
        result['success'] = True
    except Exception as e:
        logger.error(str(e))
        result['info'] = e
    return jsonify(result)


@app.route('/waf/api/Certs', methods=['GET'])
def get_certs():
    result = {'success': False, "data": []}
    try:
        ct = Cert.get_all(status=1)
        print ct
        for c in ct:
            result['data'].append({
                'nid': c.nid,
                'name': c.name,
            })
        result['success'] = True
    except Exception as e:
        logger.error(str(e))
        result['info'] = str(e)
    return jsonify(result)


@app.route('/waf/api/WebConfigList', methods=['POST'])
def web_config_list():
    result = {'success': False}
    try:
        request_data = request.get_json()
        cluster = request_data.get('cluster', '')
        https_port = 443
        http_port = 80
        cert_nid = None
        clu = Cluster.get(nid=cluster, status=1)
        if clu:
            https = request_data.get('https')
            http = request_data.get('http')
            https_trans = request_data.get('https_trans')
            websocket = request_data.get('websocket', 0)
            if not (https or http):
                raise Exception('Both https and http loss: ',
                                request_data['name'])
            if type(https) != int or type(http) != int or \
                    type(https_trans) != int or type(websocket) != int:
                raise Exception('Parameter type error.')
            if request_data.get('https_port'):
                https_port = ','.join(request_data['https_port'])
            if request_data.get('http_port'):
                http_port = ','.join(request_data['http_port'])
            if https == 1:
                cert_nid = request_data.get('cert_nid')
                if not (cert_nid and Cert.get(nid=cert_nid)):
                    raise Exception('Cert loss: ', request_data['name'])
            web = Web(
                cluster_id=clu.id,
                cluster=clu.nid,
                conf_type='',
                https_trans=https_trans,
                https_port=https_port,
                http_port=http_port,
                https=https,
                http=http,
                name=request_data['name'],
                # user=user['nid'],
                mark=request_data.get('mark'),
                # conf_file=request_data.get('conf_file'),
                cert=cert_nid
            ).create()
            # 默认web停用
            web = web.update(web_status=-1)
            if web:
                ser = request_data['server']
                if not ser:
                    web.delete()
                    raise Exception('Server loss: ', ser)
                if type(ser) != list:
                    web.delete()
                    raise Exception('Server type error: ', ser)
                for s in ser:
                    if type(s) != list:
                        web.delete()
                        raise Exception('Server element type error: ', ser)
                    Server(
                        cluster=clu.nid,
                        web=web.nid,
                        web_id=web.id,
                        site_name=web.name,
                        # user=user['nid'],
                        seq=0,
                        proxy_service=','.join(s),
                        location_pattern='/',
                        location_url='',
                        rewrite_flag='nowrite',
                        rewrite_matches='',
                        rewrite_pattern='',
                        websocket=websocket,
                        slb_alg=0,
                        http_back=1
                    ).create()
                result['success'] = True
                result['info'] = 'File configuration success'
            else:
                result['info'] = '站点域名记录已经存在'
        else:
            result['info'] = '集群环境不存在'
    except Exception as e:
        logger.error(str(e))
        result['info'] = str(e)
    return jsonify(result)


@app.route('/waf/api/webdatas', methods=['GET'])
def web_datas():
    result = {'success': False, 'data': {}}
    try:
        page = request.args.get('page', 1)
        size = request.args.get('size', 10)

        cluster_nid = request.args
        cluster_nid = cluster_nid['nid']
        if not cluster_nid:
            result['info'] = 'nid lose'
            return jsonify(result)

        web_paginate = Web.query.filter_by(cluster=cluster_nid).paginate(int(page), int(size), False)
        total_pages = web_paginate.pages
        current_page = web_paginate.page
        items = web_paginate.items

        web_data = []
        for web in items:
            temp_web = web.to_dict()
            for server in Server.get_all(web=web.nid):
                temp_web['servers'] = []
                temp_web['servers'].append(server.to_dict())
            web_data.append(temp_web)

        result['data'] = {
            'total_pages': total_pages,
            'current_page': current_page,
            'web_datas': web_data,
        }
        result['success'] = True
    except Exception as e:
        logger.error(str(e))
        result['info'] = str(e)
    return jsonify(result)


@app.route('/waf/api/WebConfig/<nid>', methods=['GET', 'POST', 'DELETE', 'PUT'])
@sso.require_login
def web_handle(user, nid):
    result = {'success': False}
    try:
        web = Web.get(nid=nid, status=1)
        if web:
            if request.method == 'POST':
                request_data = request.get_json()
                clu = Cluster.get(nid=web.cluster)
                if request_data.get('https') == '1':
                    cert_nid = request_data.get('cert_nid')
                    if not cert_nid:
                        raise Exception('请选择证书')
                    else:
                        cert = Cert.get(nid=cert_nid, status=1)
                    if cert:
                        cert_nid = cert.nid
                    else:
                        request_data['http'] = 1
                        request_data['https_trans'] = 0
                        request_data['https'] = 0
                        result['info'] = '证书错误'
                        cert_nid = None
                    request_data['cert_nid'] = cert_nid
                web = web.update(
                    https=int(request_data.get('https', 0)),
                    http=int(request_data.get('http', 1)),
                    conf_type=request_data['conf_type'],
                    https_trans=int(request_data.get('https_trans', 0)),
                    conf_file=request_data.get('conf_file'),
                    mark=request_data.get('mark'),
                    cert=request_data.get('cert_nid')
                    # web_status=int(request_data.get('web_status'), 1)
                )
                ser = request_data.get('server')
                if ser and (type(ser) == list):
                    for s in ser:
                        sf = Server.get(nid=s['nid'])
                        if not sf:
                            Server(
                                cluster=clu.nid,
                                web=web.nid,
                                web_id=web.id,
                                site_name=web.name,
                                user=user['nid'],
                                seq=int(s.get('order', 0)),
                                proxy_service=','.join(s['proxy_service']),
                                location_pattern=s.get('location_pattern', '/'),
                                location_url=s.get('location_url'),
                                rewrite_flag=s.get('rewrite_flag', 'nowrite'),
                                rewrite_matches=s.get('rewrite_matches'),
                                rewrite_pattern=s.get('rewrite_pattern'),
                                websocket=int(s.get('websocket', 0)),
                                slb_alg=int(s.get('slb_alg', 0)),
                                http_back=int(s.get('http_back', 1)),
                                status=int(s.get('status', 1))
                            ).create()
                        else:
                            sf.update(
                                seq=int(s.get('order', 0)),
                                proxy_service=','.join(s['proxy_service']),
                                location_pattern=s.get('location_pattern', '/'),
                                location_url=s.get('location_url'),
                                rewrite_flag=s.get('rewrite_flag', 'nowrite'),
                                rewrite_matches=s.get('rewrite_matches'),
                                rewrite_pattern=s.get('rewrite_pattern'),
                                websocket=int(s.get('websocket', 0)),
                                slb_alg=int(s.get('slb_alg', 0)),
                                http_back=int(s.get('http_back', 1)),
                                status=int(s.get('status', 1))
                            )
                assemble = Assemble(web.nid)
                # if not request_data.get('conf_file', ''):
                #     raise Exception('Get config file fail.')
                conf_text = assemble.update_file_by_ngx(nid, request_data.get('conf_file', ''))

                if conf_text['success']:
                    if conf_text['text']:
                        # 测试配置文件
                        web_ = Web.get(nid=web.nid)
                        test_result = test_ngx(web_)
                        if test_result['success']:
                            # 测试成功下发
                            asyn_salt(clu_nid=clu.nid, op='web_edit',
                                      nid=web.nid, user=user['nid'])
                            result['data'] = {'nid': web.nid}
                            result['success'] = True
                        else:
                            # 测试不成功
                            result['info'] = test_result['info']
                    else:
                        # 不做操作
                        result['success'] = True
                else:
                    result['info'] = conf_text.get('info')
            if request.method == 'GET':
                result['data'] = {
                    'nid': web.nid,
                    'name': web.name,
                    'cname': web.cname,
                    'https': web.https,
                    'http': web.http,
                    'cluster': web.cluster,
                    'https_trans': web.https_trans,
                    'defend_web_policy': web.defend_web_policy,
                    'defend_cc_count': web.defend_cc_policy1,
                    'defend_cc_time': web.defend_cc_policy2,
                    'defend_custom_policy': web.defend_custom_policy,
                    'defend_custom': web.defend_custom,
                    'defend_web': web.defend_web,
                    'defend_cc': web.defend_cc,
                    'defend_blacklist': web.defend_blacklist,
                    'http_port': web.http_port.split(','),
                    'https_port': web.https_port.split(','),
                    'status': web.web_status,
                    'conf_type': web.conf_type,
                    'conf_file': web.conf_file,
                    'mark': web.mark,
                    'cert': web.cert,
                }
                servers = []
                for server in Server.get_all(web=web.nid, status=1):
                    servers.append({
                        'nid': server.nid,
                        'name': server.name,
                        'cluster': server.cluster,
                        'order': server.seq,
                        'location_pattern': server.location_pattern,
                        'location_url': server.location_url,
                        'proxy_service': server.proxy_service.split(','),
                        'rewrite_flag': server.rewrite_flag,
                        'rewrite_matches': server.rewrite_matches,
                        'rewrite_pattern': server.rewrite_pattern,
                        'websocket': server.websocket,
                        'slb_alg': server.slb_alg,
                        'http_back': server.http_back,
                        'status': server.status,
                    })
                result['data']['server'] = servers
                result['success'] = True
            if request.method == 'DELETE':
                web = web.update(status=-1)
                # asyn_salt(clu_nid=web.cluster, op='web_del', nid=web.nid, user=user['nid'])
                result['data'] = {'nid': web.nid}
                result['success'] = True
            if request.method == 'PUT':
                request_data = request.get_json()
                web_status = request_data.get('web_status')
                if web_status:
                    kwargs = {'web_status': web_status}
                    if not web.user:
                        # 添加web和server的user nid
                        kwargs['user'] = user.get('nid')
                        servers_ = Server.get_all(web=web.nid)
                        for server_ in servers_:
                            if not server_.user:
                                server_.update(user=user.get('nid'))
                        web = web.update(**kwargs)
                        conf_text = Assemble(web.nid).ngx_file()
                        if not conf_text['success']:
                            raise Exception(conf_text.get('info'))
                    else:
                        web = web.update(**kwargs)

                    if web_status == '1':
                        # 下发前测试配置文件
                        test_result = test_ngx(web)
                        if test_result['success']:
                            # 测试成功下发
                            asyn_salt(clu_nid=web.cluster, op='web_stop',
                                      nid=web.nid, user=user['nid'])
                            result['data'] = {'nid': web.nid}
                            result['success'] = True
                        else:
                            # 测试不成功, web_status回退
                            web_status = str(-int(web_status))
                            web.update(web_status=web_status)
                            result['info'] = test_result['info']
                    else:
                        # 删除下发的nginx文件
                        asyn_salt(clu_nid=web.cluster, op='web_stop',
                                  nid=web.nid, user=user['nid'])
                        result['data'] = {'nid': web.nid}
                        result['success'] = True
                else:
                    web = web.update(
                        defend_web=int(request_data.get('defend_web', 0)),
                        defend_cc=int(request_data.get('defend_cc', 0)),
                        defend_blacklist=int(request_data.get('defend_blacklist', 0)),
                        defend_custom=int(request_data.get('defend_custom', 0)),
                        defend_web_policy=request_data.get('defend_web_policy'),
                        defend_cc_policy1=int(request_data.get('defend_cc_count', 1000000)),
                        defend_cc_policy2=int(request_data.get('defend_cc_time', 5)),
                        defend_custom_policy=request_data.get('defend_custom_policy')
                    )
                    # 下发前测试配置文件
                    if web:
                        test_result = test_ngx(web)
                        # test_result = {'success': True}
                        if test_result['success']:
                            asyn_salt(clu_nid=web.cluster, op='waf_conf', nid=web.nid, user=user['nid'])
                            result['data'] = {'nid': web.nid}
                            result['success'] = True
                        else:
                            # 测试不成功, web_status回退
                            web_status = str(-int(web_status))
                            web.update(web_status=web_status)
                            result['info'] = test_result['info']
        else:
            result['info'] = '网站不存在'
        # 记录
        clu = Cluster.get(nid=web.cluster)
        Recored.record_web_config(user, clu, web, result['success'],
                                  method=request.method)
    except Exception as e:
        logger.error(str(e))
        result['info'] = str(e)
    return jsonify(result)


@app.route('/waf/api/Statis', methods=['GET', 'POST'])
@sso.require_login
def statis_query(user):
    result = {'success': False}
    try:
        now = datetime.now()
        time_format = "%Y-%m-%d %H:%M:%S"
        cluster = request.values.get('cluster')
        kind = request.values.get('kind', default='access')
        nid = request.values.get('nid')
        start_time = request.values.get('start_time', default=(now-timedelta(days=1)).strftime(time_format))
        end_time = request.values.get('end_time', default=now.strftime(time_format))
        page = request.values.get('page', type=int, default=1)
        size = request.values.get('size', type=int, default=10)

        clu_sw = False
        if not cluster:
            cluster = user['cluster'][0]['nid']
        else:
            clu_sw = True
        clu = Cluster.get(status=1, nid=cluster)

        if clu:
            data = {}
            webs = []
            for w in Web.get_all(user=user['nid'], status=1):
                webs.append({
                    'nid': w.nid,
                    'name': w.name
                })
            if nid:
                web = Web.get(nid=nid, status=1)
                if web:
                    field = 'appName'
                    web_nid = web.name
                else:
                    field = 'web_nid'
                    web_nid = nid
            else:
                field = 'user_nid'
                web_nid = user['nid']
            index_list = []
            date_str_index = 'ngx_access_log'
            do_charts = ["top_ip", "views", "top_ua", "top_status", "top_web"]
            if kind == 'attack':
                do_charts = ["top_ip", "views", "top_attack_type"]
                date_str_index = 'waf_log'
            start_time_d = datetime.strptime(start_time, time_format)
            end_time_d = datetime.strptime(end_time, time_format)
            es_host = clu.eshost.split(',')
            es = Elasticsearch(es_host)
            while start_time_d <= end_time_d:
                date_str = start_time_d.strftime("{0}-%Y%m%d".format(date_str_index))
                index_list.append(date_str)
                try:
                    es.search(index=date_str)
                except Exception as e:
                    logger.error(str(e))
                    index_list.remove(date_str)
                start_time_d += timedelta(days=1)
            querys = {
                'top_ip': {"sort": [], "query": {"bool": {"must": [
                    {"match_all": {}},
                    {"term": {field: web_nid}},
                    {"range": {"time": {"gte": start_time, "lte": end_time}}}]
                }}, "from": 0, "aggs": {"data": {"terms": {"field": "clientIp", "size": "10"}}}, "size": 0},
                'views': {"sort": [], "query": {"bool": {"must": [
                    {"match_all": {}},
                    {"term": {field: web_nid}},
                    {"range": {"time": {"gte": start_time, "lte": end_time}}}]
                }}, "from": 0, "aggs": {"data": {"date_histogram": {
                    "field": "time", "interval": "hour",
                    "min_doc_count": 0, "extended_bounds": {"min": start_time, "max": end_time}
                }}}, "size": 0},
                'top_ua': {"sort": [], "query": {"bool": {"must": [
                    {"match_all": {}},
                    {"term": {field: web_nid}},
                    {"range": {"time": {"gte": start_time, "lte": end_time}}}]
                }}, "from": 0, "aggs": {"data": {"terms": {"field": "http_user_agent", "size": "10"}}}, "size": 0},
                'top_web': {"sort": [], "query": {"bool": {"must": [
                    {"match_all": {}},
                    {"term": {field: web_nid}},
                    {"range": {"time": {"gte": start_time, "lte": end_time}}}]
                }}, "from": 0, "aggs": {"data": {"terms": {"field": "host", "size": "10"}}}, "size": 0},
                'top_status': {"sort": [], "query": {"bool": {"must": [
                    {"match_all": {}},
                    {"term": {field: web_nid}},
                    {"range": {"time": {"gte": start_time, "lte": end_time}}}]
                }}, "from": 0, "aggs": {"data": {"terms": {"field": "status", "size": "10"}}}, "size": 0},
                'top_attack_type': {"sort": [], "query": {"bool": {"must": [
                    {"match_all": {}},
                    {"term": {field: web_nid}},
                    {"range": {"time": {"gte": start_time, "lte": end_time}}}]
                }}, "from": 0, "aggs": {"data": {"terms": {"field": "rule_id", "size": "10"}}}, "size": 0}
                }
            if request.method == 'GET':
                for c in do_charts:
                    try:
                        chat_data = []
                        if index_list:
                            querys_data = querys[c]
                            if clu_sw:
                                del querys_data['query']['bool']['must'][1]
                            es_data = es.search(index=index_list, body=querys_data)
                            bucket_data = es_data['aggregations']['data']['buckets']
                            if c == 'top_ip':
                                for a in bucket_data:
                                    geo_data = geoip(a['key'])
                                    chat_data.append({
                                        'name': a['key'],
                                        'value': a['doc_count'],
                                        'city': geo_data['city'],
                                        'latitude': geo_data['latitude'],
                                        'longitude': geo_data['longitude'],
                                        'country_name': geo_data['country_name']
                                    })
                            else:
                                chat_data = bucket_data
                        else:
                            chat_data = []
                        data[c] = chat_data
                    except Exception as e:
                        logger.error(str(e))
                data['webs'] = webs
                result['data'] = data
                result['success'] = True
            if request.method == 'POST':
                start_data = (page-1)*size
                request_data = request.get_json()
                table_query = {"query": {"bool": {"must": [{"match_all": {}},
                                                           {"range": {"time": {"gte": start_time, "lte": end_time}}},
                                                           {"term": {field: web_nid}},
                                                           ]}},
                               "from": start_data, "size": size, "sort": [], "aggs": {}}
                if request_data:
                    for r in request_data:
                        if r in [
                            "clientIp", "request_uri", "rule_id",
                            "risk_level", "rule_desc", "attack_tag", "upstream_addr"
                        ]:
                            if request_data[r]:
                                if r in ["risk_level"]:
                                    reg_str = "term"
                                else:
                                    reg_str = "prefix"
                                table_query["query"]["bool"]["must"].append({reg_str: {r: request_data[r]}})
                es_data = es.search(index=index_list, body=table_query)
                hits_data = es_data['hits']['hits']
                hits_datas = []
                for d in hits_data:
                    hits_datas.append({
                        "_source": d.get('_source')
                    })
                total = es_data['hits']['total']
                if total > 10000:
                    total = 10000
                result['data'] = hits_datas
                result['webs'] = webs
                result['pages'] = {"size": size, "page": page, "total": total}
                result['success'] = True
        else:
            result['info'] = '集群不存在'
    except Exception as e:
        logger.error(str(e))
        result['info'] = str(e)
    return jsonify(result)


@app.route('/waf/api/Cluster', methods=['GET', 'POST', 'PUT'])
@sso.require_login
def cluster_manage(user):
    result = {'success': False}
    try:
        if request.method == 'GET':
            data = []
            for cluster in Cluster.get_all(status=1):
                data.append({
                    'nid': cluster.nid,
                    'name': cluster.name,
                    'label': cluster.label,
                    'cname': cluster.cname,
                    'salt_api': cluster.salt_api,
                    'salt_user': cluster.salt_user,
                    'salt_pass': cluster.salt_pass,
                    'salt_eauth': cluster.salt_eauth,
                    'eshost': cluster.eshost,
                    'ngxhost': cluster.ngxhost,
                    'ngx_path': cluster.ngx_path,
                    'ssl_dir': cluster.ssl_dir,
                    'waf_conf_path': cluster.waf_conf_path,
                    'site_dir': cluster.site_dir,
                    'status': cluster.clu_status
                })
            result['success'] = True
            # 记录
            Recored.record_check_list(user, '集群')
        if request.method == 'POST':
            request_data = request.get_json()
            cluster = Cluster(
                name=request_data['name'],
                label=request_data['label'],
                cname=request_data['cname'],
                eshost=request_data['eshost'],
                ngxhost=request_data['ngxhost'],
                ngx_path=request_data['ngx_path'],
                ssl_dir=request_data['ssl_dir'],
                waf_conf_path=request_data['waf_conf_path'],
                site_dir=request_data['site_dir'],
                salt_api=request_data['salt_api'],
                salt_user=request_data['salt_user'],
                salt_pass=request_data['salt_pass'],
                salt_eauth=request_data['salt_eauth'],
                clu_status=1,
                user=user['nid']
            ).create()
            # 添加集群前检查salt模块健康
            salt_client = SaltClient(cluster.nid)
            res = salt_client.login_post()
            if not res:
                # 失败，回退集群
                cluster.delete()
                raise Exception("Salt test no pass :",
                                salt_client.action_url)
            # 下发全部证书到此集群上
            # CertHandler.sync_certs(cluster.nid, user)

            result['data'] = {'nid': cluster.nid}
            result['success'] = True
            # 记录
            Recored.record_handle_info(user, cluster.name, '集群', result['success'])
    except Exception as e:
        logger.error(str(e))
        result['info'] = str(e)
    return jsonify(result)


@app.route('/waf/api/ClusterReload/<nid>', methods=['GET'])
@sso.require_login
def cluster_reload(user, nid):
    """
        获取集群reload时间
    """
    result = {'success': False}
    try:
        cluster = Cluster.get(nid=nid, status=1)
        now_time = datetime.now()
        if cluster.reload_time > now_time:
            result['time'] = cluster.reload_time.strftime('%Y-%m-%d %H:%M:%S')
        else:
            result['time'] = now_time.strftime('%Y-%m-%d %H:%M:%S')
        result['success'] = True
    except Exception as e:
        logger.error(str(e))
        result['info'] = str(e)
    return jsonify(result)


@app.route('/waf/api/Cluster/<nid>', methods=['GET', 'POST', 'DELETE', 'PUT'])
@sso.require_login
def cluster_action(user, nid):
    result = {'success': False}
    try:
        cluster = Cluster.get(nid=nid, status=1)
        if cluster:
            if request.method == 'POST':
                request_data = request.get_json()
                # if 'ngxhost' in request_data and \
                #         cluster.ngxhost != request_data.get('ngxhost'):
                # 添加集群前检查salt模块健康salt_api
                salt_client = SaltClient(nid)
                res = salt_client.test_login_post(request_data['salt_api'],
                                                  request_data['salt_user'],
                                                  request_data['salt_pass'],
                                                  request_data['salt_eauth'])
                if not res:
                    raise Exception("Salt test no pass :",
                                    request_data['salt_api'])
                cluster = cluster.edit(request_data)
                # 下发所有证书和配置文件到添加的机器上
                CertHandler.sync_conf_files(cluster, user)

                result['data'] = {'nid': cluster.nid}
                result['success'] = True
            if request.method == 'GET':
                result['data'] = {
                    'nid': cluster.nid,
                    'name': cluster.name,
                    'label': cluster.label,
                    'cname': cluster.cname,
                    'salt_api': cluster.salt_api,
                    'salt_user': cluster.salt_user,
                    'salt_pass': cluster.salt_pass,
                    'salt_eauth': cluster.salt_eauth,
                    'eshost': cluster.eshost,
                    'ngxhost': cluster.ngxhost,
                    'ngx_path': cluster.ngx_path,
                    'ssl_dir': cluster.ssl_dir,
                    'waf_conf_path': cluster.waf_conf_path,
                    'site_dir': cluster.site_dir,
                    'status': cluster.clu_status
                }
                result['success'] = True
            if request.method == 'DELETE':
                status = -1
                # request_data = request.get_json()
                # if request_data:
                #     status = int(request_data.get('status', -1))
                cluster = cluster.update(status=status)
                # for w in Web.get_all(cluster=cluster.nid):
                #   w.update(status=status)
                result['success'] = True
            if request.method == 'PUT':
                asyn_salt(clu_nid=cluster.nid, op='reload', nid=cluster.nid, user=user['nid'])
                result['success'] = True
        else:
            result['info'] = '集群不存在'
        # 记录
        Recored.record_handle_info(user, cluster.name, '集群配置', result['success'], request.method)
    except Exception as e:
        logger.error(str(e))
        result['info'] = str(e)
    return jsonify(result)


@app.route('/waf/api/Cert', methods=['GET', 'POST'])
@sso.require_login
def api_cert_list(user):
    result = {'success': False}
    try:
        if request.method == 'GET':
            page = request.values.get('page', type=int, default=1)
            size = request.values.get('size', type=int, default=10)
            start = request.values.get('start', type=int, default=0)
            draw = request.values.get('draw', type=int, default=1)
            data = []
            if start:
                page = start / size + 1
            ct = Cert.get_page(page, size, user['role'], user['nid'])
            for c in ct.items:
                data.append({
                    'nid': c.nid,
                    'name': c.name,
                    'subject': c.subject,
                    'issuer': c.issuer,
                    'start': c.start,
                    'expire': c.expire,
                })
            result['data'] = {
                'certs': data,
                'pages': {'total': ct.total, 'page': page, 'size': size, 'draw': draw}
            }
            result['success'] = True
            # 记录
            Recored.record_check_list(user, '证书')
        if request.method == 'POST':
            request_data = request.get_json()
            name = request_data['name']
            cert = request_data['cert']
            keys = request_data['keys']
            parser = parser_ssl(cert)
            if parser:
                ct = Cert(
                    name=name,
                    cert=cert,
                    keys=keys,
                    subject=parser['subject'],
                    issuer=parser['issuer'],
                    start=parser['start'],
                    expire=parser['expire'],
                    user=user['nid']
                ).create()
                # for clu in Cluster.get_all(status=1):
                #     asyn_salt(clu_nid=clu.nid, op='cert', nid=ct.nid, user=user['nid'])
                result['nid'] = ct.nid
                result['success'] = True
            else:
                result['info'] = '证书格式错误'
            # 记录
            Recored.record_handle_info(user, cert.name, '证书', result['success'])
    except Exception as e:
        logger.error(str(e))
        result['info'] = str(e)
    return jsonify(result)


@app.route('/waf/api/Cert/<nid>', methods=['GET', 'POST', 'DELETE'])
@sso.require_login
def cert_action(user, nid):
    result = {'success': False}
    try:
        cert = Cert.get(nid=nid, status=1)
        if cert:
            if request.method == 'POST':
                request_data = request.get_json()
                cert_data = request_data['cert']
                keys_data = request_data['keys']
                parser = parser_ssl(cert_data)
                if parser:
                    # 判断是否过期
                    if parser['expire'] < datetime.now():
                        raise Exception('Cert past due: ', parser['expire'])
                    cert = cert.update(
                        keys=keys_data,
                        cert=cert_data,
                        subject=parser['subject'],
                        issuer=parser['issuer'],
                        start=parser['start'],
                        expire=parser['expire'],
                        user=user['nid']
                    )
                    # 每个集群找到其中一个域名配置，并且下发，自动更新证书
                    CertHandler.update_cert(cert.nid, user)

                    result['data'] = {'nid': cert.nid}
                    result['success'] = True
                else:
                    result['info'] = '证书格式错误'
            if request.method == 'GET':
                result['data'] = {
                    'nid': cert.nid,
                    'name': cert.name,
                    'keys': cert.keys,
                    'cert': cert.cert,
                    'subject': cert.subject,
                    'issuer': cert.issuer,
                    'start': cert.start,
                    'expire': cert.expire,
                }
                result['success'] = True
            if request.method == 'DELETE':
                cert.update(status=-1)
                # 对应站点配置文件修改
                # for clu in Cluster.get_all(status=1):
                #     asyn_salt(clu_nid=clu.nid, op='cert', nid=cert.nid, user=user['nid'])
                result['success'] = True
        else:
            result['info'] = '证书不存在'
        # 记录
        Recored.record_handle_info(user, cert.name, '证书', result['success'], request.method)
    except Exception as e:
        logger.error(str(e))
        result['info'] = str(e)
    return jsonify(result)


@app.route('/waf/api/User', methods=['GET', 'POST'])
@sso.require_login
def api_user_list(user):
    result = {'success': False}
    try:
        if request.method == 'GET':
            page = request.values.get('page', type=int, default=1)
            size = request.values.get('size', type=int, default=10)
            start = request.values.get('start', type=int, default=0)
            draw = request.values.get('draw', type=int, default=1)
            search = request.values.get('search')
            data = []
            if start:
                page = start / size + 1
            admin = Admin.get_page(page, size, search)
            for c in admin.items:
                clu = []
                if c.clusters:
                    for cc in c.clusters:
                        if cc.status == 1:
                            clu.append({
                                'nid': cc.nid,
                                'name': cc.name
                            })
                data.append({
                    'nid': c.nid,
                    'name': c.name,
                    'username': c.username,
                    'email': c.email,
                    'phone': c.phone,
                    'role': c.role,
                    'origin': c.origin,
                    'clusters': clu
                })
            result['data'] = {
                'cluster': user['cluster'],
                'users': data,
                'pages': {'total': admin.total, 'page': page, 'size': size, 'draw': draw}
            }
            result['success'] = True
            # 记录
            Recored.record_check_list(user, '用户')
        if request.method == 'POST':
            request_data = request.get_json()
            clusters = request_data.get('clusters')
            clusters_d = []
            if clusters:
                for c in clusters:
                    cluster = Cluster.get(status=1, nid=c)
                    if cluster:
                        clusters_d.append(cluster)
            admin = Admin(
                username=request_data['username'],
                email=request_data['email'],
                phone=request_data['phone'],
                password=request_data['password'],
                role=int(request_data['role']),
                origin=request_data['origin'],
                clusters=clusters_d,
                originator=user['nid']
            ).create()
            result['success'] = True
            # 记录
            Recored.record_handle_info(user, admin.username, '用户', result['success'])
    except Exception as e:
        logger.error(str(e))
        result['info'] = str(e)
    return jsonify(result)


@app.route('/waf/api/User/<nid>', methods=['GET', 'POST', 'DELETE'])
@sso.require_login
def user_action(user, nid):
    result = {'success': False}
    try:
        admin = Admin.get(nid=nid, status=1)
        if admin:
            if request.method == 'POST':
                request_data = request.get_json()
                admin = admin.edit(request_data)
                result['data'] = {'nid': admin.nid}
                result['success'] = True
            if request.method == 'GET':
                clusters = []
                for a in admin.clusters.all():
                    clusters.append(a.nid)
                result['data'] = {
                    'nid': admin.nid,
                    'name': admin.name,
                    'username': admin.username,
                    'email': admin.email,
                    'phone': admin.phone,
                    'role': admin.role,
                    'origin': admin.origin,
                    'clusters': clusters
                }
                result['success'] = True
            if request.method == 'DELETE':
                admin.update(status=-1)
                result['success'] = True
        else:
            result['info'] = '用户不存在'
        # 记录
        Recored.record_handle_info(user, admin.account, '用户', result['success'], request.method)
    except Exception as e:
        logger.error(str(e))
        result['info'] = str(e)
    return jsonify(result)


@app.route('/waf/api/Msg', methods=['GET', 'POST'])
@sso.require_login
def api_msg_list(user):
    result = {'success': False}
    try:
        if request.method == 'GET':
            page = request.values.get('page', type=int, default=1)
            size = request.values.get('size', type=int, default=10)
            start = request.values.get('start', type=int, default=0)
            draw = request.values.get('draw', type=int, default=1)
            data = []
            if start:
                page = start / size + 1
            msg = Msg.get_page(page, size, user['role'], user['nid'])
            for m in msg.items:
                try:
                    target = ''
                    if m.genre in ['web_edit', 'web_add', 'web_stop', 'web_del', 'waf_conf']:
                        target = Web.get(nid=m.web).name
                    elif m.genre in ['reload', 'rules', 'white_list', 'policy']:
                        target = Cluster.get(nid=m.web).name
                    data.append({
                        'nid': m.nid,
                        'time': m.gmt_created,
                        'content': json.loads(m.content),
                        'genre': m.genre,
                        'target': target,
                        'username': Admin.get(nid=m.user).name if Admin.get(nid=m.user) else ''
                    })
                    m.update(msg_status=-1)
                except Exception as e:
                    str(e)
            result['data'] = {
                'msgs': data,
                'pages': {'total': msg.total, 'page': page, 'size': size, 'draw': draw}
            }
            result['success'] = True
            # 记录
            Recored.record_check_list(user, '消息')
    except Exception as e:
        logger.error(str(e))
        result['info'] = str(e)
    return jsonify(result)


@app.route('/waf/api/Msg/<web_nid>', methods=['GET'])
@sso.require_login
def api_fail_msg(user, web_nid):
    result = {'success': False, 'data': {}}
    try:
        data = []
        msg = Msg.get_by_web(user['role'], user['nid'], web=web_nid)
        web = Web.get(nid=web_nid)

        # for m in msg.items:
        print 'msg.gmt_modified',msg.gmt_modified
        print 'web.gmt_modified',web.gmt_modified
        if msg and msg.gmt_modified > web.gmt_modified:

            content = json.loads(msg.content)
            if content.get('fail', ''):
                target = ''
                if msg.genre in ['web_edit', 'web_add', 'web_stop',
                                 'web_del', 'waf_conf']:
                    target = Web.get(nid=msg.web).name
                elif msg.genre in ['reload', 'rules', 'white_list',
                                   'policy']:
                    target = Cluster.get(nid=msg.web).name
                data = {
                    'nid': msg.nid,
                    # 'time': msg.gmt_created,
                    # 'content': json.loads(msg.content),
                    'fails': content['fail'],
                    'genre': msg.genre,
                    'target': target,
                    # 'username': Admin.get(nid=m.user).name if Admin.get(nid=m.user) else ''
                }
                # msg.update(msg_status=-1)
                result['data'] = data
                result['success'] = True
    except Exception as e:
        logger.error(str(e))
        result['info'] = str(e)
    return jsonify(result)


@app.route('/waf/api/Rules', methods=['GET', 'POST', 'PUT', 'DELETE'])
@sso.require_login
def api_rule_list(user):
    result = {'success': False}
    try:
        if request.method == 'GET':
            page = request.values.get('page', type=int, default=1)            
            size = request.values.get('size', type=int, default=10)
            start = request.values.get('start', type=int, default=0)
            draw = request.values.get('draw', type=int, default=1)
            search = request.values.get('search')
            stage = request.values.get('stage')
            data = []
            if start:
                page = start / size + 1
            rules = WafRules.get_page(page, size, user['role'], user['nid'], search, stage)
            for r in rules.items:
                data.append({
                    'nid': r.nid,
                    'risk_level': r.risk_level,
                    'tags': r.tags,
                    'f_rule_status': r.f_rule_status,
                    'gmt_modify': r.gmt_modified,
                    'gmt_create': r.gmt_created,
                    'editor': r.editor,
                    'f_rule_name': r.f_rule_name,
                    'f_rule_desc': r.f_rule_desc,
                    'f_rule_id': r.f_rule_id,
                    'id': r.id,
                    'f_rule': None,
                    'stage': r.stage
                })
            result['data'] = {
                'rule': data,
                'pages': {'total': rules.total, 'page': page, 'size': size, 'draw': draw}
            }
            result["success"] = True
            # 记录
            Recored.record_check_list(user, '规则')
        if request.method == 'POST':
            data = request.get_json()
            rule = WafRules(
                f_rule_name=data.get("f_rule_name"),
                f_rule_desc=data.get("f_rule_desc"),
                f_rule=json.dumps(data.get("f_rule", [])),
                tags=data.get("tags"),
                f_rule_status=data.get("f_rule_status"),
                risk_level=data.get("risk_level"),
                user=user['nid'],
                stage=data.get("stage")
            ).create()
            print "aaaaaaaa", rule
            result['nid'] = rule.nid
            result["success"] = True
            # 记录
            Recored.record_handle_info(user, rule.f_rule_name, '规则', result["success"])
    except Exception as e:
        logger.error(str(e))
        result['info'] = str(e)
    return jsonify(result)


@app.route('/waf/api/Rules/<nid>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@sso.require_login
def api_rule_edit(user, nid):
    result = {'success': False}
    #try:
    rule = WafRules.get(status=1, nid=nid)
    if rule:
        if request.method == 'GET':
            result['data'] = {
                'nid': rule.nid,
                'risk_level': rule.risk_level,
                'tags': rule.tags,
                'f_rule_status': rule.f_rule_status,
                'gmt_modify': rule.gmt_modified,
                'gmt_create': rule.gmt_created,
                'editor': rule.editor,
                'f_rule_name': rule.f_rule_name,
                'f_rule_desc': rule.f_rule_desc,
                'f_rule_id': rule.f_rule_id,
                'id': rule.id,
                'f_rule': json.loads(rule.f_rule),
                'stage': rule.stage
            }
            result["success"] = True
        if request.method == 'POST':
            request_data = request.get_json()
            request_data['f_rule'] = json.dumps(request_data.get('f_rule', []))
            rule = rule.edit(request_data)
            # 查询规则使用的集群 salt下发confi
            policy_id_set = set()
            for f in RequestFilter.get_all(rule_id=rule.id):
                policy = Policy.get(id=f.policy_id, status=1)
                if policy:
                    policy_id_set.add(policy.uuid)
            for f in ResponseFilter.get_all(rule_id=rule.id):
                policy = Policy.get(id=f.policy_id, status=1)
                if policy:
                    policy_id_set.add(policy.uuid)

            cluster_set = set()
            for uuid in policy_id_set:
                for w in Web.get_policy(nid=uuid):
                    cluster_set.add(w.cluster)
            for cluster in cluster_set:
                asyn_salt(clu_nid=cluster, op='rules', nid=cluster, user=user['nid'])
            result["success"] = True
        # if request.method == 'DELETE':
        #     rule.update(status=-1)
        #     result["success"] = True
        # if request.method == 'PUT':
        #     request_data = request.get_json()
        #     rule.update(f_rule_status=int(request_data.get('status', 0)))
        #     result["success"] = True
    else:
        result['info'] = '规则不存在'
        # 记录
        Recored.record_handle_info(user, rule.f_rule_name, '规则', result["success"], request.method)
    '''
    except Exception as e:
        logger.error(str(e))
        result['info'] = str(e)
    '''
    return jsonify(result)


@app.route('/waf/api/Policy', methods=['GET', 'POST'])
@sso.require_login
def api_policy_list(user):
    result = {'success': False}
    try:
        if request.method == 'GET':
            page = request.values.get('page', type=int, default=1)
            size = request.values.get('size', type=int, default=10)
            start = request.values.get('start', type=int, default=0)
            draw = request.values.get('draw', type=int, default=1)
            data = []
            rules = []
            if start:
                page = start / size + 1
            policy = Policy.get_page(page, size, user['role'], user['name'])
            for p in policy.items:
                data.append({
                    'uuid': p.uuid,
                    'name': p.name,
                    'kind': p.kind,
                    'action': p.action,
                    'upload_file_access': p.upload_file_access,
                    'request_body_access': p.request_body_access,
                    'response_body_access': p.response_body_access,
                    'cluster': p.cluster
                })
            result['data'] = {
                'cluster': user['cluster'],
                'policies': data,
                'pages': {'total': policy.total, 'page': page, 'size': size, 'draw': draw}
            }
            result['success'] = True
            # 记录
            Recored.record_check_list(user, '策略')
        if request.method == 'POST':
            request_data = request.get_json()
            kind = request_data.get('kind', 'custom')
            if user['role'] != 5:
                kind = 'custom'
            rules = []
            rule_data = request_data.get('rules', [])
            if rule_data:
                for r in rule_data:
                    rule = WafRules.get(status=1, nid=r)
                    if rule:
                        rules.append(rule)
            policy = Policy(
                name=request_data['name'],
                mode=int(request_data.get('mode', 0)),
                action=request_data.get('action', 'DENY'),
                action_vars=json.dumps({"redirect_url": request_data.get('redirect_url', '')}),
                kind=kind,
                rules=rules,
                cluster=request_data.get('cluster'),
                user=user['nid']
            ).create()
            result['data'] = {'uuid': policy.uuid}
            result['success'] = True
            # 记录
            Recored.record_handle_info(user, policy.name, '策略', result['success'])
    except Exception as e:
        logger.error(str(e))
        result['info'] = str(e)
    return jsonify(result)


@app.route('/waf/api/Whitelist', methods=['GET', 'POST'])
@sso.require_login
def api_whitelist_list(user):
    result = {'success': False}
    try:
        if request.method == 'GET':
            page = request.values.get('page', type=int, default=1)
            size = request.values.get('size', type=int, default=10)
            start = request.values.get('start', type=int, default=0)
            draw = request.values.get('draw', type=int, default=1)
            data = []
            if start:
                page = start / size + 1
            wt_list = WhiteList.get_page(page, size, user['role'], user['nid'])
            for wt in wt_list.items:
                data.append({
                    'nid': wt.nid,
                    'rule_desc': wt.w_rule_desc,
                    'rule': json.loads(wt.w_rule),
                    'time': wt.gmt_modified,
                    'status': wt.w_rule_status
                })
            sites = []
            if user['role'] == 1:
                for w in Web.get_all(status=1, user=user['nid']):
                    sites.append({'nid': w.nid, 'name': w.name, 'kind': 'web'})
            else:
                if user['role'] == 5:
                    sites.append({'nid': '', 'name': '全部站点', 'kind': 'cluster'})
                for cu in user['cluster']:
                    sites.append({'nid': cu['nid'], 'name': cu['name'], 'kind': 'cluster'})
            result['data'] = {
                'whitelist': data,
                'sites': sites,
                'pages': {'total': wt_list.total, 'page': page, 'size': size, 'draw': draw}
            }
            result['success'] = True
            # 记录
            Recored.record_check_list(user, '白名单')
        if request.method == 'POST':
            clus = []
            request_data = request.get_json()
            wt_data = {
                "URI": request_data.get("w_url"),
                "IP": request_data.get("w_ip"),
                "HOST": request_data.get("w_host")
            }
            for s in request_data.get("site", []):
                if s == "":
                    clus = []
                    break
                clu = Cluster.get(status=1, nid=s)
                if clu:
                    clus.append(clu)
            wt_list = WhiteList(
                w_rule_desc=request_data["w_rule_desc"],
                w_rule_status=int(request_data.get('w_rule_status', 0)),
                w_rule=json.dumps(wt_data),
                user=user['nid'],
                cluster=clus
            ).create()

            # 下发到salt 更新config.json
            clus_s = wt_list.cluster.all()
            if not clus_s:
                clus_s = Cluster.get_all(status=1)
            for c in clus_s:
                asyn_salt(clu_nid=c.nid, op='white_list', nid=c.nid, user=user['nid'])

            result['success'] = True
            # 记录
            Recored.record_handle_info(user, wt_list.w_rule_desc, '白名单', result['success'])
    except Exception as e:
        logger.error(str(e))
        result['info'] = str(e)
    return jsonify(result)


@app.route('/waf/api/Whitelist/<nid>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@sso.require_login
def api_whitelist_edit(user, nid):
    result = {'success': False}
    try:
        wt_list = WhiteList.get(status=1, nid=nid)
        if wt_list:
            if request.method == 'GET':
                webs = []
                webs_data = wt_list.cluster.all()
                if webs_data:
                    for s in webs_data:
                        webs.append({"nid": s.nid, "name": s.name, "kind": "web"})
                else:
                    webs.append({"nid": "", "name": "全部站点", "kind": "web"})
                result['data'] = {
                    'nid': wt_list.nid,
                    'rule_desc': wt_list.w_rule_desc,
                    'rule': json.loads(wt_list.w_rule),
                    'time': wt_list.gmt_modified,
                    'webs': webs,
                    'status': wt_list.w_rule_status
                }
                result["success"] = True
            if request.method == 'DELETE':
                wt_list.update(status=-1)
                result["success"] = True
            if request.method == 'POST':
                request_data = request.get_json()
                wt_list.edit(request_data)

                # 下发到salt更新config.json
                clus_s = wt_list.cluster.all()
                if not clus_s:
                    clus_s = Cluster.get_all(status=1)
                for c in clus_s:
                    asyn_salt(clu_nid=c.nid, op='white_list', nid=c.nid, user=user['nid'])

                result["success"] = True
        else:
            result['info'] = '规则不存在'
        # 记录
        Recored.record_handle_info(user, wt_list.w_rule_desc, '白名单', result['success'], request.method)
    except Exception as e:
        logger.error(str(e))
        result['info'] = str(e)
    return jsonify(result)


@app.route('/waf/api/AttackGraph', methods=['GET', 'POST'])
@sso.require_login
def api_attack_graph(user):
    result = {'success': False, 'data': []}
    try:
        now = datetime.now()
        time_format = "%Y-%m-%d %H:%M:%S"
        date_str_index = 'waf_log'
        # date_str_index = 'ngx_access_log'
        start_time = request.values.get('start_time', default=(now - timedelta(days=1)).strftime(time_format))
        end_time = request.values.get('end_time', default=now.strftime(time_format))
        start_time_d = datetime.strptime(start_time, time_format)
        end_time_d = datetime.strptime(end_time, time_format)
        for c in user['cluster']:
            try:
                clu = Cluster.get(nid=c.get('nid'), status=1)
                if clu:
                    index_list = []
                    es_host = clu.eshost.split(',')
                    es = Elasticsearch(es_host)
                    while start_time_d <= end_time_d:
                        date_str = start_time_d.strftime("{0}-%Y%m%d".format(date_str_index))
                        index_list.append(date_str)
                        try:
                            es.search(index=date_str)
                        except Exception as e:
                            logger.error(str(e))
                            index_list.remove(date_str)
                        start_time_d += timedelta(days=1)
                    query = {
                        "query": {
                            "bool": {
                                "must": [
                                    {
                                        "range": {
                                            "time": {
                                                "gt": (now - timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")
                                            }
                                            # "order": {
                                            #   "time": "desc"
                                            # },
                                        }
                                    }
                                ]
                            }
                        },
                        "size": 0
                    }
                    # print index_list
                    es_data = es.search(index=index_list, body=query)
                    # print es_data
                    query_datas = es_data["hits"]["hits"]
                    for data in query_datas:
                        print data
                        try:
                            srcIp = data["_source"]["remote_addr"]
                            destIp = data["_source"]["server_addr"]
                            location_rem = geoip(destIp)
                            location_ser = geoip(srcIp)
                            data_geo = {
                                'srcIp': srcIp,
                                'srcPort': data["_source"].get('server_port'),
                                'type': data["_source"].get('attack_tag'),
                                # 'type': data["_source"]["status"],
                                'destIp': destIp,
                                'destName': location_rem["city"],
                                'destLocX': location_rem["longitude"],
                                'destLocY': location_rem["latitude"],
                                'time': data["_source"]["time"],
                                'srcName': location_ser["city"],
                                'srcLocX': location_ser["longitude"],
                                'srcLocY': location_ser["latitude"]
                            }
                            result['data'].append(data_geo)
                        except Exception as e:
                            logger.error(str(e))
            except Exception as e:
                logger.error(str(e))
    except Exception as e:
        logger.error(str(e))
        result['info'] = str(e)
    # 记录
    Recored.record_check_list(user, '趋势图')
    return jsonify(result)


# @app.route('/core/api/v1/config', methods=['GET', 'POST'])
# @sso.require_login
# def api_core_config(user):
#     result = {
#         "message": "",
#         "code": 400,
#         "hash": "",
#         "version": "1.0",
#         "datas": []
#     }
#     try:
#         sid = request.values.get('sid')
#         if sid:
#             ngx = Ngx.get(sid=sid, status=1, ngx_status=1)
#             if ngx:
#                 clu = Cluster.get(nid=ngx.cluster, status=1, clu_status=1)
#                 if clu:
#                     for w in Web.get_all(cluster=clu.nid, status=1, web_status=1):
#                         waf_data = Assemble(w.nid).waf_file()
#                         if waf_data:
#                             result['datas'].append(waf_data)
#                     result['code'] = 200
#                     result['message'] = clu.nid
#             else:
#                 ngx = Ngx(
#                     sid=sid,
#                     host=request.values.get('host'),
#                     name=request.values.get('name')
#                 ).create()
#                 result['code'] = 201
#                 result['message'] = "add nginx success"
#     except Exception as e:
#         logger.error(str(e))
#         result['code'] = 500
#         result['message'] = str(e)
#     return jsonify(result)


@app.route('/devops/api/site', methods=['GET'])
def api_devops_site():
    result = {'success': False, 'data': []}
    keys = request.values.get('keys', default="")
    try:
        if request.method == 'GET':
            if keys == "2d0965af7f6ee1a1ac33fdd95e2afc69":
                for w in Web(status=1, web_status=1).get_all():
                    if w.clusters.status == 1:
                        result['data'].append({
                            'name': w.name,
                            'https': w.https,
                            'http': w.http,
                            'https_port': w.https_port,
                            'http_port': w.http_port,
                            'mark': w.mark,
                            'cluster': w.clusters.name
                        })
                result["success"] = True
            else:
                result['info'] = 'keys wrong'
    except Exception as e:
        logger.error(str(e))
        result['info'] = str(e)
    return jsonify(result)


@app.route('/Rules', methods=['GET'])
@sso.require_login
def rules_tpl(user):
    return render_template('Rules.html', user=user)


@app.route('/Rules/<nid>', methods=['GET'])
@sso.require_login
def rules_edit_tpl(user, nid):
    return render_template('RulesEdit.html', user=user, nid=nid)


@app.route('/Policy', methods=['GET'])
@sso.require_login
def policy_tpl(user):
    return render_template('Policy.html', user=user)

@app.route('/Whitelist', methods=['GET'])
@sso.require_login
def whitelist_tpl(user):
    return render_template('Whitelist.html', user=user)


@app.route('/Index', methods=['GET'])
@sso.require_login
def index_tp(user):
    return render_template('base.html', user=user)


@app.route('/Dashboard', methods=['GET'])
@sso.require_login
def dashboard_tp(user):
    return render_template('View.html', user=user)


@app.route('/', methods=['GET'])
@sso.require_login
def dashboard(user):
    return render_template('WebConfig.html', user=user)


@app.route('/Cluster', methods=['GET'])
@sso.require_login
def clu_tpl(user):
    return render_template('Cluster.html', user=user, cluster=Cluster.get_all(status=1))


@app.route('/User', methods=['GET'])
@sso.require_login
def user_tpl(user):
    return render_template('User.html', user=user)


@app.route('/Attack', methods=['GET'])
@sso.require_login
def attack_tpl(user):
    return render_template('Attack.html', user=user)



@app.route('/WebConfig', methods=['GET'])
@sso.require_login
def web_tpl(user):
    return render_template('WebConfig.html', user=user)


@app.route('/Cert', methods=['GET'])
@sso.require_login
def cert_list(user):
    return render_template('Cert.html', user=user)


@app.route('/Msg', methods=['GET'])
@sso.require_login
def msg_list(user):
    return render_template('Msg.html', user=user)


@app.route('/t', methods=['GET'])
def tp_tpl():
    return "Power By V"


# @app.route('/PointLogin')
# def point_login():
#     return redirect('https://waf.console.anlink.tech')


@app.route('/Login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        result = {'success': False, "msg": ''}
        username = request.json.get("username", "")
        password = request.json.get("password", "")
        if (username != "") & (password != ""):
            admin_query = Admin.get(username=username, status=1, origin='aegis_waf')
            if admin_query:
                # 先验证登录状态
                if not admin_query.auth_status():
                    # 验证次数过多处理
                    result['msg'] = '登录次数过多，请稍后再试'
                    return jsonify(result)
                if admin_query.check_password(password):
                    clu = []
                    clusters_data = Cluster.get_all(status=1)
                    for a in clusters_data:
                        if a.status == 1:
                            clu.append({'name': a.name, 'id': a.id, 'nid': a.nid})
                    user = {
                        'name': admin_query.username,
                        'nid': admin_query.nid,
                        'role': admin_query.role,
                        'cluster': clu,
                        'orgin': 'aegis_waf'
                    }
                    session['user'] = user
                    # 登录成功处理
                    admin_query.auth_pass()
                    result['success'] = True
                    result['msg'] = url_for('dashboard')
                    # return redirect(url_for('dashboard'))
                else:
                    # 密码验证错误
                    admin_query.record_auth()
                    result['msg'] = '密码错误!'
            else:
                result['msg'] = '该用户不存在!'
        return jsonify(result)
    return render_template("Login.html")


@app.route('/logout')
@sso.require_login
def logout(user):
    return sso.logout(user)


@app.route('/health')
def health():
    return 'ok'


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(403)
def page_forbidden(e):
    return render_template('403.html'), 403


@app.route('/tttttt', methods=['GET'])
def ttttt_ttt():
    result = {'success': False, 'data': []}
    search = request.values.get('search', default="")
    try:
        if request.method == 'GET':
            if search:
                for w in Web.get_like(search=search):
                    conf_text = Assemble(w.nid).ngx_file()
                    text_status = False
                    if conf_text['success']:
                        path_f = 'data/{0}/{1}/'.format(search, w.cluster)
                        if not os.path.exists(path_f):
                            os.makedirs(path_f)
                        with open(path_f+str(w.nid)+'.outer', 'w') as f1:
                            f1.write(conf_text['text'])
                            text_status = True
                    result['data'].append({
                        'nid': w.nid,
                        'name': w.name,
                        'text': text_status
                    })
                result["success"] = True
            else:
                result['info'] = 'search none'
    except Exception as e:
        logger.error(str(e))
        result['info'] = str(e)
    return jsonify(result)


@app.route('/test', methods=['GET'])
def ttttt_tt():
    result = {'success': False, 'data': []}
    try:
        Web.update_origin()
        result['success'] = True
    except Exception as e:
        logger.error(str(e))
        result['info'] = str(e)
    return jsonify(result)

