import pinyin
import datetime
from typing import *

__all__ = ["Person"]

class Person():
    """
    common class of a person. 

    Attributes:
        uuid (str): 人员UUID (数据中心A00)
        name (str): 人员姓名
        name_pinyin (str): 人员姓名拼音首字母
        gender (str): 性别{'1': 男, '2': 女}
        minzu (str): 民族
        origo (str): 籍贯
        birthplace (str): 出生地
        photo (str): 照片路径
        edu_ft (str): 最高全日制教育学历
        edu_ft_school (str): 最高全日制教育学校
        edu_pt (str): 最高在职教育学历
        edu_pt_school (str): 最高在职教育学校
        cur_position (str): 现任职位
        cur_adminrank (str): 现任行政级别
        time_birth (datetime.date): 生日
        time_joinparty (datetime.date): 入党时间
        time_startwork (datetime.date): 开始工作时间

    Functions:
        attr2dict(): 获得该实例的所有公开访问属性, 以字典形式返回
    """
    def __init__(self, **kwargs) -> None:
        # 公有属性
        self.uuid: str = None                       #人员UUID (数据中心A00)
        self.gender: str = None                     #性别{1: 男, 2: 女}
        self.minzu: str = None                      #民族
        self.origo: str = None                      #籍贯
        self.birthplace: str = None                 #出生地
        self.photo: str = None                      #照片路径
        self.edu_ft: str = None                     #最高全日制教育学历
        self.edu_ft_school: str = None              #最高全日制教育学校
        self.edu_pt: str = None                     #最高在职教育学历
        self.edu_pt_school: str = None              #最高在职教育学校
        self.cur_position: str = None               #现任职位
        self.cur_adminrank: str = None              #现任行政级别

        # 私有属性,其中一部分被@property和@*.setter修饰为公开访问属性
        self.__name: str = None                     #人员姓名
        self.__name_pinyin: str = None              #人员姓名拼音首字母
        self.__time_birth: datetime.date = None     #生日
        self.__time_joinparty: datetime.date = None #入党时间
        self.__time_startwork: datetime.date = None #工作时间

        # 所有公有属性带参初始化赋值
        public_attrs = [key for key in self.__dict__.keys() if key[0]!='_']
        for attr in public_attrs:
            if kwargs.get(attr, False):
                self.__setattr__(attr, kwargs[attr])

        # 被@property和@*.setter修饰的私有属性初始化赋值
        if kwargs.get('name', False):
            self.__name = kwargs['name']

        if kwargs.get('name_pinyin', False):    #若传入了name_pinyin则直接用该值初始化self.name_pinyin
            self.__name_pinyin = kwargs['name_pinyin']
        elif self.__name is not None:   # 若没传入name_pinyin，但传入了name，则由name自动生成self.name_pinyin
            self.__name_pinyin = pinyin.get_initial(self.__name, delimiter='').upper()

        if kwargs.get('time_birth', False):
            self.time_birth = kwargs['time_birth']
        if kwargs.get('time_joinparty', False):
            self.time_joinparty = kwargs['time_joinparty']
        if kwargs.get('time_startwork', False):
            self.time_startwork = kwargs['time_startwork']

    @property
    def name(self) -> str:
        return self.__name
    @name.setter
    def name(self, name:str):
        self.__name = name
        # 给name赋值时自动生成name_pinyin
        self.__name_pinyin = pinyin.get_initial(self.__name, delimiter='').upper()

    @property
    def name_pinyin(self) -> str:
        return self.__name_pinyin
    @name_pinyin.setter
    def name_pinyin(self, name_pinyin:str):
        self.__name_pinyin = name_pinyin

    @property
    def time_birth(self) -> datetime.date:
        return self.__time_birth
    @time_birth.setter
    def time_birth(self, time_birth: datetime.date):
        if time_birth and (not isinstance(time_birth, datetime.date)):
            raise TypeError("time_birth must be an instance datetime.date or a None")
        self.__time_birth = time_birth

    @property
    def time_joinparty(self) -> datetime.date:
        return self.__time_joinparty
    @time_joinparty.setter
    def time_joinparty(self, time_joinparty: datetime.date):
        if time_joinparty and (not isinstance(time_joinparty, datetime.date)):
            raise TypeError("time_joinparty must be an instance of datetime.date or a None")
        self.__time_joinparty = time_joinparty

    @property
    def time_startwork(self) -> datetime.date:
        return self.__time_startwork
    @time_startwork.setter
    def time_startwork(self, time_startwork: datetime.date):
        if time_startwork and (not isinstance(time_startwork, datetime.date)):
            raise TypeError("time_startwork must be an instance of datetime.date or a None")
        self.__time_startwork = time_startwork

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