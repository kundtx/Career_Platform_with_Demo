import abc
import datetime
import json
from typing import *
from ...common import Person
from .. import driver
import re


__all__ = ["CareerDBPersonMapper", "DatacenterPersonMapper", "JsonPersonMapper"]


class PersonMapperInterface(abc.ABC):
    """
    Person类的持久化接口类, 所有对Person类的持久化类都应继承本接口类, 并实现接口
    对于仅用于读的持久化数据源(如txt、JSON文件), 可以将save实现为一个空函数或在函数中raise一个IOError
    """
    @abc.abstractmethod
    def getById(self, id: str) -> Person or None:
        pass

    @abc.abstractmethod
    def getByIdList(self, id_list: List[str]) -> List[Person]:
        pass

    @abc.abstractmethod
    def getAll(self) -> Iterable[Person]:
        pass

    @abc.abstractmethod
    def save(self, person_list: List[Person]) -> int:
        pass

class CareerDBPersonMapper(PersonMapperInterface):
    """
    适用于系统内部CAREER数据库的PersonMapper
    """

    __table = "person"                          # Person类对应数据库表名
    __primary_key = 'uuid'                      # Person类对应数据库表主键的属性名
    __attr2field_map = {                        # Person类实例属性和数据库表字段对应关系以及数据类型
        'uuid': ('person_uuid', str), 
        'name': ('person_name', str), 
        'name_pinyin': ('person_namepinyin', str), 
        'gender': ('person_gender', str), 
        'minzu': ('person_minzu', str), 
        'origo': ('person_origo', str), 
        'birthplace': ('person_birthplace', str), 
        'photo': ('person_photo', str), 
        'edu_ft': ('edu_ft', str), 
        'edu_ft_school': ('edu_ft_school', str), 
        'edu_pt': ('edu_pt', str), 
        'edu_pt_school': ('edu_pt_school', str), 
        'time_birth': ('time_birth', datetime.date), 
        'time_joinparty': ('time_joinparty', datetime.date),
        'time_startwork': ('time_startwork', datetime.date),
        'cur_position': ('cur_position', str), 
        'cur_adminrank': ('cur_adminrank', str)
    }
    def __init__(self, db_obj=None):
        if db_obj:
            self.__db_obj = db_obj  # 数据库操作对象
        else:
            self.__db_obj = driver.MysqlDB() # 默认数据库操作对象
        self.__fields_str = ','.join([v[0] for v in self.__attr2field_map.values()]) # 初始化时把数据库字段列表字符串计算好

    def getById(self, id: str) -> Person or None:
        """
        按唯一索引列表查询Person. 无结果返回None
        """
        sql = (
            "SELECT {} FROM {} ".format(self.__fields_str, self.__table) +
            "WHERE {}=%s".format(self.__attr2field_map[self.__primary_key][0])
        )
        res = self.__db_obj.query(sql, (id,))
        if len(res) == 0:
            return None
        return Person(**dict(zip(self.__attr2field_map.keys(), res[0])))

    def getByIdList(self, id_list: List[str]) -> Iterable[Person]:
        """
        按唯一索引列表查询对应Person列表. 无结果返回空列表.
        注意，返回的Person列表可能和传入的id_list长度不一样！请考虑到id_list中某些id可能在数据库没有对应记录，以及数据库的事务隔离问题！
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
        return [Person(**dict(zip(self.__attr2field_map.keys(), res))) for res in all_res]

    def getAll(self) -> Iterable[Person]:
        """
        返回数据库中全部Person. 无结果返回空迭代器.
        注意，返回的Person列表可能和传入的id_list长度不一样！请考虑到id_list中某些id可能在数据库没有对应记录，以及数据库的事务隔离问题！
        """
        # TODO 当前只实现了将结果全部fetch到内存中并返回整个列表，需要实现为带Buffer的迭代器以支持内存无法承受的数据量
        sql = (
            "SELECT {} FROM {} ".format(self.__fields_str, self.__table)
        )
        all_res = self.__db_obj.query(sql)
        return [Person(**dict(zip(self.__attr2field_map.keys(), res))) for res in all_res]

    def save(self, person_list: List[Person]) -> int:
        sql = (
            "REPLACE INTO {} ({}) VALUES %s".format(self.__table, self.__fields_str)
        )
        aff_rows = self.__db_obj.execute_many(sql, [(tuple([person.__getattribute__(attr) for attr in self.__attr2field_map.keys()]), ) for person in person_list])
        return aff_rows


class DatacenterPersonMapper(PersonMapperInterface):
    """
    适用于数据中心的PersonMapper
    """    
    __A01_FUNC = "ods.ods_gb_v721_szdp_a01_function_cur"
    __A01 = "ods.ods_gb_v721_szdp_a01_cur"
    __GB3304 = "ods.ods_gb_V721_szdp_gb3304_cur"
    
    __table = "{} A01_FUNCTION".format(__A01_FUNC)                   # Person类对应数据库表名
    __primary_key = 'uuid'                                           # Person类对应数据库表主键的属性名
    __attr2field_map = {                                             # Person类实例属性和数据库表字段对应关系以及数据类型
        'uuid': ('A01_FUNCTION.A00', str), 
        'name': ("REGEXP_SUBSTR(A01_A0101,'[^(]+',1,1)", str), 
        'gender': ('(SELECT A0104 FROM {} A01 WHERE A01_FUNCTION.A00 = A01.A00)'.format(__A01), str), 
        'minzu': ('(SELECT DMCPT FROM {} GB3304 WHERE DMCOD =(SELECT A0117 FROM {} A01 WHERE A01_FUNCTION.A00 = A01.A00))'.format(__GB3304, __A01), str), 
        'origo': ('A01_A0111B_A0111A_RMB', str), 
        'birthplace': ('A01_A0114B_A0114A_RMB', str), 
        'photo': ('(SELECT ZDYXA0106 FROM {} A01 WHERE A01_FUNCTION.A00 = A01.A00)'.format(__A01), str), 
        'edu_ft': ('A08_A0801', str), 
        'edu_ft_school': ('A08_A0806_zg', str), 
        'edu_pt': ('A08_A0814_A0830_ZZ_RMB', str), 
        'edu_pt_school': ('A08_A0806_A0809_ZZ_RMB', str), 
        'time_birth': ('A01_A0107_noage', datetime.date), 
        'time_joinparty': ('A01_A0144_2', datetime.date),
        'time_startwork': ('(SELECT A0134 FROM {} A01 WHERE A01_FUNCTION.A00 = A01.A00)'.format(__A01), datetime.date),
        'cur_position': ('A16_A1603', str), 
        'cur_adminrank': ('A05_A0501B', str)
    }
    def __init__(self, db_obj=None):
        if db_obj:
            self.__db_obj = db_obj  # 数据库操作对象
        else:
            self.__db_obj = driver.DamengDB() # 默认数据库操作对象
        self.__fields_str = ','.join([v[0] for v in self.__attr2field_map.values()]) # 初始化时把数据库字段列表字符串计算好

    def __format_dict(self, raw_dict:Dict[str, Any]) -> Dict[str, Any]:
        if raw_dict["name"]:
            raw_dict["name"] = raw_dict["name"].replace('\u3000', "").strip()
        if raw_dict["time_birth"]:
            raw_dict["time_birth"] = datetime.datetime.strptime(raw_dict["time_birth"], "%Y.%m").date()

        if raw_dict["time_joinparty"]:
            raw_dict["time_joinparty"] = raw_dict["time_joinparty"].strip()
            if re.match("^[0-9]{4}.[0-9]{2}$", raw_dict["time_joinparty"]):
                raw_dict["time_joinparty"] = datetime.datetime.strptime(raw_dict["time_joinparty"], "%Y.%m").date()
            else:
                raw_dict["time_joinparty"] = None
        
        if isinstance(raw_dict["time_startwork"], datetime.datetime):
            raw_dict["time_startwork"] = raw_dict["time_startwork"].date()
        else:
            raw_dict["time_startwork"] = None

        return raw_dict

    def getById(self, id: str) -> Person or None:
        """
        按唯一索引列表查询Person. 无结果返回None
        """
        sql = (
            "SELECT {} FROM {} ".format(self.__fields_str, self.__table) +
            "WHERE {}=?".format(self.__attr2field_map[self.__primary_key][0])
        )
        res = self.__db_obj.query(sql, (id,))
        if len(res) < 1:
            return None
        res_dict = self.__format_dict(dict(zip(self.__attr2field_map.keys(), res[0])))

        return Person(**res_dict)

    def getByIdList(self, id_list: List[str]) -> List[Person]:
        all_res = []
        for i in range(0, len(id_list), 1000):
            sql = (
                "SELECT {} FROM {} ".format(self.__fields_str, self.__table) + 
                "WHERE {} IN ({})".format(self.__attr2field_map['uuid'][0], ",".join(["\'{}\'".format(u) for u in id_list[i:i+1000]]))
            )
            all_res += self.__db_obj.query(sql)

        all_dict = [self.__format_dict(dict(zip(self.__attr2field_map.keys(), res))) for res in all_res]
            
        return [Person(**d) for d in all_dict]

    def getAll(self) -> Iterable[Person]:
        sql = (
            "SELECT {} FROM {} ".format(self.__fields_str, self.__table)
        )
        all_res = self.__db_obj.query(sql)

        all_dict = [self.__format_dict(dict(zip(self.__attr2field_map.keys(), res))) for res in all_res]
            
        return [Person(**d) for d in all_dict]

    def save(self, person_list: List[Person]) -> int:
        raise IOError("DatacenterPersonMapper is readonly")


class JsonPersonMapper(PersonMapperInterface):
    """
    用于读取和保存JSON文件的PersonMapper
    """
    
    __idkey = 'uuid'                                # 代表id的属性名
    __attr2jsonkey_map = {                          # Person类实例属性名和JSON键对应关系和数据类型                  
        'uuid': ('person_uuid', str), 
        'name': ('person_name', str), 
        'name_pinyin': ('person_namepinyin', str), 
        'gender': ('person_gender', str), 
        'minzu': ('person_minzu', str), 
        'origo': ('person_origo', str), 
        'birthplace': ('person_birthplace', str), 
        'photo': ('person_photo', str), 
        'edu_ft': ('edu_ft', str), 
        'edu_ft_school': ('edu_ft_school', str), 
        'edu_pt': ('edu_pt', str), 
        'edu_pt_school': ('edu_pt_school', str), 
        'time_birth': ('time_birth', datetime.date), 
        'time_joinparty': ('time_joinparty', datetime.date),
        'time_startwork': ('time_startwork', datetime.date),
        'cur_position': ('cur_position', str), 
        'cur_adminrank': ('cur_adminrank', str)
    }
    # __attr2jsonkey_map = {                          # Person类实例属性名和JSON键对应关系和数据类型                  
    #     'uuid': ('uid', str), 
    #     'name': ('name', str), 
    #     'name_pinyin': ('person_namepinyin', str), 
    #     'gender': ('gender', str), 
    #     'minzu': ('nation', str), 
    #     'origo': ('origo', str), 
    #     'birthplace': ('birthplace', str), 
    #     'photo': ('person_photo', str), 
    #     'edu_ft': ('edu_ft_career', str), 
    #     'edu_ft_school': ('edu_ft_school', str), 
    #     'edu_pt': ('edu_pt_career', str), 
    #     'edu_pt_school': ('edu_pt_school', str), 
    #     'time_birth': ('birthday', datetime.date), 
    #     'time_joinparty': ('t_party', datetime.date),
    #     'time_startwork': ('t_job', datetime.date),
    #     'cur_position': ('position', str), 
    #     'cur_adminrank': ('rank', str)
    # }
    def __init__(self):
        self.__jsonidkey = self.__attr2jsonkey_map[self.__idkey][0]

    def __json2person(self, json_dict:Dict, none_as_emptystr:bool=False):
        """
        将一个JSON字典转为一个Person对象
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
                    continue
                if attr_type is datetime.date:
                    time = json_dict[jsonkey]
                    if len(time) == 7:
                        p_kwargs[attr] = datetime.datetime.strptime(json_dict[jsonkey], "%Y.%m").date()
                    elif len(time) == 10:
                        p_kwargs[attr] = datetime.datetime.strptime(json_dict[jsonkey], "%Y-%m-%d").date()
                    else:
                        raise ValueError("Illegal date string format, should be 'YYYY-MM' or 'YYYY-MM-DD'")
                    continue
                else:
                    raise TypeError("缺少对应的转换规则，请在这段源码里加上")

        # 创建Person实例
        res = Person(**p_kwargs)
        return res

    def __person2json(self, person:Person, none_as_emptystr:bool=False):
        """
        将一个Person对象转为一个符合JSON规范的字典
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

    def getById(self, file_path: str, id: str) -> Person or None:
        """
        按唯一索引查找JSON文件中的记录,以Person对象返回. 无结果返回None
        """

        with open(file_path, 'r', encoding='utf-8') as f:
            json_obj = json.load(f)

        for j in json_obj:
            if j[self.__jsonidkey] == id:
                return self.__json2person(j)
        return None
    
    def getByIdList(self, file_path: str, id_list: List[str]) -> List[Person]:
        """
        按唯一索引列表查找JSON文件中的所有匹配记录,以Person对象列表返回. 无结果返回空列表
        """

        with open(file_path, 'r', encoding='utf-8') as f:
            json_obj = json.load(f)

        filtered_json_obj = list(filter(lambda x:x[self.__jsonidkey] in id_list, json_obj))
        
        res = []
        for j in filtered_json_obj:
            res.append(self.__json2person(j))
        return res

    def getAll(self, file_path: str) -> Iterable[Person]:
        """
        读取JSON文件中全部记录,以Person对象列表返回. 无结果返回空列表
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            json_obj = json.load(f)

        res = []
        for j in json_obj:
            res.append(self.__json2person(j))
        return res

    def save(self, person_list: List[Person], save_path: str=None) -> int:
        """
        将person_list转为JSON保存为新的文件.
        """
        if save_path:
            json_list = [self.__person2json(p) for p in person_list]
            with open(save_path, 'w+', encoding='utf-8') as f:
                json.dump(obj=json_list, fp=f, ensure_ascii=False, indent=2)
        else:
            raise IOError("save_path must be indicated")
