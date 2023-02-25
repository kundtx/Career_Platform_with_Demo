import abc
import datetime
import json
from typing import *
from ...common import Relative
from .. import driver
import re


__all__ = ["CareerDBRelativeMapper", "DatacenterRelativeMapper"]


class RelativeMapperInterface(abc.ABC):
    """
    Relative类的持久化接口类, 所有对Relative类的持久化类都应继承本接口类, 并实现接口
    对于仅用于读的持久化数据源(如txt、JSON文件), 可以将save实现为一个空函数或在函数中raise一个IOError
    """
    @abc.abstractmethod
    def getById(self, id: str) -> Relative or None:
        pass

    @abc.abstractmethod
    def getByIdList(self, id_list: List[str]) -> List[Relative]:
        pass

    @abc.abstractmethod
    def getByPersonuuid(self, person_uuid:str) -> List[Relative]:
        pass

    @abc.abstractmethod
    def getByPersonuuidList(self, person_uuid_list:List[str]) -> List[Relative]:
        pass
    
    # @abc.abstractmethod
    # def getByRelPersonuuid(self, person_uuid:str) -> List[Relative]:
    #     pass

    # @abc.abstractmethod
    # def getByRelPersonuuidList(self, person_uuid_list:List[str]) -> List[Relative]:
    #     pass

    @abc.abstractmethod
    def getAll(self) -> Iterable[Relative]:
        pass

    @abc.abstractmethod
    def save(self, relative_list: List[Relative]) -> int:
        pass

    @abc.abstractmethod
    def updateRelativeUuid(self) -> int:
        """
        更新亲属的UUID
        通过姓名与生日得到person表中的uuid
        """
        pass

    @abc.abstractmethod
    def getUpdateLastTime(self) -> datetime.date:
        """
        获取最后的更新时间
        """
        pass

    @abc.abstractmethod
    def getByUpdatetime(self, time_update: datetime.date) -> List[Relative]:
        """
        按 更新时间 查询返回在更新时间之后的所有 Relative. 无结果返回空列表
        """
        pass


