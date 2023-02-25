import abc
import datetime
import json
from typing import *
from ...common import Experience
from .. import driver


__all__ = ["CareerDBExperienceMapper", "DatacenterExperienceMapper", "JsonExperienceMapper"]

class ExperienceMapperInterface(abc.ABC):
    """
    Experience类的持久化接口类, 所有对Experience类的持久化类都应继承本接口类, 并实现接口
    对于仅用于读的持久化数据源(如txt、JSON文件), 可以将save实现为一个空函数或在函数中raise一个IOError
    """
    @abc.abstractmethod
    def getById(self, id:Tuple[str, int]) -> Experience or None:
        """
        按唯一索引(exp_uuid, splitnum)查询返回一个Experience. 无结果返回None
        """
        pass

    @abc.abstractmethod
    def getByIdList(self, id_list:List[Tuple[str, int]]) -> List[Experience]:
        """
        按唯一索引(exp_uuid, splitnum)列表查询返回一批Experience. 无结果返回空列表
        """
        pass

    @abc.abstractmethod
    def getByExpuuid(self, uuid:str) -> List[Experience]:
        """
        按exp_uuid查询返回exp_uuid相同的多个Experience. 无结果返回空列表
        """
        pass

    @abc.abstractmethod
    def getByExpuuidList(self, uuid_list:List[str]) -> List[Experience]:
        """
        按唯exp_uuid_list列表查询返回一批Experience. 无结果返回空列表
        """
        pass

    @abc.abstractmethod
    def getByPersonuuid(self, person_uuid:str) -> List[Experience]:
        """
        按person_uuid查询返回属于一个Person的多个Experience. 无结果返回空列表
        """
        pass

    @abc.abstractmethod
    def getByPersonuuidList(self, person_uuid_list:List[str]) -> List[Experience]:
        """
        按person_uuid_list查询返回属于一批Person的所有Experience. 无结果返回空列表
        """
        pass

    @abc.abstractmethod
    def getAll(self) -> Iterable[Experience]:
        """
        返回全部的Experience. 无结果返回空列表
        """
        pass

    @abc.abstractmethod
    def save(self, replace_by:str, exp_list: List[Experience]) -> int:
        """
        保存一批Experience. 返回受影响行数.

        Params:
            replace_by：指定保存时的替换方式.
                        replace_by="id": 数据库中存在(uuid, splitnum)相同的记录时，删除原记录，插入新记录.
                        replace_by="exp_uuid": 对exp_list中出现的所有exp_uuid，先删除每一个exp_uuid在数据库中的全部记录，再插入exp_list
                        replace_by="person_uuid": 对exp_list中出现的所有person_uuid，先删除每一个person_uuid在数据库中的全部记录，再插入exp_list
        """
        pass


