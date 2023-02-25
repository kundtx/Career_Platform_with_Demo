import pinyin
import datetime
from typing import *

__all__ = ["Relationship"]

class Relationship():
    """
    common class of a Relationship. 

    Attributes:
        rel_id (int): 关系记录id
        rel_type (int): 关系类型
        person_uuid_from (str): 关系所属的人员UUID
        person_uuid_to (str): 关系指向的人员UUID'
        exp_uuid_from (str): 关系所属的经历UUID, 与经历无关则为NULL
        exp_uuid_to (str): 关系指向的经历UUID, 与经历无关则为NULL
        time_start (datetime.date): 关系开始日期
        time_end (datetime.date): 关系结束日期
        rel_info (str): 关系附加信息

    Functions:
        attr2dict(): 获得该实例的所有公开访问属性, 以字典形式返回
    """
    REL_TYPE_DICT = {
        101: '前任', 102: '继任', 103: '同事', 104: '上级', 105: '下级',
        201: '同乡', 202: '校友'
    }
    def __init__(self, **kwargs) -> None:
        # 公有属性
        self.rel_id:int = None              #关系记录id
        self.rel_type:int = None            #关系类型
        self.person_uuid_from:str = None    #关系所属的人员UUID
        self.person_uuid_to:str = None      #关系指向的人员UUID'
        self.exp_uuid_from:str = None       #关系所属的经历UUID, 与经历无关则为NULL
        self.exp_uuid_to:str = None         #关系指向的经历UUID, 与经历无关则为NULL
        self.rel_info:str = None            #关系附加信息

        # 私有属性,其中一部分被@property和@*.setter修饰为公开访问属性
        self.__time_start: datetime.date = None             # 关系开始日期
        self.__time_end: datetime.date = None               # 关系结束日期

        # 所有公有属性带参初始化赋值
        public_attrs = [key for key in self.__dict__.keys() if key[0]!='_']
        for attr in public_attrs:
            if kwargs.get(attr, False):
                self.__setattr__(attr, kwargs[attr])

        # 被@property和@*.setter修饰的私有属性初始化赋值
        if kwargs.get('time_start', False):
            self.time_start = kwargs['time_start']
        if kwargs.get('time_end', False):
            self.time_end = kwargs['time_end']

    @property
    def time_start(self) -> datetime.date:
        return self.__time_start
    @time_start.setter
    def time_start(self, time:datetime.date):
        if time and (not isinstance(time, datetime.date)):
            raise TypeError("time_start must be an instance of datetime.date or a None")
        self.__time_start = time

    @property
    def time_end(self) -> datetime.date:
        return self.__time_end
    @time_end.setter
    def time_end(self, time:datetime.date):
        if time and (not isinstance(time, datetime.date)):
            raise TypeError("time_end must be an instance of datetime.date or a None")
        self.__time_end = time

    def __str__(self) -> str:
        """
        使用str(对象)将对象转为字符串时，返回所有外部可访问的"{属性:属性值}"
        """
        return str(self.attr2dict())

    def attr2dict(self) -> Dict[str, Any]:
        """
        将对象公共属性转为{属性名:属性值}的词典
        """
        # __init__时创建的公有属性和属性值
        attrs = {name: value for name, value in self.__dict__.items() if name[0] != "_"}
        # 被@property修饰符创建的公有属性和属性值
        properties = {name: self.__getattribute__(name) for name, obj in vars(self.__class__).items() if isinstance(obj, property)}
        attrs.update(properties)
        
        return attrs