class CareerDBRelativeMapper(RelativeMapperInterface):
    """
    适用于系统内部CAREER数据库的RelativeMapper
    """

    __table = "person_relative"                        # Relative类对应数据库表名
    __primary_key = 'relative_id'                      # Relative类对应数据库表主键的属性名
    __attr2field_map = {                        # Relative类实例属性和数据库表字段对应关系以及数据类型
        'relative_id': ('relative_id', str),
        'relative_name': ('relative_name', str),
        'relative_birthday': ('relative_birthday', datetime.date),
        'relative_type': ('relative_type', str),
        'relative_uuid': ('relative_uuid', str),
        'person_uuid': ('person_uuid', str)
        # 'time_update': ('time_update', datetime.date)  # 根据更新时间同步最新数据
    }

    def __init__(self, db_obj=None):
        if db_obj:
            self.__db_obj = db_obj  # 数据库操作对象
        else:
            self.__db_obj = driver.MysqlDB() # 默认数据库操作对象
        self.__fields_str = ','.join([v[0] for v in self.__attr2field_map.values()]) # 初始化时把数据库字段列表字符串计算好

    def getById(self, id: str) -> Relative or None:
        """
        按唯一索引列表查询Relative. 无结果返回None
        """
        sql = (
            "SELECT {} FROM {} ".format(self.__fields_str, self.__table) +
            "WHERE {}=%s".format(self.__attr2field_map[self.__primary_key][0])
        )
        res = self.__db_obj.query(sql, (id,))
        if len(res) == 0:
            return None
        return Relative(**dict(zip(self.__attr2field_map.keys(), res[0])))

    def getByIdList(self, id_list: List[str]) -> Iterable[Relative]:
        """
        按唯一索引列表查询对应Relative列表. 无结果返回空列表.
        注意,返回的Relative列表可能和传入的id_list长度不一样!请考虑到id_list中某些id可能在数据库没有对应记录,以及数据库的事务隔离问题！
        """
        # TODO 当前只实现了将结果全部fetch到内存中返回整个列表，需要实现为带Buffer的迭代器以支持内存无法承受的数据量
        sql = (
            "SELECT {} FROM {} ".format(self.__fields_str, self.__table) +
            "WHERE {} IN %s".format(self.__attr2field_map[self.__primary_key][0])
        )
        all_res = []
        # 每次使用WHERE IN查询1000个
        for i in range(0, len(id_list), 1000):
            all_res += self.__db_obj.query(sql, (id_list[i:i+1000], ))
        return [Relative(**dict(zip(self.__attr2field_map.keys(), res))) for res in all_res]

    def getByPersonuuid(self, person_uuid:str) -> List[Relative]:
        sql = (
            "SELECT {} FROM {} ".format(self.__fields_str, self.__table) +
            "WHERE {}=%s".format(self.__attr2field_map['person_uuid'][0])
        )
        res = self.__db_obj.query(sql, (id,))
        if len(res) == 0:
            return None
        return Relative(**dict(zip(self.__attr2field_map.keys(), res[0])))

    def getByPersonuuidList(self, person_uuid_list:List[str]) -> List[Relative]:
        sql = (
            "SELECT {} FROM {} ".format(self.__fields_str, self.__table) +
            "WHERE {} IN %s".format(self.__attr2field_map['person_uuid'][0])
        )
        all_res = []
        # 每次使用WHERE IN查询1000个
        for i in range(0, len(person_uuid_list), 1000):
            all_res += self.__db_obj.query(sql, (person_uuid_list[i:i+1000], ))
        return [Relative(**dict(zip(self.__attr2field_map.keys(), res))) for res in all_res]

    def getAll(self) -> Iterable[Relative]:
        """
        返回数据库中全部Relative. 无结果返回空迭代器.
        注意,返回的Relative列表可能和传入的id_list长度不一样!请考虑到id_list中某些id可能在数据库没有对应记录,以及数据库的事务隔离问题！
        """
        # TODO 当前只实现了将结果全部fetch到内存中并返回整个列表，需要实现为带Buffer的迭代器以支持内存无法承受的数据量
        sql = (
            "SELECT {} FROM {} ".format(self.__fields_str, self.__table)
        )
        all_res = self.__db_obj.query(sql)
        return [Relative(**dict(zip(self.__attr2field_map.keys(), res))) for res in all_res]

    def save(self, relative_list: List[Relative]) -> int:
        sql = (
            "REPLACE INTO {} ({}) VALUES %s".format(self.__table, self.__fields_str)
        )
        aff_rows = self.__db_obj.execute_many(sql, [(tuple([relative.__getattribute__(attr) for attr in self.__attr2field_map.keys()]), ) for relative in relative_list])
        return aff_rows

    def updateRelativeUuid(self) -> int:
        sql = f'''
            UPDATE {self.__table} 
                SET relative_uuid = (
                    SELECT
                        person_uuid 
                    FROM
                        person 
                    WHERE
                        person_name = relative_name 
                        AND time_birth = relative_birthday)
            '''
        return self.__db_obj.execute(sql)

    def getUpdateLastTime(self) -> datetime.date:
        sql = f"select max(time_update) as time_update from {self.__table}"
        all_res = self.__db_obj.query(sql)
        return all_res[0][0] if all_res[0][0] else datetime.date(2000, 1, 1)

    def getByUpdatetime(self, time_update: datetime.date) -> List[Relative]:
        pass