class CareerDBExperienceMapper(ExperienceMapperInterface):
    """
    适用于系统内部CAREER数据库的ExperienceMapper
    """

    __table = "exp"                                     # Experience类对应数据库表明
    __primary_key = ('uuid', 'splitnum')                # Experience类对应数据库主键的属性名
    __attr2field_map = {                                # Experience类实例属性和数据库表字段对应关系以及数据类型
        'uuid': ('exp_uuid', str), 
        'splitnum': ('exp_splitnum', int), 
        'ordernum': ('exp_ordernum', int), 
        'text': ('text_', str), 
        'text_token': ('text_token', str), 
        'text_raw': ('text_raw', str), 
        'text_rawpinyin': ('text_rawpinyin', str), 
        'text_rawrefine': ('text_rawrefine', str),
        'text_rawsplit': ('text_rawsplit', str), 
        'text_rawtoken': ('text_rawtoken', str),
        'time_start': ('time_start', datetime.date), 
        'time_end': ('time_end', datetime.date),
        'adminrank': ('adminrank', str),
        'person_uuid': ('person_uuid', str)
    }

    def __init__(self, db_obj=None):
        if db_obj:
            self.__db_obj = db_obj  # 数据库操作对象
        else:
            self.__db_obj = driver.MysqlDB() # 默认数据库操作对象
        self.__fields_str = ','.join([v[0] for v in self.__attr2field_map.values()])    # 初始化时把数据库字段列表字符串计算好
        self.__primary_key_db = tuple([self.__attr2field_map[k][0] for k in self.__primary_key])   # 初始化时把数据库组合主键计算好

    def getById(self, id: Tuple[str, int]) -> Experience or None:
        if not (isinstance(id, (tuple, list)) and len(id)==len(self.__primary_key_db)):
            raise ValueError("exp表的唯一Id是({}), 请检查传入参数是否正确.".format(','.join(self.__primary_key_db)))
        sql = (
            "SELECT {} FROM {} ".format(self.__fields_str, self.__table) + 
            "WHERE ({})=%s".format(','.join(self.__primary_key_db))
        )
        res = self.__db_obj.query(sql, (id,))
        if len(res) == 0:
            return None
        return Experience(**dict(zip(self.__attr2field_map.keys(), res[0])))
    
    def getByIdList(self, id_list: List[Tuple[str, int]]) -> List[Experience]:
        if len(id_list)>0 and (not (isinstance(id_list[0], [tuple, list]) and len(id_list[0])==len(self.__primary_key_db))):
            raise ValueError("exp表的唯一Id是({}), 请检查传入参数是否正确.".format(','.join(self.__primary_key_db)))
        sql = (
            "SELECT {} FROM {} ".format(self.__fields_str, self.__table) + 
            "WHERE ({}) IN %s".format(','.join(self.__primary_key_db))
        )
        all_res = []
        # 每次使用WHERE IN查询1000个
        for i in range(0, len(id_list), 1000):
            all_res += self.__db_obj.query(sql, (id_list[i:i+1000], ))
        return [Experience(**dict(zip(self.__attr2field_map.keys(), res))) for res in all_res]

    def getByExpuuid(self, uuid: str) -> List[Experience]:
        sql = (
            "SELECT {} FROM {} ".format(self.__fields_str, self.__table) + 
            "WHERE {}=%s".format(self.__attr2field_map['uuid'][0])
        )
        all_res = self.__db_obj.query(sql, (uuid,))
        return [Experience(**dict(zip(self.__attr2field_map.keys(), res))) for res in all_res]

    def getByExpuuidList(self, uuid_list: List[str]) -> List[Experience]:
        sql = (
            "SELECT {} FROM {} ".format(self.__fields_str, self.__table) + 
            "WHERE {} IN %s".format(self.__attr2field_map['uuid'][0])
        )
        all_res = []
        # 每次使用WHERE IN查询1000个
        for i in range(0, len(uuid_list), 1000):
            all_res += self.__db_obj.query(sql, (uuid_list[i:i+1000], ))
        return [Experience(**dict(zip(self.__attr2field_map.keys(), res))) for res in all_res]

    def getByPersonuuid(self, person_uuid: str) -> List[Experience]:
        sql = (
            "SELECT {} FROM {} ".format(self.__fields_str, self.__table) + 
            "WHERE {}=%s".format(self.__attr2field_map['person_uuid'][0])
        )
        all_res = self.__db_obj.query(sql, (person_uuid, ))
        return [Experience(**dict(zip(self.__attr2field_map.keys(), res))) for res in all_res]

    def getByPersonuuidList(self, person_uuid_list: List[str]) -> List[Experience]:
        sql = (
            "SELECT {} FROM {} ".format(self.__fields_str, self.__table) + 
            "WHERE {} IN %s".format(self.__attr2field_map['person_uuid'][0])
        )
        all_res = []
        # 每次使用WHERE IN查询1000个
        for i in range(0, len(person_uuid_list), 1000):
            all_res += self.__db_obj.query(sql, (person_uuid_list[i:i+1000], ))
        return [Experience(**dict(zip(self.__attr2field_map.keys(), res))) for res in all_res]

    def getAll(self) -> Iterable[Experience]:
        # TODO 当前只实现了将结果全部fetch到内存中并返回整个列表，需要实现为带Buffer的迭代器以支持内存无法承受的数据量
        sql = (
            "SELECT {} FROM {} ".format(self.__fields_str, self.__table)
        )
        all_res = self.__db_obj.query(sql)
        return [Experience(**dict(zip(self.__attr2field_map.keys(), res))) for res in all_res]

    def save(self, replace_by:str, exp_list: List[Experience]) -> int:
        aff_rows = 0
        if replace_by == "id":
            sql = (
                "REPLACE INTO {} ({}) VALUES %s".format(self.__table, self.__fields_str)
            )
            aff_rows = self.__db_obj.execute_many(sql, [(tuple([exp.__getattribute__(attr) for attr in self.__attr2field_map.keys()]), ) for exp in exp_list])
        
        elif replace_by == "exp_uuid":
            # 获取exp_list中所有出现的exp_uuid
            exp_uuid_set = set()
            for exp in exp_list:
                exp_uuid_set.add(exp.uuid)
            exp_uuid_list = list(exp_uuid_set)
            
            # 删除所有exp_uuid_list中的记录
            sql = (
            "DELETE FROM {} ".format(self.__table) + 
            "WHERE {} IN %s".format(self.__attr2field_map['uuid'][0])
            )
            for i in range(0, len(exp_uuid_list), 1000):
                aff_rows += self.__db_obj.execute(sql, (exp_uuid_list[i:i+1000], ))

            # 插入exp_list
            sql = (
                "REPLACE INTO {} ({}) VALUES %s".format(self.__table, self.__fields_str)
            )
            aff_rows += self.__db_obj.execute_many(sql, [(tuple([exp.__getattribute__(attr) for attr in self.__attr2field_map.keys()]), ) for exp in exp_list])

        elif replace_by == "person_uuid":
            # 获取exp_list中所有出现的person_uuid
            person_uuid_set = set()
            for exp in exp_list:
                person_uuid_set.add(exp.person_uuid)
            person_uuid_list = list(person_uuid_set)
            
            # 删除所有exp_uuid_list中的记录
            sql = (
            "DELETE FROM {} ".format(self.__table) + 
            "WHERE {} IN %s".format(self.__attr2field_map['person_uuid'][0])
            )
            for i in range(0, len(person_uuid_list), 1000):
                aff_rows += self.__db_obj.execute(sql, (person_uuid_list[i:i+1000], ))

            # 插入exp_list
            sql = (
                "REPLACE INTO {} ({}) VALUES %s".format(self.__table, self.__fields_str)
            )
            aff_rows += self.__db_obj.execute_many(sql, [(tuple([exp.__getattribute__(attr) for attr in self.__attr2field_map.keys()]), ) for exp in exp_list])

        else:
            raise ValueError("invalid replace_by value, should be 'id' or 'exp_uuid' or 'person_uuid' ")

        return aff_rows


