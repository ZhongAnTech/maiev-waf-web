### 安装手册
#### 安装前期准备

1，默认已经安装了MySQL、Redis、pip等工具

#### 安装步骤
1，Git拉取代码

2，修改config.py
```
1，修改MYSQL_CONFIG配置
2，修改REDIS_CONFIG配置
```
3，安装虚拟环境
```
sudo su - root
pip install virtualenv
cd ~/aegis-waf3
virtualenv  venv
source venv/bin/activate
```
4，安装包
```
pip install -r requirements.txt
注意：
    安装MySQL-python失败解决办法：
    yum install mysql-devel
    yum install gcc python-devel
    pip install MySQL-python
继续执行pip install -r requirements.txt
```
5，测试
```
python app.py
访问ip：8081，访问登录页面，安装成功
```
6，初始账号
```
1，登录mysql，use database waf_v4
2，插入test用户, 密码 test
INSERT INTO `admin` VALUES (1, 'dc89de56159b2a8ac35e86dd3e029800', NULL, NULL, '9b46470028fb76c22dcb9e6381a22e2d', 'test', '098f6bcd4621d373cade4e832627b4f6', 'testv4@aa.com', NULL, '15617039999', '2019-10-14 15:18:30', '2019-12-12 14:21:54', 2, 'aegis_waf', 1, 0, NULL);
```
7，后台运行程序
```
1，nohup python app.py 2>&1 > /var/log/aegis-waf4.log &
2,查看日志，tail -f /var/log/aegis-waf4.log 
```
8，修改密码
```
用户管理,编辑修改密码，或者添加新的用户删除test用户
```
