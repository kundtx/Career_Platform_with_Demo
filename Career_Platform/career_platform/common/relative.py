import pinyin
import datetime
from typing import *

__all__ = ["Relative"]

class Relative():
    """
    common class of a Relative. 

    Attributes:
        relative_id 亲属主键 (数据中心A36.recordid)
        relative_name 亲属姓名
        relative_birthday 亲属生日
        relative_type 称谓代码 (数据中心A3604B, 码表GB4761) 
        relative_uuid 亲属的person_uuid (该亲属在person表中时本字段才有值)
        person_uuid 亲属所属人员的person_uuid

    Functions:
        attr2dict(): 获得该实例的所有公开访问属性, 以字典形式返回
    """
    def __init__(self, **kwargs) -> None:
        # 公有属性
        self.relative_id:str = None                         # 亲属主键 (数据中心A36.recordid)
        self.relative_name:str = None                       # 亲属姓名
        self.relative_birthday:datetime.date = None         # 亲属生日
        self.relative_type:str = None                       # 称谓代码 (数据中心A3604B, 码表GB4761) 
        self.relative_uuid:str = None                       # 亲属的person_uuid (该亲属在person表中时本字段才有值)
        self.person_uuid:str = None                         # 亲属所属人员的person_uuid

        # 全量同步，暂不考虑增量同步
        # self.time_update:datetime.date = None               # 根据更新时间同步最新数据

        # 私有属性,其中一部分被@property和@*.setter修饰为公开访问属性
        pass

        # 所有公有属性带参初始化赋值
        public_attrs = [key for key in self.__dict__.keys() if key[0]!='_']
        for attr in public_attrs:
            if kwargs.get(attr, False):
                self.__setattr__(attr, kwargs[attr])

        # 被@property和@*.setter修饰的私有属性初始化赋值
        pass

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