import os, sys
import pickle
from typing import *
import re
import copy
from ....common import Experience
import torch

from . import ner
sys.modules['ner'] = ner

CKPT_PATH = os.path.join(os.path.dirname(__file__), "ner/ckpts")

__all__ = ["segment"]   # 只对外暴露segment函数


def segment(exp_list:List[Experience], in_position:bool=False, callback:Callable=None) -> List[Experience]:
    """
    对列表中每一个Experience的text_rawsplit中的每一个split进行: NER分词->去除U标签

    结果保存在text_rawtoken

    Params:
        exp_list: 传入的经历列表
        in_position: True则在传入exp_list上原地修改并返回原exp_list. False则深拷贝后修改并返回新的
        callback: 回调函数, 需要能够接收一个包含函数执行状态信息的dict, 可以用来查看执行进度
    """
    if not in_position:
        exp_list = copy.deepcopy(exp_list)

    tokenizer = BCTokenizer()

    # 用于传入callback的状态字典
    __status_dict = {
        "description": "[exp_parser]-segment",
        "total": len(exp_list),
        "iternum": 0
    }
    for iternum, exp in enumerate(exp_list):
        if exp.text_rawsplit is not None:
            split_list = exp.text_rawsplit.split("|")
            text_rawtoken = "|".join(tokenizer.parse_strings(split_list))  # 对text_rawsplit的每一个split子串进行: NER分词、去除U标签
            exp.text_rawtoken = text_rawtoken if text_rawtoken != "" else None

        # 调用callback函数
        __status_dict["iternum"] = iternum
        if callback is not None:
            callback(__status_dict)
    
    return exp_list


class BCTokenizer():
    """
    用于NER解析的bilstm_crf模型
    """

    # 存放模型的类变量，全局单例
    crf_word2id = None
    crf_tag2id = None
    bilstm_model = None

    # 禁止转移
    prohibitions = {
                    #"<start>": ["MO", "EO", "MP", "EP", "BS" , "MS", "ES", "ML", "EL"],
                    "<start>": ["MO", "EO", "MP", "EP", "MS", "ES", "ML", "EL"],
                    "EL": ["MO", "EO", "MP", "EP", "MS", "ES", "ML", "EL"],
                    "EO": ["BO", "MO", "EO", "MP", "EP", "MS", "ES", "ML", "EL"],
                    "ES": ["BO", "MO", "EO", "MP", "EP", "MS", "ES", "ML", "EL"],
                    "EP": ["BO", "MO", "EO", "BP", "MP", "EP", "BS" , "MS", "ES", "BL", "ML", "EL"],   # 禁止双 P
                    # "EU": ["MO", "EO", "MP", "EP", "MS", "ES", "ML", "EL"],
                    }
    # 只能转移
    restrictions = {"BL": ["ML", "EL"],
                    "ML": ["ML", "EL"],
                    "BO": ["MO", "EO"],
                    "MO": ["MO", "EO"],
                    "BS": ["MS", "ES"],
                    "MS": ["MS", "ES"],
                    "BP": ["MP", "EP"],
                    "MP": ["MP", "EP"],
                    # "BU": ["MU", "EU"],
                    # "MU": ["MU", "EU"],
                    }

    def __init__(self):
        if self.bilstm_model is None:   # 仅在全局第一次实例化BCTokenizer时加载模型
            self.__init_model()   
    
    @classmethod
    def __init_model(cls):
        cls.crf_word2id = cls.__load_model(os.path.join(CKPT_PATH,'crf_word2id.pkl'), device="cpu")
        cls.crf_tag2id = cls.__load_model(os.path.join(CKPT_PATH,'crf_tag2id.pkl'), device="cpu")
        cls.bilstm_model = cls.__load_model(os.path.join(CKPT_PATH, 'bilstm_crf.pkl'), device=('cuda' if torch.cuda.is_available() else 'cpu'))
        cls.bilstm_model.best_model.check_transmat(cls.prohibitions, cls.restrictions, cls.crf_tag2id)
        cls.bilstm_model.model.bilstm.bilstm.flatten_parameters()  # remove warning

    @staticmethod
    def __load_model(file_name:str, device="cpu"):
        """
        加载模型
        """
        with open(file_name, "rb") as f:
            model = torch.load(f, map_location=torch.device(device))
        return model
    
    @staticmethod
    def __prepocess_data_for_lstmcrf(text_list:List[str]) -> List[List[str]]:
        """
        将列表中每一个字符串转为字符列表，并为每一个字符列表添加结束标记<end>
        """
        char_lists:List[List[str]] = [list(i) for i in text_list]
        for i in range(len(char_lists)):
            char_lists[i].append("<end>")
        return char_lists

    @staticmethod
    def __parser(state_sequence, sentence):
        """
        将bilstm_crf预测的tag合并,并和句子中对应词拼接. 同时还会将U标签去除
        """
        results = []
        for i in range(len(state_sequence)):
            if state_sequence[i][1] in ["U"]:
                continue
            results.append(sentence[i])
            if state_sequence[i][0] in ["E", "S"]:
                entity_state = state_sequence[i][1]
                results.append(entity_state)
                results.append(" ")
        result = "".join(results)
        
        extra_U = ["退休", "待分", "待安"]
        # 如果extra_U中的词出现在结果中则直接返回空字符串
        if re.match(".*({})".format("|".join(extra_U)), result) is None:
            return "".join(results)
        else:
            return ""

    def parse_strings(self, text_list:List[str]) -> List[str]:
        """
        对字符串列表中的每一个字符串进行NER解析
        """
        
        # [['广东省汕尾市委副书记'], ...] 转为 [['广', '东', '省', '汕', '尾', '市', '委', '副', '书', '记', '<end>'], ...]
        char_lists = self.__prepocess_data_for_lstmcrf(text_list)

        # 生成 [['BL', 'ML', 'EL', 'BO', 'MO', 'MO', 'EO', 'BP', 'MP', 'EP'], ...]
        pred_tag_lists = self.bilstm_model.predict(char_lists, self.crf_word2id, self.crf_tag2id)

        segment_list = []
        for i in range(len(pred_tag_lists)):
            segment = self.__parser(pred_tag_lists[i], char_lists[i])
            segment = segment.strip()
            if segment != "":
                segment_list.append(segment)
        
        return segment_list
