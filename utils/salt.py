# -*- coding:utf-8 -*-

import threading
import requests
import base64
import json
from modules import Web, Cluster, Cert, Msg, Policy, WhiteList
from datetime import datetime, timedelta
from utils.tools import ts2date
from utils.log import log_setting
from config import  SPAN_TIME


class SaltClient:

    def __init__(self, clu_nid):
        self.cluster = None
        self.salt_token = None
        self.logger = log_setting("salt_client")
        self.login_url = None
        self.action_url = None
        self.username = None
        self.password = None
        self.minion = None
        self.eauth = 'pam'
        self.verify = False
        self.ssl_dir = '/alidata1/conf/tengine/ssl/'
        self.site_dir = '/alidata1/conf/tengine/vhost/'
        self.waf_conf_path = '/alidata1/app/aegis_waf_iv/config.json'
        self.ngx_path = '/alidata1/app/tengine/sbin/nginx'
        self.load_data(clu_nid)

    def load_data(self, clu_nid):
        self.cluster = Cluster.get(nid=clu_nid)
        if self.cluster:
            self.salt_token = self.cluster.salt_token
            self.action_url = self.cluster.salt_api
            self.login_url = self.action_url + '/login'
            self.username = self.cluster.salt_user
            self.password = self.cluster.salt_pass
            self.minion = self.cluster.ngxhost
            if self.cluster.salt_eauth:
                self.eauth = self.cluster.salt_eauth
            if self.cluster.site_dir:
                self.site_dir = self.cluster.site_dir
            if self.cluster.waf_conf_path:
                self.waf_conf_path = self.cluster.waf_conf_path
            if self.cluster.ssl_dir:
                self.ssl_dir = self.cluster.ssl_dir
            if self.cluster.ngx_path:
                self.ngx_path = self.cluster.ngx_path

    def login(self):
        if not self.salt_token:
            login_res = self.login_post()
        elif self.cluster.salt_expire_time < (datetime.now() - timedelta(minutes=5)):
            login_res = self.login_post()
        else:
            login_res = True
        return login_res

    def test_login_post(self, salt_api, username, password, eauth):
        data = {
            "username": username,
            "password": password,
            "eauth": eauth
        }
        try:
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json; charset=UTF-8',
                'User-Agent': 'py-saltclient'
            }
            res = requests.post(salt_api + '/login', json=data,
                                headers=headers, verify=self.verify).json()

            if res:
                login_result = res["return"][0]
                self.salt_token = login_result.get("token")
                self.cluster = self.cluster.update(
                    salt_token=self.salt_token,
                    salt_start_time=ts2date(login_result.get("start")),
                    salt_expire_time=ts2date(login_result.get("expire"))
                )
                return True
        except Exception, e:
            self.logger.error("login salt_api failed:%s", e)
        # return self.post_func(data)

    def login_post(self):
        data = {
            "username": self.username,
            "password": self.password,
            "eauth": self.eauth
        }
        return self.post_func(data)

    def post_func(self, data):
        try:
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json; charset=UTF-8',
                'User-Agent': 'py-saltclient'
            }
            res = requests.post(self.login_url, json=data, headers=headers, verify=self.verify).json()

            if res:
                login_result = res["return"][0]
                self.salt_token = login_result.get("token")
                self.cluster = self.cluster.update(
                    salt_token=self.salt_token,
                    salt_start_time=ts2date(login_result.get("start")),
                    salt_expire_time=ts2date(login_result.get("expire"))
                )
                return True
        except Exception, e:
            self.logger.error("login salt_api failed:%s", e)

    def call_api(self, data, last=False):
        res = None
        if self.login():
            try:
                headers = {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json; charset=UTF-8',
                    'X-Auth-Token': self.salt_token
                }
                print "--------------------------------------"
                print data
                print "--------------------------------------"
                response = requests.post(self.action_url, json=data, headers=headers, verify=self.verify)
                print "response:", response.text
                print "response status:", response.status_code
                if response.status_code == 401 and not last:
                    self.cluster.update(salt_token=None)
                    self.salt_token = None
                    res = self.call_api(data=data, last=True)
                else:
                    self.logger.info("call_api response:%s", response.text)
                    return response.text
            except Exception, e:
                self.logger.error("call_api failed:%s", e)
        else:
            self.logger.error("call_api failed: login salt_api failed")
        return res

    def push_conf(self, op, nid, user):
        result = {'suc': [], 'fail': []}
        arg_data = {}
        if op in ['web_edit', 'web_add', 'web_stop', 'web_del']:
            web = Web.get(nid=nid)
            if (web.status == -1)or(web.web_status == -1):
                status = -1
            else:
                status = 1
            arg_data = {
                'op': op,
                'web': web.name,
                'nid': web.nid,
                'status': status,
                'nginx_file': base64.b64encode(web.conf_file),
                'site_dir': self.site_dir,
                'cert_nid': web.cert,
                'ssl_dir': self.ssl_dir,
                'ssl_key_file': None,
                'ssl_cert_file': None
            }
            if web.cert:
                cert = Cert.get(nid=web.cert)
                if cert:
                    arg_data['ssl_key_file'] = base64.b64encode(cert.keys)
                    arg_data['ssl_cert_file'] = base64.b64encode(cert.cert)
            self.logger.error(json.dumps(arg_data))
        if op == 'waf_conf':
            web = Web.get(nid=nid, status=1)
            if web:
                arg_data = {
                    'op': op,
                    'nid': web.nid,
                    'web': web.name,
                    'waf_file': self.waf_cluster_data(self.cluster.nid),
                    'waf_conf_path': self.waf_conf_path
                }

        if op == 'reload':
            arg_data = {
                'op': op,
                'nid': nid
            }

        if op in ['rules', 'white_list', 'policy']:
            arg_data = {
                'op': op,
                'nid': nid,
                'waf_file': self.waf_cluster_data(nid),
                'waf_conf_path': self.waf_conf_path
            }
        arg_data['ngx_path'] = self.ngx_path
        arg_data['reload_time'] = None
        now_time = datetime.now()
        if not self.cluster.reload_time:
            self.cluster.update(reload_time=now_time)
        else:
            time_span = (now_time-self.cluster.reload_time).total_seconds()
            if time_span >= SPAN_TIME:
                self.cluster.update(reload_time=now_time)
            elif (time_span < SPAN_TIME) & (time_span >= 0):
                time_reload = SPAN_TIME-time_span
                arg_data['reload_time'] = time_reload
                # reload的时间
                reload_time = now_time + timedelta(seconds=time_reload)
                self.cluster.update(reload_time=reload_time)
            elif time_span < 0:
                arg_data['reload_time'] = time_span
        if self.minion:
            for host in self.minion.split(','):
                try:
                    data = {
                        'client': 'local',
                        'tgt': host,
                        'fun': 'waf.run',
                        'arg': arg_data
                    }
                    res = self.call_api(data)
                    res = json.loads(res)
                    res = res['return'][0][host]
                    if type(res) == dict:
                        if res.get('success'):
                            if res.get('info') == "":
                                res['info'] = "nginx reload success"
                            result['suc'].append({host: res.get('info')})
                        else:
                            result['fail'].append({host: res.get('info')})
                    else:
                        result['fail'].append({host: res})
                except Exception as e:
                    self.logger.error("call_api failed:%s", e)
                    result['fail'].append({host: "call_api failed "+str(e)})
            Msg(genre=op, content=json.dumps(result), web=nid, user=user).create()
            if op in ['web_stop', 'web_del', 'web_add']:
                w_del = Web.get(nid=nid)
                if w_del:
                    if result.get('fail'):
                        if op == 'web_stop':
                            w_del.update(web_status=1)
                        if op == 'web_del':
                            w_del.update(status=1)
                        if op == 'web_add':
                            w_del.update(web_status=1)
        return result

    def waf_cluster_data(self, nid):
        result = {
            "datas": [], 
            "rules": {}, 
            "clu_nid": nid,
            "message": "", 
            "code": 500, 
            "hash": "", 
            "version": "4.0"
        }
        # 组装白名单数据
        white_data = []
        whites = []
        for wt in self.cluster.white.all():
            if (wt.status == 1) and (wt.w_rule_status == 1):
                whites.append(wt)
        for www in WhiteList.get_all(status=1, w_rule_status=1):
            if not www.cluster.all():
                whites.append(www)
        for w in whites:
            try:
                w_data = json.loads(w.w_rule)
                for a in w_data:
                    if w_data[a]:
                        white_data.append({a: w_data[a]})
            except Exception as e:
                self.logger.error('WhiteList append error: %s' % str(e))
        for web in self.cluster.webs:
            #try:
            if web.status == 1:                     
                defend_custom_policy = web.defend_custom_policy
                if not web.defend_custom:
                    defend_custom_policy = None
                filters_rules = self.get_filters_and_rules(
                    base_policy_uuid=web.defend_web_policy,
                    custom_policy_uuid=defend_custom_policy)
                web_policy = {
                    "data": {
                        "black_mode": web.defend_blacklist,
                        "waf_mode": web.defend_web,
                        "cc_mode": web.defend_cc,
                        "cc_max": web.defend_cc_policy1,
                        "cc_period": web.defend_cc_policy2,
                        "white_list": white_data,
                    },
                    "site_name": web.name,
                    "nid": web.nid
                }
                web_policy['data'].update(filters_rules['config'])
                web_policy['data']['filters'] = filters_rules['request_filters']
                web_policy['data']['body_filters'] = filters_rules['response_filters']
                web_policy['data']['header_filters'] = filters_rules['response_header_filters']
                result['rules'].update(filters_rules['rules'])
                result['datas'].append(web_policy)
            #except Exception as e:
                #self.logger.error('waf data append error: %s' % str(e))
        self.logger.error(json.dumps(result))
        result["code"] = 200
        return result        

    def get_filters_and_rules(self, base_policy_uuid, custom_policy_uuid=None):
        result = {
            'rules': {},
            'config': {},
            'request_filters': [],
            'response_filters': [],
            'response_header_filters': []
        }
        base_policy = Policy.get(status=1, policy_status=1, uuid=base_policy_uuid)
        if not base_policy:
            return result
        result['config'] = {
            'upload_file_access': base_policy.upload_file_access,
            'request_body_access': base_policy.request_body_access,
            'request_body_limit': base_policy.request_body_limit,
            'request_body_nofile_limit': base_policy.request_body_nofile_limit,
            'response_body_access': base_policy.response_body_access,
            'response_body_mime_type': base_policy.response_body_mime_type,
            'response_body_limit': base_policy.response_body_limit
        }

        # 组装request filter
        for f in base_policy.request_filters:
            rq = {
                'rule_id': str(f.rule_id),
                'mode': 1,
                'action': f.rule_action,
                'action_vars': json.loads(f.action_vars)
            }
            if rq['action'] == 'DEFAULT':
                rq['action'] = base_policy.action
                rq['action_vars'] = json.loads(base_policy.action_vars)
            result['request_filters'].append(rq)
            if not result['rules'].has_key(f.rule_id):
                waf_rule = f.rule
                match = json.loads(waf_rule.f_rule if waf_rule.f_rule else [])
                for item in match:
                    if item['operator'] == 'CTN' or item['operator'] == 'NCT':
                        item['value'] = item['value'].split(',')
                rule = {
                    'rule_name': waf_rule.f_rule_name,
                    'attack_tag': waf_rule.tags if waf_rule.tags else '',
                    'risk_level': waf_rule.risk_level if waf_rule.risk_level else 1,
                    'id': str(waf_rule.id),
                    'match': match,
                    'desc': waf_rule.f_rule_desc if waf_rule.f_rule_desc else ''
                }
                result['rules'][f.rule_id] = rule
        # 组装response (body) filter
        for f in base_policy.response_filters:
            rp = {
                'rule_id': str(f.rule_id),
                'mode': 1,
                'action': f.rule_action,
                'action_vars': json.loads(f.action_vars)
            }
            result['response_filters'].append(rp)
            if not result['rules'].has_key(f.rule_id):
                waf_rule = f.rule
                match = json.loads(waf_rule.f_rule if waf_rule.f_rule else [])
                for item in match:
                    if item['operator'] == 'CTN' or item['operator'] == 'NCT':
                        item['value'] = item['value'].split(',')
                rule = {
                    'rule_name': waf_rule.f_rule_name,
                    'attack_tag': waf_rule.tags if waf_rule.tags else '',
                    'risk_level': waf_rule.risk_level if waf_rule.risk_level else 1,
                    'id': str(waf_rule.id),
                    'match': match,
                    'desc': waf_rule.f_rule_desc if waf_rule.f_rule_desc else ''
                }
                result['rules'][f.rule_id] = rule

        # 组装response header filter
        for f in base_policy.response_header_filters:
            rph = {
                'rule_id': str(f.rule_id),
                'mode': 1,
                'action': f.rule_action,
                'action_vars': json.loads(f.action_vars)
            }
            result['response_header_filters'].append(rph)
            if not result['rules'].has_key(f.rule_id):
                waf_rule = f.rule
                match = json.loads(waf_rule.f_rule if waf_rule.f_rule else [])
                for item in match:
                    if item['operator'] == 'CTN' or item['operator'] == 'NCT':
                        item['value'] = item['value'].split(',')
                rule = {
                    'rule_name': waf_rule.f_rule_name,
                    'attack_tag': waf_rule.tags if waf_rule.tags else '',
                    'risk_level': waf_rule.risk_level if waf_rule.risk_level else 1,
                    'id': str(waf_rule.id),
                    'match': match,
                    'desc': waf_rule.f_rule_desc if waf_rule.f_rule_desc else ''
                }
                result['rules'][f.rule_id] = rule

        if custom_policy_uuid:
            custom_policy = Policy.get(status=1, policy_status=1, uuid=custom_policy_uuid)
            result['config'] = {
                'upload_file_access': custom_policy.upload_file_access,
                'request_body_access': custom_policy.request_body_access,
                'request_body_limit': custom_policy.request_body_limit,
                'request_body_nofile_limit': custom_policy.request_body_nofile_limit,
                'response_body_access': custom_policy.response_body_access,
                'response_body_mime_type': custom_policy.response_body_mime_type,
                'response_body_limit': custom_policy.response_body_limit
            }
            for f in custom_policy.request_filters:
                rq = {
                    'rule_id': str(f.rule_id),
                    'mode': 1,
                    'action': f.rule_action,
                    'action_vars': json.loads(f.action_vars)
                }
                if rq['action'] == 'DEFAULT':
                    rq['action'] = base_policy.action
                    rq['action_vars'] = json.loads(base_policy.action_vars)
                for rf in result['request_filters']:
                    if rf['rule_id'] == rq['rule_id']:
                        del rf
                result['request_filters'].append(rq)
                if not result['rules'].has_key(f.rule_id):
                    waf_rule = f.rule
                    match = json.loads(waf_rule.f_rule if waf_rule.f_rule else [])
                    for item in match:
                        if item['operator'] == 'CTN' or item['operator'] == 'NCT':
                            item['value'] = item['value'].split(',')
                    rule = {
                        'rule_name': waf_rule.f_rule_name,
                        'attack_tag': waf_rule.tags if waf_rule.tags else '',
                        'risk_level': waf_rule.risk_level if waf_rule.risk_level else 1,
                        'id': str(waf_rule.id),
                        'match': match,
                        'desc': waf_rule.f_rule_desc if waf_rule.f_rule_desc else ''
                    }
                    result['rules'][f.rule_id] = rule
            for f in custom_policy.response_filters:
                rp = {
                    'rule_id': str(f.rule_id),
                    'mode': 1,
                    'action': f.rule_action,
                    'action_vars': json.loads(f.action_vars)
                }
                for rf in result['response_filters']:
                    if rf['rule_id'] == rp['rule_id']:
                        del rf
                result['response_filters'].append(rp)
                if not result['rules'].has_key(f.rule_id):
                    waf_rule = f.rule
                    match = json.loads(waf_rule.f_rule if waf_rule.f_rule else [])
                    for item in match:
                        if item['operator'] == 'CTN' or item['operator'] == 'NCT':
                            item['value'] = item['value'].split(',')
                    rule = {
                        'rule_name': waf_rule.f_rule_name,
                        'attack_tag': waf_rule.tags if waf_rule.tags else '',
                        'risk_level': waf_rule.risk_level if waf_rule.risk_level else 1,
                        'id': str(waf_rule.id),
                        'match': match,
                        'desc': waf_rule.f_rule_desc if waf_rule.f_rule_desc else ''
                    }
                    result['rules'][f.rule_id] = rule
            # 组装response header filter
            for f in custom_policy.response_header_filters:
                rph = {
                    'rule_id': str(f.rule_id),
                    'mode': 1,
                    'action': f.rule_action,
                    'action_vars': json.loads(f.action_vars)
                }
                for rf in result['response_header_filters']:
                    if rf['rule_id'] == rph['rule_id']:
                        del rf
                result['response_header_filters'].append(rph)
                if not result['rules'].has_key(f.rule_id):
                    waf_rule = f.rule
                    match = json.loads(waf_rule.f_rule if waf_rule.f_rule else [])
                    for item in match:
                        if item['operator'] == 'CTN' or item['operator'] == 'NCT':
                            item['value'] = item['value'].split(',')
                    rule = {
                        'rule_name': waf_rule.f_rule_name,
                        'attack_tag': waf_rule.tags if waf_rule.tags else '',
                        'risk_level': waf_rule.risk_level if waf_rule.risk_level else 1,
                        'id': str(waf_rule.id),
                        'match': match,
                        'desc': waf_rule.f_rule_desc if waf_rule.f_rule_desc else ''
                    }
                    result['rules'][f.rule_id] = rule

        return result
    
    def waf_file_cluster(self, nid):
        result = {
            "datas": [], "policy_data": {}, "clu_nid": nid,
            "message": "", "code": 500, "hash": "", "version": "1.1"
        }
        # 组装白名单数据
        white_data = []
        whites = []
        for wt in self.cluster.white.all():
            if (wt.status == 1) and (wt.w_rule_status == 1):
                whites.append(wt)
        for www in WhiteList.get_all(status=1, w_rule_status=1):
            if not www.cluster.all():
                whites.append(www)
        for w in whites:
            try:
                w_data = json.loads(w.w_rule)
                for a in w_data:
                    if w_data[a]:
                        white_data.append({a: w_data[a]})
            except Exception as e:
                self.logger.error('WhiteList append error: %s' % str(e))

        # 组装集群web数据
        policise = []
        # Rules
        rules = {}
        for web in self.cluster.webs:
            try:
                if web.status == 1:
                    result['datas'].append({
                        "data": {
                            "black_mode": web.defend_blacklist,
                            "waf_mode": web.defend_web,
                            "cc_mode": web.defend_cc,
                            "cc_max": web.defend_cc_policy1,
                            "cc_period": web.defend_cc_policy2,
                            "white_list": white_data,
                            "filters": [web.defend_web_policy, web.defend_custom_policy],
                        },
                        "site_name": web.name,
                        "nid": web.nid
                    })
                    policise.extend([web.defend_web_policy, web.defend_custom_policy])
            except Exception as e:
                self.logger.error('waf data append error: %s' % str(e))
        policise = list(set(policise))

        # 组装策略
        for p in policise:
            policy = Policy.get(status=1, policy_status=1, uuid=p)
            if policy:
                policy_datas = []
                for f in policy.rules.all():
                    if (f.status == 1) and (f.f_rule_status == 1):
                        try:
                            match = json.loads(f.f_rule if f.f_rule else {})
                            for m in match:
                                if m.get("operator") == "contain" or m.get("operator") == "!contain":
                                    m["value"] = m["value"].split(",")
                            policy_datas.append({
                                "action": policy.action,
                                "action_vars": json.loads(policy.action_vars if policy.action_vars else {}),
                                "mode": policy.mode,
                                "rule": {
                                    "attack_tag": f.tags if f.tags else "",
                                    "risk_level": f.risk_level if f.risk_level else 1,
                                    "id": str(f.id),
                                    "match": match,
                                    "desc": f.f_rule_desc if f.f_rule_desc else ""
                                },
                                "rule_id": str(f.id)
                            })
                        except Exception as e:
                            self.logger.error('web waf filters append error: %s' % str(e))
                result['policy_data'][policy.nid] = policy_datas
        result["code"] = 200
        return result


def sss(clu_nid, op, nid, user):
    SaltClient(clu_nid).push_conf(op, nid, user)


def asyn_salt(clu_nid, op, nid, user):
    t = threading.Thread(target=sss, args=(clu_nid, op, nid, user))
    t.start()
