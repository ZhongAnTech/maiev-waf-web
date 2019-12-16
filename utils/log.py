# -*- coding: utf-8 -*-

import os
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler


def log_setting(app_name, env="local", path=None, is_micro_service=True):
    logger = logging.getLogger(app_name)
    if not len(logger.handlers):
        if path:
            log_dir = path
        else:
            # 在本地的话则以当前文件路径写日志
            if env == "local":
                log_dir = os.path.normpath(os.path.join(os.path.abspath(os.path.dirname(__file__)), "logs"))
            else:
                log_dir = "/alidata1/admin/%s/logs/" % (app_name)
        if not os.path.isdir(log_dir):
                os.makedirs(log_dir)
        file_fmt = "%s-source_%s_appName_%s_logType_%s.log"
        source = "microService" if is_micro_service else "regular"
        now_dt_str = datetime.now().strftime("%Y-%m-%d")
        info_file_name = os.path.join(log_dir, file_fmt % (now_dt_str, source, app_name, "info"))
        error_file_name = os.path.join(log_dir, file_fmt % (now_dt_str, source, app_name, "error"))
        # 定义一个RotatingFileHandler，最多备份5个日志文件，每个日志文件最大10M
        Rthandler = RotatingFileHandler(info_file_name, maxBytes=10 * 1024 * 1024, backupCount=5)
        Rthandler.setLevel(logging.INFO)
        # 该handler 把Error以上错误信息记录到日志
        Ethandler = RotatingFileHandler(error_file_name, maxBytes=10 * 1024 * 1024, backupCount=5)
        Ethandler.setLevel(logging.ERROR)
        # 在创建一个handler，用于输出到控制台
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        # 定义handler的输出格式
        if is_micro_service:
            formatter = logging.Formatter(
                '%(asctime)s [%(threadName)s-%(thread)d] %(levelname)s [%(funcName)s] [%(filename)s:%(lineno)d] [trace=,span=,parent=,name=,app=,begintime=,endtime=] - %(message)s'
            )
        else:
            formatter = logging.Formatter(
                '%(asctime)s [%(threadName)s-%(thread)d] %(levelname)s [%(funcName)s] [%(filename)s:%(lineno)d] - %(message)s'
            )
        Rthandler.setFormatter(formatter)
        Ethandler.setFormatter(formatter)
        ch.setFormatter(formatter)
        # 给logger添加handler
        logger.addHandler(Rthandler)
        logger.addHandler(Ethandler)
        logger.addHandler(ch)
    return logger


if __name__ == '__main__':
    test_logger = log_setting("testapp", env="local")
    test_logger.info("asdfasdfasdfasdfasdfsadfsadf")
    test_logger.error("asdfasdfasdfasdfasdfsadfsadf")