import datetime
from typing import *

__all__ = ["Label"]

class Label():
    """
    common class of a label. 

    Attributes:
        label_id (int): 标签id,
        label_code (str): 标签代码,
        label_text (str): 标签文本,
        label_category (int): '标签类别',
        label_source (int): 标签来源,
        label_info (str): 标签附加信息,
        person_uuid (str): 标签所属人员UUID,
        exp_uuid (str): 标签对应经历UUID, 标签来源非经历时为空值,
        eval_uuid (str): 标签对应评价材料UUID, 标签来源非评价材料时为空值,
        time_start (datetime.date): 标签开始日期,
        time_end (datetime.date): 标签结束日期

    Functions:
        attr2dict(): 获得该实例的所有公开访问属性, 以字典形式返回
    """
    def __init__(self, **kwargs) -> None:
        # 公有属性
        self.label_id:int = None
        self.label_code:str = None
        self.label_text:str = None
        self.label_category:int = None
        self.label_source:int = None
        self.label_info:str = None
        self.person_uuid:str = None
        self.exp_uuid:str = None
        self.eval_uuid:str = None
        self.time_start:datetime.date = None
        self.time_end:datetime.date = None

        # 私有属性,其中一部分被@property和@*.setter修饰为公开访问属性
        self.__time_start:datetime.date = None
        self.__time_end:datetime.date = None

        # 所有公有属性带参初始化赋值
        public_attrs = [key for key in self.__dict__.keys() if key[0]!='_']
        for attr in public_attrs:
            if kwargs.get(attr, False):
                self.__setattr__(attr, kwargs[attr])

        # 被@property和@*.setter修饰的私有属性初始化赋值
        if kwargs.get('time_start', False):
            self.__time_start = kwargs['time_start']
        if kwargs.get('time_end', False):
            self.__time_end = kwargs['time_end']

    @property
    def time_start(self) -> str:
        return self.__time_start
    @time_start.setter
    def time_start(self, time:datetime.date):
        if time and (not isinstance(time, datetime.date)):
            raise TypeError("time_start must be an instance of datetime.date")
        self.__time_start = time

    @property
    def time_end(self) -> str:
        return self.__time_end
    @time_end.setter
    def time_end(self, time:datetime.date):
        if time and (not isinstance(time, datetime.date)):
            raise TypeError("time_end must be an instance of datetime.date")
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