class DatacenterExperienceMapper(ExperienceMapperInterface):
    """
    用于读取和保存数据中心的ExperienceMapper
    """
    __table = "ods.ods_gb_v721_szdp_a16_cur"         # Experience类对应数据库表明
    __primary_key = 'uuid'               # Experience类对应数据库主键的属性名
    __attr2field_map = {
        'uuid': ('recordid', str), 
        'text_raw': ('TRIM(A1603)', str), 
        'time_start': ('A1601', datetime.date), 
        'time_end': ('A1602', datetime.date), 
        'person_uuid': ('A00', str)
    }

    def __init__(self, db_obj=None):
        if db_obj:
            self.__db_obj = db_obj  # 数据库操作对象
        else:
            self.__db_obj = driver.DamengDB()

        self.__fields_str = ','.join([v[0] for v in self.__attr2field_map.values()])
        self.__primary_key_db = self.__attr2field_map[self.__primary_key][0]

    def __format_dict(self, raw_dict:Dict[str, Any]) -> Dict[str, Any]:
        if raw_dict['text_raw'] == "":
            raw_dict['text_raw'] = None
        if raw_dict['time_start']:
            raw_dict['time_start'] = raw_dict['time_start'].date()
            if raw_dict['time_end']:
                raw_dict['time_end'] = raw_dict['time_end'].date()
            else:
                raw_dict['time_end'] = datetime.date.max
        else:
            raw_dict['time_start'] = None

        return raw_dict

    def getById(self, file_path: str, id: str) -> Experience or None:
        raise IOError("这个接口没实现，如有需要请在此处实现")
    def getByIdList(self, file_path: str, id_list: List[str]) -> List[Experience]:
        raise IOError("这个接口没实现，如有需要请在此处实现")
    def getByPersonuuid(self, person_uuid: str) -> List[Experience]:
        raise IOError("这个接口没实现，如有需要请在此处实现")
    def getByPersonuuidList(self, person_uuid_list: List[str]) -> List[Experience]:
        raise IOError("这个接口没实现，如有需要请在此处实现")
    def save(self, exp_list:List[Experience]) -> int:
        raise IOError("DatacenterExperienceMapper is readonly")

    def getByExpuuid(self, uuid: str) -> List[Experience]:
        sql = (
            "SELECT {} FROM {} ".format(self.__fields_str, self.__table) + 
            "WHERE {}=?".format(self.__attr2field_map['uuid'][0])
        )
        all_res = self.__db_obj.query(sql, (uuid, ))
        
        all_dict = [self.__format_dict(dict(zip(self.__attr2field_map.keys(), res))) for res in all_res]

        return [Experience(**d) for d in all_dict]

    def getByExpuuidList(self, uuid_list: List[str]) -> List[Experience]:
        all_res = []
        for i in range(0, len(uuid_list), 1000):
            sql = (
                "SELECT {} FROM {} ".format(self.__fields_str, self.__table) + 
                "WHERE {} IN ({})".format(self.__attr2field_map['uuid'][0], ",".join(["\'{}\'".format(u) for u in uuid_list[i:i+1000]]))
            )
            all_res += self.__db_obj.query(sql)

        all_dict = [self.__format_dict(dict(zip(self.__attr2field_map.keys(), res))) for res in all_res]
            
        return [Experience(**d) for d in all_dict]

    def getAll(self) -> List[Experience]:
        sql = (
            "SELECT {} FROM {} ".format(self.__fields_str, self.__table)
        )
        all_res = self.__db_obj.query(sql)
        
        all_dict = [self.__format_dict(dict(zip(self.__attr2field_map.keys(), res))) for res in all_res]

        return [Experience(**d) for d in all_dict]

