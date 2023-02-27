# -*- coding: utf-8 -*-
"""
@Time ： 2022/9/14 23:39
@Auth ： luchengyue@sz.tsinghua.edu.cn
@File ：database.py
@IDE ：PyCharm
@Motto：ABC(Always Be Coding)
"""
import asyncio
import logging
import aiomysql
import traceback
from py2neo import Graph
from aioneo4j import Neo4j
from typing import Any, List, Dict, Tuple, Union, Callable, Awaitable

from Career_API.utils import *
from Career_Platform.career_platform.config import careerDB_config, neo4j_config

logobj = logging.getLogger('mysql')

use_pool = False


class APmysql:
    async def __get_connection(self):
        while (True):
            try:
                logobj.debug('will init mysql pool~')
                loop = asyncio.get_event_loop()
                db_opt = careerDB_config.copy()
                db_opt['db'] = db_opt['database']
                db_opt.pop('database')
                conn = await aiomysql.connect(**db_opt, autocommit=False, loop=loop, cursorclass=aiomysql.DictCursor)
            except Exception as E:
                print('Error connecting to database:{0}'.format(E))
                print('Reconnect in 3 sec...')
                await asyncio.sleep(3)
            else:
                break
        return conn

    async def connect(self):
        return await self.__get_connection()

    async def query(self, query, param=None, commit=False):
        conn = await self.connect()
        cur = await conn.cursor()
        try:
            await cur.execute(query, param)
            return await cur.fetchall()
        except:
            logobj.error(traceback.format_exc())
        finally:
            if cur:
                await cur.close()
            if commit:
                await conn.commit()


class APmysqlPool:
    __pool = None

    def __init__(self):
        self.coon = None
        self.pool = None

    @staticmethod
    async def initpool():
        if APmysqlPool.__pool is None:
            try:
                logobj.debug('will init mysql pool~')
                db_opt = careerDB_config.copy()
                db_opt['db'] = db_opt['database']
                db_opt.pop('database')
                __pool = await aiomysql.create_pool(
                    **db_opt,
                    minsize=5,
                    maxsize=10,
                    autocommit=False
                )
                if __pool:
                    APmysqlPool.__pool = __pool
                    return __pool
                else:
                    raise 'init mysql pool error'
            except:
                logobj.error('init mysql pool error', exc_info=True)
                print(traceback.format_exc())
        else:
            return APmysqlPool.__pool

    async def getCurosr(self):
        conn = await self.pool.acquire()
        cur = await conn.cursor(aiomysql.DictCursor)
        return conn, cur

    async def query(self, query, param=None, commit=False):
        conn, cur = await self.getCurosr()
        try:
            await cur.execute(query, param)
            return await cur.fetchall()
        except:
            logobj.error(traceback.format_exc())
        finally:
            if cur:
                await cur.close()
            if commit:
                await conn.commit()
            await self.pool.release(conn)


async def getmysqlobj():
    if use_pool:
        mysqlobj = APmysqlPool()
        pool = await mysqlobj.initpool()
        mysqlobj.pool = pool
    else:
        mysqlobj = APmysql()
    return mysqlobj


async def search_exp_raw_with_uid_and_erid(uid: Union[int, str], erid: Union[int, str]):
    mysqlobj = await getmysqlobj()
    exp_info = (await mysqlobj.query(f'select text_raw, exp_ordernum from exp where person_uuid="{uid}" and exp_uuid="{erid}";'))[0]
    return exp_info['text_raw'], exp_info['exp_ordernum']


async def search_uname_with_uid(uid: Union[int, str]):
    mysqlobj = await getmysqlobj()
    res = await mysqlobj.query(f'select person_name from person where person_uuid="{uid}";')
    if len(res) == 1:
        uname = res[0]['person_name']
        return uname
    else:
        return None


async def search_info_with_uid(list_of_uid: List):
    mysqlobj = await getmysqlobj()
    result = []
    for uid in list_of_uid:
        res = await mysqlobj.query(f'select * from person where person_uuid="{uid}";')
        if len(res) == 1:
            user_info = res[0].copy()
            data = await mysqlobj.query(f'select * from exp where person_uuid="{uid}";')
            for d in data:
                d['time_start'] = str(d['time_start'])
                d['time_end'] = str(d['time_end'])
            #     raw_exp, rkey = await search_exp_raw_with_uid_and_erid(uid, d['exp_uuid'])
            #     d['raw_data'] = raw_exp
            #     d['raw_processed'] = d['text_raw']
            #     d['text_raw'] = replace_seg(d['text_rawsplit'])
            #     d['rkey'] = rkey
            user_info['data'] = data
            result.append(user_info)
    return result


async def search_rid_with_uid(uid: Union[int, str]):
    mysqlobj = await getmysqlobj()
    res = await mysqlobj.query(f'select exp_uuid from exp where person_uuid="{uid}";')
    return [r['exp_uuid'] for r in res]


async def search_exp_with_uid_and_rid(uid: Union[int, str], rid: Union[int, str]):
    mysqlobj = await getmysqlobj()
    result = await mysqlobj.query(f'select text_raw, text_rawsplit from exp where person_uuid="{uid}" and exp_ordernum="{rid}";')
    return result


async def fuzzy_matching_names_with_pinyin(condition: str):
    mysqlobj = await getmysqlobj()
    pairs = await mysqlobj.query(
        f'select person_uuid, person_name from person where person_namepinyin like "%{"%".join(condition.upper().split())}%";')
    return pairs


