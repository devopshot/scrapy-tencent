# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import codecs
import json
from pymysql.cursors import DictCursor
from twisted.enterprise import adbapi


class TencentMysqlPipeline(object):

    def __init__(self, dbpool, table_name):
        self.dbpool = dbpool
        self.table_name = table_name

    @classmethod
    def from_crawler(cls, crawler):
        table_name = crawler.settings.get('TABLE_NAME')
        dbparams = dict(
            host=crawler.settings['MYSQL_HOST'],  # 读取settings中的配置
            db=crawler.settings['MYSQL_DB'],
            user=crawler.settings['MYSQL_USER'],
            passwd=crawler.settings['MYSQL_PASSWD'],
            port=int(crawler.settings['MYSQL_PORT']),
            charset=crawler.settings['MYSQL_CHARSET'],  # 编码要加上，否则可能出现中文乱码问题
            connect_timeout=int(crawler.settings['MYSQL_TIMEOUT']),
            cursorclass=DictCursor,
        )
        dbpool = adbapi.ConnectionPool("pymysql", **dbparams)
        return cls(
            dbpool=dbpool,
            table_name=table_name
        )

    def process_item(self, item, spider):
        # 使用Twisted将mysql插入变成异步执行,runInteraction可以将传入的函数变成异步的
        try:
            query = self.dbpool.runInteraction(self._do_insert, item, spider)  # 调用插入的方法
            query.addErrback(self._handle_error, item, spider)  # 调用异常处理方法
        except Exception as err:
            spider.logger.info("错误发生 %s" % str(err))
        return item

    def _do_insert(self, tx, item, spider):
        """插入数据库"""
        sql = """insert into {} (RecruitPostName,CountryName,LocationName,BGName,
                          CategoryName, Responsibility,LastUpdateTime)
                    values(%s,%s,%s,%s,%s,%s,%s)""".format(self.table_name)
        params = (
            item['RecruitPostName'],
            item['CountryName'],
            item['LocationName'],
            item['BGName'],
            item['CategoryName'],
            item['Responsibility'],
            item['LastUpdateTime']
        )
        spider.logger.info("插入数据： %s: [%s]" % (spider.name, item['RecruitPostName']))
        tx.execute(sql, params)

    def _handle_error(self, failue, item, spider):
        spider.logger.error('[%s] Spider update to database error: %s \
                 when dealing with site: %s' % (spider.name, failue.value, item.get('site_name')))