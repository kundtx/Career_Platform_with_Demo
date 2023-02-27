#!/usr/bin/env python3
# coding=utf-8
import os, sys
import treelib
from ...common import Experience, Person
import pickle
import json
from treelib import Tree
from .utils import *
from .neo4j import Neo4jAdapter
from typing import List, Tuple, Dict, Callable
import datetime

__all__ = ["octree"]

data_path = os.path.dirname(__file__) + "/data"


def octree(exp_list:List[Experience], person_list:List[Person], export_json: bool = True) -> Dict or None:
    """
    Build octree from experiences and export json file if needed

    Params:
        exp_list: a list of all the experiences to be inserted
        person_list: a list of all the person related to experiences in exp_list
        export_json: export json tree if True

    Returns:
         Diction of octree or None
         
    ############################################################
    INFORMATION LOSS:
    1. skip none or wrong rank info experience
    2. filter for top 10% : get_main_children (removed)
    3. only one class is labeled , what about multi class?
    4. if no class is detected, and the node's depth > 0.7 ,
       then label it and its children
    ############################################################
    """
    uid2name = {p.uuid:p.name for p in person_list}
    oct = CTree()
    nodes_rel_dict = oct.build_tree(exp_list)
    adapter = Neo4jAdapter()
    adapter.treelib_to_neo4j(nodes_rel_dict, oct.interval_dict, init=True)
    adapter.compute_csn(oct, exp_list, uid2name, start=1960, end=float(datetime.date.today().strftime("%Y.%m")))
    if export_json:
        return oct.export_json_tree(uid2name)


class CNode(dict):
    def __init__(self, id, name=None, count=None):
        self.id = id  # Represents a different ID, each node has a different ID eg:0,1,2,3
        self.name = name  # eg: ”深圳市”“南山区“ ”南山街道”
        self.count = count
        self.score = 0  # a score to indicate the importance of the node (the current
        # implementation is the sum of all node counts in its subtree)
        super().__init__(self, name=name)  # attribute in json export
        super().__init__(self, count=count)
        super().__init__(self, score=self.score)
        super().__init__(self, id=self.id)

    def setname(self, name):
        self.name = name
        self['name'] = self.name

    def count_plus(self):
        self.count = self.count + 1
        self['count'] = self.count

    def score_plus(self):
        self.score = self.score + 1
        self['score'] = self.score


