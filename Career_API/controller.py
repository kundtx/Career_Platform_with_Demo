# -*- coding: utf-8 -*-
"""
@Time ： 2022/9/14 23:38
@Auth ： luchengyue@sz.tsinghua.edu.cn
@File ：controller.py
@IDE ：PyCharm
@Motto：ABC(Always Be Coding)
"""

import json
import os, sys
import aiofiles
from quart import Blueprint, jsonify, request, redirect, render_template, make_response, url_for
from quart_cors import route_cors
import uuid
from datetime import datetime
import Career_Platform.career_platform as CP
from Career_API import utils
from Career_API.utils import *
from Career_API.database import *

backend = Blueprint('backend', __name__)

# 开发环境样例数据路径
SAMPLE_DATA_FOLDER = os.path.join(os.path.dirname(__file__), "../Career_Platform/demo/sample_data/")

''' ----------API Demo Web Page---------- '''


@backend.route('/', methods=['GET'])
async def index():
    return redirect(url_for("backend.apiDemo"))


@backend.route('/apiDemo', methods=['GET', 'POST'])
async def apiDemo():
    """
    apiDemo网页
    """
    return await render_template("apiDemo.html")


@backend.route('/getApiData', methods=['GET'])
async def getApiData():
    """
    返回demo/apiData.json中的api数据, 用于给前端渲染API文档网页
    """
    async with aiofiles.open(os.path.abspath(os.path.dirname(__file__)) + '/demo/apiData.json', 'r', encoding='utf-8') as f:
        apiData = await f.read()
    return apiData, 200, {"Content-Type": "application/json"}


''' ----------APP Demo Web Page---------- '''


@backend.route('/appDemo', methods=['GET'])
async def appDemo():
    """
    appDemo网页
    """
    return await render_template("appDemo.html")


''' ----------Demo APIs---------- '''


@backend.route('/analysis', methods=['GET', 'POST'])
@route_cors(allow_origin='*')
async def resume_analysis():
    if request.method == 'GET':
        j = request.args
    elif request.method == 'POST':
        j = await request.get_json()
    else:
        return {'error_code': 0, 'message': '无此方法'}, 200
    if not isinstance(j, Dict):
        return {'error_code': 0, 'message': '无法获取请求数据'}, 200
    if isinstance(txt := j.get('txt'), str):
        list_of_experience = []
        list_of_person = []
        for line in txt.split("\n"):
            line = line.strip()
            if line.startswith("#"):
                current_person = line[1:-1]
                pid = uuid.uuid1().__str__()
                list_of_person.append(CP.common.Person(uuid=pid,name=current_person))
            else:
                try:
                    interval, t = line.split(" ")
                    start,end = interval.split("-")
                except:
                    continue
                list_of_experience.append(
                    CP.common.Experience(uuid=uuid.uuid1().__str__(),
                                         time_start=datetime.strptime(start,"%Y.%m"),
                                         time_end=datetime.strptime(end,"%Y.%m"),
                                         text_raw=t,
                                         person_uuid=pid)
                )
        list_of_experience = CP.algorithm.exp_parser.refine(list_of_experience)
        list_of_experience = CP.algorithm.exp_parser.segment(list_of_experience)
        list_of_experience = CP.algorithm.exp_parser.rebuild(list_of_experience)
        result = []
        for e in list_of_experience:
            result.append(e.text_token)
        
        # build octree
        if len(result)>1:
            CP.algorithm.network.octree(exp_list=list_of_experience, 
                                    person_list=list_of_person,
                                    export_json=False)

        return jsonify({'result': result})


@backend.route('/visual_octree', methods=['GET', 'POST'])
@route_cors(allow_origin='*')
async def visual_octree():
    echartsData, nodesRelatlon = await run_sync(get_visual_octree)()
    return jsonify({'echartsData': echartsData, 'nodesRelation': nodesRelatlon})


@backend.route('/visual_csn', methods=['GET', 'POST'])
@route_cors(allow_origin='*')
async def visual_csn():
    echartsData, nodesRelatlon = await run_sync(get_visual_csn)()
    return jsonify({'echartsData': echartsData, 'nodesRelation': nodesRelatlon})

