from typing import Tuple, List, Dict
import abc
import pymysql
from ... import config
import time
import warnings

try:
    from dbutils.pooled_db import PooledDB
except Exception as e:
    print("[WARNING] failed to import PooledDB. System down graded.")



__all__ = ["MysqlDB", "PooledMysqlDB"]


class DBInterface(abc.ABC):
    """
    数据库接口类，所有的数据库访问类都应继承此抽象类，并实现接口
    """
    @abc.abstractmethod
    def connect():
        """
        获取数据库链接的接口，应返回一个数据库连接。
        """
        pass

    @abc.abstractmethod
    def query():
        """
        单条语句查询接口，应返回结果集
        """
        pass

    @abc.abstractmethod
    def query_many():
        """
        单条语句多次查询接口，应返回合并后的结果集
        """

    @abc.abstractmethod
    def execute():
        """
        单条语句执行接口，应返回受影响的行数
        """

    @abc.abstractmethod
    def execute_many():
        """
        单条语句多次执行接口，应返回受影响的行数总数
        """

    
class MysqlDB(DBInterface):
    """
    对mysql驱动的普通封装.


    """
    def __init__(self, config:Dict=config.careerDB_config):
        self.config = config

    def __get_connection(self):
        while(True):
            try:
                conn = pymysql.connect(autocommit=False, **self.config)
            except Exception as E:
                print('Error connecting to database:{0}'.format(E))
                print('Reconnect in 3 sec...')
                time.sleep(3)
            else:
                break
        return conn
            
    def connect(self):
        return self.__get_connection()

    def query(self, sql:str, args:Tuple=None):
        conn = self.__get_connection()
        cursor = conn.cursor()

        aff_rows = cursor.execute(sql, args)
        res = cursor.fetchall()

        conn.commit()
        conn.close()

        return res

    def query_many(self, sql:str, args_list:List[Tuple]):
        conn = self.__get_connection()
        cursor = conn.cursor()

        aff_rows = cursor.executemany(sql, args_list)
        res = cursor

        conn.commit()
        conn.close()

        return res

    def execute(self, sql:str, args:Tuple=None):
        conn = self.__get_connection()
        cursor = conn.cursor()

        conn.begin()
        try:
            aff_rows = cursor.execute(sql, args)
        except Exception as e:
            conn.rollback()
            print("Database Error: {}".format(str(e)))
            print("Database execution canceled, database rollback completed.")
            aff_rows = None
        else:
            conn.commit()
        conn.close()
        return aff_rows

    def execute_many(self, sql:str, args_list:List[Tuple]):
        conn = self.__get_connection()
        cursor = conn.cursor()

        conn.begin()
        try:
            aff_rows = cursor.executemany(sql, args_list)
        except Exception as e:
            conn.rollback()
            print("Database Error: {}".format(str(e)))
            print("Database execution canceled, database rollback completed.")
            aff_rows = None
        else:
            conn.commit()
        conn.close()
        return aff_rows


class PooledMysqlDB(DBInterface):
    """
    对MySQL数据库连接池的封装.
    本类所有实例共享一个数据库连接池, 连接池在第一个实例创建时初始化, 故config参数仅在第一个实例创建时生效.
    """
    __pool = None       # 连接池对象，只在PooledMysqlDB第一次实例化的时候创建，所有实例共享
    __config = None     # 连接配置

    def __init__(self, config:Dict=config.careerDB_config):
        if not self.__pool:
            self.__init_pool(config)
 
    @classmethod
    def __init_pool(cls, config):
        cls.__config = config
        while(True):
            try:
                cls.__pool = PooledDB(pymysql, 
                                mincached=4, 
                                maxcached=None,
                                maxshared=None,
                                maxconnections = 0, 
                                blocking = False, 
                                maxusage = None, 
                                setsession = None, 
                                reset = True, 
                                failures = None, 
                                ping = 1,
                                autocommit=False,
                                **cls.__config)
            except Exception as E:
                print('Error initializing database connection pool:{0}'.format(E))
                print('Retry in 3 sec...')
                time.sleep(3)
            else:
                break

    def __get_connection(self):
        return self.__pool.connection(shareable=False)
    
    def connect(self):
        return self.__get_connection()

    def query(self, sql:str, args:Tuple=None):
        conn = self.__get_connection()
        cursor = conn.cursor()

        aff_rows = cursor.execute(sql, args)
        res = cursor.fetchall()

        conn.commit()
        conn.close()

        return res

    def query_many(self, sql:str, args_list:List[Tuple]):
        conn = self.__get_connection()
        cursor = conn.cursor()

        aff_rows = cursor.executemany(sql, args_list)
        res = cursor

        conn.commit()
        conn.close()

        return res

    def execute(self, sql:str, args:Tuple=None):
        conn = self.__get_connection()
        cursor = conn.cursor()

        conn.begin()
        try:
            aff_rows = cursor.execute(sql, args)
        except Exception as e:
            conn.rollback()
            print("Database Error: {}".format(str(e)))
            print("Database execution canceled, database rollback completed.")
            aff_rows = None
        else:
            conn.commit()
        conn.close()
        return aff_rows

    def execute_many(self, sql:str, args_list:List[Tuple]):
        conn = self.__get_connection()
        cursor = conn.cursor()

        conn.begin()
        try:
            aff_rows = cursor.executemany(sql, args_list)
        except Exception as e:
            conn.rollback()
            print("Database Error: {}".format(str(e)))
            print("Database execution canceled, database rollback completed.")
            aff_rows = None
        else:
            conn.commit()
        conn.close()
        return aff_rows
