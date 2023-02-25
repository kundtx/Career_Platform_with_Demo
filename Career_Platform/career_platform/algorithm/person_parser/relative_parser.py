from typing import *
from ...persistent.driver import MysqlDB
from . import relative_util as rela_util
from . import relative_code as rela_code
from ...common import Relationship

__all__ = ["export_relativeship"]


def export_relativeship(callback: Callable = None) -> List[Relationship]:
    """
    导出亲属关系
    直接亲属关系：
    1. A(人员表)->B(亲属表)->B(人员表)
    间接亲属关系：
    1. A(人员表)->B(亲属表)，C(人员表)->B(亲属表)，A与C有亲属关系
    2. A(人员表)->B(亲属表)->B(人员表)->C(亲属表)->D(人员表), A与D有亲属关系
    """
    # 用于传入callback的状态字典
    __status_dict = {
        "description": "[relative_parser]-export_relativeship",
        "total": 3,
        "iternum": 0
    }
    # 直接亲属关系：
    rela_list = __direct_relative()
    __callback_exec(callback, __status_dict, 1)
    # 间接亲属关系
    # 第一种情况
    rela_list += __indirect_relative_1()
    __callback_exec(callback, __status_dict, 2)
    # 第二种情况
    rela_list += __indirect_relative_2()
    __callback_exec(callback, __status_dict, 3)

    return rela_list


def __callback_exec(callback: Callable = None, __status_dict: Tuple = None, iternum: int = 0):
    # 调用callback函数
    __status_dict["iternum"] = iternum
    if callback is not None:
        callback(__status_dict)


def __direct_relative(callback: Callable = None) -> List[Relationship]:
    """
    直接亲属关系：
    1. A(人员表)->B(亲属表)->B(人员表)
    """
    sql = f'''
        SELECT
            pa.person_uuid AS person_from_uuid
            ,pa.person_gender AS person_from_gender	
            ,pb.person_uuid AS person_to_uuid
            ,prb.relative_type AS relative_type
        FROM
            person pa
            -- A(人员表)->B(亲属表)
            INNER JOIN person_relative prb ON pa.person_uuid = prb.person_uuid
            -- B(亲属表)->B(人员表)
            INNER JOIN person pb ON pb.person_uuid = prb.relative_uuid
    '''

    db_obj = MysqlDB()
    conn = db_obj.connect()
    # cursor = conn.cursor()
    all_res = db_obj.query(sql)
    # conn.commit()
    conn.close()

    attr2field_map = {  # 属性和数据库表字段对应关系以及数据类型
        'person_from_uuid': ('person_from_uuid', str),  # A用户 person_uuid
        'person_from_gender': ('person_from_gender', int),  # A用户性别
        'person_to_uuid': ('person_to_uuid', str),  # D用户 person_uuid
        'relative_type': ('relative_type', str),  # A关联的B亲属称谓
    }

    data = [dict(zip(attr2field_map.keys(), res)) for res in all_res]

    rela_list = []
    for rela in data:
        relationship = Relationship(
            rel_type=203  # 亲属关系
            , person_uuid_from=rela["person_from_uuid"]
            , person_uuid_to=rela["person_to_uuid"]
            , rel_info=rela_code.code[rela["relative_type"]]  # 称谓
        )
        rela_list.append(relationship)

    # 保存关系
    # cem = CP.persistent.mapper.CareerDBRelationshipMapper()
    # return cem.save(replace_by="id", relationship_list=rela_list)
    return rela_list


