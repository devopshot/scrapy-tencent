# -*- coding: utf-8 -*
import logging
import pymysql
from collections import namedtuple

logger  = logging.getLogger(__file__)

__all__ = ['MySQLBase', 'MySQLPool']


class MySQLPool(object):
    """"""

    def __init__(self, DBconf, sql=None, num=1000):
        self.dbconf = DBconf
        self.sql = sql
        self.num = num

    def __enter__(self):
        try:
            self.cnx = self.__connect_remote()
            self.cursor = self.cnx.cursor()
        except pymysql.Error:
            pass
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __connect_remote(self):
        try:
            return pymysql.connect(
                host=self.dbconf.get("ip"),
                user=self.dbconf.get("db_user"),
                password=self.dbconf.get("db_passwd"),
                port=self.dbconf.get("db_port"),
                db=self.dbconf.get("db_name"),
                connect_timeout=self.dbconf.get("timeout", 3),
                max_allowed_packet=1024 * 1024 * 1024,
                charset='utf8'
            )
        except pymysql.Error as ef:
            logger.error("连接数据库失败: {ef}".format(ef=ef.__str__()))
            raise pymysql.Error(ef.__str__())

    def dictfetchall(self):
        "Return all rows from a cursor as a dict"
        columns = [col[0] for col in self.cursor.description]

        return [
            dict(zip(columns, row))
            for row in self.cursor.fetchall()
        ]

    def namedtuplefetchall(self):
        "Return all rows from a cursor as a namedtuple"
        desc = self.cursor.description
        nt_result = namedtuple('Result', [col[0] for col in desc])
        return [nt_result(*row) for row in self.cursor.fetchall()]

    def execute_for_query(self, sql, num=1000):
        try:
            count = self.execute(sql)
            col = self.dictfetchall()
            result = self.fetchmany(num=num)
            return count, result, col
        except pymysql.Error as ef:
            logger.error("数据库操作失败: {ex}".format(ex=str(ef)))
            return -1

    def execute_for_queryOne(self, sql):
        try:
            count = self.execute(sql)
            result = self.fetchone()
            return count, result
        except pymysql.Error as ef:
            logger.error("数据库操作失败: {ex}".format(ex=str(ef)))
            return ef.__str__()

    def execute_for_queryAll(self, sql):
        try:
            count = self.execute(sql)
            result = self.fetchall()
            return count, result
        except pymysql.Error as ef:
            logger.error("数据库操作失败: {ex}".format(ex=str(ef)))
            return ef.__str__()

    def execute_for_commit(self, sql, num=1000):
        try:
            count = self.execute(sql)
            col = self.dictfetchall()
            result = self.fetchmany()
            self.cnx.commit()
            return count, result, col
        except pymysql.Error as ef:
            logger.error("数据库操作失败: {ex}".format(ex=str(ef)))
            return -1

    def execute(self, sql):
        return self.cursor.execute(sql)

    def fetchall(self):
        return self.cursor.fetchall()

    def fetchmany(self, num=1000):
        return self.cursor.fetchmany(size=num)

    def fetchone(self):
        return self.cursor.fetchone()

    def close(self):
        if hasattr(self, 'cnx')and self.cnx:
            self.cnx.close()

    def get_value(self):
        pass


