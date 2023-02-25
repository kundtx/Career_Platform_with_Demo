from ...common import Evaluation
from ...common import Label
from typing import *
from .phrase_grouding import FuzzyMatch

__all__ = ["label_eval"]



def label_eval(eval_list:List[Evaluation], callback:Callable=None) -> List[Label]:
    """
    对eval_list中所有Evaluation进行主观标签分析, 返回得到的标签列表

    Params: 
        eval_list: 待分析的Evaluation对象列表
        callback: 回调函数, 需要能够接收一个包含函数执行状态信息的dict, 可以用来查看执行进度
    """


    return __label_eval_fuzzy_match(eval_list=eval_list, callback=callback)


def __label_eval_fuzzy_match(eval_list:List[Evaluation], callback:Callable=None) -> List[Label]:
    """
    基于FuzzyWuzzy的label_eval函数
    """
    
    # 用于传入callback的状态字典
    __status_dict = {
        "description": "[label_eval]-fuzzy_match",
        "total": len(eval_list),
        "iternum": 0
    }

    matcher = FuzzyMatch()

    label_result:List[Label] = []
    for iternum, eval in enumerate(eval_list):
        cur_match_list = matcher.fuzzy_match(long_text=eval.text, thresh=60)

        for match in cur_match_list:
            label_result.append(Label(label_text=match["label"],
                                        label_info=match["count"],
                                        label_code=match["code"],
                                        label_category=2, 
                                        label_source=301, 
                                        person_uuid=eval.person_uuid,
                                        eval_uuid=eval.uuid,
                                        time_start=eval.time_start,
                                        ))


        # 调用callback函数
        __status_dict["iternum"] = iternum
        if callback is not None:
            callback(__status_dict)

    return label_result
