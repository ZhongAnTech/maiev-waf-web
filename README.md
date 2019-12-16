#### 获取网站列表
#### GET /waf/api/WebConfig?page=1&size=10
#### GET /waf/api/WebConfig?page=1&size=10&search=test.com   
>   搜索
######

###### json返回数据包
```
{
  "data": {
    "certs": [], 
    "pages": {
      "page": 1, 
      "size": 20, 
      "total": 2
    }, 
    "webs": [
      {
        "cluster": "a2d04bbb218bf65610996502726d0c31", 
        "cname": null, 
        "defend_blacklist": 1, 
        "defend_cc": 1, 
        "defend_web": 1, 
        "http": 1, 
        "https": 1, 
        "name": "test.com", 
        "name_host": [
          "69.172.200.235"
        ], 
        "nid": "c3a525f54b5f2ee121747ee5ed3d5829", 
        "server": [
          {
            "location_url": null, 
            "proxy_service": [
              "10.1.1.1:8080", 
              "10.1.1.1:8081", 
              "10.1.1.1:8082"
            ]
          }
        ], 
        "status": 1
      }, 
      {
        "cluster": "a2d04bbb218bf65610996502726d0c31", 
        "cname": null, 
        "defend_blacklist": 1, 
        "defend_cc": 1, 
        "defend_web": 1, 
        "http": 1, 
        "https": 1, 
        "name": "test.com", 
        "name_host": [
          "69.172.200.235"
        ], 
        "nid": "ed66728e57bcb0b0f04cc0c9c212d26e", 
        "server": [
          {
            "location_url": null, 
            "proxy_service": [
              "10.1.1.1:8080", 
              "10.1.1.1:8081", 
              "10.1.1.1:8082"
            ]
          }
        ], 
        "status": 1
      }
    ]
  }, 
  "success": true
}
```
> pages 分页信息  page当前页  size单页条数  total数据总条数

> webs  []数组   web数据信息

>  cname

>   defend_blacklist    defend_cc   defend_web   分别为 黑名单服务 cc攻击防护服务 Web应用攻击防护 的启用停用状态 

> name_host  实时解析的域名地址

> proxy_service 服务器地址

> success boolean型 接口返回成功状态






#### 添加网站
#### POST /waf/api/WebConfig

###### standard  版本 
######  json请求数据包
```
{
  "cert": "-----------------------------", 
  "cert_name": "anlink", 
  "cert_nid": "1b8dd894b769aedff4f794d31618725d", 
  "conf_type": "standard", 
  "http": 1, 
  "https": 1, 
  "https_trans": 1, 
  "keys": "-----------------------------", 
  "name": "test.com", 
  "server": [
    {
      "http_back": 1, 
      "proxy_service": [
        "10.1.1.1:8080", 
        "10.1.1.1:8081", 
        "10.1.1.1:8082"
      ], 
      "slb_alg": 1
    }
  ]
}
```
> name 域名    string

> https   协议类型 int  1为开启 0 为关闭

> http   协议类型 int  1为开启 0 为关闭

> cert_nid  证书nid  string  新建证书不用传,用于选择已有证书

> cert  证书文本  string  新建证书必须传

> keys  证书密钥文本  string  新建证书必须传

> conf_type   固定为standard

> https_trans   HTTPS强转 int 开启为1  关闭为0

> server 后端服务器信息 为[]数组   

> slb_alg   负载均衡算法 int  1为ip hash 0为轮询

> http_back  HTTP回源  int   1为开启 0为关闭


###### professional  版本
```
{
"cluster":"1b8dd894b769aedff4f794d31618725d",
"name": "test.com",
"https_port":[
"443",
"8443"
],
"http_port":[
"80",
"8080"
],
"https":1,
"http":1,
"cert_nid":"1b8dd894b769aedff4f794d31618725d",
"cert_name":"anlink",
"cert":"-----------------------------",
"keys":"-----------------------------",
"conf_type":"professional",
"conf_file":"---------------------------",
"https_trans":1,
"server":[
{
"order":1,
"proxy_service":["10.1.1.3:8080","10.1.1.4:8081","10.1.1.5:8082"],
"location_pattern":"~*",
"location_url":"/aaa",
"rewrite_flag":"/aaa/$(.)",
"rewrite_matches":"aaa",
"rewrite_pattern":"$",
"websocket":0,
"slb_alg":1,
"http_back":1
},
{
"order":2,
"proxy_service":["10.1.1.1:8080","10.1.1.1:8081","10.1.1.1:8082"],
"location_pattern":"~*",
"location_url":"/aaa",
"rewrite_flag":"/aaa/$(.)",
"rewrite_matches":"aaa",
"rewrite_pattern":"$",
"websocket":0,
"slb_alg":1,
"http_back":1
}
]
}

```



#### GET /waf/api/WebConfig/ed66728e57bcb0b0f04cc0c9c212d26e
```
{
  "data": {
    "cert": {
      "cert": "-----------------------------", 
      "keys": "-----------------------------", 
      "name": "anlink", 
      "nid": "473fc399dc98a39293b81ae0be0cb911"
    }, 
    "cluster": "a2d04bbb218bf65610996502726d0c31", 
    "cname": null, 
    "defend_blacklist": 1, 
    "defend_cc": -1, 
    "defend_cc_count": null, 
    "defend_cc_time": null, 
    "defend_custom": 1, 
    "defend_custom_policy": null, 
    "defend_web": 0, 
    "defend_web_policy": null, 
    "http": 1, 
    "http_port": [
      "80", 
      "8080"
    ], 
    "https": 1, 
    "https_port": [
      "443", 
      "8443"
    ], 
    "https_trans": 0, 
    "name": "test.com", 
    "nid": "ed66728e57bcb0b0f04cc0c9c212d26e", 
    "server": [
      {
        "cluster": "a2d04bbb218bf65610996502726d0c31", 
        "http_back": 1, 
        "location_pattern": null, 
        "location_url": null, 
        "name": null, 
        "nid": "642dbb8dc0b045ecd91685334127e9d0", 
        "order": null, 
        "proxy_service": [
          "10.1.1.1:8080", 
          "10.1.1.1:8081", 
          "10.1.1.1:8082"
        ], 
        "rewrite_flag": null, 
        "rewrite_matches": null, 
        "rewrite_pattern": null, 
        "server_status": 1, 
        "slb_alg": 1, 
        "websocket": 0
      }
    ], 
    "status": 1
  }, 
  "success": true
}
```


Web应用攻击防护   defend_web  1开启 模式为防御   0开启模式为告警  -1关闭

Web应用攻击防护策略 defend_web_policy   int   严格3   宽松2 正常1

CC安全防护    defend_cc   1开启  -1关闭

请求阈值   defend_cc_count  int

统计时间窗口   defend_cc_time  int


黑名单服务    defend_blacklist  1开启  -1关闭


精准访问控制    defend_custom  1开启 模式为防御   0开启模式为告警  -1关闭

精准访问控制防护策略 defend_web_policy   int     严格3   宽松2 正常1