async def fuzzy_matching_exps_with_pinyin(condition: str):
    mysqlobj = await getmysqlobj()
    pairs = await mysqlobj.query(
        f'select person_uuid, exp_uuid, text_raw from exp where text_rawpinyin like "%{"%".join(condition.upper().split())}%";')
    return pairs


async def fuzzy_matching_names_with_hanzi(condition: str):
    mysqlobj = await getmysqlobj()
    pairs = await mysqlobj.query(
        f'select person_uuid, person_name from person where person_name like "%{"%".join(condition.upper().split())}%";')
    return pairs


async def fuzzy_matching_exps_with_hanzi(condition: str):
    mysqlobj = await getmysqlobj()
    pairs = await mysqlobj.query(
        f'select person_uuid, exp_uuid, text_raw from exp where text_raw like "%{"%".join(condition.upper().split())}%";')
    return pairs


async def search_relationship_with_uid_and_rid(uid: Union[int, str], rid: Union[int, str]):
    mysqlobj = await getmysqlobj()
    res = await mysqlobj.query(f'select * from relationship where person_uuid_from="{uid}" and exp_uuid_from="{rid}"')
    for r in res:
        r['time_start'] = str(r['time_start'])
        r['time_end'] = str(r['time_end'])
    return res


async def find_resume(uid: Union[int, str]):
    mysqlobj = await getmysqlobj()
    res = await mysqlobj.query(f'select * from label where person_uuid="{uid}";')
    if len(res) > 0:
        label_dicts = {}
        for r in res:
            if r['label_text'] not in label_dicts:
                label_dicts[r['label_text']] = [[str(r['time_start']), str(r['time_end'])]]
            else:
                label_dicts[r['label_text']].append([str(r['time_start']), str(r['time_end'])])
        return label_dicts
    else:
        return None


async def get_neo4j_stats():
    '''retrieve statistic info from neo4j
    Args: None
    Returns: Dict contains <statistics name: statistics value> pairs
    '''
    async with Neo4j(f'http://{neo4j_config["user"]}:{neo4j_config["password"]}@{neo4j_config["host"]}:7474/') as neo4j:
        nodeCount_Leaf = (await neo4j.cypher('''MATCH (n:Leaf) RETURN COUNT(n);'''))['data'][0][0]
        nodeCount_Node = (await neo4j.cypher('''MATCH (n:Node) RETURN COUNT(n);'''))['data'][0][0]

        nodeCount_YearUser = (await neo4j.cypher('''MATCH (n:YearUser) RETURN COUNT(n);'''))['data'][0][0]
        relCount_Col = (await neo4j.cypher('''MATCH ()-[R:Col]-() RETURN COUNT(R)'''))['data'][0][0]
        relCount_Rank = (await neo4j.cypher('''MATCH ()-[R:Rank]-() RETURN COUNT(R)'''))['data'][0][0]

        statistics = {"nodeCount_Leaf":nodeCount_Leaf,
                    "nodeCount_Node":nodeCount_Node,
                    "nodeCount_YearUser":nodeCount_YearUser,
                    "relCount_Col":relCount_Col,
                    "relCount_Rank":relCount_Rank}

        return statistics


async def get_mysql_stats():
    '''retrieve statistic info from mysql
    Args: None
    Returns: Dict contains <statistics name: statistics value> pairs
    '''
    mysqlobj = await getmysqlobj()
    rowCount_user_data = (await mysqlobj.query('SELECT COUNT(*) AS count FROM exp;'))[0]['count']
    rowCount_user_info = (await mysqlobj.query('SELECT COUNT(*) AS count FROM person;'))[0]['count']

    statistics = {"rowCount_expParsed": rowCount_user_data,
                  "rowCount_userNum": rowCount_user_info,
                  "rowCount_expRaw": rowCount_user_data / 2}

    return statistics


def get_visual_octree():
    GraphDatabase = Graph(neo4j_config)
    cql_col = "MATCH p=((m:Root)-[*]->(n:Leaf)) RETURN p Limit 10"
    col_y = GraphDatabase.run(cql_col).to_series()
    echartsData = []
    nodesRelatlon = []
    nodesID = set()
    edgesID = set()

    for p in col_y:
        for n in p.nodes:
            labels = list(n.labels)
            if len(labels) > 1:
                labels.remove("Node")
            if n['id'] not in nodesID:
                echartsData.append({'id':str(n['id']), 'name': n['name'], 'category': labels[0]})
                nodesID.add(n['id'])

        for r in p.relationships:
            if r.identity not in edgesID:
                nodesRelatlon.append({
                    'source': str(r.start_node['id']),
                    'target': str(r.end_node['id']),
                    'name': 'R'
                })
                edgesID.add(r.identity)
    return echartsData, nodesRelatlon


def get_visual_csn():
    GraphDatabase = Graph(neo4j_config)
    cql_col = "MATCH p=()-[r:Rank|Col|Rank_cross]->() RETURN p LIMIT 25"
    col_y = GraphDatabase.run(cql_col).to_ndarray()
    echartsData = []
    nodesRelatlon = []
    for p in col_y:
        for n in p[0][0].nodes:
            labels = list(n.labels)
            echartsData.append({'name': n['name'], 'category': labels[0]})
        for r in p[0][0].relationships:
            nodesRelatlon.append({
                'source': r.start_node['name'],
                'target': r.end_node['name'],
                'name': type(r).__name__
            })
    return echartsData, nodesRelatlon
