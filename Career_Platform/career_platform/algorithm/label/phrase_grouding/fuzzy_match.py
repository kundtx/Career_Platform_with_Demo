from fuzzywuzzy import fuzz
from typing import *
import re
import json
import os
import pandas as pd

__all__ = ["FuzzyMatch"]

DEFAULT_EVAL_LABEL_PATH = os.path.dirname(__file__) + "/eval_label.json"


class FuzzyMatch:

    # 默认用于模糊匹配的标签及短句集合
    __pattern_list:List[Dict] = None

    def __init__(self):
        # 仅在第一次实例化时载入类变量__pattern_list,所有实例共享
        if self.__pattern_list is None:
            self.__load_pattern_list()

    @classmethod
    def __load_pattern_list(cls, file_path:str=DEFAULT_EVAL_LABEL_PATH):
        """
        载入类变量__pattern_list
        """
        with open(file_path, "r", encoding="utf-8") as f:
            pattern_list = json.load(f)

        # 只选第二级
        cls.__pattern_list = list(filter(lambda x:x["label_level"]==2, pattern_list))

    def fuzzy_match(self, long_text:str, thresh:int=65, pattern_list=None) -> List[Dict]:
        """
        将long_text拆成短句后, 同pattern_list中各标签的phrase集进行模糊匹配, 按pattern_list中的标签分别统计成功匹配的短句数

        Params:
            long_text: 待匹配长文本
            thresh: 短句的模糊匹配成功阈值
            pattern_list: None时使用默认的标签集, 无特殊需要请保持默认

        Returns: 
            字典列表, 包含每个匹配成功的标签和其匹配成功次数, 示例: 
            [
                {
                    "label": "标签名",
                    "code": "标签代码",
                    "count": 成功匹配计数,
                    "match": [
                        (分数1,匹配短语1),
                        (分数2,匹配短语2),
                        ...
                    ]
                }
            ]
        """
        if long_text is None or long_text.strip() == "":
            return []

        # 默认使用类变量__pattern_list
        if pattern_list is None:
            pattern_list = self.__pattern_list

        # 将long_text拆成短句
        phrase_list = [ph for ph in re.split("[，,。.；;\n ]", long_text) if ph != ""]

        lb_res_dict = {}
        for pat in pattern_list:
            for ph in phrase_list:
                # 标签的所有phrase集合中模糊匹配分最高的作为该标签的得分
                score = fuzz.ratio(ph, pat["label_text"])
                # 分数没超过阈值则不匹配
                if score < thresh:
                    continue

                # 分数超过阈值则计数+1
                if lb_res_dict.get(pat['label_id'], False):
                    lb_res_dict[pat['label_id']]['count'] += 1
                    lb_res_dict[pat['label_id']]['match'].append((score, ph))
                else:
                    lb_res_dict[pat['label_id']] = {}
                    lb_res_dict[pat['label_id']]['label'] = pat['label_text']
                    lb_res_dict[pat['label_id']]['code'] = pat['label_id']
                    lb_res_dict[pat['label_id']]['count'] = 1
                    lb_res_dict[pat['label_id']]['match'] = [(score, ph), ]

        # 将匹配结果转换为返回格式
        lb_res_list = list(lb_res_dict.values())

        # 按匹配计数从大到小排序
        lb_res_list = sorted(lb_res_list, key=lambda x:x["count"], reverse=True)
        
        return lb_res_list


def generate_eval_label_json_from_xls(csv_path:str, json_save_path:str) -> None:
    """
    将xls文件中的标签,转为可以被FuzzyMatch使用的JSON格式
    """
    df = pd.read_csv(csv_path)

    # 处理缺失
    df = df.fillna("0")
    # 将ID转为字符串
    df[df.columns[1]] = df[df.columns[1]].astype('int').astype('str')
    df[df.columns[5]] = df[df.columns[5]].astype('int').astype('str')
    # 将处理好的excel表转为list
    data_list = df.to_numpy().tolist()

    data_list = sorted(data_list, key=lambda x:x[1])

    # 只要最后两级
    eval_label_list = []
    for row in data_list:
        level = None
        # 判断是第几级
        id_stripped = row[1].strip("0")  # 去掉末尾0
        if len(id_stripped) == 5 or len(id_stripped) == 6:
            level = 1
        elif len(id_stripped) == 7 or len(id_stripped) == 8:
            level = 2
        else:
            # 不属于这两级直接跳过
            continue

        eval_label_list.append({
                "label_id": row[1],
                "label_text": row[2],
                "label_level": level,
                "parent_id": row[5]
        })
    
    with open(json_save_path, "w", encoding="utf-8") as f:
        json.dump(eval_label_list, f, ensure_ascii=False, indent=4)

    """生成嵌套列表的代码, 目前已弃用"""
    # eval_label_dict = {}
    # # 将标签转换为嵌套列表，以表示标签层次关系，只存两级
    # for row in data_list:
    #     level = None
    #     # 判断是第几级
    #     id_stripped = row[1].strip("0")  # 去掉末尾0
    #     if len(id_stripped) == 5 or len(id_stripped) == 6:
    #         level = 1
    #     elif len(id_stripped) == 7 or len(id_stripped) == 8:
    #         level = 2
    #     else:
    #         # 不属于这两级直接跳过
    #         continue

    #     if level == 1:
    #         eval_label_dict[id_stripped] = {
    #             "label_id": row[1],
    #             "label_text": row[2],
    #             "label_level": level,
    #             "parent_id": row[5],
    #             "child_label": []
    #         }
    #     if level == 2:
    #         if eval_label_dict.get(row[1][0:-2], False):
    #             eval_label_dict[row[1][0:-2]]["child_label"].append(
    #                 {
    #                     "label_id": row[1],
    #                     "label_text": row[2],
    #                     "label_level": level,
    #                     "parent_id": row[5],
    #                     "child_label": None
    #                 }
    #             )
    # eval_label_list = list(eval_label_dict.values())
    # eval_label_list = sorted(eval_label_list, key=lambda x:x["label_id"])
    # with open(json_save_path, "w", encoding="utf-8") as f:
    #     json.dump(eval_label_list, f, ensure_ascii=False, indent=4)