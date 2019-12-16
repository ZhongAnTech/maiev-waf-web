# -*- coding: utf-8 -*-

import json

from utils import sso
from app import app
from modules import Policy, RequestFilter, ResponseFilter, WafRules, ResponseHeaderFilter
from flask import render_template, request, jsonify
from utils.log import log_setting
logger = log_setting(app_name="aegis_waf_4.0")


@app.route('/PolicyEdit/<uuid>', methods=['GET'])
@sso.require_login
def policy_edit_tpl(user, uuid):
    clusters = []
    if user['role'] == 5:
        clusters.append({'nid': 'all', 'name': '全部集群', 'kind': 'cluster'})
    for cu in user['cluster']:
        clusters.append({'nid': cu['nid'], 'name': cu['name'], 'kind': 'cluster'})
    return render_template('PolicyEdit.html', user=user, uuid=uuid, clusters=clusters)

@app.route('/waf/api/PolicyEdit/<uuid>', methods=['GET', 'POST', 'DELETE', 'PUT'])
@sso.require_login
def policy_edit_action(user, uuid):
    result = {'success': False}
    if request.method == 'GET':
        if user['role'] == 5:
            policy = Policy.get(uuid=uuid, status=1)
        else:
            policy = Policy.get(uuid=uuid, status=1)
        if policy:
            result['data'] = policy.to_dict()
            result['success'] = True
        else:
            result['info'] = '未找到策略'

    if request.method in ['POST', 'PUT']:
        request_data = request.get_json()
        if uuid == 'new':
            #try:
            policy = Policy(
                name=request_data.get('name'),
                kind=request_data.get('kind'),
                cluster=request_data.get('cluster'),
                action=request_data.get('action'),
                action_vars=json.dumps(request_data.get('action_vars')),
                version='v4',
                user=user['nid'],
                upload_file_access=request_data.get('upload_file_access'),
                request_body_access=request_data.get('request_body_access'),
                request_body_limit=request_data.get('request_body_limit'),
                request_body_nofile_limit=request_data.get('request_body_nofile_limit'),
                response_body_access=request_data.get('response_body_access'),
                response_body_limit=request_data.get('response_body_limit'),
                response_body_mime_type=request_data.get('response_body_mime_type'),
                request_filters=[],
                response_filters=[],
                response_header_filters=[]
            ).create()
            request_filters_list = request_data.get('request_filters', [])
            response_filters_list = request_data.get('response_filters', [])
            response_header_filters = request_data.get('response_header_filters', [])
            for i in xrange(len(request_filters_list)):
                RequestFilter.create(
                    rule_id=request_filters_list[i].get('rule_id'),
                    policy_id=policy.id,
                    order=i,
                    rule_action=request_filters_list[i].get('rule_action'),
                    action_vars=json.dumps(request_filters_list[i].get('action_vars', '{}'))
                )
            for i in xrange(len(response_filters_list)):
                ResponseFilter.create(
                    rule_id=response_filters_list[i].get('rule_id'),
                    policy_id=policy.id,
                    order=i,
                    rule_action=response_filters_list[i].get('rule_action'),
                    action_vars=json.dumps(response_filters_list[i].get('action_vars', '{}'))
                )
            for i in xrange(len(response_header_filters)):
                ResponseHeaderFilter.create(
                    rule_id=response_header_filters[i].get('rule_id'),
                    policy_id=policy.id,
                    order=i,
                    rule_action=response_header_filters[i].get('rule_action'),
                    action_vars=json.dumps(response_header_filters[i].get('action_vars', '{}'))
                )
            result['success'] = True
            '''
            except Exception as e:
                logger.error('create policy failed: %s', str(e))
                result['info'] = 'create policy failed:' + str(e)  
            '''          
        else:
            if user['role'] == 5:
                policy = Policy.get(uuid=uuid, status=1)
            else:
                policy = Policy.get(uuid=uuid, status=1)
            if policy:
                try:
                    for f in policy.request_filters:
                        f.delete()
                    for f in policy.response_filters:
                        f.delete()
                    for f in policy.response_header_filters:
                        f.delete()
                    policy.edit(
                        name=request_data.get('name'),
                        kind=request_data.get('kind'),
                        cluster=request_data.get('cluster'),
                        action=request_data.get('action'),
                        action_vars=json.dumps(request_data.get('action_vars')),
                        user=user['name'],
                        request_body_access=request_data.get('request_body_access'),
                        upload_file_access=request_data.get('upload_file_access'),
                        request_body_limit=request_data.get('request_body_limit'),
                        request_body_nofile_limit=request_data.get('request_body_nofile_limit'),
                        response_body_access=request_data.get('response_body_access'),
                        response_body_limit=request_data.get('response_body_limit'),
                        response_body_mime_type=request_data.get('response_body_mime_type')                     
                    )
                    request_filters_list = request_data.get('request_filters', [])
                    response_filters_list = request_data.get('response_filters', [])
                    response_header_filters = request_data.get('response_header_filters', [])
                    print response_header_filters
                    for i in xrange(len(request_filters_list)):
                        RequestFilter.create(
                            rule_id=request_filters_list[i].get('rule_id'),
                            policy_id=policy.id,
                            order=i,
                            rule_action=request_filters_list[i].get('rule_action'),
                            action_vars=json.dumps(request_filters_list[i].get('action_vars', '{}'))
                        )
                    for i in xrange(len(response_filters_list)):
                        ResponseFilter.create(
                            rule_id=response_filters_list[i].get('rule_id'),
                            policy_id=policy.id,
                            order=i,
                            rule_action=response_filters_list[i].get('rule_action'),
                            action_vars=json.dumps(response_filters_list[i].get('action_vars', '{}'))
                        )
                    for i in xrange(len(response_header_filters)):
                        ResponseHeaderFilter.create(
                            rule_id=response_header_filters[i].get('rule_id'),
                            policy_id=policy.id,
                            order=i,
                            rule_action=response_header_filters[i].get('rule_action'),
                            action_vars=json.dumps(response_header_filters[i].get('action_vars', '{}'))
                        )
                    result['success'] = True
                except Exception as e:
                    logger.error('update policy failed: %s',str(e))
                    result['info'] = 'update policy failed:' + str(e)              
            else:
                result['info'] = '未找到策略'
    if request.method == 'DELETE':
        if user['role'] == 5:
            policy = Policy.get(uuid=uuid, status=1)
        else:
            policy = Policy.get(uuid=uuid, user=user['name'], status=1)
        if policy:
            try:
                for f in policy.request_filters:
                    logger.error('********** filter_id **** %s', f.id)
                    f.delete()
                for f in policy.response_filters:
                    logger.error('********** filter_id **** %s', f.id)
                    f.delete()
                policy.delete()
                result['success'] = True
            except Exception as e:
                logger.error('delete policy failed: %s', str(e))
                result['info'] = 'delete policy failed:' + str(e)            
        else:
            result['info'] = '未找到策略'
    return jsonify(result)
    
@app.route('/waf/api/PolicyRules', methods=['GET'])
@sso.require_login
def policy_rules_action(user):
    result = {'success': False}
    try:
        stage = request.args.get('stage', None)
        rules = WafRules.get_all(status=1, stage=stage)
        rule_list = [ item.to_dict() for item in rules ]
        result['success'] = True
        result['data'] = rule_list
    except Exception as e:
        logger.error('get rules failed: %s', str(e))
        result['info'] = 'get rules failed:' + str(e) 
    return jsonify(result)