''' ----------Export APIs---------- '''


@backend.route('/export_user_data', methods=['GET', 'POST'])
async def export_user_data():
    if request.method == 'GET':
        j = request.args
    elif request.method == 'POST':
        j = await request.get_json()
    else:
        return {'error_code': 0, 'message': '无此方法'}, 200
    if not isinstance(j, Dict):
        return {'error_code': 0, 'message': '无法获取请求数据'}, 200
    if list_of_uid := j.get('list_of_uid'):
        if isinstance(list_of_uid, int):
            list_of_uid = [str(list_of_uid)]
        elif isinstance(list_of_uid, str):
            list_of_uid = [list_of_uid]
        elif isinstance(list_of_uid, List):
            list_of_uid = list_of_uid
        else:
            return {'error_code': -1, 'message': 'list_of_uid字段错误'}, 200

        result = await search_info_with_uid(list_of_uid)

        if len(result) != len(list_of_uid):
            return {'error_code': -2, 'message': '无此用户'}, 200

        return jsonify({'result': result})
    else:
        return {'error_code': -1, 'message': 'list_of_name字段错误'}, 200


#@backend.route('/export_json_tree', methods=['GET'])
async def export_json_tree():
    if not os.path.isfile('Career_API/octree_temp.json'):
        return {'error_code': -1, 'message': '无此文件'}, 404
    async with utils.LOCK_OCTREE.reader_lock:
        async with aiofiles.open('Career_API/octree_temp.json', 'r', encoding='utf-8') as f:
            json_tree = await f.read()

    return json_tree, 200, {"Content-Type": "application/json"}


''' ----------Functional APIs---------- '''


@backend.route('/name_fuzzy_matching', methods=['GET', 'POST'])
async def name_fuzzy_matching():
    """ CareerSocialNetwork
        names fuzzy matching
    Input:
        condition: string
    Output:
        result:
    """
    if request.method == 'GET':
        j = request.args
    elif request.method == 'POST':
        j = await request.get_json()
    else:
        return {'error_code': 0, 'message': '无此方法'}, 200
    if not isinstance(j, Dict):
        return {'error_code': 0, 'message': '无法获取请求数据'}, 200
    if isinstance(condition := j.get('condition'), str):
        if check_contain_chinese(condition):
            result = await fuzzy_matching_names_with_hanzi(condition)
        else:
            result = await fuzzy_matching_names_with_pinyin(condition)
        if len(result) == 0:
            return {'error_code': -2, 'message': '无此用户'}, 200
        return jsonify({'result': result})
    else:
        return {'error_code': -1, 'message': 'condition字段错误'}, 200


@backend.route('/exp_fuzzy_matching', methods=['GET', 'POST'])
async def exp_fuzzy_matching():
    """ CareerSocialNetwork
        experiences fuzzy matching
    Input:
        condition: string
    Output:
        result:
    """
    if request.method == 'GET':
        j = request.args
    elif request.method == 'POST':
        j = await request.get_json()
    else:
        return {'error_code': 0, 'message': '无此方法'}, 200
    if not isinstance(j, Dict):
        return {'error_code': 0, 'message': '无法获取请求数据'}, 200
    if isinstance(condition := j.get('condition'), str):
        if check_contain_chinese(j['condition']):
            result = await fuzzy_matching_exps_with_hanzi(condition)
        else:
            result = await fuzzy_matching_exps_with_pinyin(condition)
        if len(result) == 0:
            return {'error_code': -2, 'message': '无此经历'}, 200
        else:
            for r in result:
                r['uname'] = await search_uname_with_uid(r['person_uuid'])
        return jsonify({'result': result})
    else:
        return {'error_code': -1, 'message': 'condition字段错误'}, 200


