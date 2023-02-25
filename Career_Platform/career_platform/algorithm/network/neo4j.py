from py2neo import Graph, Node
from py2neo.bulk import create_nodes, create_relationships
from py2neo.ogm import GraphObject, RelatedObjects, Property, RelatedTo, RelatedFrom, Label
from py2neo.database import Schema
from py2neo.data import walk
import os, sys
from .utils import *
from .csn import CareerSocialNetwork, get_rank, school_mate
from typing import List, Tuple, Dict, Callable
from ...config import neo4j_config


# =========================================
class CNodeNEO(GraphObject):
    __primarylabel__ = 'Node'
    # 定义主键
    __primarykey__ = 'id'
    # 定义类的属性
    name = Property()
    id = Property()
    identifier = Property()
    count = Property()
    # score = Property(default=0)
    interval = Property(default=(1970, 9999))
    # 定义类的标签
    leaf = Label()
    root = Label()
    Org = Label()
    Loc = Label()
    # 定义CNodeNEO指向的关系
    children = RelatedTo('CNodeNEO', 'R')
    parent = RelatedFrom('CNodeNEO', 'R')

    def count_plus(self):
        self.count = self.count + 1


class Neo4jAdapter(object):
    def __init__(self):
        self.GraphDatabase = Graph(neo4j_config)
        self.schema = Schema(self.GraphDatabase)
        self.schema.create_index("Node", "id")
        # much faster to build tree, very important index

    def treelib_to_neo4j(self, nodes_rel_dict: Dict[List, List], interval_dict: Dict, init: bool) -> None:
        if init:
            # self._init_tree()
            self.GraphDatabase.delete_all()

        '''batch nodes addition'''
        keys = ["id", "name", "identifier", "count", "interval"]
        data_nodes_org = []
        data_nodes_loc = []
        data_nodes = []
        data_leaves = []
        relationship_data = nodes_rel_dict['rel']

        '''nodes data with count info'''
        all_nodes = nodes_rel_dict['nodes']
        for nid, node in all_nodes.items():
            data = node.data
            interval = interval_dict[data['id']]

            if data['count'] > 0 and data['name'][-1] == "P":  # leaf
                data_leaves.append([data['id'], data['name'], nid, data['count'], interval])
            else:
                if data['name'][-1] == "O":
                    data_nodes_org.append([data['id'], data['name'], nid, data['count'], interval])
                elif data['name'][-1] == "L":
                    data_nodes_loc.append([data['id'], data['name'], nid, data['count'], interval])
                else:
                    data_nodes.append([data['id'], data['name'], nid, data['count'], interval])

        create_nodes(self.GraphDatabase.auto(), data_nodes, labels={"Node"}, keys=keys)
        create_nodes(self.GraphDatabase.auto(), data_nodes_loc, labels={"Node", "Loc"}, keys=keys)
        create_nodes(self.GraphDatabase.auto(), data_nodes_org, labels={"Node", "Org"}, keys=keys)
        create_nodes(self.GraphDatabase.auto(), data_leaves, labels={"Node", "Leaf"}, keys=keys)

        root = self.get_node(0)
        root.root = True
        self.GraphDatabase.push(root)
        # links bulk insertion
        create_relationships(self.GraphDatabase.auto(), relationship_data, "R",
                             start_node_key=("Node", "id", "name"), end_node_key=("Node", "id", "name"))

    def compute_csn(self, lib_tree, exp_list, uid2name, start, end) -> CareerSocialNetwork:
        """
        Use CQL to search career relationships in octree.
        Then save them into neo4j
        """
        csn = CareerSocialNetwork(start, end)
        csn.store_user_resume_nodes(exp_list, uid2name)
        colleague_list = []
        superior_list_same = []
        superior_list_cross = []
        col_set = set()  # 同事记录
        sup_set = set()  # 上下级记录
        '''同一叶节点（同一职位）为同事关系'''
        leafs_y = self.match_nodes_by_tag("Leaf")
        for l in leafs_y:
            # l_tag = self.leaf_tag[l['id']]
            l_resumes = lib_tree.resume_record[l['id']]
            pairs = user_pair(l_resumes, l_resumes, start, end)
            for mid, nid, period in pairs:
                if (mid, nid) in col_set or (nid, mid) in col_set:  # 由于对称性，需要去重
                    continue
                colleague_list.append([mid, nid, period])
                col_set.add((mid, nid))
        '''两跳：同级同僚'''
        rank_dict = get_rank_dict()
        cql_col = "match (m:Leaf)<-[:R]-(o:Node)-[:R]->(n:Leaf) " \
                  "where m.interval[0]<=n.interval[0]<=m.interval[1] and " \
                  "not o:Loc and not o:Root and not o:Leaf " \
                  "return m,n"
        col_y = self.GraphDatabase.run(cql_col).to_ndarray()
        for m, n in col_y:
            if (m, n) in sup_set or (n, m) in sup_set:
                continue
            sup_set.add((m, n))  # 对称性去重
            m_resumes = lib_tree.resume_record[m['id']]
            n_resumes = lib_tree.resume_record[n['id']]
            pairs_rank = user_pair_with_rank(m_resumes, n_resumes, lib_tree.rank_record, start, end)

            '''根据职级信息判断是否有两跳的上下级关系'''
            is_rank = False
            for mid, nid, m_key, n_key, period in pairs_rank:
                m_level = rank_dict.get(m_key, -1)
                n_level = rank_dict.get(n_key, -1)
                # TODO: ADD LOG ON ERROR RANK
                # if m_key not in rank_dict.keys() or n_key not in rank_dict.keys():
                #     lib_tree.logger.error("Unknown job level:" + m_key + n_key)
                if m_level == -1 or n_level == -1:
                    # TODO: 没有职级信息时，使用职位名称进行判断
                    if get_rank(m["name"], n["name"]) == 1:
                        superior_list_same.append([mid, nid, m_key, n_key, period])
                        is_rank = True
                    elif get_rank(m["name"], n["name"]) == -1:
                        superior_list_same.append([nid, mid, n_key, m_key, period])
                        is_rank = True
                    else:
                        continue
                else:
                    is_rank = True
                    if m_level > n_level:  # level 越小， 职称越高
                        superior_list_same.append([nid, mid, n_key, m_key, period])
                    elif m_level < n_level:
                        superior_list_same.append([mid, nid, m_key, n_key, period])
                    else:
                        is_rank = False
            '''不是上下级的会属于同事'''
            if is_rank:
                continue
            pairs = user_pair(m_resumes, n_resumes, start, end)
            for mid, nid, period in pairs:
                if (mid, nid) in col_set or (nid, mid) in col_set:  # 由于对称性，需要去重
                    continue
                else:
                    colleague_list.append([mid, nid, period])
                    col_set.add((mid, nid))

        '''三跳：跨组织上下级'''
        cql_rank = "match (m:Leaf)<-[:R]-(o1:Node)-[:R]->(o2:Node)-[:R]->(n:Leaf) " \
                   "where m.interval[0]<=n.interval[0]<=m.interval[1] and " \
                   "not o2:Loc and not o2:Leaf and " \
                   "not o1:Root and not o1:Loc and not o1:Leaf " \
                   "return m,n"
        rank_y = self.GraphDatabase.run(cql_rank).to_ndarray()
        for m, n in rank_y:
            m_resumes = lib_tree.resume_record[m['id']]
            n_resumes = lib_tree.resume_record[n['id']]
            pairs_rank = user_pair_with_rank(m_resumes, n_resumes, lib_tree.rank_record, start, end)

            for mid, nid, m_key, n_key, period in pairs_rank:
                m_level = rank_dict.get(m_key, -1)
                n_level = rank_dict.get(n_key, -1)
                if m_key not in rank_dict.keys() or n_key not in rank_dict.keys():
                    lib_tree.logger.error("Unknown job level:" + m_key + n_key)
                if m_level == -1 or n_level == -1:
                    if (m["name"] in school_mate or n["name"] in school_mate) and \
                            (mid, nid) not in col_set and \
                            (nid, mid) not in col_set:  # 同学认为是同事
                        colleague_list.append([mid, nid, period])
                        col_set.add((mid, nid))
                    # TODO: 没有职级信息时，使用职位名称进行判断
                    elif get_rank(m["name"], n["name"]) == 1:  # 只考虑 A>B的情况
                        superior_list_cross.append([mid, nid, m_key, n_key, period])
                else:
                    if m_level > n_level:  # level 越小， 职称越高
                        superior_list_cross.append([nid, mid, n_key, m_key, period])
                    elif m_level < n_level:
                        superior_list_cross.append([mid, nid, m_key, n_key, period])
        print("******** Storing social net(col:{} sup_s:{} sup_c:{}) ".format(len(colleague_list), len(superior_list_same), len(superior_list_cross)))
        csn.store_social_network(colleague_list, superior_list_same, superior_list_cross)
        return csn

    # =============================================================================
    # Main APIs for CTree
    # =============================================================================

    def get_parent(self, node: CNodeNEO):  # faster
        result = self.GraphDatabase.run("match (p)-[r: R]->(q:Node{id:" + str(node.id) + "}) return p")
        record = result.evaluate()
        return CNodeNEO.wrap(record)

    # def get_parent(self, node: CNodeNEO):
    #     return [i for i in node.parent][0]

    def get_children(self, node: CNodeNEO):
        result = self.GraphDatabase.run("match (q:Node{id:" + str(node.id) + "})-[r: R]->(p) return p")
        record = [CNodeNEO.wrap(i['p']) for i in result]
        return record
        # return [i for i in node.children]

    def get_node(self, id):
        return CNodeNEO.match(self.GraphDatabase, id).first()

    def get_prefix_name(self, n: CNodeNEO):
        if n.root is True:
            return ""
        parent = self.get_parent(n)
        result = self.get_prefix_name(parent) + n.name
        return result

    def get_prefix_name_cql(self, n):  # CQL even slower
        result = []
        if isinstance(n, CNodeNEO):
            x = n.id
        else:
            x = n
        path = self.GraphDatabase.run("match p=((m:Node{id:{x}})<-[*]-(o:Root)) return p", x=x).evaluate()
        for i in walk(path):
            if isinstance(i, Node):
                result.append(i["name"])
        result.reverse()
        return ''.join(result)

    def get_prefix_id(self, n: CNodeNEO):
        if n.root is True:
            return ""
        parent = n.parent
        result = self.get_prefix_id(parent)
        result.append(n.id)
        return result

    def prefix_match(self, entry, n: CNodeNEO = None):

        # convert all nodes to its full name
        # find the longer common prefix
        # return the node (perfect match or not)
        if not n:
            n = self.get_node(0)

        children = [(len(i.name), i) for i in self.get_children(n)]

        children.sort(reverse=False, key=lambda x: x[0])

        node_prefix = self.get_prefix_name(n)
        # print(node_prefix)

        if entry == node_prefix:
            return (n, True)

        # print(children)

        for _, c in children:
            if entry.strip(node_prefix).startswith(c.name):
                (n, is_success) = self.prefix_match(entry, n=c)
                if is_success:
                    return (n, True)
        return (n, False)

    # =============================================================================
    # Internal functions
    # =============================================================================

    def match_nodes_by_tag(self, tag):
        results = []
        for l in self.GraphDatabase.nodes.match(tag):
            results.append(l)  # turn Node into CNodeNEO
            # results.append(CNodeNEO.wrap(l))  # turn Node into CNodeNEO
        return results

    def remove_node(self, node):
        self.GraphDatabase.delete(node)

    def create_node(self, tag, identifier, id, name, count):
        tx = self.GraphDatabase.begin()
        assert id == identifier  # 一样的，但是项目中有些地方用了id，有些用了identifier
        new_node = CNodeNEO()
        new_node.id = id
        new_node.identifier = identifier
        new_node.name = name
        new_node.count = count
        if tag == "root":
            new_node.root = True
        if tag == "leaf":
            new_node.leaf = True
        tx.create(new_node)  # 创建节点和关系
        tx.commit()  # 将以上更改一次提交
        return new_node

    def depth(self, node: CNodeNEO):
        depth_now = 0
        n = node
        while n.root is not True:
            n = self.get_parent(n)
            depth_now += 1
        return depth_now

    def get_depth_position(self, node: CNodeNEO):
        depth_now = self.depth(node)
        depth_leaf = depth_now
        n = node
        while n.leaf is not True:
            n = self.get_children(n)[0]
            depth_leaf += 1

        return depth_now / depth_leaf
