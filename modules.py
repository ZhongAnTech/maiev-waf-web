# -*- coding: utf-8 -*-

import json
import hashlib
import sys
import datetime as dt
from datetime import datetime
from app import db
from config import ENV, ERROR_COUNT, AUTH_SPAN_TIME
from utils.log import log_setting
from utils.tools import get_key, get_hash, get_uuid
from sqlalchemy import or_
from base_models import CompatibleModel
reload(sys)
sys.setdefaultencoding('utf-8')

logger = log_setting(app_name="aegis_waf_4.0_mysql")


cluster_admin = db.Table(
    'cluster_admin', db.Model.metadata,
    db.Column('cluster_id', db.Integer, db.ForeignKey('cluster.id')),
    db.Column('admin_id', db.Integer, db.ForeignKey('admin.id')),
    db.Column('id', db.Integer, primary_key=True)
)


cluster_white = db.Table(
    'cluster_white', db.Model.metadata,
    db.Column('cluster_id', db.Integer, db.ForeignKey('cluster.id')),
    db.Column('white_id', db.Integer, db.ForeignKey('white_list.id')),
    db.Column('id', db.Integer, primary_key=True)
)


class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nid = db.Column(db.String(64))
    userId = db.Column(db.Integer)
    name = db.Column(db.String(64))
    originator = db.Column(db.String(64))
    username = db.Column(db.String(64))
    password = db.Column(db.String(64))
    email = db.Column(db.String(64))
    no = db.Column(db.String(64))
    phone = db.Column(db.String(64))
    gmt_created = db.Column(db.DateTime)
    gmt_modified = db.Column(db.DateTime)
    role = db.Column(db.Integer)
    origin = db.Column(db.String(64))
    status = db.Column(db.Integer)
    webs = db.relationship('Web')
    clusters = db.relationship('Cluster', secondary=cluster_admin,
                               backref=db.backref('admins', lazy='dynamic'), lazy='dynamic')
    # 记录登录失败
    error_count = db.Column(db.Integer)
    login_time = db.Column(db.DateTime)

    def record_auth(self):
        # 密码验证错误处理
        kwargs = {}
        if self.error_count:
            if self.error_count >= ERROR_COUNT:
                kwargs['login_time'] = datetime.utcnow()
                kwargs['error_count'] = 0
            else:
                kwargs['error_count'] = self.error_count + 1
        else:
            kwargs['error_count'] = 1
        return self._update(**kwargs)

    def auth_status(self):
        if self.login_time:
            if datetime.utcnow() > (self.login_time + dt.timedelta(minutes=AUTH_SPAN_TIME)):
                return True
        else:
            return True

    def auth_pass(self):
        kwargs = {'error_count': 0, 'login_time': None}
        return self._update(**kwargs)

    def save(self):
        try:
            self.password = hashlib.md5(str(self.password).encode('utf-8')).hexdigest()
            if self.origin == "anlink":
                self.role = 1
            db.session.add(self)
            db.session.commit()
            return self
        except Exception as e:
            db.session.rollback()
            logger.error('save Admin error: %s' % str(e))

    def check_password(self, password):
        if self.password == hashlib.md5(str(password).encode('utf-8')).hexdigest():
            return True
        else:
            return False

    def create(self):
        self.status = 1
        self.gmt_modified = self.gmt_created = datetime.now()
        self.nid = get_key()
        return self.save()

    def edit(self, d):
        self.gmt_modified = datetime.now()
        if type(d) == dict:
            for key in d:
                if key in ["username", "password", "role"]:
                    setattr(self, key, d[key])
                if key == 'clusters':
                    clusters_d = []
                    if d['clusters']:
                        for c in d['clusters']:
                            print c
                            cluster = Cluster.get(status=1, nid=c)
                            if cluster:
                                clusters_d.append(cluster)
                    self.clusters = clusters_d
        return self.save()

    def _update(self, **kwargs):
        self.gmt_modified = datetime.now()
        for key in kwargs:
            setattr(self, key, kwargs[key])
        db.session.add(self)
        db.session.commit()
        return self

    def update(self, **kwargs):
        self.gmt_modified = datetime.now()
        for key in kwargs:
            setattr(self, key, kwargs[key])
        return self.save()

    @classmethod
    def get(cls, **kwargs):
        return cls.query.filter_by(**kwargs).first()

    @classmethod
    def get_all(cls, **kwargs):
        return cls.query.filter_by(**kwargs).all()

    @classmethod
    def get_page(cls, page, size, search):
        if search:
            return cls.query.filter(
                cls.status == 1,
                cls.username.like('%' + search + '%')
            ).order_by(cls.gmt_modified.desc()).paginate(page, size, error_out=False)
        return cls.query.filter(
            cls.status == 1
        ).order_by(cls.gmt_modified.desc()).paginate(page, size, error_out=False)