@backend.route('/query_individual_relationship', methods=['GET', 'POST'])
async def query_individual_relationship():
    """ CareerSocialRelationship
            query all trajectory
        Input:
            uid: int or str
            type: none, int, str or list
        Output:

    """
    if request.method == 'GET':
        j = request.args
    elif request.method == 'POST':
        j = await request.get_json()
    else:
        return {'error_code': 0, 'message': '无此方法'}, 200
    if not isinstance(j, Dict):
        return {'error_code': 0, 'message': '无法获取请求数据'}, 200
    if isinstance(uid := j.get('uid'), (int, str)):
        if (type := j.get('type')) is None:
            type = [0, 1, 2]
        elif isinstance(type, (int, str)):
            type = [int(type)]
        else:
            type = [int(t) for t in type]
        result = []
        if 0 in type:
            if (res := await search_countrymen_with_uid(uid)) is not None:
                for r in res:
                    r['type'] = '0'
                result.extend(res)
        if 1 in type:
            if (res := await search_schoolfellow_with_uid(uid)) is not None:
                for r in res:
                    r['type'] = '1'
                result.extend(res)
        if 2 in type:
            if (res := await search_family_member_with_uid(uid)) is not None:
                for r in res:
                    r['type'] = '2'
                result.extend(res)
        if len(result) > 0:
            return jsonify({'result': result})
        else:
            return {'error_code': -2, 'message': '无结果'}, 200
    else:
        return {'error_code': -1, 'message': 'uid字段错误'}, 200


@backend.route('/query_social_relationship', methods=['GET', 'POST'])
async def query_social_relationship():
    """ CareerSocialRelationship
        query all trajectory
    Input:
        uid: int or str
        rid: none, int, str or list
    Output:

    """
    if request.method == 'GET':
        j = request.args
    elif request.method == 'POST':
        j = await request.get_json()
    else:
        return {'error_code': 0, 'message': '无此方法'}, 200
    if not isinstance(j, Dict):
        return {'error_code': 0, 'message': '无法获取请求数据'}, 200
    if isinstance(uid := j.get('uid'), (int, str)):
        if (rid := j.get('rid')) is None:
            rid = await search_rid_with_uid(j['uid'])
        elif isinstance(rid, (int, str)):
            rid = [int(rid)]
        else:
            rid = [int(r) for r in rid]
        if len(rid) == 0:
            return {'error_code': -3, 'message': '无此经历'}, 200
        try:
            result = []
            for r in rid:
                output = await search_relationship_with_uid_and_rid(uid, rid)
                if output:
                    result.append({'rid': r, 'data': output})
        except KeyError:
            return {'error_code': -3, 'message': '无此经历'}, 200
        if len(result) == 0:
            return {'error_code': -2, 'message': '无结果'}, 200
        for _result in result:
            for data in _result['data']:
                res = await search_exp_with_uid_and_rid(data['uid'], data['rid'])
                if len(res) > 0:
                    data['raw'] = replace_seg(res[-1]['seg'])
        return jsonify({'result': result})
    else:
        return {'error_code': -1, 'message': 'uid字段或rid字段错误'}, 200


@backend.route('/generate_label_map', methods=['GET', 'POST'])
async def generate_label_map():
    if request.method == 'GET':
        j = request.args
    elif request.method == 'POST':
        j = await request.get_json()
    else:
        return {'error_code': 0, 'message': '无此方法'}, 200
    if not isinstance(j, Dict):
        return {'error_code': 0, 'message': '无法获取请求数据'}, 200
    if isinstance(uid := j.get('uid'), (int, str)):
        result = await find_resume(uid)
        if result:
            return jsonify({'result': result})
        else:
            return {'error_code': -2, 'message': '无此用户'}, 200
    else:
        return {'error_code': -1, 'message': 'uid字段错误'}, 200


''' ---------- System Info APIs ---------- '''

@backend.route('/get_database_stats', methods=['GET'])
async def get_database_stats():
    "获取数据库统计信息"
    res_dict = {}
    neo4j_stats = await get_neo4j_stats()
    mysql_stats = await get_mysql_stats()

    res_dict.update(neo4j_stats)
    res_dict.update(mysql_stats)

    res_dict.update({"num_knowledgeGraph": 2, "nodeAttNum_OCtree": 4, "nodeAttNum_SocialNet": 5})

    return res_dict