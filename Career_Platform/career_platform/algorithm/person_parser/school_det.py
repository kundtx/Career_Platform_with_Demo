from typing import *
import numpy as np
import sys, os
import ahocorasick

__all__ = ["SchoolDetHelper"]


DATA_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), "../exp_parser/rebuild/location_recover")


class SchoolDetHelper():
    """
    学校检测时辅助工具, 只在第一次实例化时加载, 全局单例

    Attributes:
        school2pc_dict:           高校名回查[省,市]词典, 有后缀

    Function:
        detect_by_school2pc_AC(): 用高校AC自动机检测句子中的高校名, 以推断地点, 返回所有匹配位置和对应[省市]
    """
    school2fullname_dict = None
    school2fullname_AC = None

    def __init__(self):
        # 只需初次实例化时初始化各类变量, 之后就不用了
        if self.school2fullname_dict is None:
            self.__init_school2fullname_dict()
            self.__init_school2fullname_AC()

    def detect_fullname(self, text:str) -> List[Tuple[str, str]]:
        """
        用高校AC自动机检测句子中的高校名, 返回高校全名
        """
        results = []
        for res in self.school2fullname_AC.iter_long(text):
            results.append(res[1])
        return results

    @classmethod
    def __init_school2fullname_dict(cls):
        """
        加载高校名称回查高校全名的词典
        """
        cls.school2fullname_dict:Dict[str, str] = {}
        pugao_csv = np.loadtxt(DATA_DIR + "/全国普通高等学校名单_2021.csv", dtype=str, delimiter=",", encoding="utf-8")
        # supplement_csv = np.loadtxt(DATA_DIR + "/高校补充名单.csv", dtype=str, delimiter=",", encoding="utf-8")

        for school in pugao_csv:
            alias_list = school[0].split("/")
            for alias in alias_list:
                cls.school2fullname_dict[alias] = alias_list[0]

    @classmethod
    def __init_school2fullname_AC(cls):
        """
        初始化高校匹配AC自动机
        """
        cls.school2fullname_AC = ahocorasick.Automaton()
        for name, full_name in cls.school2fullname_dict.items():
            cls.school2fullname_AC.add_word(name, (name, full_name))
        cls.school2fullname_AC.make_automaton()