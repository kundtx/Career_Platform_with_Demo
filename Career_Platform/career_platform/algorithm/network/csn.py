# !/usr/bin/env python3
# -*- coding:utf-8 -*-
from py2neo import Graph, Node, Relationship
from py2neo.database import Schema
from itertools import islice
import pymysql
from py2neo.ogm import GraphObject, Related, Property, RelatedTo, RelatedFrom, Label
from py2neo.bulk import create_nodes, create_relationships
from typing import List, Tuple, Dict, Callable, Iterable
from ...config import neo4j_config
from ...common import Experience
import datetime

school_mate = ['学习P', '学生P', '专业S']


def get_rank(user1, user2):
    leader_level = ["部长P", "省长P", "副部长P", "副省长P", "厅长P", "局长P", "副厅长P", "副局长P",
                    "处长P", "县长P", "副处长P", "副县长P", "科长P", "乡长P", "副科长P", "副乡长P"]
    servant_level1 = ["一级巡视员P", "二级巡视员P", "一级调研员P", "二级调研员P", "三级调研员P", "四级调研员P",
                      "一级主任科员P", "二级主任科员P", "三级主任科员P", "四级主任科员P", "一级科员P", "二级科员P"]
    servant_level2 = ["巡视员P", "副巡视员P", "调研员P", "副调研员P", "主任科员P", "副主任科员P", "科员P"]

    if user1 in servant_level1 and user2 in servant_level1:
        if servant_level1.index(user1) < servant_level1.index(user2):
            return 1
        else:
            return -1
    if user1 in servant_level2 and user2 in servant_level2:
        # print(user1,user2)
        if servant_level2.index(user1) < servant_level2.index(user2):
            return 1
        else:
            return -1
    if user1 in leader_level and user2 in leader_level:
        if leader_level.index(user1) // 2 < leader_level.index(user2) // 2:
            return 1
        else:
            return -1
    if user1 == user2[1:] and user2[0] == "副":
        return 1
    elif user2 == user1[1:] and user1[0] == "副":
        return -1
    else:
        return 0


def batch(iterable, n=1):
    l = len(iterable)
    for ndx in range(0, l, n):
        yield iterable[ndx:min(ndx + n, l)]


class UserNodeNEO(GraphObject):
    __primarylabel__ = 'YearUser'
    # 定义主键
    __primarykey__ = 'id'  # id = year + user_id
    # 定义类的属性
    name = Property()  # uid
    id = Property()  # 2010156
    tag = Property()  # 深圳市L罗湖区L教育局O人事科S干部P
    # 定义类的标签
    # leaf = Label()
    # 定义同事关系
    colleague = Related('UserNodeNEO', 'C')
    # 定义上下级关系
    subordinate = RelatedTo('UserNodeNEO', 'R')
    superior = RelatedFrom('UserNodeNEO', 'R')


class CareerSocialNetwork(object):
    def __init__(self, start, end):
        self.start = start
        self.end = end
        self.GraphDatabase = Graph(neo4j_config)
        self.schema = Schema(self.GraphDatabase)
        self.schema.create_index("YearUser", "id")  # much faster to build tree, very important index

    def get_node(self, id):
        return UserNodeNEO.match(self.GraphDatabase, id).first()

    def batch_node_insert(self, data: List, keys: List[str]) -> None:
        batch_size = 10000
        for b in batch(data, batch_size):
            create_nodes(self.GraphDatabase.auto(), b, labels={"YearUser"}, keys=keys)

    def batch_relation_insert(self, data: List, R: str) -> None:
        batch_size = 10000
        count = 1
        for b in batch(data, batch_size):
            count += 1
            create_relationships(self.GraphDatabase.auto(), b, R,
                                 start_node_key=("YearUser", "id"),
                                 end_node_key=("YearUser", "id"))

    def store_user_resume_nodes(self, exp_list: List[Experience], uid2name: Dict, init=True) -> None:
        """
        store YearUser Nodes and Trajectory edges
        """
        # if init:
        #     self.GraphDatabase.delete_all()  # clear
        # as with merge_nodes, also WriteBatch is another way(but only in newer version py2neo)
        keys = ["id", "name", "uid", "tag", "raw", "interval"]
        nodes_data = []
        career_track = []
        last_exp_uuid = {}
        last_splitnum={}
        exp_list_sorted = sorted(exp_list, key=lambda x:datetime.date.min if x.time_start is None else x.time_start)
        exp_list_sorted = sorted(exp_list_sorted, key=lambda x:"0" if x.person_uuid is None else x.person_uuid)
        '''Build career trajectory and store nodes'''
        for exp in exp_list_sorted:
            person_uuid = exp.person_uuid
            exp_uuid = exp.uuid
            splitnum = exp.splitnum
            interval = str(exp.time_start) + "——" + str(exp.time_end)
            id = str(exp_uuid) + '+' + str(splitnum)
            if exp.text:
                job = exp.text.strip().replace("MBA", "管理学硕士").replace("EMBA", "管理学硕士").replace("||", "|")
            else:
                continue
            nodes_data.append([id, uid2name.get(person_uuid, "null"), person_uuid, exp.text_token, job, interval])
            if person_uuid not in last_exp_uuid:
                last_exp_uuid[person_uuid] = exp_uuid
                last_splitnum[exp_uuid] = str(splitnum)
                continue
            if last_exp_uuid[person_uuid] == exp_uuid:  # uuid doesn't change
                if splitnum > 0:
                    last_id = str(exp_uuid) + '+' + str(splitnum - 1)
                    career_track.append(((last_id), {}, (id)))
            else:  # uuid has changed
                last_id = last_exp_uuid[person_uuid] + '+' + last_splitnum[last_exp_uuid[person_uuid]]
                career_track.append(((last_id), {}, (id)))
            # record for track
            last_exp_uuid[person_uuid] = exp_uuid
            last_splitnum[exp_uuid] = str(splitnum)
        print("******** Inserting {} YearUser Nodes **************".format(len(nodes_data)))
        self.batch_node_insert(nodes_data, keys=keys)
        print("******** Inserting {} Trajectory Rels *************".format(len(career_track)))
        self.batch_relation_insert(career_track, "trajectory")

    def store_social_network(self, colleague_list, superior_list_same, superior_list_cross):
        relationship_col = []
        relationship_rank_same = []
        relationship_rank_cross = []

        for col in colleague_list:
            # print(col)
            mid, nid, year = col
            relationship_col.append(((mid), {"period": year}, (nid)))

        for col in superior_list_same:
            # print(col)
            mid, nid, m_rank, n_rank, year = col
            relationship_rank_same.append(((mid),
                                           {"period": year, "subordinate": n_rank, "superior": m_rank},
                                           (nid)))

        for col in superior_list_cross:
            # print(col)
            mid, nid, m_rank, n_rank, year = col
            relationship_rank_cross.append(((mid),
                                            {"period": year, "subordinate": n_rank, "superior": m_rank},
                                            (nid)))

        # print(len(relationship_col))
        # print(len(relationship_rank_same))
        # print(len(relationship_rank_cross))
        self.batch_relation_insert(relationship_col, "Col")
        self.batch_relation_insert(relationship_rank_same, "Rank")
        self.batch_relation_insert(relationship_rank_cross, "Rank_cross")
