import pinyin
import datetime
from typing import *

__all__ = ["Experience"]

class Experience():
    """
    common class of experience.

    Attributes:
        uuid (str): 经历在数据中心的UUID (数据中心A16主键)
        splitnum (int): 编号, 代表本经历是对应经历原文的第几个兼职拆分结果. 若没被拆分过则为0
        ordernum (int): 编号, 代表本经历是对应Person的第几条经历
        person_uuid (str): 经历所属人员UUID (数据中心A00)
        text (str): 经历文本
        text_token (str): 经历文本的token
        text_raw (str): 经历原文
        text_rawpinyin (str): 经历原文(首字母拼音)
        text_rawrefine (str): 经历原文(refine后)
        text_rawsplit (str): 经历原文(adjunct_split后)
        text_rawtoken (str): 经历原文(segment后)
        adminrank (str): 经历行政级别
        time_start (datetime.date): 经历开始日期
        time_end (datetime.date): 经历结束日期
    
    Functions:
        attr2dict(): 获得该实例的所有公开访问属性, 以字典形式返回
        duration(): 返回经历持续时间, 以月或日为单位, 默认以月为单位
    """
    def __init__(self, **kwargs):
        # 公有属性
        self.uuid: str = None                               # 履历在数据中心的uuid（A16主键）
        self.splitnum: int = 0                              # 编号，代表本条记录是对应经历原文的第几个兼职拆分结果. 若没被拆分则为0
        self.ordernum: int = None                           # 编号，代表本记录是对应人员的第几条经历
        self.person_uuid: str = None                        # 经历所属人员UUID（数据中心A00）
        
        self.text: str = None                               # 经历文本
        self.text_token: str = None                         # 经历文本的token
        self.text_raw: str = None                           # 经历原文
        self.text_rawpinyin: str = None                     # 经历原文（首字母拼音）
        self.text_rawrefine: str = None                     # 经历原文（refine后）
        self.text_rawsplit: str = None                      # 经历原文（adjunct_split后）
        self.text_rawtoken: str = None                      # 经历原文（tokenize后）
        self.adminrank: str = None                          # 经历行政级别

        # 私有属性,其中一部分被@property和@*setter修饰为公开访问属性
        self.__time_start: datetime.date = None             # 经历开始日期
        self.__time_end: datetime.date = None               # 经历结束日期

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
    
    def duration(self, unit:str="month") -> int or None:
        """
        返回经历的持续时间, 通过time_start和time_end计算得到
        
        Params:
            unit (str): 持续时间的单位，可以是"month"或"day"
        """
        # 起止时间有None则返回None
        if (self.time_start is None) or (self.time_end is None):
            return None

        if unit == "month":
            # 经历time_end为datetime.date.max时，返回time_start到今天的时间
            if self.time_end == datetime.date.max:
                today = datetime.date.today()
                return (today.year-self.time_start.year)*12 + today.month - self.time_start.month
            else:
                return (self.time_end.year-self.time_start.year)*12 + self.time_end.month - self.time_start.month

        elif unit == "day":
            # 经历time_end为datetime.date.max时，返回time_start到今天的时间
            if self.time_end == datetime.date.max:
                return (datetime.date.today() - self.time_start).days
            # 否则返回time_end-time_start
            else:
                return (self.time_end - self.time_start).days
        else:
            raise ValueError('Illegal unit value \"%s\", should be \"month\" or \"day\"' % unit)