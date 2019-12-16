# -*- coding: utf-8 -*-
# from app import db, log_setting
from datetime import datetime
from app import db
from models import handle_user
from utils.log import log_setting

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

logger = log_setting(app_name="aegis_waf_4.0")


class Recored(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_nid = db.Column(db.String(64))
    user_role = db.Column(db.Integer)
    user_name = db.Column(db.String(64))
    operation = db.Column(db.String(128))
    gmt_created = db.Column(db.DateTime)
    gmt_modified = db.Column(db.DateTime)

    @classmethod
    def get_page(cls, page, size, search, role, nid):
        return cls.query.filter(
            cls.operation.like('%' + search + '%')
        ).order_by(cls.gmt_modified.desc()).paginate(page, size, error_out=False)

    def save(self):
        try:
            db.session.add(self)
            db.session.commit()
            return self
        except Exception as e:
            db.session.rollback()
            logger.error('save Recored error: %s' % str(e))

    @classmethod
    def create(cls, **kwargs):
        k_ = {'gmt_modified': datetime.now(), 'gmt_created': datetime.now()}
        kwargs.update(k_)
        return cls(**kwargs).save()

    @classmethod
    def record(cls, user, operation):
        kwargs = {
            'user_nid': user.get('nid'),
            'user_name': user.get('name'),
            'user_role': user.get('role'),
            'operation': operation,
        }
        return cls.create(**kwargs)

    @classmethod
    def get_operation_by_method(cls, method, parameter):
        op_ = ''
        if not method:
            op_ = '新增' + parameter + '：'
        elif method == 'POST':
            op_ = '修改' + parameter + '：'
        elif method == 'GET':
            op_ = '查看' + parameter + '：'
        elif method == 'DELETE':
            op_ = '删除' + parameter + '：'
        elif method == 'PUT':
            op_ = '编辑' + parameter + '：'
        return op_

    @classmethod
    def record_web_manage(cls, user, clu):
        operation = user.get('name') + '查看了' + clu.name + '的网站列表'
        # return cls.record(user, operation)
        return

    @classmethod
    def record_web_config(cls, user, clu, web, success, method=None):
        op_ = cls.get_operation_by_method(method, '应用')
        operation = user.get('name') + '在' + clu.name + op_ + web.name + '，成功' if success else '，失败'
        return cls.record(user, operation)

    @classmethod
    def record_check_list(cls, user, parameter):
        """
        记录查看列表
        :param user: 当前用户
        :param parameter: 模块名
        """
        operation = user.get('name') + '查看了' + parameter + '列表'
        # return cls.record(user, operation)
        return

    @classmethod
    def record_handle_info(cls, user, name, parameter, success, method=None):
        """
        记录每条数据的操作
        :param user: 当前用户
        :param name: 数据name
        :param parameter: 模块名
        :param success: true or false
        :param method: 请求模式, 默认None是记录创建新的数据
        """
        op_ = cls.get_operation_by_method(method, parameter)
        operation = user.get('name') + op_ + name + '，成功' if success else '，失败'
        return cls.record(user, operation)