class JsonExperienceMapper(ExperienceMapperInterface):
    """
    用于读取和保存JSON文件的ExperienceMapper
    """
    
    __idkey = ('uuid','splitnum')                   # 代表id的属性名
    __attr2jsonkey_map = {                          # Experience类实例属性和JSON键名以及数据类型的对应关系
        'uuid': ('exp_uuid', str), 
        'splitnum': ('exp_splitnum', int), 
        'ordernum': ('exp_ordernum', int), 
        'text': ('text_', str), 
        'text_token': ('text_token', str), 
        'text_raw': ('text_raw', str), 
        'text_rawpinyin': ('text_rawpinyin', str), 
        'text_rawrefine': ('text_rawrefine', str),
        'text_rawsplit': ('text_rawsplit', str), 
        'text_rawtoken': ('text_rawtoken', str),
        'time_start': ('time_start', datetime.date), 
        'time_end': ('time_end', datetime.date),
        'adminrank': ('adminrank', str),
        'person_uuid': ('person_uuid', str)
    }
    def __init__(self):
        self.__jsonidkey = tuple([self.__attr2jsonkey_map[k][0] for k in self.__idkey])

    def __json2exp(self, json_dict:Dict, none_as_emptystr:bool=False):
        """
        将一个JSON字典转为一个Experience对象
        """
        # json里的空字符串算不算None
        none_in_json = "" if none_as_emptystr else None

        # 将json中的字符串值转为对应属性的数据类型
        p_kwargs = {}
        for attr in self.__attr2jsonkey_map.keys():
            jsonkey, attr_type = self.__attr2jsonkey_map[attr]
            if (json_dict.get(jsonkey, False) and json_dict[jsonkey]!=none_in_json and json_dict[jsonkey]!=None):
                # 各类型转换规则
                if attr_type is str:
                    p_kwargs[attr] = str(json_dict[jsonkey])
                elif attr_type is int:
                    p_kwargs[attr] = int(json_dict[jsonkey])
                elif attr_type is datetime.date:
                    time = json_dict[jsonkey]
                    # 自适应不同格式的年月日
                    if len(time) == 4:
                        p_kwargs[attr] = datetime.datetime.strptime(json_dict[jsonkey], "%Y").date()
                    elif len(time) == 7:
                        p_kwargs[attr] = datetime.datetime.strptime(json_dict[jsonkey], "%Y.%m").date()
                    elif len(time) == 10:
                        p_kwargs[attr] = datetime.datetime.strptime(json_dict[jsonkey], "%Y-%m-%d").date()
                    else:
                        raise ValueError("Illegal date string format, should be 'YYYY' or 'YYYY-MM' or 'YYYY-MM-DD'")
                    
                    # 如果年份是9999，则设置为datetime.date.max，即9999.12.31
                    if p_kwargs[attr].year == 9999:
                        p_kwargs[attr] = datetime.date.max
                else:
                    raise TypeError("缺少对应的转换规则，请在这段源码里加上")

        # 创建Experience实例
        res = Experience(**p_kwargs)
        return res

    def __exp2json(self, person:Experience, none_as_emptystr:bool=False):
        """
        将一个Experience对象转为一个符合JSON规范的字典
        """
        json_dict = {}
        for attr in self.__attr2jsonkey_map.keys():
            attr_value = person.__getattribute__(attr)
            # 各类型转换规则
            if isinstance(attr_value, (str, int, float)):  #str、int、float类型原封不动
                attr_value = attr_value
            elif isinstance(attr_value, datetime.date):  # date类型转为YYYY-MM-DD字符串
                attr_value = attr_value.strftime("%Y-%m-%d")
            elif attr_value is None:    # None转为空字符（可选）若不转则json.dump后会变为null
                attr_value = '' if none_as_emptystr else None
            else:
                raise TypeError("没有该类型对应的转化规则，请检查属性类型是否正确，或是在这段代码中添加该类型的转换规则")
            json_dict[self.__attr2jsonkey_map[attr][0]]  = attr_value
        
        return json_dict

    def getById(self, file_path: str, id: str) -> Experience or None:
        raise IOError("这个接口没实现，如有需要请在此处实现")
    def getByIdList(self, file_path: str, id_list: List[str]) -> List[Experience]:
        raise IOError("这个接口没实现，如有需要请在此处实现")
    def getByExpuuid(self, uuid: str) -> List[Experience]:
        raise IOError("这个接口没实现，如有需要请在此处实现")
    def getByExpuuidList(self, uuid_list: List[str]) -> List[Experience]:
        raise IOError("这个接口没实现，如有需要请在此处实现")
    def getByPersonuuid(self, person_uuid: str) -> List[Experience]:
        raise IOError("这个接口没实现，如有需要请在此处实现")
    def getByPersonuuidList(self, person_uuid_list: List[str]) -> List[Experience]:
        raise IOError("这个接口没实现，如有需要请在此处实现")

    def getAll(self, file_path: str) -> List[Experience]:
        """
        读取JSON文件中全部记录,以Experience对象列表返回. 无结果返回空列表
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            json_obj = json.load(f)

        res = []
        for j in json_obj:
            res.append(self.__json2exp(j))
        return res

    def save(self, exp_list: List[Experience], save_path: str=None) -> int:
        """
        将exp_list转为JSON保存为新的文件.
        """
        if save_path:
            json_list = [self.__exp2json(p) for p in exp_list]
            with open(save_path, 'w+', encoding='utf-8') as f:
                json.dump(obj=json_list, fp=f, ensure_ascii=False, indent=2)
        else:
            raise IOError("save_path must be indicated")
