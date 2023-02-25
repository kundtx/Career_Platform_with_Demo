import abc
import datetime
import json
from typing import *
from ...common import Evaluation
from .. import driver

__all__ = ["CareerDBEvaluationMapper", "DatacenterEvaluationMapper", "JsonEvaluationMapper"]


class EvaluationMapperInterface(abc.ABC):
    """
    Evaluation类的持久化接口类, 所有对Evaluation类的持久化类都应继承本接口类, 并实现接口
    对于仅用于读的持久化数据源(如txt、JSON文件), 可以将save实现为一个空函数或在函数中raise一个IOError
    """

    @abc.abstractmethod
    def getById(self, id: str) -> Evaluation or None:
        """
        按唯一索引(uuid)查询返回一个Evaluation. 无结果返回None
        """
        pass

    @abc.abstractmethod
    def getByIdList(self, id_list: List[str]) -> List[Evaluation]:
        """
        按唯一索引(uuid)列表查询返回一批Evaluation. 无结果返回空列表
        """
        pass

    @abc.abstractmethod
    def getByPersonuuid(self, person_uuid: str) -> List[Evaluation]:
        """
        按person_uuid查询返回属于一个Person的多个Evaluation. 无结果返回空列表
        """
        pass

    @abc.abstractmethod
    def getByPersonuuidList(self, person_uuid_list: List[str]) -> List[Evaluation]:
        """
        按person_uuid_list查询返回属于一批Person的所有Evaluation. 无结果返回空列表
        """
        pass

    @abc.abstractmethod
    def getByUpdatetime(self, time_update: datetime.date) -> List[Evaluation]:
        """
        按 更新时间 查询返回在更新时间之后的所有Evaluation. 无结果返回空列表
        """
        pass

    @abc.abstractmethod
    def getUpdateLastTime(self) -> datetime.date:
        """
        获取最后的更新时间
        """
        pass

    @abc.abstractmethod
    def getAll(self) -> Iterable[Evaluation]:
        """
        返回全部的Evaluation. 无结果返回空列表
        """
        pass

    @abc.abstractmethod
    def save(self, replace_by: str, eval_list: List[Evaluation]) -> int:
        """
        保存一批Evaluation. 返回受影响行数.

        Params:
            replace_by: 指定保存时的替换方式.
                        replace_by="id": 数据库中存在(uuid)相同的记录时，删除原记录，插入新记录.
                        replace_by="person_uuid": 对eval_list中出现的所有person_uuid, 先删除每一个person_uuid在数据库中的全部记录，再插入eval_list
        """
        pass