class Web(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nid = db.Column(db.String(64), unique=True)
    user = db.Column(db.String(64))
    name = db.Column(db.String(256))
    https_trans = db.Column(db.Integer)
    https = db.Column(db.Integer)
    http = db.Column(db.Integer)
    https_port = db.Column(db.String(256))
    http_port = db.Column(db.String(256))
    cert = db.Column(db.String(64))
    conf_file = db.Column(db.TEXT)
    waf_file = db.Column(db.TEXT)
    cluster = db.Column(db.String(64))
    conf_type = db.Column(db.String(64))
    env = db.Column(db.String(64))
    cname = db.Column(db.String(256))
    net_env = db.Column(db.Integer)
    origin = db.Column(db.String(64))  # 记录cong_file的hash值
    mark = db.Column(db.String(512))
    gmt_created = db.Column(db.DateTime)
    gmt_modified = db.Column(db.DateTime)
    web_status = db.Column(db.Integer)
    defend_web = db.Column(db.Integer)
    defend_cc = db.Column(db.Integer)
    defend_blacklist = db.Column(db.Integer)
    defend_custom = db.Column(db.Integer)
    defend_web_policy = db.Column(db.String(256))
    defend_cc_policy = db.Column(db.String(256))
    defend_cc_policy1 = db.Column(db.Integer)
    defend_cc_policy2 = db.Column(db.Integer)
    defend_blacklist_policy = db.Column(db.String(256))
    defend_blacklist_policy1 = db.Column(db.String(256))
    defend_blacklist_policy2 = db.Column(db.String(256))
    defend_blacklist_policy3 = db.Column(db.String(256))
    defend_custom_policy = db.Column(db.String(256))
    token = db.Column(db.String(64))
    status = db.Column(db.Integer)
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'))
    cluster_id = db.Column(db.Integer, db.ForeignKey('cluster.id'))
    cert_id = db.Column(db.Integer, db.ForeignKey('cert.id'))
    servers = db.relationship('Server')
    certs = db.relationship('Cert')
    clusters = db.relationship('Cluster')

    def save(self):
        try:
            db.session.add(self)
            db.session.commit()
            return self
        except Exception as e:
            db.session.rollback()
            logger.error('save Web error: %s' % str(e))

    def create(self):
        # 域名集群唯一
        if self.get(status=1, name=self.name, cluster=self.cluster):
            logger.error('该集群上站点域名记录已经存在')
            raise Exception('该集群上站点域名记录已经存在')
        self.gmt_modified = self.gmt_created = datetime.now()
        self.nid = get_key()
        self.token = get_key()
        self.status = 1
        self.web_status = 1
        self.defend_web = -1
        self.defend_cc = 1
        self.defend_blacklist = 1
        self.defend_custom = -1
        self.defend_cc_policy1 = 1000000
        self.defend_cc_policy2 = 5
        self.conf_type = 'professional'  # 默认显示标准配置
        return self.save()

    def update(self, **kwargs):
        self.gmt_modified = datetime.now()
        for key in kwargs:
            setattr(self, key, kwargs[key])
        return self.save()

    def to_dict(self):
        resp_dict = {
            'nid': self.nid,
            'name': self.name,
            'cname': self.cname,
            'https': self.https,
            'http': self.http,
            'cluster': self.cluster,
            'https_trans': self.https_trans,
            'defend_web_policy': self.defend_web_policy,
            'defend_cc_count': self.defend_cc_policy1,
            'defend_cc_time': self.defend_cc_policy2,
            'defend_custom_policy': self.defend_custom_policy,
            'defend_custom': self.defend_custom,
            'defend_web': self.defend_web,
            'defend_cc': self.defend_cc,
            'defend_blacklist': self.defend_blacklist,
            'http_port': self.http_port.split(','),
            'https_port': self.https_port.split(','),
            'status': self.web_status,
            'conf_type': self.conf_type,
            'conf_file': self.conf_file,
            'mark': self.mark,
            'cert': self.cert,
        }
        return resp_dict

    @classmethod
    def get(cls, **kwargs):
        return cls.query.filter_by(**kwargs).first()

    @classmethod
    def get_like(cls, search):
        return cls.query.filter(
            cls.name.like('%' + search),
            cls.status == 1,
            cls.web_status == 1
        ).all()

    @classmethod
    def get_all(cls, **kwargs):
        return cls.query.filter_by(**kwargs).all()

    @classmethod
    def get_policy(cls, nid):
        return cls.query.filter(
            or_(cls.defend_web_policy == nid, cls.defend_custom_policy == nid),
            cls.status == 1
        ).group_by(cls.cluster)
    
    # @classmethod
    # def get_policy_clusters(cls, uuid):
    #     return cls.query(cls.cluster).filter(or_(cls.defend_web_policy == nid, cls.defend_custom_policy == nid),
    #         cls.status == 1).group_by(cls.cluster)

    @classmethod
    def get_pages(cls, offset, limit, search, clu, user):
        if user == "admin":
            if search:
                return cls.query.filter(
                    cls.status == 1,
                    cls.cluster == clu,
                    cls.name.like('%' + search + '%')
                ).order_by(cls.id.desc()).limit(limit).offset(offset)
            return cls.query.filter(
                cls.status == 1,
                cls.cluster == clu,
            ).order_by(cls.id.desc()).limit(limit).offset(offset)
        else:
            if search:
                return cls.query.filter(
                    cls.status == 1,
                    cls.cluster == clu,
                    cls.user == user,
                    cls.name.like('%' + search + '%')
                ).order_by(cls.id.desc()).limit(limit).offset(offset)
            return cls.query.filter(
                cls.status == 1,
                cls.cluster == clu,
                cls.user == user
            ).order_by(cls.id.desc()).limit(limit).offset(offset)

    @classmethod
    def get_page(cls, page, size, search, clu, role, nid):
        if search:
            return cls.query.filter(
                cls.status == 1,
                cls.cluster == clu,
                cls.name.like('%' + search + '%')
            ).order_by(cls.gmt_modified.desc()).paginate(page, size, error_out=False)
        return cls.query.filter(
            cls.status == 1,
            cls.cluster == clu,
        ).order_by(cls.gmt_modified.desc()).paginate(page, size, error_out=False)

    @classmethod
    def get_certs(cls, user):
        return db.session.query(cls.cert_name, cls.cert, cls.keys).filter(
            cls.user == user,
            cls.status == 1
        ).distinct().all()

    def edit(self, d):
        self.gmt_modified = datetime.now()
        if type(d) == dict:
            for key in d:
                if key in ["server", "https", "http", "web_status", "status", "defend_web", "defend_cc"]:
                    setattr(self, key, d[key])
        return self.save()

    @classmethod
    def update_origin(cls):
        webs = cls.query.all()
        for web_ in webs:
            if not web_.origin:
                web_.origin = get_hash(web_.conf_file)
        db.session.commit()

    def delete(self):
        try:
            db.session.delete(self)
            db.session.commit()
            return self
        except Exception as e:
            db.session.rollback()
            logger.error('delete Web error: %s' % str(e))


class Server(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nid = db.Column(db.String(64))
    web = db.Column(db.String(64))
    name = db.Column(db.String(64))
    site_name = db.Column(db.String(256))
    cluster = db.Column(db.String(64))
    seq = db.Column(db.Integer)
    location_pattern = db.Column(db.String(64))
    location_url = db.Column(db.String(64))
    proxy_service = db.Column(db.String(2056))
    rewrite_flag = db.Column(db.String(64))
    rewrite_matches = db.Column(db.String(64))
    rewrite_pattern = db.Column(db.String(64))
    websocket = db.Column(db.Integer)
    slb_alg = db.Column(db.Integer)
    http_back = db.Column(db.Integer)
    user = db.Column(db.String(64))
    gmt_created = db.Column(db.DateTime)
    gmt_modified = db.Column(db.DateTime)
    status = db.Column(db.Integer)
    env = db.Column(db.String(64))
    net_env = db.Column(db.Integer)
    web_id = db.Column(db.Integer, db.ForeignKey('web.id'))

    def save(self):
        try:
            db.session.add(self)
            db.session.commit()
            return self
        except Exception as e:
            db.session.rollback()
            logger.error('save Server error: %s' % str(e))

    def create(self):
        self.gmt_modified = self.gmt_created = datetime.now()
        self.nid = get_key()
        self.status = 1
        return self.save()

    def update(self, **kwargs):
        self.gmt_modified = datetime.now()
        for key in kwargs:
            setattr(self, key, kwargs[key])
        return self.save()

    def to_dict(self):
        resp_dict = {
            'nid': self.nid,
            'name': self.name,
            'cluster': self.cluster,
            'order': self.seq,
            'location_pattern': self.location_pattern,
            'location_url': self.location_url,
            'proxy_service': self.proxy_service.split(','),
            'rewrite_flag': self.rewrite_flag,
            'rewrite_matches': self.rewrite_matches,
            'rewrite_pattern': self.rewrite_pattern,
            'websocket': self.websocket,
            'slb_alg': self.slb_alg,
            'http_back': self.http_back,
            'status': self.status,

        }
        return resp_dict

    @classmethod
    def get(cls, **kwargs):
        return cls.query.filter_by(**kwargs).first()

    @classmethod
    def get_all(cls, **kwargs):
        return cls.query.filter_by(**kwargs).all()

    def edit(self, d):
        self.gmt_modified = datetime.now()
        if d:
            for key in d:
                if key in ["name", "username", "email", "phone", "status"]:
                    setattr(self, key, d[key])
        return self.save()

    def delete(self):
        try:
            db.session.delete(self)
            db.session.commit()
            return self
        except Exception as e:
            db.session.rollback()
            logger.error('delete Server error: %s' % str(e))


class Cert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nid = db.Column(db.String(64))
    user = db.Column(db.String(64))
    name = db.Column(db.String(128))
    cert = db.Column(db.TEXT)
    keys = db.Column(db.TEXT)
    expire = db.Column(db.DateTime)
    start = db.Column(db.DateTime)
    issuer = db.Column(db.String(256))
    subject = db.Column(db.String(256))
    gmt_created = db.Column(db.DateTime)
    gmt_modified = db.Column(db.DateTime)
    status = db.Column(db.Integer)
    webs = db.relationship('Web', lazy='select')

    def save(self):
        try:
            db.session.add(self)
            db.session.commit()
            return self
        except Exception as e:
            db.session.rollback()
            logger.error('save Cert error: %s' % str(e))

    def create(self):
        self.status = 1
        self.gmt_modified = self.gmt_created = datetime.now()
        self.nid = get_key()
        return self.save()

    def update(self, **kwargs):
        self.gmt_modified = datetime.now()
        for key in kwargs:
            setattr(self, key, kwargs[key])
        return self.save()

    @classmethod
    def get(cls, **kwargs):
        return cls.query.filter_by(**kwargs).first()

    @classmethod
    def get_all(cls, **kwargs):
        return cls.query.filter_by(**kwargs).all()

    @classmethod
    def get_page(cls, page, size, role, nid):
        if role == 5:
            return cls.query.filter(
                cls.status == 1,
            ).order_by(cls.gmt_modified.desc()).paginate(page, size, error_out=False)
        else:
            return cls.query.filter(
                cls.status == 1,
                cls.user == nid
            ).order_by(cls.gmt_modified.desc()).paginate(page, size, error_out=False)


class Ngx(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nid = db.Column(db.String(64))
    name = db.Column(db.String(256))
    user = db.Column(db.String(64))
    host = db.Column(db.String(64))
    sid = db.Column(db.String(64))
    cluster = db.Column(db.String(64))
    ssl_dir = db.Column(db.String(512))
    site_dir = db.Column(db.String(512))
    ngx_path = db.Column(db.String(512))
    waf_conf_path = db.Column(db.String(512))
    waf_conf_file = db.Column(db.TEXT)
    ngx_conf_file = db.Column(db.TEXT)
    ngx_ctl_file = db.Column(db.TEXT)
    ngx_status = db.Column(db.Integer)
    reload_time = db.Column(db.DateTime)
    gmt_created = db.Column(db.DateTime)
    gmt_modified = db.Column(db.DateTime)
    cluster_id = db.Column(db.Integer, db.ForeignKey('cluster.id'))
    status = db.Column(db.Integer)

    def save(self):
        try:
            db.session.add(self)
            db.session.commit()
            return self
        except Exception as e:
            db.session.rollback()
            logger.error('save Ngx error: %s' % str(e))

    def create(self):
        self.gmt_modified = self.gmt_created = datetime.now()
        self.nid = get_key()
        self.status = 1
        self.ngx_status = 1
        return self.save()

    def update(self, **kwargs):
        self.gmt_modified = datetime.now()
        for key in kwargs:
            setattr(self, key, kwargs[key])
        return self.save()

    @classmethod
    def get(cls, **kwargs):
        return cls.query.filter_by(**kwargs).first()

    @classmethod
    def get_all(cls, **kwargs):
        return cls.query.filter_by(**kwargs).all()

    def edit(self, d):
        self.gmt_modified = datetime.now()
        if d:
            for key in d:
                if key in ["name", "username", "email", "phone", "status"]:
                    setattr(self, key, d[key])
        return self.save()

    def delete(self):
        try:
            db.session.delete(self)
            db.session.commit()
            return self
        except Exception as e:
            db.session.rollback()
            logger.error('delete Ngx error: %s' % str(e))


class Cluster(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nid = db.Column(db.String(64))
    name = db.Column(db.String(64))
    label = db.Column(db.String(256))
    cname = db.Column(db.String(256))
    env = db.Column(db.String(64))
    user = db.Column(db.String(64))
    net_env = db.Column(db.Integer)
    salt_api = db.Column(db.String(256))
    salt_user = db.Column(db.String(64))
    salt_pass = db.Column(db.String(64))
    salt_token = db.Column(db.String(64))
    salt_eauth = db.Column(db.String(64))
    salt_start_time = db.Column(db.DateTime)
    salt_expire_time = db.Column(db.DateTime)
    eshost = db.Column(db.String(1024))
    ngxhost = db.Column(db.String(1024))
    ssl_dir = db.Column(db.String(512))
    site_dir = db.Column(db.String(512))
    ngx_path = db.Column(db.String(512))
    waf_conf_path = db.Column(db.String(512))
    waf_conf_file = db.Column(db.TEXT)
    ngx_conf_file = db.Column(db.TEXT)
    ngx_ctl_file = db.Column(db.TEXT)
    clu_status = db.Column(db.Integer)
    gmt_created = db.Column(db.DateTime)
    gmt_modified = db.Column(db.DateTime)
    reload_time = db.Column(db.DateTime)
    status = db.Column(db.Integer)
    ngxs = db.relationship('Ngx', lazy='select')
    webs = db.relationship('Web', lazy='select')
    white = db.relationship('WhiteList', secondary=cluster_white,
                            backref=db.backref('clusterwhitess', lazy='dynamic'), lazy='dynamic')

    def save(self):
        try:
            db.session.add(self)
            db.session.commit()
            return self
        except Exception as e:
            db.session.rollback()
            logger.error('save Cluster error: %s' % str(e))

    def create(self):
        c_ = self.get(status=1)
        if c_:
            return c_
        self.status = 1
        self.gmt_modified = self.gmt_created = datetime.now()
        self.nid = get_key()
        return self.save()

    def update(self, **kwargs):
        self.gmt_modified = datetime.now()
        for key in kwargs:
            setattr(self, key, kwargs[key])
        return self.save()

    @classmethod
    def get(cls, **kwargs):
        return cls.query.filter_by(**kwargs).first()

    @classmethod
    def get_all(cls, **kwargs):
        return cls.query.filter_by(**kwargs).all()

    def edit(self, d):
        self.gmt_modified = datetime.now()
        if d:
            for key in d:
                if key in [
                    "label", "cname",
                   "salt_api", "salt_user", "salt_pass", "salt_eauth",
                   "eshost", "ngxhost",
                   "ngx_path", "ssl_dir", "waf_conf_path", "site_dir", "clu_status"]:
                    setattr(self, key, d[key])
        return self.save()

    def delete(self):
        try:
            db.session.delete(self)
            db.session.commit()
            return self
        except Exception as e:
            db.session.rollback()
            logger.error('delete Cluster error: %s' % str(e))


class WhiteList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nid = db.Column(db.String(64))
    w_rule_id = db.Column(db.String(64))
    w_rule_desc = db.Column(db.String(255))
    w_rule = db.Column(db.String(2048))
    w_rule_status = db.Column(db.Integer)
    web = db.Column(db.String(64))
    user = db.Column(db.String(64))
    gmt_created = db.Column(db.DateTime)
    gmt_modified = db.Column(db.DateTime)
    status = db.Column(db.Integer)
    cluster = db.relationship('Cluster', secondary=cluster_white,
                              backref=db.backref('whitesclus', lazy='dynamic'), lazy='dynamic')

    def save(self):
        try:
            db.session.add(self)
            db.session.commit()
            return self
        except Exception as e:
            db.session.rollback()
            logger.error('save WhiteList error: %s' % str(e))

    def create(self):
        self.gmt_modified = self.gmt_created = datetime.now()
        self.nid = get_key()
        self.status = 1
        return self.save()

    def update(self, **kwargs):
        self.gmt_modified = datetime.now()
        for key in kwargs:
            setattr(self, key, kwargs[key])
        return self.save()

    @classmethod
    def get(cls, **kwargs):
        return cls.query.filter_by(**kwargs).first()

    @classmethod
    def get_all(cls, **kwargs):
        return cls.query.filter_by(**kwargs).all()

    @classmethod
    def get_page(cls, page, size, role, nid):
        if role == 5:
            return cls.query.filter(
                cls.status == 1
            ).order_by(cls.gmt_modified.desc()).paginate(page, size, error_out=False)
        else:
            return cls.query.filter(
                cls.status == 1,
                cls.user == nid
            ).order_by(cls.gmt_modified.desc()).paginate(page, size, error_out=False)

    def edit(self, d):
        self.gmt_modified = datetime.now()
        if d:
            w_rule = {}
            for key in d:
                if key in ["w_rule_status", "w_rule_desc"]:
                    setattr(self, key, d[key])
                if key in ["w_ip", "w_url", "w_host"]:
                    keys = None
                    if key == "w_ip":
                        keys = 'IP'
                    if key == "w_url":
                        keys = 'URI'
                    if key == "w_host":
                        keys = 'HOST'
                    if keys:
                        w_rule[keys] = d[key]
                    setattr(self, 'w_rule', json.dumps(w_rule))
                if key == "site":
                    site = []
                    for a in d[key]:
                        if not a:
                            site = []
                            break
                        else:
                            web = Cluster.get(nid=a, status=1)
                            if web:
                                site.append(web)
                    setattr(self, "cluster", site)
        return self.save()

    def delete(self):
        try:
            db.session.delete(self)
            db.session.commit()
            return self
        except Exception as e:
            db.session.rollback()
            logger.error('delete WhiteList error: %s' % str(e))


class WafRules(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nid = db.Column(db.String(64))
    stage = db.Column(db.String(64))
    f_rule_id = db.Column(db.String(64))
    f_rule_name = db.Column(db.String(255))
    f_rule_desc = db.Column(db.String(255))
    f_rule = db.Column(db.String(4096))
    f_rule_status = db.Column(db.Integer)
    tags = db.Column(db.String(255))
    risk_level = db.Column(db.Integer)
    user = db.Column(db.String(64))
    gmt_created = db.Column(db.DateTime)
    gmt_modified = db.Column(db.DateTime)
    status = db.Column(db.Integer)
    editor = db.Column(db.String(64))
    

    def save(self):
        try:
            db.session.add(self)
            db.session.commit()
            return self
        except Exception as e:
            db.session.rollback()
            logger.error('save WafRules error: %s' % str(e))

    def create(self):
        self.f_rule_status = 1
        self.gmt_modified = self.gmt_created = datetime.now()
        self.nid = get_key()
        self.status = 1
        return self.save()

    def update(self, **kwargs):
        self.f_rule_status = 1
        self.gmt_modified = datetime.now()
        for key in kwargs:
            setattr(self, key, kwargs[key])
        return self.save()

    def edit(self, d):
        self.gmt_modified = datetime.now()
        if type(d) == dict:
            for key in d:
                if key in ["stage", "f_rule_name", "f_rule_desc", "risk_level", "tags", "f_rule", "status"]:
                    setattr(self, key, d[key])
        return self.save()

    @classmethod
    def get(cls, **kwargs):
        return cls.query.filter_by(**kwargs).first()

    @classmethod
    def get_all(cls, **kwargs):
        return cls.query.filter_by(**kwargs).all()

    @classmethod
    def get_page(cls, page, size, role, nid, search, stage=None):
        if stage:
            if search:
                if role == 5:
                    return cls.query.filter(
                        cls.status == 1,
                        cls.f_rule_name.like('%' + search + '%'),
                        cls.stage == stage
                    ).order_by(cls.gmt_modified.desc()).paginate(page, size, error_out=False)
                else:
                    return cls.query.filter(
                        cls.status == 1,
                        cls.user == nid,
                        cls.f_rule_name.like('%' + search + '%'),
                        cls.stage == stage
                    ).order_by(cls.gmt_modified.desc()).paginate(page, size, error_out=False)
            else:
                if role == 5:
                    return cls.query.filter(
                        cls.status == 1,
                        cls.stage == stage
                    ).order_by(cls.gmt_modified.desc()).paginate(page, size, error_out=False)
                else:
                    return cls.query.filter(
                        cls.status == 1,
                        cls.user == nid,
                        cls.stage == stage
                    ).order_by(cls.gmt_modified.desc()).paginate(page, size, error_out=False)
        else:
            if search:
                if role == 5:
                    return cls.query.filter(
                        cls.status == 1,
                        cls.f_rule_name.like('%' + search + '%')
                    ).order_by(cls.gmt_modified.desc()).paginate(page, size, error_out=False)
                else:
                    return cls.query.filter(
                        cls.status == 1,
                        cls.user == nid,
                        cls.f_rule_name.like('%' + search + '%')
                    ).order_by(cls.gmt_modified.desc()).paginate(page, size, error_out=False)
            else:
                if role == 5:
                    return cls.query.filter(
                        cls.status == 1
                    ).order_by(cls.gmt_modified.desc()).paginate(page, size, error_out=False)
                else:
                    return cls.query.filter(
                        cls.status == 1,
                        cls.user == nid
                    ).order_by(cls.gmt_modified.desc()).paginate(page, size, error_out=False)
    
    def fields(self):
        return self._sa_class_manager._all_key_set

    def to_dict(self):
        fields_dict = {}
        for field in self.fields():
            fields_dict[field] = getattr(self, field)
        return fields_dict

class Policy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(64), index=True)
    name = db.Column(db.String(64))
    kind = db.Column(db.String(64))
    action = db.Column(db.String(64))
    action_vars = db.Column(db.String(2048))
    version = db.Column(db.String(64))
    user = db.Column(db.String(64))
    gmt_created = db.Column(db.DateTime)
    gmt_modified = db.Column(db.DateTime)
    status = db.Column(db.Integer)
    policy_status = db.Column(db.Integer)
    cluster = db.Column(db.String(64))
    upload_file_access = db.Column(db.Integer)
    request_body_access = db.Column(db.Integer)
    request_body_limit = db.Column(db.Integer)
    request_body_nofile_limit = db.Column(db.Integer)
    response_body_access = db.Column(db.Integer)
    response_body_mime_type = db.Column(db.String(1024))
    response_body_limit = db.Column(db.Integer)
    cluster_id = db.Column(db.Integer, db.ForeignKey('cluster.id'))
    request_filters = db.relationship('RequestFilter', back_populates='policy', lazy='select')
    response_filters = db.relationship('ResponseFilter', back_populates='policy', lazy='select')
    response_header_filters = db.relationship('ResponseHeaderFilter', back_populates='policy', lazy='select')


    def to_dict(self):
        resp_dict = {
            'id': self.id,
            'uuid': self.uuid,
            'name': self.name,
            'kind': self.kind,
            'action': self.action,
            'action_vars': json.loads(self.action_vars),
            'version': self.version,
            'user': self.user,
            'gmt_created': self.gmt_created,
            'gmt_modified': self.gmt_modified,
            'status': self.status,
            'cluster': self.cluster,
            'upload_file_access': self.upload_file_access,
            'request_body_access': self.request_body_access,
            'request_body_limit': self.request_body_limit,
            'request_body_nofile_limit': self.request_body_nofile_limit,
            'response_body_access': self.response_body_access,
            'response_body_mime_type': self.response_body_mime_type,
            'response_body_limit': self.response_body_limit,
            'request_filters': [ tmp.to_dict() for tmp in self.request_filters ],
            'response_filters': [ tmp.to_dict() for tmp in self.response_filters ],
            'response_header_filters': [ tmp.to_dict() for tmp in self.response_header_filters ]
        }
        return resp_dict       

    def save(self):
        try:
            db.session.add(self)
            db.session.commit()
            return self
        except Exception as e:
            db.session.rollback()
            logger.error('save Policy error: %s' % str(e))

    def create(self):
        self.gmt_modified = self.gmt_created = datetime.now()
        self.status = 1
        self.policy_status = 1
        self.uuid = get_uuid()
        return self.save()

    def update(self, **kwargs):
        self.gmt_modified = datetime.now()
        for key in kwargs:
            setattr(self, key, kwargs[key])
        return self.save()
    
    def delete(self):
        try:
            db.session.delete(self)
            db.session.commit()
            return self
        except Exception as e:
            db.session.rollback()
            logger.error('delete WhiteList error: %s' % str(e))   

    @classmethod
    def get(cls, **kwargs):
        return cls.query.filter_by(**kwargs).first()

    @classmethod
    def get_page(cls, page, size, role, username):
        if role == 5:
            return cls.query.filter(
                cls.status == 1,
            ).order_by(cls.gmt_modified.desc()).paginate(page, size, error_out=False)
        else:
            return cls.query.filter(
                cls.status == 1,
                # cls.user == username
            ).order_by(cls.gmt_modified.desc()).paginate(page, size, error_out=False)

    @classmethod
    def get_all(cls, **kwargs):
        return cls.query.filter_by(**kwargs).all()

    def edit(self, **kwargs):
        self.gmt_modified = datetime.now()
        for k, v in kwargs.items():
            if k in ['name', 'kind', 'action', 'action_vars', 'cluster', 'policy_status', 'user', 'request_body_access',
                     'request_body_limit', 'upload_file_access', 'request_body_nofile_limit', 'response_body_access',
                     'response_body_mime_type', 'response_body_limit']:
                setattr(self, k, v)
        return self.save()

    @classmethod
    def get_all_clu(cls, nid):
        return cls.query.filter(
            or_(cls.cluster == nid, cls.cluster == "all"), cls.status == 1, cls.policy_status == 1
        ).all()

class RequestFilter(CompatibleModel):
    id = db.Column(db.Integer, primary_key=True)
    rule_id = db.Column(db.Integer, db.ForeignKey('waf_rules.id'))
    policy_id = db.Column(db.Integer, db.ForeignKey('policy.id'))
    order = db.Column(db.Integer)
    rule_action = db.Column(db.String(64))
    action_vars = db.Column(db.String(2048))
    rule = db.relationship("WafRules", uselist=False)
    policy = db.relationship("Policy", back_populates='request_filters')
    gmt_created = db.Column(db.DateTime, default=datetime.utcnow())
    gmt_modified = db.Column(db.DateTime, default=datetime.utcnow())

    def to_dict(self):
        resp_dict = {
            'id': self.id,
            'order': self.order,
            'rule_action': self.rule_action,
            'action_vars': json.loads(self.action_vars),
            'rule_id': self.rule_id,
            'rule_name': self.rule.f_rule_name
        }
        return resp_dict

class ResponseFilter(CompatibleModel):

    id = db.Column(db.Integer, primary_key=True)
    rule_id = db.Column(db.Integer, db.ForeignKey('waf_rules.id'))
    policy_id = db.Column(db.Integer, db.ForeignKey('policy.id'))
    order = db.Column(db.Integer)
    rule_action = db.Column(db.String(64))
    action_vars = db.Column(db.String(2048))
    rule = db.relationship("WafRules", uselist=False)
    policy = db.relationship("Policy", back_populates='response_filters')
    gmt_created = db.Column(db.DateTime, default=datetime.utcnow())
    gmt_modified = db.Column(db.DateTime, default=datetime.utcnow())

    def to_dict(self):
        resp_dict = {
            'id': self.id,
            'order': self.order,
            'rule_action': self.rule_action,
            'action_vars': json.loads(self.action_vars),
            'rule_id': self.rule_id,
            'rule_name': self.rule.f_rule_name
        }
        return resp_dict

class ResponseHeaderFilter(CompatibleModel):

    id = db.Column(db.Integer, primary_key=True)
    rule_id = db.Column(db.Integer, db.ForeignKey('waf_rules.id'))
    policy_id = db.Column(db.Integer, db.ForeignKey('policy.id'))
    order = db.Column(db.Integer)
    rule_action = db.Column(db.String(64))
    action_vars = db.Column(db.String(2048))
    rule = db.relationship("WafRules", uselist=False)
    policy = db.relationship("Policy", back_populates='response_header_filters')
    gmt_created = db.Column(db.DateTime, default=datetime.utcnow())
    gmt_modified = db.Column(db.DateTime, default=datetime.utcnow())

    def to_dict(self):
        resp_dict = {
            'id': self.id,
            'order': self.order,
            'rule_action': self.rule_action,
            'action_vars': json.loads(self.action_vars),
            'rule_id': self.rule_id,
            'rule_name': self.rule.f_rule_name
        }
        return resp_dict

class BackUp(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nid = db.Column(db.String(64))
    file_data = db.Column(db.TEXT)
    file_type = db.Column(db.String(64))
    web = db.Column(db.String(64))
    remake = db.Column(db.String(256))
    gmt_created = db.Column(db.DateTime)
    gmt_modified = db.Column(db.DateTime)
    status = db.Column(db.Integer)

    def save(self):
        try:
            db.session.add(self)
            db.session.commit()
            return self
        except Exception as e:
            db.session.rollback()
            logger.error('save BackUp error: %s' % str(e))

    def create(self):
        self.gmt_modified = self.gmt_created = datetime.now()
        self.nid = get_key()
        self.remake = get_hash(self.file_data)
        self.status = 1
        return self.save()

    def create_backup(self):
        try:
            backup = self.get_by_web(web=self.web)
            if backup:
                web_ = Web.get(nid=self.web, status=1, web_status=1)
                if not web_.origin:
                    raise Exception('web has no conf mark: ', web_.name)
                #  判断标准配置是上一次的记录，还是新的修改, 根据origin标记判断
                if get_hash(self.file_data) != web_.origin:

                    hash_value = get_hash(self.file_data)
                    backup.file_data = self.file_data
                    backup.remake = hash_value
                    backup.gmt_modified = datetime.now()
                    web_.conf_file = self.file_data
                    web_.origin = hash_value
                    web_.gmt_modified = datetime.now()
                    db.session.commit()
                return self
            else:
                return self.create()
        except Exception as e:
            db.session.rollback()
            logger.error('BackUp update error: %s' % str(e))

    def update(self):
        try:
            self.gmt_modified = datetime.now()
            db.session.commit()
            return self
        except Exception as e:
            db.session.rollback()
            logger.error('update BackUp error: %s' % str(e))

    @classmethod
    def get_by_web(cls, **kwargs):
        # if role != 5:
        #     kwargs['user'] = nid
        #     kwargs['status'] = 1
        kwargs['status'] = 1
        return cls.query.filter_by(**kwargs).\
            order_by(cls.gmt_modified.desc()).first()


class Msg(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nid = db.Column(db.String(64))
    content = db.Column(db.TEXT)
    genre = db.Column(db.String(64))
    web = db.Column(db.String(64))
    gmt_created = db.Column(db.DateTime)
    gmt_modified = db.Column(db.DateTime)
    status = db.Column(db.Integer)
    msg_status = db.Column(db.Integer)
    user = db.Column(db.String(64))

    def save(self):
        try:
            db.session.add(self)
            db.session.commit()
            return self
        except Exception as e:
            db.session.rollback()
            logger.error('save Msg error: %s' % str(e))

    def create(self):
        self.gmt_modified = self.gmt_created = datetime.now()
        self.nid = get_key()
        self.status = self.msg_status = 1
        return self.save()

    @classmethod
    def get(cls, **kwargs):
        return cls.query.filter_by(**kwargs).first()

    @classmethod
    def get_all(cls, **kwargs):
        return cls.query.filter_by(**kwargs).all()

    @classmethod
    def get_by_web(cls, role, nid, **kwargs):
        if role != 5:
            kwargs['user'] = nid
            kwargs['status'] = 1
        return cls.query.filter_by(**kwargs).order_by(cls.gmt_created.desc()).first()

    @classmethod
    def get_page(cls, page, size, role, nid):
        if role == 5:
            return cls.query.filter(
                cls.status == 1,
            ).order_by(cls.id.desc()).paginate(page, size, error_out=False)
        else:
            return cls.query.filter(
                cls.status == 1,
                cls.user == nid
            ).order_by(cls.id.desc()).paginate(page, size, error_out=False)

    def update(self, **kwargs):
        self.gmt_modified = datetime.now()
        for key in kwargs:
            setattr(self, key, kwargs[key])
        return self.save()
