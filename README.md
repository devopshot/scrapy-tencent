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


#### 分析
pywebio + pyecharts 分析

```python
from pyecharts import options as opts
from pyecharts.charts import Bar, Pie, Map, Geo
from pyecharts.charts import WordCloud
from pyecharts.faker import Faker
from pyecharts.globals import ChartType
from pyecharts.globals import SymbolType
from pywebio.output import put_html
from pywebio.platform.django import webio_view
```
**全国招聘城市**
```python
sql = "select LocationName, COUNT(*) as num  from tencent.tencent WHERE CountryName = '中国' GROUP BY LocationName  ORDER BY num DESC"
    key = []
    value = []
    with MySQLBase(PARAM) as f:
        count, res = f.execute_for_queryAll(sql)
    c = (
        Geo()
            .add_schema(maptype="china")
            .add(
            "",
            [[x[0][:2], x[1]] for x in res],
            type_=ChartType.EFFECT_SCATTER,
        )
            .set_series_opts(label_opts=opts.LabelOpts(is_show=True,formatter='{b|{b}}', rich={
            "b": {"fontSize": 14,},
        }))
            .set_global_opts(
            visualmap_opts=opts.VisualMapOpts(max_=620),
            title_opts=opts.TitleOpts(title="全国招聘", subtitle="哪些城市招聘人数最多"),
        )

    )

    c.width = "100%"
    c.height = "600px"
    put_html(c.render_notebook())
```

**招聘人数国家TOP10**
```python
def bar1():
    sql = "select CountryName, count(*) as num  from tencent.tencent GROUP BY CountryName  ORDER BY num DESC limit 10"
    key = []
    value = []
    with MySQLBase(PARAM) as f:
        count, res = f.execute_for_queryAll(sql)
        value = [x[1] for x in res]
        key = [ x[0] for x in  res]

    c = (
        Bar()
            .add_xaxis(key)
            .add_yaxis("招聘人数", value, category_gap="50%")  # category_gap
            # 柱之间的空隙默认20%
            .set_global_opts(title_opts=opts.TitleOpts(title="腾讯招聘人数国家TOP10"))
    )
    c.width = "100%"
    return put_html(c.render_notebook())
```

**岗位类别占比**
```python
def pie():
    sql = "select CategoryName, count(*) as num  from tencent.tencent where CategoryName != '' GROUP BY CategoryName  ORDER BY num DESC  "
    key = []
    value = []
    with MySQLBase(PARAM) as f:
        count, res = f.execute_for_queryAll(sql)
    c = (
        Pie()
            .add(
            "",
            [list(x) for x in res ],
            center=["50%", "50%"],
        )
            .set_global_opts(
            title_opts=opts.TitleOpts(title="腾讯招聘岗位类别", subtitle="人数及占比"),
            legend_opts=opts.LegendOpts(pos_left="right", orient="vertical"),
        )
            .set_series_opts(label_opts=opts.LabelOpts(formatter="{b|{b}: }{c}  {per|{d}%}  ",
                                                       rich={
                                                           "per": {
                                                               "color": "#eee",
                                                               "backgroundColor": "#334455",
                                                               "padding": [2, 4],
                                                               "borderRadius": 2,
                                                           },
                                                       },
                                                       ))

    )
    c.width = "100%"
    return put_html(c.render_notebook())
```
**各个部门招聘人数**
```python
def bar4():
    sql = "select BGName, COUNT(*) as num  from tencent.tencent  GROUP BY BGName  ORDER BY num  DESC"
    key = []
    value = []
    with MySQLBase(PARAM) as f:
        count, res = f.execute_for_queryAll(sql)
        value = [x[1] for x in res]
        key = [ x[0] for x in  res]
    c = (
        Bar()
            .add_xaxis(key)
            .add_yaxis("", value)
            .reversal_axis()
            .set_series_opts(label_opts=opts.LabelOpts(position="right"))
            .set_global_opts(title_opts=opts.TitleOpts(title="部门招聘岗位"))

    )

    c.width = "100%"
    put_html(c.render_notebook())
```