class DatacenterRelativeMapper(RelativeMapperInterface):
    """
    适用于数据中心的RelativeMapper
    """    
    __A36 = "ods.ods_gb_v721_szdp_a36_cur"
    
    __table = "{} A36".format(__A36)                    # Relative类对应数据库表名
    __primary_key = 'relative_id'                          # Relative类对应数据库表主键的属性名
    __attr2field_map = {                                # Relative类实例属性和数据库表字段对应关系以及数据类型
        'relative_id': ('recordid', str),
        'relative_name': ('a3601', str),
        'relative_birthday': ('A3607', datetime.date),
        'relative_type': ('a3604b', str),
        # 'relative_uuid': ('relative_uuid', str),
        'person_uuid': ('a00', str),

        # 'relative_level': ('relative_level', str),
        'delflag': ('DELFLAG', str),
        # 'time_update': ('UPDATETIME', datetime.date)
    }

    def __init__(self, db_obj=None):
        if db_obj:
            self.__db_obj = db_obj  # 数据库操作对象
        else:
            self.__db_obj = driver.DamengDB() # 默认数据库操作对象
        self.__fields_str = ','.join([v[0] for v in self.__attr2field_map.values()]) # 初始化时把数据库字段列表字符串计算好

    def __format_dict(self, raw_dict:Dict[str, Any]) -> Dict[str, Any]:
        if raw_dict["relative_birthday"]:
            raw_dict["relative_birthday"] = datetime.date(raw_dict["relative_birthday"].date().year, raw_dict["relative_birthday"].date().month,1)

        # if isinstance(raw_dict["time_update"], datetime.datetime):
        #     raw_dict["time_update"] = raw_dict["time_update"].date()
        # else:
        #     raw_dict["time_update"] = None

        return raw_dict

    def getById(self, id: str) -> Relative or None:
        """
        按唯一索引列表查询Relative. 无结果返回None
        """
        sql = (
            "SELECT {} FROM {} ".format(self.__fields_str, self.__table) +
            "WHERE {}=?".format(self.__attr2field_map[self.__primary_key][0])
        )
        res = self.__db_obj.query(sql, (id,))
        if len(res) < 1:
            return None
        res_dict = self.__format_dict(dict(zip(self.__attr2field_map.keys(), res[0])))

        return Relative(**res_dict)

    def getByIdList(self, id_list: List[str]) -> List[Relative]:
        all_res = []
        for i in range(0, len(id_list), 1000):
            sql = (
                "SELECT {} FROM {} ".format(self.__fields_str, self.__table) + 
                "WHERE {} IN ({})".format(self.__attr2field_map[self.__primary_key][0], ",".join(["\'{}\'".format(u) for u in id_list[i:i+1000]]))
            )
            all_res += self.__db_obj.query(sql)

        all_dict = [self.__format_dict(dict(zip(self.__attr2field_map.keys(), res))) for res in all_res]
            
        return [Relative(**d) for d in all_dict]

    def getAll(self) -> Iterable[Relative]:
        # TODO: 后续需要考虑根据删除标志（delflag）获取数据
        sql = (
            "SELECT {} FROM {}".format(self.__fields_str, self.__table)
        )
        all_res = self.__db_obj.query(sql)

        all_dict = [self.__format_dict(dict(zip(self.__attr2field_map.keys(), res))) for res in all_res]
            
        return [Relative(**d) for d in all_dict]

    def getByPersonuuid(self, person_uuid:str) -> List[Relative]:
        raise IOError("DatacenterRelativeMapper doesn't provide this function")

    def getByPersonuuidList(self, person_uuid_list:List[str]) -> List[Relative]:
        raise IOError("DatacenterRelativeMapper doesn't provide this function")

    def save(self, relative_list: List[Relative]) -> int:
        raise IOError("DatacenterRelativeMapper is readonly")

    def updateRelativeUuid(self) -> int:
        pass

    def getUpdateLastTime(self) -> datetime.date:
        pass

    def getByUpdatetime(self, time_update: datetime.date) -> List[Relative]:
        sql = (
                "SELECT {} FROM {} ".format(self.__fields_str, self.__table) +
                "WHERE {} >= ?".format(self.__attr2field_map['time_update'][0])
        )
        all_res = self.__db_obj.query(sql, (time_update.strftime("%Y-%m-%d")))
        return [Relative(**dict(zip(self.__attr2field_map.keys(), res))) for res in all_res]