class CareerDBEvaluationMapper(EvaluationMapperInterface):
    """
    适用于系统内部CAREER数据库的 EvaluationMapper
    """

    __table = "evaluation"  # 对应数据库表名
    __primary_key = 'uuid'  # 对应数据库主键的属性名
    __attr2field_map = {  # 实例属性和数据库表字段对应关系以及数据类型
        'uuid': ('eval_uuid', str),
        'person_uuid': ('person_uuid', str),
        'text': ('eval_text', str),
        'deficiency': ('eval_deficiency', str),
        'source': ('eval_source', str),
        'memo': ('eval_memo', str),
        'time_start': ('time_start', datetime.date),
        'time_create': ('time_create', datetime.date),
        'time_update': ('time_update', datetime.date),
        'ordernum': ('ordernum', int),
        'effective': ('effective', str),
        'ismatch': ('ismatch', str)
    }

    def __init__(self, db_obj=None):
        if db_obj:
            self.__db_obj = db_obj  # 数据库操作对象
        else:
            self.__db_obj = driver.MysqlDB()  # 默认数据库操作对象
        self.__fields_str = ','.join([v[0] for v in self.__attr2field_map.values()])  # 初始化时把数据库字段列表字符串计算好
        self.__primary_key_db = self.__attr2field_map[self.__primary_key][0]  # 初始化时把数据库主键计算好

    def getById(self, id: str) -> Evaluation or None:
        sql = (
                "SELECT {} FROM {} ".format(self.__fields_str, self.__table) +
                "WHERE {}=%s".format(self.__primary_key_db)
        )
        res = self.__db_obj.query(sql, (id,))
        if len(res) == 0:
            return None
        return Evaluation(**dict(zip(self.__attr2field_map.keys(), res[0])))

    def getByIdList(self, id_list: List[str]) -> List[Evaluation]:
        sql = (
                "SELECT {} FROM {} ".format(self.__fields_str, self.__table) +
                "WHERE {} IN %s".format(self.__primary_key_db)
        )
        all_res = []
        # 每次使用WHERE IN查询1000个
        for i in range(0, len(id_list), 1000):
            all_res += self.__db_obj.query(sql, (id_list[i:i + 1000],))
        return [Evaluation(**dict(zip(self.__attr2field_map.keys(), res))) for res in all_res]

    def getByPersonuuid(self, person_uuid: str) -> List[Evaluation]:
        sql = (
                "SELECT {} FROM {} ".format(self.__fields_str, self.__table) +
                "WHERE {}=%s".format(self.__attr2field_map['person_uuid'][0])
        )
        all_res = self.__db_obj.query(sql, (person_uuid,))
        return [Evaluation(**dict(zip(self.__attr2field_map.keys(), res))) for res in all_res]

    def getByPersonuuidList(self, person_uuid_list: List[str]) -> List[Evaluation]:
        sql = (
                "SELECT {} FROM {} ".format(self.__fields_str, self.__table) +
                "WHERE {} IN %s".format(self.__attr2field_map['person_uuid'][0])
        )
        all_res = []
        # 每次使用WHERE IN查询1000个
        for i in range(0, len(person_uuid_list), 1000):
            all_res += self.__db_obj.query(sql, (person_uuid_list[i:i + 1000],))
        return [Evaluation(**dict(zip(self.__attr2field_map.keys(), res))) for res in all_res]

    def getByUpdatetime(self, time_update: datetime.date) -> List[Evaluation]:
        sql = (
                "SELECT {} FROM {} ".format(self.__fields_str, self.__table) +
                "WHERE {} >= %s".format(self.__attr2field_map['time_update'][0])
        )
        all_res = self.__db_obj.query(sql, (time_update.strftime("%Y-%m-%d")))
        return [Evaluation(**dict(zip(self.__attr2field_map.keys(), res))) for res in all_res]

    def getUpdateLastTime(self) -> datetime.date:
        sql = (
            "select max(time_update) as time_update from evaluation "
            # order by time_update desc LIMIT 10
        )
        all_res = self.__db_obj.query(sql)
        return all_res[0][0] if all_res[0][0] else datetime.date(2022,1,1)

    def getAll(self) -> Iterable[Evaluation]:
        # TODO 当前只实现了将结果全部fetch到内存中并返回整个列表，需要实现为带Buffer的迭代器以支持内存无法承受的数据量
        sql = (
            "SELECT {} FROM {} ".format(self.__fields_str, self.__table)
        )
        all_res = self.__db_obj.query(sql)
        return [Evaluation(**dict(zip(self.__attr2field_map.keys(), res))) for res in all_res]

    def save(self, replace_by: str, eval_list: List[Evaluation]) -> int:
        aff_rows = 0
        if replace_by == "id":
            sql = (
                "REPLACE INTO {} ({}) VALUES %s".format(self.__table, self.__fields_str)
            )
            aff_rows = self.__db_obj.execute_many(sql, [
                (tuple([eval.__getattribute__(attr) for attr in self.__attr2field_map.keys()]),) for eval in
                eval_list])

        elif replace_by == "person_uuid":
            # 获取eval_list中所有出现的person_uuid
            person_uuid_set = set()
            for eval in eval_list:
                person_uuid_set.add(eval.person_uuid)
            person_uuid_list = list(person_uuid_set)

            # 删除所有exp_uuid_list中的记录
            sql = (
                    "DELETE FROM {} ".format(self.__table) +
                    "WHERE {} IN %s".format(self.__attr2field_map['person_uuid'][0])
            )
            for i in range(0, len(person_uuid_list), 1000):
                aff_rows += self.__db_obj.execute(sql, (person_uuid_list[i:i + 1000],))

            # 插入eval_list
            sql = (
                "REPLACE INTO {} ({}) VALUES %s".format(self.__table, self.__fields_str)
            )
            aff_rows += self.__db_obj.execute_many(sql, [
                (tuple([eval.__getattribute__(attr) for attr in self.__attr2field_map.keys()]),) for eval in
                eval_list])

        else:
            raise ValueError("invalid replace_by value, should be 'id' or 'exp_uuid' or 'person_uuid' ")

        return aff_rows


