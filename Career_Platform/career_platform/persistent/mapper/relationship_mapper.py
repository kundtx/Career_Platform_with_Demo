import abc
import datetime
import json
from typing import *
from ...common import Relationship
from .. import driver

__all__ = ["CareerDBRelationshipMapper"]

class RelationshipMapperInterface(abc.ABC):
    """
    Relationship类的持久化接口类, 所有对Relationship类的持久化类都应继承本接口类, 并实现接口
    对于仅用于读的持久化数据源(如txt、JSON文件), 可以将save实现为一个空函数或在函数中raise一个IOError
    """
    @abc.abstractmethod
    def getById(self, id:int) -> Relationship or None:
        """
        按唯一索引rel_id查询返回一个Relationship. 无结果返回None
        """
        pass

    @abc.abstractmethod
    def getByIdList(self, id_list:List[int]) -> List[Relationship]:
        """
        按唯一索引rel_id列表查询返回一批Relationship. 无结果返回空列表
        """
        pass

    @abc.abstractmethod
    def getByExpuuid(self, uuid:str) -> List[Relationship]:
        """
        按exp_uuid查询返回exp_uuid_from匹配的多个Relationship. 无结果返回空列表
        """
        pass

    @abc.abstractmethod
    def getByExpuuidList(self, uuid_list:List[str]) -> List[Relationship]:
        """
        按唯exp_uuid_list列表查询exp_uuid_from匹配的一批Relationship. 无结果返回空列表
        """
        pass

    @abc.abstractmethod
    def getByPersonuuid(self, person_uuid:str) -> List[Relationship]:
        """
        按person_uuid查询返回属于一个Person(即person_uuid_from匹配)的多个Relationship. 无结果返回空列表
        """
        pass

    @abc.abstractmethod
    def getByPersonuuidList(self, person_uuid_list:List[str]) -> List[Relationship]:
        """
        按person_uuid_list查询返回属于一批Person(即person_uuid_from匹配)的所有Relationship. 无结果返回空列表
        """
        pass

    @abc.abstractmethod
    def getAll(self) -> Iterable[Relationship]:
        """
        返回全部的Relationship. 无结果返回空列表
        """
        pass

    @abc.abstractmethod
    def save(self, replace_by:str, rel_list: List[Relationship]) -> int:
        """
        保存一批Relationship. 返回受影响行数.

        Params:
            replace_by：指定保存时的替换方式.
                        replace_by="id": 数据库中存在rel_id相同的记录时, 删除原记录, 插入新记录.
                        replace_by="exp_uuid": 对rel_list中出现的所有exp_uuid_from, 先删除每一个exp_uuid_from的全部记录, 再插入rel_list
                        replace_by="person_uuid": 对rel_list中出现的所有person_uuid_from, 先删除每一个person_uuid_from的全部记录, 再插入rel_list
        """
        pass


