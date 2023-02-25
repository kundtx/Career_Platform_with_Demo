import re
import copy
from typing import *
from ...common import Relative, Relationship, Person
from ...persistent.driver import MysqlDB
from .school_det import SchoolDetHelper

__all__ = ["recover_school_name", "match_rel_A00", "export_rel_relationship", "export_alumni_relationship", "export_tx_relationship"]


def recover_school_name(person_list:List[Person], in_position:bool=False, callback:Callable=None) -> List[Person]:
    """
    将传入的person_list中每一个Person的edu_ft_school检测并恢复成官方学校名(若校名更变过则恢复成当前该学校名称)

    Params:
        person_list: 待检测恢复学校名的Person列表
        in_position: True则在传入person_list上原地修改并返回原person_list. False则深拷贝后修改并返回新的
        callback: 回调函数, 需要能够接收一个包含函数执行状态信息的dict, 可以用来查看执行进度
    """
    if not in_position:
        person_list = copy.deepcopy(person_list)

    # 用于传入callback的状态字典
    __status_dict = {
        "description": "[person_parser]-recover_school_name",
        "total": len(person_list),
        "iternum": 0
    }

    school_det_obj = SchoolDetHelper()
    for iternum, person in enumerate(person_list):
        if person.edu_ft_school is None:
            continue
        school_det_res = school_det_obj.detect_fullname(person.edu_ft_school)
        if len(school_det_res) > 0:
            person.edu_ft_school = school_det_res[0][1]
        elif re.match(".+(学院|大学|学校)", person.edu_ft_school):
            person.edu_ft_school = re.match(".+(学院|大学|学校|党校|银行|中学)", person.edu_ft_school)[0]

        # 调用callback函数
        __status_dict["iternum"] = iternum
        if callback is not None:
            callback(__status_dict)

    return person_list


def match_rel_A00(rel_list:List[Relative], in_position:bool=False, callback:Callable=None) -> List[Relative]:
    """
    将传入的rel_list中每一个Relative的名字和生日同person表中的名字生日匹配, 获得person_uuid(数据中心A00)

    Params:
        rel_list: 待匹配person_uuid的Relative列表
        in_position: True则在传入rel_list上原地修改并返回原rel_list. False则深拷贝后修改并返回新的
        callback: 回调函数, 需要能够接收一个包含函数执行状态信息的dict, 可以用来查看执行进度
    """
    if not in_position:
        rel_list = copy.deepcopy(rel_list)
    db_obj = MysqlDB()
    conn = db_obj.connect()

    # 用于传入callback的状态字典
    __status_dict = {
        "description": "[person_parser]-match_rel_A00",
        "total": len(rel_list),
        "iternum": 0
    }

    for iternum, rel in enumerate(rel_list):
        if (rel.relative_name is None) or (rel.relative_birthday is None):
            continue
        cursor = conn.cursor()

        aff_rows = cursor.execute("SELECT person_uuid FROM person WHERE person_name=%s AND time_birth=%s",(rel.relative_name, rel.relative_birthday))
        res = cursor.fetchone()
        if res:
            rel.relative_uuid = res
            
        # 调用callback函数
        __status_dict["iternum"] = iternum
        if callback is not None:
            callback(__status_dict)

    conn.commit()
    conn.close()

    return rel_list


def export_rel_relationship(rel_list:List[Relative], callback:Callable=None) -> List[Relationship]:
    """
    将传入的rel_list中每一个Relative导出为Relationship

    Params:
        rel_list: 待导出的Relative列表
        callback: 回调函数, 需要能够接收一个包含函数执行状态信息的dict, 可以用来查看执行进度
    """

    result_rels:List[Relationship] = []

    # 用于传入callback的状态字典
    __status_dict = {
        "description": "[person_parser]-export_rel_relshp",
        "total": len(rel_list),
        "iternum": 0
    }

    for iternum, rel in enumerate(rel_list):
        if (rel.person_uuid is None) or (rel.relative_uuid is None):
            continue
        result_rels.append(Relationship(rel_type=203, 
                                        person_uuid_from=rel.person_uuid, person_uuid_to=rel.relative_uuid, 
                                        rel_info=rel.relative_type))

        # 调用callback函数
        __status_dict["iternum"] = iternum
        if callback is not None:
            callback(__status_dict)

    return result_rels
    

def export_alumni_relationship(person_list:List[Person], callback:Callable=None) -> List[Relationship]:
    """
    对传入的person_list匹配校友, 导出为Relationship

    Params:
        person_list: 待导出校友关系的Person列表
        callback: 回调函数, 需要能够接收一个包含函数执行状态信息的dict, 可以用来查看执行进度
    """
    result_rels:List[Relationship] = []
    db_obj = MysqlDB()
    conn = db_obj.connect()

    # 用于传入callback的状态字典
    __status_dict = {
        "description": "[person_parser]-export_alumni_relshp",
        "total": len(person_list),
        "iternum": 0
    }

    for iternum, person in enumerate(person_list):
        if person.edu_ft_school is None:
            continue
        cursor = conn.cursor()

        aff_rows = cursor.execute("SELECT person_uuid FROM person WHERE edu_ft_school=%s", person.edu_ft_school)
        res = cursor.fetchall()

        for i in res:
            if (i[0] is None) or (i[0] == person.uuid):
                continue
            result_rels.append(Relationship(rel_type=202, 
                                            person_uuid_from=person.uuid, person_uuid_to=i[0], 
                                            rel_info=person.edu_ft_school))

        # 调用callback函数
        __status_dict["iternum"] = iternum
        if callback is not None:
            callback(__status_dict)

    conn.commit()
    conn.close()

    return result_rels


def export_tx_relationship(person_list:List[Person], callback:Callable=None) -> List[Relationship]:
    """
    对传入的person_list匹配同乡, 导出为Relationship

    Params:
        person_list: 待导出同乡关系的Person列表
        callback: 回调函数, 需要能够接收一个包含函数执行状态信息的dict, 可以用来查看执行进度
    """
    result_rels:List[Relationship] = []
    db_obj = MysqlDB()
    conn = db_obj.connect()

    # 用于传入callback的状态字典
    __status_dict = {
        "description": "[person_parser]-export_tx_relshp",
        "total": len(person_list),
        "iternum": 0
    }

    for iternum, person in enumerate(person_list):
        if person.birthplace is None:
            continue
        cursor = conn.cursor()

        aff_rows = cursor.execute("SELECT person_uuid FROM person WHERE person_birthplace=%s", person.birthplace)
        res = cursor.fetchall()

        for i in res:
            if (i[0] is None) or (i[0] == person.uuid):
                continue
            result_rels.append(Relationship(rel_type=201, 
                                            person_uuid_from=person.uuid, person_uuid_to=i[0], 
                                            rel_info=person.birthplace))

        # 调用callback函数
        __status_dict["iternum"] = iternum
        if callback is not None:
            callback(__status_dict)

    conn.commit()
    conn.close()

    return result_rels