class DatacenterEvaluationMapper(EvaluationMapperInterface):
    """
    适用于数据中心的 Mapper
    """

    __user_name = "ods"  # 正式用户
    # __user_name = "CAREER"  # 测试用户
    __table = "{}.ods_gb_v721_szdp_zssr_a_gbpj_cur".format(__user_name)  # 对应数据库表名
    __primary_key = 'uuid'  # 对应数据库表主键的属性名
    __attr2field_map = {  # 实例属性和数据库表字段对应关系以及数据类型
        'uuid': ('recordid', str),
        'person_uuid': ('A00', str),
        'text': ('GBPJ', str),
        'ordernum': ('PINDEX', int),
        'source': ('data_source_id', str),
    }

    def __init__(self, db_obj=None):
        if db_obj:
            self.__db_obj = db_obj  # 数据库操作对象
        else:
            self.__db_obj = driver.DamengDB()  # 默认数据库操作对象
        self.__fields_str = ','.join([v[0] for v in self.__attr2field_map.values()])  # 初始化时把数据库字段列表字符串计算好
        self.__primary_key_db = self.__attr2field_map[self.__primary_key][0]  # 初始化时把数据库主键计算好

    def __format_dict(self, raw_dict: Dict[str, Any]) -> Dict[str, Any]:
        if isinstance(raw_dict["time_start"], datetime.datetime):
            raw_dict["time_start"] = raw_dict["time_start"].date()
        else:
            raw_dict["time_start"] = None

        if isinstance(raw_dict["time_create"], datetime.datetime):
            raw_dict["time_create"] = raw_dict["time_create"].date()
        else:
            raw_dict["time_create"] = None

        if isinstance(raw_dict["time_update"], datetime.datetime):
            raw_dict["time_update"] = raw_dict["time_update"].date()
        else:
            raw_dict["time_update"] = None

        return raw_dict

    def getById(self, id: str) -> Evaluation or None:
        sql = (
                "SELECT {} FROM {} ".format(self.__fields_str, self.__table) +
                "WHERE {}=?".format(self.__primary_key_db)
        )
        res = self.__db_obj.query(sql, (id,))
        if len(res) == 0:
            return None
        return Evaluation(**dict(zip(self.__attr2field_map.keys(), res[0])))

    def getByIdList(self, id_list: List[str]) -> List[Evaluation]:
        all_res = []
        for i in range(0, len(id_list), 1000):
            sql = (
                    "SELECT {} FROM {} ".format(self.__fields_str, self.__table) +
                    "WHERE {} IN ({})".format(self.__attr2field_map['uuid'][0],
                                              ",".join(["\'{}\'".format(u) for u in id_list[i:i + 1000]]))
            )
            all_res += self.__db_obj.query(sql)

        all_dict = [self.__format_dict(dict(zip(self.__attr2field_map.keys(), res))) for res in all_res]

        return [Evaluation(**d) for d in all_dict]

    def getByPersonuuid(self, person_uuid: str) -> List[Evaluation]:
        sql = (
                "SELECT {} FROM {} ".format(self.__fields_str, self.__table) +
                "WHERE {}=?".format(self.__attr2field_map['person_uuid'][0])
        )
        all_res = self.__db_obj.query(sql, (person_uuid,))
        return [Evaluation(**dict(zip(self.__attr2field_map.keys(), res))) for res in all_res]

    def getByPersonuuidList(self, person_uuid_list: List[str]) -> List[Evaluation]:
        all_res = []
        for i in range(0, len(person_uuid_list), 1000):
            sql = (
                    "SELECT {} FROM {} ".format(self.__fields_str, self.__table) +
                    "WHERE {} IN ({})".format(self.__attr2field_map['person_uuid'][0],
                                              ",".join(["\'{}\'".format(u) for u in person_uuid_list[i:i + 1000]]))
            )
            all_res += self.__db_obj.query(sql)

        all_dict = [self.__format_dict(dict(zip(self.__attr2field_map.keys(), res))) for res in all_res]

        return [Evaluation(**d) for d in all_dict]

    def getByUpdatetime(self, time_update: datetime.date) -> List[Evaluation]:
        sql = (
                "SELECT {} FROM {} ".format(self.__fields_str, self.__table) +
                "WHERE {} >= ?".format(self.__attr2field_map['time_update'][0])
        )
        all_res = self.__db_obj.query(sql, (time_update.strftime("%Y-%m-%d")))
        return [Evaluation(**dict(zip(self.__attr2field_map.keys(), res))) for res in all_res]

    def getAll(self) -> Iterable[Evaluation]:
        # TODO 当前只实现了将结果全部fetch到内存中并返回整个列表，需要实现为带Buffer的迭代器以支持内存无法承受的数据量
        sql = (
            "SELECT {} FROM {} ".format(self.__fields_str, self.__table)
        )
        all_res = self.__db_obj.query(sql)
        return [Evaluation(**dict(zip(self.__attr2field_map.keys(), res))) for res in all_res]

    def save(self, replace_by: str, eval_list: List[Evaluation]) -> int:
        raise IOError("DatacenterEvaluationMapper is readonly")

    def getUpdateLastTime(self) -> datetime.date:
        pass


