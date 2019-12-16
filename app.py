#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/10/13 下午3:10
# @Author  : Vern

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import MYSQL_CONFIG, ENV, FLK, SPAN_CERT
from utils.tools import CustomJSONEncoder
from flask_cors import CORS


app = Flask(__name__)
app.json_encoder = CustomJSONEncoder
app.config['SQLALCHEMY_DATABASE_URI'] = MYSQL_CONFIG[ENV]
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = '\x05\x80R1\x08^91\xf3\x85\xaf\x8b,\xa8\x9d\xd9?\xd8\xc6\x90N\x05\xa0\xb4'

db = SQLAlchemy(app)

CORS(app)

from view import *
from policy_view import *

db.create_all()

if __name__ == '__main__':
    app.run(threaded=True, host='0.0.0.0', port=FLK[ENV]["PORT"], debug=FLK[ENV]["Debug"])