class MySQLBase(MySQLPool):

    def get_processlists(self):
        """获取连接进程信息"""
        sql = """select id,user,host,db,time,state,command,info from information_schema.processlist;"""
        return self.execute_for_query(sql)

    def get_db_size(self):
        """获取库的大小"""
        dataList = []
        sql = """SELECT table_schema, Round(Sum(data_length + index_length) / 1024 / 1024, 1) as size,count(TABLE_NAME) as total_table
													FROM information_schema.tables where table_schema not in ("performance_schema","information_schema","mysql","sys")
													GROUP BY table_schema;"""
        db_size = self.execute_for_query(sql)
        if isinstance(db_size, tuple):
            for ds in db_size[1]:
                dataList.append({"db_name": ds[0], "size": ds[1], "total_table": ds[2]})
        return dataList

    def get_db_tables(self, dbname):
        dataList = []
        sql = """SELECT TABLE_NAME,TABLE_COMMENT,ENGINE,ROW_FORMAT,CREATE_TIME,TABLE_ROWS FROM 
		INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA='{dbname}';""".format(dbname=dbname)
        data = self.execute_for_query(sql)
        if isinstance(data, tuple):
            for ds in data[1]:
                dataList.append({"TABLE_NAME": ds[0], "TABLE_COMMENT": ds[1], "ENGINE": ds[2], "ROW_FORMAT": ds[3],
                                 "CREATE_TIME": ds[4], "TABLE_ROWS": ds[5]})
        return dataList

    def get_db_table_info(self, dbname):
        dataList = []
        sql = """select table_schema,table_name,table_rows,round((DATA_LENGTH+INDEX_LENGTH)/1024/1024,2) as size,engine,
		row_format,table_collation from information_schema.tables where table_schema = '{dbname}' 
		order by table_rows desc;""".format(dbname=dbname)
        data = self.execute_for_query(sql)
        if isinstance(data, tuple):
            for ds in data[1]:
                dataList.append(
                    {"db_name": ds[0], "table_name": ds[1], "table_rows": ds[2], "table_size": ds[3], "engine": ds[4],
                     "row_format": ds[5], "table_collation": ds[6]})
        return dataList

    def get_db_table_columns(self, dbname, table_name):
        dataList = []
        sql = """SELECT COLUMN_NAME,COLUMN_TYPE,ifnull(COLUMN_DEFAULT,''),IS_NULLABLE,EXTRA,COLUMN_KEY,COLUMN_COMMENT
		FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA='{dbname}' AND TABLE_NAME='{table_name}';""".format(
            dbname=dbname, table_name=table_name)
        data = self.execute_for_query(sql)
        if isinstance(data, tuple):
            for ds in data[1]:
                dataList.append(
                    {"COLUMN_NAME": ds[0], "COLUMN_TYPE": ds[1], "COLUMN_DEFAULT": ds[2], "IS_NULLABLE": ds[3], "EXTRA": ds[4],
                     "COLUMN_KEY": ds[5], "COLUMN_COMMENT": ds[6]})
        return dataList

    def get_tables(self):
        data = self.execute_for_query('show tables', 10000)
        return data

    def get_table_schema(self, dbname, table):
        sql = """SELECT TABLE_SCHEMA,TABLE_NAME,TABLE_TYPE,ENGINE,VERSION,ROW_FORMAT,
		TABLE_ROWS,concat(round(sum(DATA_LENGTH/1024/1024),2),'MB') AS DATA_LENGTH,
		MAX_DATA_LENGTH,concat(round(sum(INDEX_LENGTH/1024/1024),2),'MB') AS INDEX_LENGTH,
		DATA_FREE,AUTO_INCREMENT,CREATE_TIME,TABLE_COLLATION,TABLE_COMMENT FROM information_schema.TABLES 
		WHERE  TABLE_SCHEMA='{db}' AND TABLE_NAME='{table}';""".format(db=dbname, table=table)
        data = self.execute_for_query(sql, num=1000)
        return data

    def get_table_index(self, table):
        data = self.execute_for_query(sql="""SHOW index FROM `{table}`;""".format(table=table), num=1000)
        return data

    def get_table_desc(self, table):
        data = self.execute_for_query(sql="""show create table `{table}`;""".format(table=table), num=1000)
        return data

    def get_status(self):
        status = self.execute_for_query(sql='show status;')
        dataList = []
        if isinstance(status, tuple):
            for ds in status[1]:
                data = {'value': ds[1], 'name': ds[0].capitalize()}
                dataList.append(data)
        return dataList

    def get_global_status(self):
        dataList = []
        logs = self.execute_for_query(sql='show global variables;')
        if isinstance(logs, tuple):
            for ds in logs[1]:
                data = {'value': ds[1], 'name': ds[0].capitalize()}
                dataList.append(data)
        return dataList

    def get_master_status(self):
        masterList = []
        master_status = self.execute_for_query(sql='show master status;')
        slave_host = self.execute_for_query(
            sql="SELECT host FROM INFORMATION_SCHEMA.PROCESSLIST WHERE COMMAND='Binlog Dump';")
        if isinstance(master_status, tuple) and master_status[1]:
            count = 0
            for ds in master_status[2]:
                data = {"name": ds, "value": master_status[1][0][count]}
                count = count + 1
                masterList.append(data)
        if isinstance(slave_host, tuple) and slave_host[1]:
            sList = []
            for ds in slave_host[1]:
                sList.append(ds[0])
            masterList.append({"name": "Slave", "value": sList})
        return masterList

    def get_slave_status(self):
        slaveList = []
        slave_status = self.execute_for_query(sql="show slave status;")
        if isinstance(slave_status, tuple) and slave_status[1]:
            count = 0
            for ds in slave_status[2]:
                data = {}
                if ds.lower() in self.slave_key_list:
                    data["name"] = ds
                    data["value"] = slave_status[1][0][count]
                    slaveList.append(data)
                count = count + 1
        return slaveList

if __name__ == '__main__':
    d = dict(db_user="root", ip="10.4.55.209", db_passwd="passwd", db_port=12306,
             charset="utf8")
    sql = """select LocationName, COUNT(*) as num  from tencent.tencent WHERE CountryName = '中国' GROUP BY LocationName  ORDER BY num DESC"""
    with MySQLBase(d) as f:
        count, res = f.execute_for_queryAll(sql)
        print(res)