class JsonEvaluationMapper(EvaluationMapperInterface):
    """
    用于读取和保存JSON文件的EvaluationMapper
    """
    
    __idkey = 'uuid'                   # 代表id的属性名
    __attr2jsonkey_map = {             # Evaluation类实例属性和JSON键名以及数据类型的对应关系
        'uuid': ('eval_uuid', str),
        'person_uuid': ('person_uuid', str),
        'text': ('eval_text', str),
        'deficiency': ('eval_deficiency', str),
        'source': ('eval_source', str),
        'memo': ('eval_memo', str),
        'time_start': ('time_start', datetime.date)
    }
    def __init__(self):
        self.__jsonidkey = self.__attr2jsonkey_map[self.__idkey][0]

    def __json2eval(self, json_dict:Dict, none_as_emptystr:bool=False):
        """
        将一个JSON字典转为一个Evaluation对象
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
                        p_kwargs[attr] = datetime.datetime.strptime(json_dict[jsonkey], "%Y-%m").date()
                    elif len(time) == 10:
                        p_kwargs[attr] = datetime.datetime.strptime(json_dict[jsonkey], "%Y-%m-%d").date()
                    else:
                        raise ValueError("Illegal date string format, should be 'YYYY' or 'YYYY-MM' or 'YYYY-MM-DD'")
                    
                    # 如果年份是9999，则设置为datetime.date.max，即9999-12-31
                    if p_kwargs[attr].year == 9999:
                        p_kwargs[attr] = datetime.date.max
                else:
                    raise TypeError("缺少对应的转换规则，请在这段源码里加上")

        # 创建Evaluation实例
        res = Evaluation(**p_kwargs)
        return res

    def __eval2json(self, eval:Evaluation, none_as_emptystr:bool=False):
        """
        将一个Experience对象转为一个符合JSON规范的字典
        """
        json_dict = {}
        for attr in self.__attr2jsonkey_map.keys():
            attr_value = eval.__getattribute__(attr)
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

    def getById(self, file_path: str, id: str) -> Evaluation or None:
        raise IOError("这个接口没实现，如有需要请在此处实现")
    def getByIdList(self, file_path: str, id_list: List[str]) -> List[Evaluation]:
        raise IOError("这个接口没实现，如有需要请在此处实现")
    def getByPersonuuid(self, person_uuid: str) -> List[Evaluation]:
        raise IOError("这个接口没实现，如有需要请在此处实现")
    def getByPersonuuidList(self, person_uuid_list: List[str]) -> List[Evaluation]:
        raise IOError("这个接口没实现，如有需要请在此处实现")
    def getByUpdatetime(self, time_update: datetime.date) -> List[Evaluation]:
        raise IOError("这个接口没实现，如有需要请在此处实现")
    def getUpdateLastTime(self) -> datetime.date:
        raise IOError("这个接口没实现，如有需要请在此处实现")

    def getAll(self, file_path: str) -> List[Evaluation]:
        """
        读取JSON文件中全部记录,以Evaluation对象列表返回. 无结果返回空列表
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            json_obj = json.load(f)

        res = []
        for j in json_obj:
            res.append(self.__json2eval(j))
        return res

    def save(self, eval_list: List[Evaluation], save_path: str=None) -> int:
        """
        将eval_list转为JSON保存为新的文件.
        """
        if save_path:
            json_list = [self.__eval2json(p) for p in eval_list]
            with open(save_path, 'w+', encoding='utf-8') as f:
                json.dump(obj=json_list, fp=f, ensure_ascii=False, indent=2)
        else:
            raise IOError("save_path must be indicated")