class CareerDBRelationshipMapper(RelationshipMapperInterface):
    """
    适用于系统内部CAREER数据库的RelationshipMapper
    """

    __table = "relationship"                            # Relationship类对应数据库表明
    __primary_key = 'rel_id'                            # Relationship类对应数据库主键的属性名
    __attr2field_map = {                                # Relationship类实例属性和数据库表字段对应关系以及数据类型
        'rel_id': ('rel_id', int),
        'rel_type': ('rel_type', int),
        'person_uuid_from': ('person_uuid_from', str), 
        'person_uuid_to': ('person_uuid_to', str),
        'exp_uuid_from': ('exp_uuid_from', str),
        'exp_uuid_to': ('exp_uuid_to', str),
        'time_start': ('time_start', datetime.date), 
        'time_end': ('time_end', datetime.date),
        'rel_info': ('rel_info', str)
    }

    def __init__(self, db_obj=None):
        if db_obj:
            self.__db_obj = db_obj  # 数据库操作对象
        else:
            self.__db_obj = driver.MysqlDB() # 默认数据库操作对象
        self.__fields_str = ','.join([v[0] for v in self.__attr2field_map.values()])    # 初始化时把数据库字段列表字符串计算好
        self.__primary_key_db = self.__attr2field_map[self.__primary_key][0]   # 初始化时把数据库主键计算好

    def getById(self, id:int) -> Relationship or None:
        sql = (
            "SELECT {} FROM {} ".format(self.__fields_str, self.__table) + 
            "WHERE {}=%s".format(self.__primary_key_db)
        )
        res = self.__db_obj.query(sql, (id,))
        if len(res) == 0:
            return None
        return Relationship(**dict(zip(self.__attr2field_map.keys(), res[0])))
    
    def getByIdList(self, id_list: List[int]) -> List[Relationship]:
        sql = (
            "SELECT {} FROM {} ".format(self.__fields_str, self.__table) + 
            "WHERE {} IN %s".format(self.__primary_key_db)
        )
        all_res = []
        # 每次使用WHERE IN查询1000个
        for i in range(0, len(id_list), 1000):
            all_res += self.__db_obj.query(sql, (id_list[i:i+1000], ))
        return [Relationship(**dict(zip(self.__attr2field_map.keys(), res))) for res in all_res]

    def getByExpuuid(self, uuid: str) -> List[Relationship]:
        sql = (
            "SELECT {} FROM {} ".format(self.__fields_str, self.__table) + 
            "WHERE {}=%s".format(self.__attr2field_map['exp_uuid_from'][0])
        )
        all_res = self.__db_obj.query(sql, (uuid,))
        return [Relationship(**dict(zip(self.__attr2field_map.keys(), res))) for res in all_res]

    def getByExpuuidList(self, uuid_list: List[str]) -> List[Relationship]:
        sql = (
            "SELECT {} FROM {} ".format(self.__fields_str, self.__table) + 
            "WHERE {} IN %s".format(self.__attr2field_map['exp_uuid_from'][0])
        )
        all_res = []
        # 每次使用WHERE IN查询1000个
        for i in range(0, len(uuid_list), 1000):
            all_res += self.__db_obj.query(sql, (uuid_list[i:i+1000], ))
        return [Relationship(**dict(zip(self.__attr2field_map.keys(), res))) for res in all_res]

    def getByPersonuuid(self, person_uuid: str) -> List[Relationship]:
        sql = (
            "SELECT {} FROM {} ".format(self.__fields_str, self.__table) + 
            "WHERE {}=%s".format(self.__attr2field_map['person_uuid_from'][0])
        )
        all_res = self.__db_obj.query(sql, (person_uuid, ))
        return [Relationship(**dict(zip(self.__attr2field_map.keys(), res))) for res in all_res]

    def getByPersonuuidList(self, person_uuid_list: List[str]) -> List[Relationship]:
        sql = (
            "SELECT {} FROM {} ".format(self.__fields_str, self.__table) + 
            "WHERE {} IN %s".format(self.__attr2field_map['person_uuid_from'][0])
        )
        all_res = []
        # 每次使用WHERE IN查询1000个
        for i in range(0, len(person_uuid_list), 1000):
            all_res += self.__db_obj.query(sql, (person_uuid_list[i:i+1000], ))
        return [Relationship(**dict(zip(self.__attr2field_map.keys(), res))) for res in all_res]

    def getAll(self) -> Iterable[Relationship]:
        # TODO 当前只实现了将结果全部fetch到内存中并返回整个列表，需要实现为带Buffer的迭代器以支持内存无法承受的数据量
        sql = (
            "SELECT {} FROM {} ".format(self.__fields_str, self.__table)
        )
        all_res = self.__db_obj.query(sql)
        return [Relationship(**dict(zip(self.__attr2field_map.keys(), res))) for res in all_res]

    def save(self, replace_by:str, relationship_list: List[Relationship]) -> int:
        aff_rows = 0
        if replace_by == "id":
            sql = (
                "REPLACE INTO {} ({}) VALUES %s".format(self.__table, self.__fields_str)
            )
            aff_rows = self.__db_obj.execute_many(sql, [(tuple([relationship.__getattribute__(attr) for attr in self.__attr2field_map.keys()]), ) for relationship in relationship_list])
        
        elif replace_by == "exp_uuid":
            # 获取relationship_list中所有出现的exp_uuid_from
            exp_uuid_set = set()
            for relationship in relationship_list:
                if relationship.exp_uuid_from is None:
                    continue
                exp_uuid_set.add(relationship.exp_uuid_from)
            exp_uuid_list = list(exp_uuid_set)
            
            # 删除所有exp_uuid_list中的记录
            sql = (
            "DELETE FROM {} ".format(self.__table) + 
            "WHERE {} IN %s".format(self.__attr2field_map['exp_uuid_from'][0])
            )
            for i in range(0, len(exp_uuid_list), 1000):
                aff_rows += self.__db_obj.execute(sql, (exp_uuid_list[i:i+1000], ))

            # 插入relationship_list
            sql = (
                "INSERT INTO {} ({}) VALUES %s ON DUPLICATE KEY UPDATE rel_id=rel_id".format(self.__table, self.__fields_str)
            )
            aff_rows += self.__db_obj.execute_many(sql, [(tuple([relationship.__getattribute__(attr) for attr in self.__attr2field_map.keys()]), ) for relationship in relationship_list])

        elif replace_by == "person_uuid":
            # 获取relationship_list中所有出现的person_uuid_from
            person_uuid_set = set()
            for relationship in relationship_list:
                if relationship.person_uuid_from is None:
                    continue
                person_uuid_set.add(relationship.person_uuid_from)
            person_uuid_list = list(person_uuid_set)
            
            # 删除所有exp_uuid_list中的记录
            sql = (
            "DELETE FROM {} ".format(self.__table) + 
            "WHERE {} IN %s".format(self.__attr2field_map['person_uuid_from'][0])
            )
            for i in range(0, len(person_uuid_list), 1000):
                aff_rows += self.__db_obj.execute(sql, (person_uuid_list[i:i+1000], ))

            # 插入relationship_list
            sql = (
                "INSERT INTO {} ({}) VALUES %s ON DUPLICATE KEY UPDATE rel_id=rel_id".format(self.__table, self.__fields_str)
            )
            aff_rows += self.__db_obj.execute_many(sql, [(tuple([relationship.__getattribute__(attr) for attr in self.__attr2field_map.keys()]), ) for relationship in relationship_list])

        else:
            raise ValueError("invalid replace_by value, should be 'id' or 'exp_uuid' or 'person_uuid' ")

        return aff_rows