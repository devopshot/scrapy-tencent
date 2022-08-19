##  selenium + Firefox + Scrapy + mysql 爬虫实例

#### 目标站点
 腾讯招聘 https://careers.tencent.com/search.html

#### 安装依赖
```angular2html
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
```

#### 安装firefox驱动
下载 https://github.com/mozilla/geckodriver/releases/download/v0.31.0/geckodriver-v0.31.0-win64.zip
解压到项目根目录

#### 创建数据库表
```sql
DROP TABLE IF EXISTS `tencent`;
CREATE TABLE `tencent` (
  `RecruitPostName` varchar(255) NOT NULL COMMENT '职位名称',
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `CountryName` varchar(50) DEFAULT NULL,
  `LocationName` varchar(100) NOT NULL,
  `BGName` varchar(100) DEFAULT NULL,
  `CategoryName` varchar(100) DEFAULT NULL,
  `Responsibility` text NOT NULL,
  `LastUpdateTime` date NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_toger_unique` (`RecruitPostName`,`LocationName`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=3762 DEFAULT CHARSET=utf8mb4;
```

#### 配置
```
ROBOTSTXT_OBEY = False
# MYSQL
MYSQL_DB = "tencent"
MYSQL_USER = "root"
MYSQL_PASSWD = "xx"
MYSQL_HOST = "192.168.10.1"
MYSQL_TIMEOUT = '2'
MYSQL_CHARSET = 'utf8'
MYSQL_PORT = "12306"
TABLE_NAME = 'tencent'
```

#### 启动
```angular2html
scrapy crawl tencent
```

#### 服务的方式部署
编辑scrapy.cfg 指定scrapyd接口地址
```
[deploy:test]
url = http://服务IP:6800/
project = Tencent
```
部署 `scrapyd-deploy test --include-dependencies` 