def __indirect_relative_1(callback: Callable = None) -> List[Relationship]:
    """
    处理以下亲属关系：
    1. A(人员表)->B(亲属表)，C(人员表)->B(亲属表)，A与C有亲属关系
    """
    sql = f'''
        -- 查找同名同日的亲属
        SELECT
            CONCAT(prg.relative_name,'_',prg.relative_birthday) AS name_birthday
            ,prg.c -- 重复亲属个数
            ,pr2.person_uuid -- 亲属所属人员的person_uuid
            ,pr2.relative_type -- 称谓
            ,p.person_gender -- 性别
        FROM
            (
            SELECT
                pr.relative_name AS relative_name,
                pr.relative_birthday AS relative_birthday,
                count( 1 ) AS c 
            FROM
                person_relative pr 
            GROUP BY
                pr.relative_name,
                pr.relative_birthday 
            ) prg
            INNER JOIN person_relative pr2 ON prg.relative_name = pr2.relative_name 
                        AND prg.relative_birthday = pr2.relative_birthday 
            INNER JOIN person p on p.person_uuid = pr2.person_uuid
        WHERE
            prg.c > 1 -- 存在重复亲属
        '''

    db_obj = MysqlDB()
    conn = db_obj.connect()
    # cursor = conn.cursor()
    all_res = db_obj.query(sql)
    # conn.commit()
    conn.close()

    attr2field_map = {  # 属性和数据库表字段对应关系以及数据类型
        'name_birthday': ('name_birthday', str),  # 以姓名与出生日期作查询条件
        'count': ('c', int),  # 重复亲属个数
        'person_uuid': ('person_uuid', str),  # 亲属所属人员的person_uuid
        'relative_type': ('relative_type', str),  # 称谓
        'person_gender': ('person_gender', str)  # 性别
    }

    data = [dict(zip(attr2field_map.keys(), res)) for res in all_res]
    dataByNB = {}
    for rela in data:
        if rela["name_birthday"] in dataByNB:
            dataByNB[rela["name_birthday"]].append(rela)
        else:
            dataByNB[rela["name_birthday"]] = [rela]

    # print(v for v in (dataByNB[k] for k in dataByNB))

    rela_list = []
    for k in dataByNB:
        for v1 in dataByNB[k]:
            for v2 in dataByNB[k]:
                if v1["person_uuid"] != v2["person_uuid"]:
                    rela_str = "{}的{}".format(
                        rela_code.code[v1["relative_type"]],
                        rela_code.code[v2["relative_type"]]
                    )
                    rela_type_list = rela_util.get_relation({
                        'text': rela_str,
                        'sex': v1["person_gender"] if v1["person_gender"] else 1
                    })
                    relationship = Relationship(
                        rel_type=203  # 亲属关系
                        , person_uuid_from=v1["person_uuid"]
                        , person_uuid_to=v2["person_uuid"]
                        , rel_info=",".join(rela_type_list)  # 称谓
                    )
                    rela_list.append(relationship)
            # print(v)

    # 保存关系
    # cem = CP.persistent.mapper.CareerDBRelationshipMapper()
    # return cem.save(replace_by="id", relationship_list=rela_list)
    return rela_list


def __indirect_relative_2(callback: Callable = None) -> List[Relationship]:
    """
    处理以下亲属关系：
    2. A(人员表)->B(亲属表)->B(人员表)->C(亲属表)->D(人员表), A与D有亲属关系
    """
    sql = f'''
        SELECT
            pa.person_uuid AS person_from_uuid
            ,pa.person_gender AS person_from_gender	
            ,pd.person_uuid AS person_to_uuid
            ,prb.relative_type AS relative_b_type
            ,prc.relative_type AS relative_c_type	
        FROM
            person pa
            -- A(人员表)->B(亲属表)
            INNER JOIN person_relative prb ON pa.person_uuid = prb.person_uuid
            -- B(亲属表)->B(人员表)
            INNER JOIN person pb ON pb.person_uuid = prb.relative_uuid
            -- B(人员表)->C(亲属表)
            INNER JOIN person_relative prc ON pb.person_uuid = prc.person_uuid
            -- C(亲属表)->D(人员表)
            INNER JOIN person pd ON pd.person_uuid = prc.relative_uuid    
    '''

    db_obj = MysqlDB()
    conn = db_obj.connect()
    # cursor = conn.cursor()
    all_res = db_obj.query(sql)
    # conn.commit()
    conn.close()

    attr2field_map = {  # 属性和数据库表字段对应关系以及数据类型
        'person_from_uuid': ('person_from_uuid', str),  # A用户 person_uuid
        'person_from_gender': ('person_from_gender', int),  # A用户性别
        'person_to_uuid': ('person_to_uuid', str),  # D用户 person_uuid
        'relative_b_type': ('relative_b_type', str),  # A关联的B亲属称谓
        'relative_c_type': ('relative_c_type', str)  # B关联的C亲属称谓
    }

    data = [dict(zip(attr2field_map.keys(), res)) for res in all_res]

    rela_list = []
    for rela in data:
        rela_str = "{}的{}".format(
            rela_code.code[rela["relative_b_type"]],
            rela_code.code[rela["relative_c_type"]]
        )
        rela_type_list = rela_util.get_relation({
            'text': rela_str,
            'sex': rela["person_from_gender"] if rela["person_from_gender"] else 1
        })
        relationship = Relationship(
            rel_type=203  # 亲属关系
            , person_uuid_from=rela["person_from_uuid"]
            , person_uuid_to=rela["person_to_uuid"]
            , rel_info=",".join(rela_type_list)  # 称谓
        )
        rela_list.append(relationship)

    # 保存关系
    # cem = CP.persistent.mapper.CareerDBRelationshipMapper()
    # return cem.save(replace_by="id", relationship_list=rela_list)
    return rela_list

# if __name__ == "__main__":
#     rela_list = export_relativeship()
#     for rela in rela_list:
#         print(rela)
#     pass
