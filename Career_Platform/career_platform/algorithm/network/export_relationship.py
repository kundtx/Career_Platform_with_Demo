import py2neo
import os,sys
import re
import datetime
from ...common import Relationship
from ...config import neo4j_config
from typing import *
import json

__all__ = ["export_nid2resumes_relationship", "export_neo4j_relationship"]

TEMP_DATA_PATH = os.path.dirname(__file__) + "/data/temp"



def export_nid2resumes_relationship(file_path:str=TEMP_DATA_PATH+"/nid2resumes.json", callback:Callable=None)-> Iterable[Relationship]:
    """
    导出nid2resumes.json中的关系并转为Relationship实例, 返回一个Relationship列表

    Params:
        file_path: nid2resumes.json文件路径

    Info:
        关系代码: 101: '前任', 102: '继任'"
    """
    __status_dict = {
        "description": "[export Rels]-nid2resumes",
        "total": 0,
        "iternum": 0
    }

    result_rels = []

    nid2resumes:Dict[str, List[List[str]]] = {}    # 各nid和所属经历的对应关系
    with open(os.path.join(file_path), 'r', encoding='utf-8') as fp:
        nid2resumes = json.load(fp)

    __status_dict["total"] = len(nid2resumes)

    for nid, resume_list in nid2resumes.items():
        __status_dict["iternum"] += 1

        resume_list.sort(key=lambda x:x[3])    # 按结束时间排序resume_list
        if len(resume_list) < 2:    # 一个nid里的resume小于2个就说明没有前任/继任
            continue

        for i in range(len(resume_list)):
            cur_expuuid = resume_list[i][0].split('+')[0]
            cur_personuuid = resume_list[i][1]
            # 获取前任
            for j in range(0, i):   
                pre_expuuid = resume_list[j][0].split('+')[0]
                pre_personuuid = resume_list[j][1]
                if cur_personuuid == pre_personuuid:    # 跳过自己跟自己是前继任的情况
                    continue
                result_rels.append(Relationship(rel_type=101, 
                                                person_uuid_from=cur_personuuid, person_uuid_to=pre_personuuid,
                                                exp_uuid_from=cur_expuuid, exp_uuid_to=pre_expuuid))
            # 获取继任
            for j in range(i+1, len(resume_list)):
                succ_expuuid = resume_list[j][0].split('+')[0]
                succ_personuuid = resume_list[j][1]
                if cur_personuuid == succ_personuuid:   # 跳过自己跟自己是前继任的情况
                    continue
                result_rels.append(Relationship(rel_type=102, 
                                                person_uuid_from=cur_personuuid, person_uuid_to=succ_personuuid,
                                                exp_uuid_from=cur_expuuid, exp_uuid_to=succ_expuuid))
        
        # 调用回调函数                                        
        if callback:
            callback(__status_dict)
    
    return result_rels


def export_neo4j_relationship(config:dict=neo4j_config, callback:Callable=None) -> Iterable[Relationship]:
    """
    导出neo4j数据库中所有的关系并转为Relationship实例, 返回一个Relationship列表

    Params:
        config: neo4j数据库配置词典
        callback: 回调函数， 需要能够接收一个包含函数执行状态信息的dict, 可以用来查看执行进度

    Info:
        关系代码: 103: '同事', 104: '上级', 105: '下级'
    """

    __status_dict = {
        "description": "[export Rels]-neo4j",
        "total": 0,
        "iternum": 0
    }

    result_rels = []

    graph = py2neo.Graph("bolt://{}:{}".format(neo4j_config["host"], neo4j_config["port"]), username=neo4j_config["user"], password=neo4j_config["password"])
    TYPE_DICT = {'Col': 103, 'Rank_cross': 105, 'Rank':105}
    TYPE_DICT_REVERSE = {'Col': 103, 'Rank_cross': 104, 'Rank':104}

    __status_dict["total"] = graph.run('''MATCH (a:YearUser)-[r:Col|Rank|Rank_cross]->(b) RETURN count(r)''').data()[0]["count(r)"]

    colleague_res = graph.run('''MATCH (a:YearUser)-[r:Col|Rank|Rank_cross]->(b) RETURN r,type(r)''')
    for iternum, col in enumerate(colleague_res):
        data = col.data()
        rel_type = data["type(r)"]
        nodes = dict(data['r'].nodes[0]), dict(data['r'].nodes[1])
        time_start, time_end = data['r'].relationships[0]['period']
        
        # 时间转换为datetime.date
        if isinstance(time_start, str) and re.match("[0-9]{4}.[0-9]{2}", time_start):
            time_start = datetime.datetime.strptime(time_start, "%Y.%m").date()
        else:
            time_start = None
        if isinstance(time_end, str) and re.match("[0-9]{4}.[0-9]{2}", time_end):
            time_end = datetime.datetime.strptime(time_end, "%Y.%m").date()
        else:
            time_end = None

        # 生成正向的同事、下级Relationship
        rel1 = Relationship(rel_type=TYPE_DICT[rel_type], 
                            person_uuid_from=nodes[0]["uid"], person_uuid_to=nodes[1]["uid"],
                            exp_uuid_from=nodes[0]["id"].split('+')[0], exp_uuid_to=nodes[1]["id"].split('+')[0],
                            time_start=time_start, time_end=time_end)
        
        # 生成反向的同事、上级Relationship
        rel2 = Relationship(rel_type=TYPE_DICT_REVERSE[rel_type], 
                            person_uuid_from=nodes[1]["uid"], person_uuid_to=nodes[0]["uid"],
                            exp_uuid_from=nodes[1]["id"].split('+')[0], exp_uuid_to=nodes[0]["id"].split('+')[0],
                            time_start=time_start, time_end=time_end)
        result_rels.append(rel1)
        result_rels.append(rel2)

        # 调用回调函数
        if callback:
            __status_dict["iternum"] = iternum
            callback(__status_dict)

    return result_rels
    