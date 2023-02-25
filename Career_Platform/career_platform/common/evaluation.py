import datetime
from typing import *


class Evaluation:
    """
    common class of Evaluation.

    Attributes:
        uuid (str): 评价记录在数据中心的UUID (数据中心RECORDID主键)
        person_uuid (str): 所属人员UUID (数据中心A00)
        text (str): 评价文本 (数据中心 GBPJ)
        ordernum (int): 排序, （数据中心 PINDEX)
        effective (str): 状态:是否有效, （数据中心 SFYX)
        deficiency (str): 主要不足 （数据中心 ZYBZ)
        source (str): 来源 (数据中心 LY)
        ismatch (str): 是否匹配 （数据中心 SFPP)
        memo (str): 备注(数据中心 BZ)

        time_start (datetime.date): 时间（评价时间） (数据中心 SJ)
        time_create (datetime.date): 创建时间 (数据中心 CREATETIME)
        time_update (datetime.date): 更新时间 (数据中心 UPDATETIME)

    Functions:
        attr2dict(): 获得该实例的所有公开访问属性, 以字典形式返回
    """

    def __init__(self, **kwargs):
        # 公有属性
        self.uuid: str = None  # 评价在数据中心的uuid
        self.person_uuid: str = None  # 评价所属人员UUID（数据中心A00）
        self.text: str = None  # 评价内容文本
        self.ordernum: int = None # 排序
        self.effective: str = None #状态：是否有效
        self.ismatch: str = None
        self.deficiency: str = None
        self.source: str = None
        self.memo: str = None

        # 私有属性,其中一部分被@property和@*setter修饰为公开访问属性
        self.__time_start: datetime.date = None  # 评价日期
        self.__time_create: datetime.date = None  #
        self.__time_update: datetime.date = None  #

        # 所有公有属性带参初始化赋值
        public_attrs = [key for key in self.__dict__.keys() if key[0] != '_']
        for attr in public_attrs:
            if kwargs.get(attr, False):
                self.__setattr__(attr, kwargs[attr])

        # 被@property和@*.setter修饰的私有属性初始化赋值
        if kwargs.get('time_start', False):
            self.time_start = kwargs['time_start']
        if kwargs.get('time_create', False):
            self.time_create = kwargs['time_create']
        if kwargs.get('time_update', False):
            self.time_update = kwargs['time_update']

    @property
    def time_start(self) -> datetime.date:
        return self.__time_start

    @time_start.setter
    def time_start(self, time:datetime.date):
        if time and (not isinstance(time, datetime.date)):
            raise TypeError("time_start must be an instance of datetime.date or a None")
        self.__time_start = time

    @property
    def time_create(self) -> datetime.date:
        return self.__time_create

    @time_create.setter
    def time_create(self, time:datetime.date):
        if time and (not isinstance(time, datetime.date)):
            raise TypeError("time_create must be an instance of datetime.date or a None")
        self.__time_create = time

    @property
    def time_update(self) -> datetime.date:
        return self.__time_update

    @time_update.setter
    def time_update(self, time:datetime.date):
        if time and (not isinstance(time, datetime.date)):
            raise TypeError("time_update must be an instance of datetime.date or a None")
        self.__time_update = time

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
        properties = {name: self.__getattribute__(name) for name, obj in vars(self.__class__).items() if
                      isinstance(obj, property)}
        attrs.update(properties)

        return attrs
