from ...common import Label
import abc
import datetime
import json
from typing import *
from .. import driver

__all__ = ["CareerDBLabelMapper"]

#TODO：finish code below
class LabelMapperInterface(abc.ABC):
    """
    Label类的持久化接口类, 所有对Label类的持久化类都应继承本接口类, 并实现接口
    对于仅用于读的持久化数据源 (如txt、JSON文件), 可以将save实现为一个空函数或在函数中raise一个IOError
    """
    @abc.abstractmethod
    def getById(self, id:int) -> Label or None:
        """
        按唯一索引label_id查询返回一个Label. 无结果返回None
        """
        pass

    @abc.abstractmethod
    def getByIdList(self, id_list:int) -> List[Label]:
        """
        按唯一索引label_id列表查询返回一批Label. 无结果返回空列表
        """
        pass

    @abc.abstractmethod
    def getByExpuuid(self, exp_uuid:str) -> List[Label]:
        """
        按exp_uuid查询返回exp_uuid相同的多个Label. 无结果返回空列表
        """
        pass

    @abc.abstractmethod
    def getByExpuuidList(self, exp_uuid_list:List[str]) -> List[Label]:
        """
        按唯exp_uuid_list列表查询返回一批Label. 无结果返回空列表
        """
        pass

    @abc.abstractmethod
    def getByPersonuuid(self, person_uuid:str) -> List[Label]:
        """
        按person_uuid查询返回属于一个Person的多个Label. 无结果返回空列表
        """
        pass

    @abc.abstractmethod
    def getByPersonuuidList(self, person_uuid_list:List[str]) -> List[Label]:
        """
        按person_uuid_list查询返回属于一批Person的所有Label. 无结果返回空列表
        """
        pass

    @abc.abstractmethod
    def getAll(self) -> Iterable[Label]:
        """
        返回全部的Label. 无结果返回空列表
        """
        pass

    @abc.abstractmethod
    def save(self, replace_by:str, label_list: List[Label]) -> int:
        """
        保存一批Label. 返回受影响行数.

        Params:
            replace_by: 指定保存时的替换方式.
                        replace_by="id": 数据库中存在唯一索引相同的记录时，删除原记录，插入新记录.
                        replace_by="exp_uuid": 对label_list中出现的所有exp_uuid, 先删除每一个exp_uuid在数据库中的全部label记录, 再插入label_list
                        replace_by="person_uuid": 对label_list中出现的所有person_uuid, 先删除每一个person_uuid在数据库中的全部label记录, 再插入label_list
                        replace_by="eval_uuid": 对label_list中出现的所有eval_uuid, 先删除每一个eval_uuid在数据库中的全部label记录, 再插入label_list
        """
        pass


