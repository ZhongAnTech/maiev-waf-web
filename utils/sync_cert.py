#!/usr/bin/env python
# encoding: utf-8
from datetime import datetime, timedelta
from modules import Cluster, Web, Cert, Server
from utils.salt import asyn_salt
from utils.templet import Assemble


class CertHandler(object):

    @classmethod
    def update_cert(cls, cert_nid, user):
        """
            证书同步更新,每个集群找到其中一个域名配置下发，自动更新证书
        """
        clusters = Cluster.get_all()
        for clu_ in clusters:
            web_ = Web.get(cert=cert_nid, cluster=clu_.nid,
                           status=1, web_status=1)
            if web_:
                asyn_salt(clu_nid=clu_.nid, op='web_edit',
                          nid=web_.nid, user=user['nid'])

    @classmethod
    def sync_conf_files(cls, cluster, user):
        """
            同步域名配置文件和对应的证书，未使用的证书
            配置新域名下发时，证书自动同步
        """
        webs = Web.get_all(cluster=cluster.nid,
                           status=1, web_status=1)
        for web_ in webs:
            asyn_salt(clu_nid=cluster.nid, op='web_edit',
                      nid=web_.nid, user=user['nid'])

    @classmethod
    def sync_certs(cls, cluster, user):
        """
            新增集群，同步所有证书
        """
        web_data = []
        certs = Cert.get_all()
        for cert_ in certs:
            web = make_web(cert_, cluster, user)
            make_server(cluster, web, user)
            web_data.append(web)
            Assemble(web.nid).ngx_file()
            asyn_salt(clu_nid=cluster.nid, op='web_edit',
                      nid=web.nid, user=user['nid'])
        for web_ in web_data:
            web_.update(status=-1)

    @classmethod
    def delete_test_conf(cls, clu_nid, user):
        """
            删除所有测试配置文件
        """
        cert = Cert.get()
        name = cert.nid[:8] + cert.name[1:]
        web = Web.get(cluster=clu_nid, name=name)
        if web:
            certs = Cert.get_all()
            for cert_ in certs:
                name = cert_.nid[:8] + cert_.name[1:]
                web = Web.get(cluster=clu_nid, name=name)
                # 删除waf测试配置文件
                web.update(status=1, web_status=-1)
                asyn_salt(clu_nid=clu_nid, op='web_stop',
                          nid=web.nid, user=user['nid'])
                # 删除数据库测试数据
                servers = Server.get_all(web=web.nid)
                for ser_ in servers:
                    ser_.delete()
                web.delete()

    @classmethod
    def check_expire(cls):
        """
            检查证书过期时间
        """
        now_time = datetime.now()
        certs = Cert.get_all()
        expire_certs = []
        for cert_ in certs:
            # 证书过期时间提前三个月提醒
            if (cert_.expire - timedelta(weeks=4*3)) < now_time:
                expire_certs.append(cert_)
        return expire_certs


def make_web(cert_, cluster, user):
    name = cert_.nid[:8] + cert_.name[1:]
    return Web(
            cluster_id=cluster.id,
            cluster=cluster.nid,
            conf_type='',
            https_trans=0,
            https_port=443,
            http_port=80,
            https=1,
            http=1,
            name=name,
            user=user['nid'],
            mark='test',
            # conf_file='',
            cert=cert_.nid
        ).create()


def make_server(cluster, web, user):
    Server(
        cluster=cluster.nid,
        web=web.nid,
        web_id=web.id,
        site_name=web.name,
        user=user['nid'],
        seq=0,
        proxy_service=','.join(['127.0.0.1:8080']),
        location_pattern='/',
        location_url='',
        rewrite_flag='nowrite',
        rewrite_matches='',
        rewrite_pattern='',
        websocket=0,
        slb_alg=0,
        http_back=1
    ).create()
