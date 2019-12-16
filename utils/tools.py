# -*- coding: utf-8 -*-
import re

import pygeoip
import os
import time
import json
import random
import hashlib
import calendar
import uuid
from flask.json import JSONEncoder
from datetime import datetime, timedelta, date
from sqlalchemy.ext.declarative import DeclarativeMeta
from OpenSSL import crypto
from IPy import IP
from config import DNS, ENV
import dns.resolver

gi = pygeoip.GeoIP(os.getcwd()+'/utils/GeoLiteCity.dat')


def parser_ssl(stream):
    try:
        cert = crypto.load_certificate(crypto.FILETYPE_PEM, stream)
        subject = cert.get_subject()
        issuer = cert.get_issuer()
        return {
            'issuer': issuer.CN,
            'subject': subject.CN,
            'start': datetime.strptime(cert.get_notBefore(), "%Y%m%d%H%M%SZ"),
            'expire': datetime.strptime(cert.get_notAfter(), "%Y%m%d%H%M%SZ")
        }
    except Exception as e:
        print str(e)


def geoip(ip):
    try:
        rec = gi.record_by_addr(ip)
        if not rec:
            rec = {
                'city': 'Shanghai', 'region_code': '23', 'area_code': 0, 'time_zone': 'Asia/Shanghai', 'dma_code': 0,
                'metro_code': None, 'country_code3': 'CHN', 'latitude': 31.045600000000007,
                'postal_code': None, 'longitude': 121.3997, 'country_code': 'CN',
                'country_name': 'China', 'continent': 'AS'}
    except Exception as e:
        rec = {
            'city': 'Shanghai', 'region_code': '23', 'area_code': 0, 'time_zone': 'Asia/Shanghai', 'dma_code': 0,
            'metro_code': None, 'country_code3': 'CHN', 'latitude': 31.045600000000007,
            'postal_code': None, 'longitude': 121.3997, 'country_code': 'CN',
            'country_name': 'China', 'continent': 'AS'}
        print str(e)
    return rec


def date2ts(dt):
    ''' Converts a datetime object to UNIX timestamp in milliseconds. '''
    return long(time.mktime(dt.timetuple()))


def ts2date(timestamp, convert_to_local=False):
    ''' Converts UNIX timestamp to a datetime object. '''
    if isinstance(timestamp, (int, long, float)):
        dt = datetime.utcfromtimestamp(timestamp)
        if convert_to_local:
            # 是否转化为本地时间
            dt = dt + timedelta(hours=8)
            # 中国默认时区
        return dt
    return timestamp


def get_key():
    key = hashlib.md5(str(time.time() + random.random()).encode('utf-8')).hexdigest()
    return key

def get_uuid():
    uid = str(uuid.uuid4())
    suid = ''.join(uid.split('-'))
    return suid

def get_hash(encode_str):
    encode_str = re.sub(r'\r|\n|\t| ', '', encode_str)
    encode_data = hashlib.md5(encode_str).hexdigest()
    return encode_data


def get_ip(name, port=None):
    hosts = "找不到{0}的IP".format(name)
    try:
        my_resolver = dns.resolver.Resolver()
        my_resolver.timeout = 0.3
        my_resolver.lifetime = 0.3
        my_resolver.nameservers = DNS[ENV]
        r = my_resolver.query(name, "A")
        for i in r.response.answer:
            for j in i.items:
                hosts = str(j)
    except Exception as e:
        hosts = str(e)
    return hosts


def check_ip(name):
    try:
        name = name.split(':')
        if name:
            IP(name[0])
            return True
    except Exception as e:
        str(e)


class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        try:
            if isinstance(obj, datetime):
                if obj.utcoffset() is not None:
                    obj = obj - obj.utcoffset()
                millis = int(
                    calendar.timegm(obj.timetuple()) - 28800
                )
                return millis
            iterable = iter(obj)
        except TypeError:
            pass
        else:
            return list(iterable)
        return JSONEncoder.default(self, obj)


class LocalJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, date):
            return obj.strftime('%Y-%m-%d')
        elif isinstance(obj.__class__, DeclarativeMeta):
            # an SQLAlchemy class
            fields = {}
            for field in [x for x in dir(obj) if not x.startswith('_') and x != 'metadata']:
                data = obj.__getattribute__(field)
                try:
                    if isinstance(data, datetime):
                        data = data.strftime('%Y-%m-%d %H:%M:%S')
                    json.dumps(data)
                    # this will fail on non-encodable values, like other classes
                    fields[field] = data
                except TypeError:
                    ""
                    # fields[field] = None
            # a json-encodable dict
            return fields
        return json.JSONEncoder.default(self, obj)


def get_address(content):
    """
        根据nginx配置文件获取后端服务地址
    """
    reg1 = re.compile('.*?proxy_pass http://(.*?);', re.S)
    reg2 = re.compile('.*?server (\d.*?);', re.S)
    addresses = re.findall(reg1, content)
    ips = re.findall(reg2, content)
    addresses = list(set(addresses))
    for add_ in addresses[:]:
        if '.' not in add_:
            addresses.remove(add_)
    if addresses:
        ips.extend(addresses)
    return ips