class CareerDBLabelMapper(LabelMapperInterface):
    """
    适用于系统内部CAREER数据库的LabelMapper
    """

    __table = "label"                                     # Label类对应数据库表明
    __primary_key = 'label_id'                            # Label类对应数据库主键的属性名
    __attr2field_map = {                                  # Label类实例属性和数据库表字段对应关系以及数据类型
        'label_id': ('label_id', int),
        'label_code': ('label_code', str),
        'label_text': ('label_text', str),
        'label_category': ('label_category', int), 
        'label_source': ('label_source', int),
        'label_info': ('label_info', str),
        'person_uuid': ('person_uuid', str),
        'exp_uuid': ('exp_uuid', str),
        'eval_uuid': ('eval_uuid', str),
        'time_start': ('time_start', datetime.date),
        'time_end': ('time_end', datetime.date)
    }

    def __init__(self, db_obj=None):
        if db_obj:
            self.__db_obj = db_obj  # 数据库操作对象
        else:
            self.__db_obj = driver.MysqlDB() # 默认数据库操作对象
        self.__fields_str = ','.join([v[0] for v in self.__attr2field_map.values()])    # 初始化时把数据库字段列表字符串计算好
        self.__primary_key_db = self.__attr2field_map[self.__primary_key][0]   # 初始化时把数据库主键计算好

    def getById(self, id:int) -> Label or None:
        sql = (
            "SELECT {} FROM {} ".format(self.__fields_str, self.__table) + 
            "WHERE {}=%s".format(self.__primary_key_db)
        )
        res = self.__db_obj.query(sql, (id,))
        if len(res) == 0:
            return None
        return Label(**dict(zip(self.__attr2field_map.keys(), res[0])))
    
    def getByIdList(self, id_list: List[int]) -> List[Label]:
        sql = (
            "SELECT {} FROM {} ".format(self.__fields_str, self.__table) + 
            "WHERE {} IN %s".format(self.__primary_key_db)
        )
        all_res = []
        # 每次使用WHERE IN查询1000个
        for i in range(0, len(id_list), 1000):
            all_res += self.__db_obj.query(sql, (id_list[i:i+1000], ))
        return [Label(**dict(zip(self.__attr2field_map.keys(), res))) for res in all_res]

    def getByExpuuid(self, uuid: str) -> List[Label]:
        sql = (
            "SELECT {} FROM {} ".format(self.__fields_str, self.__table) + 
            "WHERE {}=%s".format(self.__attr2field_map['exp_uuid'][0])
        )
        all_res = self.__db_obj.query(sql, (uuid,))
        return [Label(**dict(zip(self.__attr2field_map.keys(), res))) for res in all_res]

    def getByExpuuidList(self, uuid_list: List[str]) -> List[Label]:
        sql = (
            "SELECT {} FROM {} ".format(self.__fields_str, self.__table) + 
            "WHERE {} IN %s".format(self.__attr2field_map['exp_uuid'][0])
        )
        all_res = []
        # 每次使用WHERE IN查询1000个
        for i in range(0, len(uuid_list), 1000):
            all_res += self.__db_obj.query(sql, (uuid_list[i:i+1000], ))
        return [Label(**dict(zip(self.__attr2field_map.keys(), res))) for res in all_res]

    def getByPersonuuid(self, person_uuid: str) -> List[Label]:
        sql = (
            "SELECT {} FROM {} ".format(self.__fields_str, self.__table) + 
            "WHERE {}=%s".format(self.__attr2field_map['person_uuid'][0])
        )
        all_res = self.__db_obj.query(sql, (person_uuid, ))
        return [Label(**dict(zip(self.__attr2field_map.keys(), res))) for res in all_res]

    def getByPersonuuidList(self, person_uuid_list: List[str]) -> List[Label]:
        sql = (
            "SELECT {} FROM {} ".format(self.__fields_str, self.__table) + 
            "WHERE {} IN %s".format(self.__attr2field_map['person_uuid'][0])
        )
        all_res = []
        # 每次使用WHERE IN查询1000个
        for i in range(0, len(person_uuid_list), 1000):
            all_res += self.__db_obj.query(sql, (person_uuid_list[i:i+1000], ))
        return [Label(**dict(zip(self.__attr2field_map.keys(), res))) for res in all_res]

    def getAll(self) -> Iterable[Label]:
        # TODO 当前只实现了将结果全部fetch到内存中并返回整个列表，需要实现为带Buffer的迭代器以支持内存无法承受的数据量
        sql = (
            "SELECT {} FROM {} ".format(self.__fields_str, self.__table)
        )
        all_res = self.__db_obj.query(sql)
        return [Label(**dict(zip(self.__attr2field_map.keys(), res))) for res in all_res]

    def save(self, replace_by:str, label_list: List[Label]) -> int:
        aff_rows = 0
        if replace_by == "id":
            sql = (
                "REPLACE INTO {} ({}) VALUES %s".format(self.__table, self.__fields_str)
            )
            aff_rows = self.__db_obj.execute_many(sql, [(tuple([label.__getattribute__(attr) for attr in self.__attr2field_map.keys()]), ) for label in label_list])
        
        elif replace_by == "exp_uuid":
            # 获取label_list中所有出现的exp_uuid
            exp_uuid_set = set()
            for label in label_list:
                exp_uuid_set.add(label.exp_uuid)
            exp_uuid_list = list(exp_uuid_set)
            
            # 删除所有exp_uuid_list中的记录
            sql = (
            "DELETE FROM {} ".format(self.__table) + 
            "WHERE {} IN %s".format(self.__attr2field_map['exp_uuid'][0])
            )
            for i in range(0, len(exp_uuid_list), 1000):
                aff_rows += self.__db_obj.execute(sql, (exp_uuid_list[i:i+1000], ))

            # 插入label_list
            sql = (
                "INSERT INTO {} ({}) VALUES %s".format(self.__table, self.__fields_str)
            )
            aff_rows += self.__db_obj.execute_many(sql, [(tuple([label.__getattribute__(attr) for attr in self.__attr2field_map.keys()]), ) for label in label_list])

        elif replace_by == "person_uuid":
            # 获取label_list中所有出现的person_uuid
            person_uuid_set = set()
            for label in label_list:
                person_uuid_set.add(label.person_uuid)
            person_uuid_list = list(person_uuid_set)
            
            # 删除所有exp_uuid_list中的记录
            sql = (
            "DELETE FROM {} ".format(self.__table) + 
            "WHERE {} IN %s".format(self.__attr2field_map['person_uuid'][0])
            )
            for i in range(0, len(person_uuid_list), 1000):
                aff_rows += self.__db_obj.execute(sql, (person_uuid_list[i:i+1000], ))

            # 插入label_list
            sql = (
                "INSERT INTO {} ({}) VALUES %s".format(self.__table, self.__fields_str)
            )
            aff_rows += self.__db_obj.execute_many(sql, [(tuple([label.__getattribute__(attr) for attr in self.__attr2field_map.keys()]), ) for label in label_list])
        
        elif replace_by == "eval_uuid":
            # 获取label_list中所有出现的eval_uuid
            eval_uuid_set = set()
            for label in label_list:
                eval_uuid_set.add(label.eval_uuid)
            eval_uuid_list = list(eval_uuid_set)
            
            # 删除所有exp_uuid_list中的记录
            sql = (
            "DELETE FROM {} ".format(self.__table) + 
            "WHERE {} IN %s".format(self.__attr2field_map['eval_uuid'][0])
            )
            for i in range(0, len(eval_uuid_list), 1000):
                aff_rows += self.__db_obj.execute(sql, (eval_uuid_list[i:i+1000], ))

            # 插入label_list
            sql = (
                "INSERT INTO {} ({}) VALUES %s".format(self.__table, self.__fields_str)
            )
            aff_rows += self.__db_obj.execute_many(sql, [(tuple([label.__getattribute__(attr) for attr in self.__attr2field_map.keys()]), ) for label in label_list])

        else:
            raise ValueError("invalid replace_by value, should be 'id' or 'exp_uuid' or 'person_uuid' or 'eval_uuid'")

        return aff_rows