import os, sys
import re
import json
import datetime
import copy
import logging
from typing import List, Tuple, Dict, Callable
import jieba
from jieba import posseg
from pyhanlp import *

from ....common import Experience


jieba.setLogLevel(logging.INFO)

__all__ = ["refine"] # 只向外暴露refine函数


def refine(exp_list:List[Experience], in_position:bool=False, callback:Callable=None) -> List[Experience]:
    """
    对列表中每一个Experience进行: 清洗去噪->缩略词还原->兼职拆分标记，返回新列表

    兼职拆分标记前的结果存放在text_rawrefine,
    兼职拆分标记后的结果存放在text_rawsplit.

    Params:
        exp_list: 传入的经历列表
        in_position: True则在传入exp_list上原地修改并返回原exp_list. False则深拷贝后修改并返回新的
        callback: 回调函数，需要能够接收一个包含函数执行状态信息的dict，可以用来查看执行进度
    """
    if not in_position:
        exp_list = copy.deepcopy(exp_list)

    # 用于传入callback的状态字典
    __status_dict = {
        "description": "[exp_parser]-refine",
        "total": len(exp_list),
        "iternum": 0
    }

    for iternum, exp in enumerate(exp_list):
        if exp.text_raw is None:
            continue
        text_NR = noise_remove(exp.text_raw)          # 1. 清洗去噪
        text_AR = abbreviation_recover(text_NR)     # 2. 缩略词还原
        exp.text_rawrefine = text_AR

        text_AS = adjunct_mark(text_AR)            # 3. 兼职拆分标记
        exp.text_rawsplit =  text_AS

        # 调用callback函数
        __status_dict["iternum"] = iternum
        if callback is not None:
            callback(__status_dict)

    return exp_list


def noise_remove(input_str:str) -> str or None:
    """
    清洗去噪.
    去除经历语句中的无意义字符、干扰词等，input_str需为单条完整的经历语句
    """
    result = input_str

    # 去除空格等字符
    result = re.sub("[\n\t \u00A0\u0020\u3000]", "", result)
    result = re.sub(r"\n", "", result)

    # 去除连词、副词 
    ## TODO 这完全没用阿，全都去除错了
    # _token = posseg.cut(result)
    # result = ""
    # for i in _token:
    #     if str(i.flag) != 'c' and str(i.flag) != 'd':
    #         result = result + i.word
    #     else:
    #         print(list(posseg.cut(input_str)))

    # 替换一些词
    result = re.sub("学习[,，、]+|学习$", lambda m:m.group().replace("学习","学生"), result)
    result = re.sub("任教[,，、]+|任教$", lambda m:m.group().replace("任教","教师"), result)
    result = re.sub("职务[,，、]+|职务$", "", result)

    # 去除一些无关句子
    result = re.sub("获.*?学位", "", result)
    result = re.sub("[,，/.。、]?主持.*?工作[的]?", "", result)
    result = re.sub("[,，/.。、]?从事.*?工作", "", result)
    result = re.sub("(工作)?[，,][历]?任", "", result)
    result = re.sub("[\(（\[【][^\(（\[【]*?[\)）\]】]", "", result)
    result = re.sub("[\(（\[【].*[\)）\]】]", "", result)
    result = re.sub("[0-9]{4}.?[0-9]{0,2}[—-]?", "", result)
    
    if result == "":
        return None
    return result


def abbreviation_recover(input_str:str) -> str or None:
    """
    缩略词还原.
    将经历语句中的缩略词恢复为完整词, input_str需为单条完整的经历语句
    """
    if input_str is None:
        return None
    result = input_str

    # 部分“x委”恢复成“xx委员会”
    result = result\
        .replace("委会", "委员会") \
        .replace("市委", "市委员会") \
        .replace("区委", "区委员会") \
        .replace("省委", "省委员会") \
        .replace("县委", "县委员会") \
        .replace("镇委", "镇委员会") \
        .replace("村委", "村委员会") \
        .replace("委员会员会", "委员会") # 如果要添加新的“x委”，这句replace需要放在最后

    #  开头为“市”、“省”默认恢复成“深圳市”、“广东省”
    if result.startswith('市'):
        result = '深圳' + result
    if result.startswith('省'):
        result = '广东' + result

    # 替换一些英文缩写
    result = re.sub("E?MBA", "管理学硕士", result)

    if result == "":
        return None
    return result


def adjunct_mark(input_str:str) -> str:
    """
    兼职拆分标记.
    在经历语句中添加兼职拆分标记"|"，用于之后的重建. input_str需为单条完整的经历语句
    """
    if input_str is None:
        return None
    result = input_str
    
    # 如"xxx兼职副主席"替换为"xxx副主席"
    result = result.replace("兼职", "")

    # 识别"兼任","兼",",兼",逗号,顿号之类的模式替换为拆分标记|
    # 注意先替换长串再替换短串以保证正确性
    result = re.sub("[\.,，。、；;兼]+任?", "|", result)

    # 将多个连在一起的|合并、首尾的|去掉
    result = re.sub("(\|)+", "|", result)
    result = result.strip("|")
    if result == "":
        return None

    # 如果有多个兼职
    if "|" in result:
        adj_list = result.split("|")
        # 从后向前, 判断每个拆分子串的最后一个词是否为职位词,若不是则使用最近后继子串的职位词补全
        # 例如：将"X机构、Y机构ZZ职位，A机构、B机构、C机构DD职位"补全为"X机构ZZ职位、Y机构ZZ职位，A机构DD职位、B机构DD职位、C机构DD职位"
        cur_position_suffix = ""    # 当前（即最近后继子串的）职位词后缀
        for i in range(len(adj_list)-1, -1, -1):
            hanlp_seg = HanLP.segment(adj_list[i])
            # 若最后一个词为职位词(nature是nn/nnd/nnt),则作为当前用于补全的cur_position_suffix
            if str(hanlp_seg[-1].nature).startswith('nn'):
                cur_position_suffix = hanlp_seg[-1].word
            # 若最后一个词不是职位词,则用cur_position_suffix补全
            else:
                # 跳过一些例外情况
                if len(adj_list[i])<3:                           # 太短的
                    break
                if adj_list[i][-3] == adj_list[i][-2]:           # 有时候hanlp会把"XXXXX局局长"之类的句子最后一个词分成"局局长"且词性错分为n
                    break
                
                hanlp_mistake_list = [                           # hanlp会分错词性但实际上是职位词的词
                    "书记","科员","指导员","治安员",
                    "员工","成员","人选","主管","主办","主任","组长","单元长",
                    "主操","副操","助工",
                    "排长","营长","连长","旅长","师长","军长"
                ]
                ignore_is_ok_list = [                            # 我们选择无视的情况
                    "工作", 
                ]
                if adj_list[i].endswith(tuple(hanlp_mistake_list+ignore_is_ok_list)):
                    break

                # 如果上面的例外情况都不属于，则终于可以用cur_position_suffix补全了
                adj_list[i] = adj_list[i] + cur_position_suffix
        
        result = "|".join(adj_list)

    return result