class CTree(Tree):
    def __init__(self, tree=None, deep=False):
        Tree.__init__(self, tree=tree, deep=deep)
        self.uid_userName_map = None
        self.id_num = 0  # unique id for node
        self.user_id = 1  # unique id for user
        self.interval_dict = {}
        self.resume_record = {}
        self.leaf_tag = {}
        self.rank_record = {}
        self.shenzhen_nid = None
        self.class_map = {'市政协直属': 1, '市人大直属': 2, '市委直属': 3, '市政府直属': 4, '国企事业单位': 5, '军检法机构': 6,
                          '龙华': 7, '罗湖': 8, '福田': 9, '南山': 10, '宝安': 11, '龙岗': 12, '盐田': 13, '坪山': 14,
                          '光明': 15, '深汕特别合作区': 16, '大鹏新区': 17}
        # with open(os.path.join(data_path, 'abbr_pairs.json'), 'r', encoding='utf-8') as fp:
        #     self.abbr = json.load(fp)
        # self.abbr = {**self.abbr, **dict(zip(self.abbr.values(), self.abbr.keys()))}  # Abbreviation mapping

    # =============================================================================
    # Main APIs for CTree
    # =============================================================================
    def save_tree(self, tree_path):
        with open(tree_path, "wb") as f:
            pickle.dump(self, f)

    def build_tree(self, exp_list: List[Experience], init=True) -> Dict[List, List]:
        """
        main function of OCTree. 
        1. build octree by treelib
        2. record resume information and existing interval of each node
        3. return a dict consisting of all nodes and edges
        """
        print("******** Building OCTree ****************************")
        if init:
            self.create_node(tag="root", identifier=0, data=CNode(self.id_num, "root", 0))  # root
        else:
            self.load_tree("./octree")  # TODO : LOAD OCTREE
        '''record nodes and edges for neo4j'''
        nodes_rel = {
            "nodes": self.nodes,
            "rel": []
        }
        # insert a list of parsed institution names to the tree
        for exp in iter(exp_list):
            '''get segmented/raw experience'''
            # TODO: text_token is asserted str
            if exp.text_token:
                parsed = exp.text_token.strip()
            else:
                continue
            if None in [exp.uuid,exp.person_uuid,exp.time_start,exp.time_end]:
                continue
            # get rank info ( should be a str(dict) )
            if not exp.adminrank:
                __rank = 'null'
            else:
                # TODO: rank should be like "{null:40, ‘正处级’：30}”
                __rank = exp.adminrank
            exp_id = exp.uuid + '+' + str(exp.splitnum)
            rinfo = (exp_id,
                     exp.person_uuid,
                     exp.time_start.strftime("%Y.%m"),
                     exp.time_end.strftime("%Y.%m")
                     )
            self.rank_record[exp_id] = {__rank: exp.duration()}
            '''build octree by treelib'''
            # insertion
            self.id_num += 1
            self._add_sequence_treelib(resume_info=rinfo,
                                       tokens=parsed,
                                       nodes_rel=nodes_rel)
        print("******** Updating node interval *********************")
        self.interval_dict = self.record_node_interval()
        # save resume dict
        print("******** Dumping nid2resumes dict *******************")
        with open(data_path + '/temp/nid2resumes.json', 'w', encoding='utf-8') as fp:
            json.dump(self.resume_record, fp, ensure_ascii=False, indent=2)
        return nodes_rel

    def export_json_tree(self, uid2name) -> Dict:
        # initialize json tree
        self.uid_userName_map = uid2name
        root = self.get_node(self.shenzhen_nid)
        class_map_main = {}
        class_map_all = {}
        self.get_classmap(root, class_map_main, class_map_all)
        nodes, users, path, _7class = self.tree_to_json(root,
                                                        nodes={}, users={}, path={},
                                                        _7class=[], class_map_all=class_map_all)
        json_tree = {"nodes": nodes, "users": users, "path": path, '_7class': _7class}
        return json_tree

    def tree_to_json(self, root, nodes, users, path, _7class, class_map_all):
        # init
        if nodes == {}:
            nodes = self._creat_ori_viznode('深圳市', 'None', 0, 0, 0, 0, 9999)
            nodes["children"] = [None for _ in range(len(self.class_map.keys()) + 1)]
            for _class_name, _class_index in self.class_map.items():
                nodes["children"][_class_index - 1] = \
                    self._creat_ori_viznode(_class_name, 0, 0, -1, _class_index, 0, 9999)
            nodes["children"][len(self.class_map.keys())] = \
                self._creat_ori_viznode("其他", 0, 0, -1, 18, 0, 9999)
        # insert
        for child in self.get_children(root):
            '''information of this child'''
            node_id = child.data.id
            class_id = class_map_all[node_id]
            # if class_id not in label_list:
            #     continue
            # # filter for top 10%
            # if root.data.id == self.shenzhen_nid and node_id not in self.main_children_list:
            #     continue

            name = child.data.name
            count = child.data.count
            parent = self.get_parent(child).identifier
            start, end = self.interval_dict[node_id]
            '''record the path to this node'''
            path[node_id] = {}
            path[node_id]['fullname'] = self.get_prefix_name(child)
            path[node_id]['node_path'] = self.get_prefix_id(node_id)
            # record this node in json
            ''' insert children of shenzhen into class nodes'''
            if root.data.id == self.shenzhen_nid:
                nodes["children"][class_id - 1]["children"].append(
                    self._creat_ori_viznode(name, parent, count, node_id, class_id, start, end))
                self.tree_to_json(child,
                                  nodes["children"][class_id - 1]["children"][-1],
                                  users, path, _7class, class_map_all)
            else:
                '''if not leaf, record this node in "children" list of parent(dict), then traverse its children'''
                if count == 0:
                    nodes['children'].append(
                        self._creat_ori_viznode(name, parent, count, node_id, class_id, start, end))
                    self.tree_to_json(child,
                                      nodes['children'][-1],
                                      users, path, _7class, class_map_all)
                else:  # leaf node need to record users as well
                    resume_ids = self.resume_record[node_id]
                    leaf_node = self._creat_ori_viznode(name, parent, count, node_id, class_id, start, end)
                    for exp_id, uid, startTime, endTime in resume_ids:
                        user_id = str(uid)
                        if user_id not in users:
                            users[user_id] = {}
                            users[user_id]['name'] = self.uid_userName_map.get(user_id, 'null')
                            users[user_id]['relationship'] = {}
                            users[user_id]['rank'] = {}
                            for i in range(1985, 2020):
                                users[user_id]['relationship'][i] = []
                                users[user_id]['rank'][i] = "null"

                        startTime = int(startTime[:4])
                        endTime = int(endTime[:4])
                        rank_period = self.rank_record[exp_id]
                        rank_year = {}

                        month_stack = 0
                        for k, m in rank_period.items():
                            month_stack += m
                            rank_year[k] = month_stack
                        rank_year.update((n, rank_year[n] // 12) for n in rank_year.keys())

                        start_year = 0
                        for k, y in rank_year.items():
                            for year in range(start_year + startTime, start_year + y + 1 + startTime):
                                users[user_id]['rank'][year] = k
                            start_year += y + 1

                        for i in range(max(1985, startTime), min(2019, endTime) + 1):
                            users[user_id]['relationship'][i].append(node_id)

                        leaf_node['children'].append(
                            self._creat_user_viznode(uid=uid, parent=node_id, start=startTime, end=endTime,
                                                     rank=rank_period))
                        path[self.id_num + self.user_id] = {}
                        path[self.id_num + self.user_id]['fullname'] = self.get_prefix_name(child)
                        path[self.id_num + self.user_id]['node_path'] = self.get_prefix_id(node_id)
                    nodes['children'].append(leaf_node)

        return nodes, users, path, _7class

    def record_node_interval(self) -> Dict:
        """
        This function will get the overall existing time of all the leaves
        predecessors' interval is the UNION of all its children's
        """
        restore_node_interval = {}
        leaves = self.leaves(0)
        for leaf in leaves:
            for _, _, startTime, endTime in self.resume_record.get(leaf.identifier, []):
                # only consider year
                startTime = int(startTime[:4])
                endTime = int(endTime[:4])
                # record the leaf's interval as (startTime, endTime)
                set_node_time(leaf.identifier, startTime, endTime, restore_node_interval)

            # update the time of the predecessors
            # set predecessors interval of this node as the UNION of its children's
            self._update_node_interval(leaf, restore_node_interval)

        return restore_node_interval

    '''
    APIs of octree
    '''

    def get_parent(self, node):  # faster
        return self.parent(node.identifier)

    def get_children(self, node):
        return self.children(node.identifier)
        # return [i for i in node.children]

    def get_prefix_name(self, n, remove_tag=False):
        if n.is_root():
            return ""
        parent_id = n.predecessor(self.identifier)
        if remove_tag:
            result = self.get_prefix_name(self.get_node(parent_id), remove_tag=remove_tag) + n.data.name[:-1]
        else:
            result = self.get_prefix_name(self.get_node(parent_id)) + n.data.name
        return result

    def get_prefix_id(self, n):
        if str(n) == '0':
            return []
        node = self.get_node(n)
        parent_id = node.predecessor(self.identifier)
        result = self.get_prefix_id(parent_id)
        result.append(n)
        return result

    def get_depth_position(self, node):
        depth_now = self.depth(node)
        depth_leaf = depth_now
        n = node
        while not n.is_leaf():
            n = self.get_children(n)[0]
            depth_leaf += 1

        return depth_now / depth_leaf

    '''
    Intrinsic functions
    '''

    def _add_sequence_treelib(self, resume_info: Tuple[str, int, str, str], tokens: str, nodes_rel: Dict) -> None:
        """
        main insertion loop of tree, based on treelib.
        insert each word of an experience into the prefix tree.
        :resume_info : (uuid, splitnum, time start, time end)
        :tokens : exp.text_token
        :nodes_rel: {nodes:[],rel:[]}
        """
        experience = tokens.split(' ')
        pointer = self.get_node(0)
        # 建树：以root为根, root的每一个直接后继（children字典里的key） 都是.txt中的一个开头字符串
        for i in range(len(experience)):
            word = experience[i]
            # find children of root
            children = {node.tag: node for node in self.children(pointer.identifier)}
            # search word or its abbr in children
            # TODO: abbreviation match
            """ INSERTION """
            if word in children:
                pointer = children[word]
                if i == len(experience) - 1:  # repeat leaf node
                    if pointer.data.count == 0:
                        self.leaf_tag[pointer.data.id] = ''.join(experience)
                    pointer.data.count_plus()
                    self.resume_record[pointer.data.id].append(resume_info)
            else:  # Not find in children list
                if word == "深圳市L" and self.shenzhen_nid is None:
                    # record nid of 深圳 for export json tree
                    self.shenzhen_nid = int(self.id_num)
                if i == len(experience) - 1:  # last entity is the leaf node
                    n1 = self.create_node(tag=word, identifier=self.id_num, parent=pointer.identifier,
                                          data=CNode(id=self.id_num, name=word, count=1))
                    self.resume_record[self.id_num] = [resume_info]
                    self.leaf_tag[self.id_num] = ''.join(experience)
                else:
                    n1 = self.create_node(tag=word, identifier=self.id_num, parent=pointer.identifier,
                                          data=CNode(id=self.id_num, name=word, count=0))
                    self.resume_record[self.id_num] = []
                nodes_rel['rel'].append(((pointer.identifier, pointer.tag), {}, (self.id_num, word)))
                self.id_num = self.id_num + 1
                pointer = n1
                # 新插入的子结点作为下一个根节点
            pointer.data.score_plus()

    def _update_node_interval(self, n: treelib.Node, restore_node_interval: Dict) -> None:
        if n.is_root():
            return
        if n.identifier not in restore_node_interval:
            restore_node_interval[n.identifier] = (0, 9999)
        start, end = restore_node_interval[n.identifier]
        parent = self.get_node(n.predecessor(self.identifier))
        set_node_time(parent.identifier, start, end, restore_node_interval)
        self._update_node_interval(parent, restore_node_interval)

    def _label_all_subnodes(self, root, class_map_all, class_id):
        class_map_all[root.identifier] = class_id
        if root.is_leaf():
            return
        else:
            for child in self.get_children(root):
                self._label_all_subnodes(child, class_map_all, class_id)

    def _creat_ori_viznode(self, name, parent, count, node_id, class_id, start, end):
        temp = {}
        temp['work'] = name
        temp['parent'] = parent
        temp['class_id'] = class_id
        temp['count'] = count
        temp['interval'] = (start, end)
        temp['name'] = node_id
        temp['children'] = []
        return temp

    def _creat_user_viznode(self, uid, parent, start, end, rank):
        temp = {}
        temp['user'] = self.uid_userName_map.get(uid, 'null')
        temp['class_id'] = -1
        temp['parent'] = parent
        temp['user_id'] = uid
        temp['name'] = self.id_num + self.user_id
        temp['interval'] = (start, end)
        temp['rank'] = rank
        self.user_id += 1
        return temp
