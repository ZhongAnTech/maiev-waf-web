# -*- coding: utf-8 -*-
from datetime import datetime

from utils.log import log_setting
from utils.tools import get_ip, check_ip, get_hash
from modules import Web, Server, BackUp, Cluster


class Assemble:

    def __init__(self, web_nid):
        self.web_nid = web_nid
        self.web = None
        self.server = None
        self.cluster = None
        self.logger = log_setting("salt_client")
        self.load_data(self.web_nid)

    def load_data(self, web_nid):
        self.web = Web.get(nid=web_nid, status=1)
        self.server = Server.get_all(web=self.web.nid, status=1)
        self.cluster = Cluster.get(nid=self.web.cluster)

    def ngx_file(self):
        result = {'success': True}
        web = self.web
        if web:
            try:
                servers = self.server
                SSL_DIR = "/alidata1/conf/tengine/ssl/"
                if self.cluster:
                    if self.cluster.ssl_dir:
                        SSL_DIR = self.cluster.ssl_dir
                # if web.conf_type != "custom":
                    # 拼装upstream 和 location
                upstream = ""
                location = ""
                servers = sorted(servers, key=lambda locs: locs.seq)
                for loc in servers:
                    ws = ""
                    protocol = "http"
                    rewrite = ""
                    proxy_pass = ""
                    header_host = '$host'
                    location_blank = " "
                    proxy_mode = False
                    proxy_host = str(loc.nid)
                    location_url = loc.location_url if loc.location_url else ""
                    location_pattern = loc.location_pattern if loc.location_pattern else "/"
                    rewrite_flag = loc.rewrite_flag if loc.rewrite_flag else "nowrite"
                    rewrite_matches = loc.rewrite_matches if loc.rewrite_matches else ""
                    rewrite_pattern = loc.rewrite_pattern if loc.rewrite_pattern else ""
                    if loc.proxy_service:
                        stream = ""
                        if loc.slb_alg == 1:
                            stream = "\t" + "ip_hash;\n"
                        elif loc.slb_alg == 2:
                            stream = "\t" + "session_sticky;\n"
                        for ser in loc.proxy_service.split(','):
                            if not check_ip(ser):
                                if get_ip(ser).find('Name or service not known') == -1:
                                    header_host = "$proxy_host"
                                    proxy_mode = True
                                    proxy_host = str(ser)
                                    break
                                else:
                                    result['success'] = False
                                    result['info'] = '后端服务错误,{},Name or service not known'.format(str(ser))
                            stream += "\t" + "server " + str(ser) + ";\n"
                        if not proxy_mode:
                            upstream += "\n" \
                                        "upstream " + proxy_host + " {\n" \
                                        "" + stream + "" \
                                        "}\n"
                    if rewrite_flag != "nowrite":
                        rewrite = "rewrite " + rewrite_matches + " " + rewrite_pattern + " " + rewrite_flag + ";"
                    if loc.http_back == 0:
                        protocol = "https"
                    if loc.websocket == 1:
                        ws = "\t" + "proxy_http_version 1.1;\n" \
                             "\t" + "proxy_set_header Upgrade $http_upgrade;\n" \
                             "\t" + 'proxy_set_header Connection "upgrade";\n'
                    if loc.proxy_service:
                        if proxy_host:
                            proxy_host = proxy_host.split()[0]
                        proxy_pass = "\t" + "proxy_set_header Host " + header_host + ";\n" \
                                     "\t" + "proxy_set_header walmart-target $host;\n" \
                                     "\t" + "proxy_set_header originalDomain $host;\n" \
                                     "\t" + "proxy_set_header X-Real-IP $remote_addr;\n" \
                                     "\t" + "proxy_set_header WAF aegis_3.1;\n" \
                                     "\t" + "proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n" \
                                     "\t" + "proxy_pass " + protocol + "://" + proxy_host + ";\n"
                    if location_pattern == "/" and location_url != "":
                        location_blank = ""
                    location += "location " + location_pattern + location_blank + location_url + " {\n" \
                                "\t" + rewrite + "\n" \
                                "\n" + ws + "\n" \
                                "\n" + proxy_pass + "\n" \
                                "}\n"

                # 拼装server
                server = ""
                if web.http == 1:
                    for l_port in web.http_port.split(','):
                            if (web.https_trans == 1) & (web.https == 1):
                                server += "server {\n" \
                                          "listen " + str(l_port) + ";\n" \
                                          "server_name " + web.name + ";\n" \
                                          "set $user_id " + web.user + ";\n" \
                                          "set $nid " + web.nid + ";\n" \
                                          "set $cluster " + web.cluster + ";\n" \
                                          "error_log /alidata1/logs/error_" + web.name + ".log;\n" \
                                          "access_log /alidata1/logs/access_" + web.name + ".log;\n" \
                                          "rewrite ^(.*)$ https://$host$1 permanent;\n" \
                                          "}\n"
                            else:
                                server += "\n" \
                                          "server {\n" \
                                          "listen "+str(l_port)+";\n" \
                                          "server_name " + web.name + ";\n" \
                                          "set $user_id " + web.user + ";\n" \
                                          "set $nid " + web.nid + ";\n" \
                                          "set $cluster " + web.cluster + ";\n" \
                                          "error_log /alidata1/logs/error_" + web.name + ".log;\n" \
                                          "access_log /alidata1/logs/access_" + web.name + ".log;\n" \
                                          "\n" \
                                          "" + location + "\n" \
                                          "}\n"
                if web.https == 1:
                    for ls_port in web.https_port.split(','):
                        server += "\n" \
                                  "server {\n" \
                                  "listen "+str(ls_port)+" ssl http2 spdy;\n" \
                                  "server_name " + str(web.name) + ";\n" \
                                  "set $user_id " + web.user + ";\n" \
                                  "set $nid " + web.nid + ";\n" \
                                  "set $cluster " + web.cluster + ";\n" \
                                  "ssl on;\n" \
                                  "ssl_certificate "+SSL_DIR+str(web.cert)+".pem;\n" \
                                  "ssl_certificate_key "+SSL_DIR+str(web.cert)+".key;\n" \
                                  "ssl_session_cache shared:SSL:10m;\n" \
                                  "ssl_session_timeout 10m;\n" \
                                  "keepalive_timeout 70s;\n" \
                                  "ssl_protocols TLSv1 TLSv1.1 TLSv1.2;\n" \
                                  "ssl_ciphers  'ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:" \
                                  "ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:" \
                                  "ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:" \
                                  "DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384:" \
                                  "ECDHE-ECDSA-AES128-SHA256:ECDHE-RSA-AES128-SHA256:" \
                                  "ECDHE-ECDSA-AES128-SHA:ECDHE-RSA-AES256-SHA384:ECDHE-RSA-AES128-SHA:" \
                                  "ECDHE-ECDSA-AES256-SHA384:ECDHE-ECDSA-AES256-SHA:ECDHE-RSA-AES256-SHA:" \
                                  "DHE-RSA-AES128-SHA256:DHE-RSA-AES128-SHA:DHE-RSA-AES256-SHA256:" \
                                  "DHE-RSA-AES256-SHA:ECDHE-ECDSA-DES-CBC3-SHA:ECDHE-RSA-DES-CBC3-SHA:" \
                                  "EDH-RSA-DES-CBC3-SHA:AES128-GCM-SHA256:AES256-GCM-SHA384:AES128-SHA256:" \
                                  "AES256-SHA256:AES128-SHA:AES256-SHA:DES-CBC3-SHA:!DSS';\n" \
                                  "ssl_prefer_server_ciphers on;\n" \
                                  "ssl_dhparam ssl/dhparam.pem;\n" \
                                  "error_log logs/error_" + web.name + ".log;\n" \
                                  "access_log logs/access_" + web.name + ".log;\n" \
                                  "" + location + "\n" \
                                  "}\n"
                text = upstream + "\n" + server
                if not self.web.origin:
                    # 第一次创建web时，添加conf file标记
                    self.web = web.update(conf_file=text, origin=get_hash(text))
                    BackUp(file_data=text, file_type='ngx', web=web.nid).create_backup()
                    result['text'] = text
                else:
                    if self.web.origin == get_hash(text):
                        # 说明没有做任何修改，只是保存
                        result['text'] = ''
                    else:
                        BackUp(file_data=text, file_type='ngx', web=web.nid).create_backup()
                        result['text'] = text
            except Exception as e:
                result['success'] = False
                result['info'] = 'packaging ngx config failed: %s' % str(e)
                self.logger.error('packaging ngx config failed: %s' % str(e))
        else:
            result['success'] = False
            result['info'] = 'packaging ngx config failed: not found web'
            self.logger.error('packaging ngx config failed: not found web')
        return result

    @classmethod
    def get_list(cls, content):
        content = content.replace('\n', ' ')
        content = content.replace('\r', ' ')
        contents = content.split(' ')
        for c_ in contents[:]:
            if c_ == '':
                contents.remove(c_)
        return contents

    def update_file_by_ngx(self, web_nid, content):
        """
            判断自定义配置修改文件，保持一致
        """
        result = {'success': True}
        try:
            backup_record = BackUp.get_by_web(web=web_nid)
            if not backup_record:
                backup_record = BackUp(file_data=content,
                                       file_type='ngx',
                                       web=web_nid).create()
            if not backup_record.remake:
                backup_record.remake = get_hash(backup_record.file_data)
                backup_record = backup_record.update()

            if  content and (get_hash(content) != backup_record.remake):
                # 说明自定义配置发生修改, 进行backup web更新
                backup_record.file_data = content
                backup_record.remake = get_hash(content)
                backup_record.update()
                #
                self.web.update(conf_file=content)
                result['text'] = content
            else:
                result = self.ngx_file()
        except Exception as e:
            result['success'] = False
            result['info'] = 'Update ngx config failed: %s' % str(e)
            self.logger.error('Update ngx config failed: %s' % str(e))
        return result


