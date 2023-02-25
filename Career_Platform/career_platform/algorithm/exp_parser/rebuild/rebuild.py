from typing import *
import re
import copy
from ....common import Experience
from .location_recover import location_recover

__all__ = ["rebuild"]   # 只对外暴露rebuild函数


def rebuild(exp_list:List[Experience], callback:Callable=None) -> List[Experience]:
    """
    对exp_list中的每一个Experience进行重建, 包括: 兼职命名实体补齐->Location补齐->兼职拆分
    
    重建需要用到text_rawtoken. 一个Experience可能会被重建为多个Experience. 重建后的Experience会获得text和text_token属性的值.

    Params:
        exp_list: 传入的经历列表
        callback: 回调函数, 需要能够接收一个包含函数执行状态信息的dict, 可以用来查看执行进度
    
    Returns:
        返回一个新的Experience列表, 列表长度可能比exp_list长, 这是因为exp_list中的Experience可能被重建为多个.
    """
    # 用于传入callback的状态字典
    __status_dict = {
        "description": "[exp_parser]-rebuild",
        "total": len(exp_list),
        "iternum": 0
    }

    result:List[Experience] = []

    for iternum, exp in enumerate(exp_list):
        # 跳过曾经拆分过的
        if exp.splitnum != 0:
            continue
        recovered_rawtoken = adjunct_entity_recover(exp.text_rawtoken)              # 1. 兼职命名实体补齐
        splitted_exps = adjunct_split(exp, recovered_rawtoken=recovered_rawtoken)   # 2. 兼职拆分、Location补齐
        result.extend(splitted_exps)

         # 调用callback函数
        __status_dict["iternum"] = iternum
        if callback is not None:
            callback(__status_dict)

    return result


def adjunct_entity_recover(rawtoken:str or None) -> str:
    """
    兼职命名实体补齐 + Location补齐.
    将一个含有兼职拆分标记和NER标记的字符串, 按规则补齐每一个兼职子串中的命名实体, 包括补齐Location

    Params:
        rawtoken: 含有兼职拆分标记和NER标记的字符串
    
    Example:
        输入："深圳L 广电集团O 龙岗广电中心S 主任P|东部传媒公司O 董事P|总经理P|广电中心O 党组S 书记P"

        输出："广东省L 深圳市L 广电集团O 龙岗广电中心S 主任P|广东省L 深圳市L 广电集团O 东部传媒公司O 董事P|广东省L 深圳市L 广电集团O 东部传媒公司O 总经理P|广东省L 深圳市L 广电集团O 广电中心O 党组S 书记P"
    """
    # 是None或没有兼职拆分标记就直接Location补齐后返回
    if (rawtoken is None) or ("|" not in rawtoken):
        return location_recover(rawtoken)

    text_list:List[str] = rawtoken.split("|")     # ["深圳L 广电集团O 龙岗广电中心S 主任P", "东部传媒公司O 董事P", "总经理P", "广电中心O 党组S 书记P"]
    text_list = [location_recover(text) for text in text_list]
    # 过滤空串，且如果location_recover后剩下的test_list小于等于1个元素，则直接返回
    text_list = [text for text in text_list if text.strip() != ""]
    if len(text_list) < 2:
        return text_list[0] if len(text_list) == 1 else None
        
    entity_lists:List[List[str]] = [t.split(" ") for t in text_list] # [["深圳L", "广电集团O", "龙岗广电中心S", "主任P"], ["东部传媒公司O", "董事P"], ["总经理P"], ["广电中心O", "党组S", "书记P"]]
    new_entity_lists:List[List[str]] = copy.deepcopy(entity_lists)

    # 首个兼职没有LOS的直接原样返回，没必要走接下来流程了
    if re.search("[SOL]+", text_list[0]) is None:
        return rawtoken

    # 从1往后迭代恢复new_entity_lists中第num个entity_list
    for num in range(1, len(new_entity_lists)):
        cur_head_tag = new_entity_lists[num][0][-1]  # 当前entity_list的第一个entity的标签
        cur_entity_list = new_entity_lists[num]

        # P接到最近前驱entity_list最后一个S（或O或L）后面
        if cur_head_tag == "P":
            last_SO_idx = len(new_entity_lists[num-1]) - 1
            while(last_SO_idx > -1):
                if new_entity_lists[num-1][last_SO_idx][-1] in ["S", "O", "L"]:
                    break
                last_SO_idx -= 1

            cur_entity_list = new_entity_lists[num-1][0:last_SO_idx + 1] + cur_entity_list
        
        # S接到最近前驱entity_list第一个O（或S）后面，无O则最后一个L
        if cur_head_tag == "S":
            first_O_idx = 0
            while(first_O_idx < len(new_entity_lists[num-1])):
                if new_entity_lists[num-1][first_O_idx][-1] in ["O", "S"]:
                    break
                first_O_idx += 1
            
            cur_entity_list = new_entity_lists[num-1][0:first_O_idx + 1] + cur_entity_list
        
        # O接到最近前驱entity_list的第一个O（或S）后面，无O则最后一个L
        if cur_head_tag == "O":
            # 跳过一些特例
            exception_list = [
                "致公党",
                "共青团"
            ]
            if re.search("|".join(exception_list), cur_entity_list[0]):
                continue
            
            # 找最近前驱第一个O
            first_O_idx = 0
            while(first_O_idx < len(new_entity_lists[num-1])):
                if new_entity_lists[num-1][first_O_idx][-1] in ["O", "S"]:
                    break
                first_O_idx += 1

            cur_entity_list = new_entity_lists[num-1][0:first_O_idx + 1] + cur_entity_list

        # 是L就啥也不干
        if cur_head_tag == "L":
            pass

        new_entity_lists[num] = cur_entity_list

    new_text_list = [" ".join(ents) for ents in new_entity_lists]

    # 对new_text_list中的每一个token字符串做Location补齐
    # new_text_list = [location_recover(ner_token) for ner_token in new_text_list]

    return "|".join(new_text_list)


def adjunct_split(exp:Experience, recovered_rawtoken:str) -> List[Experience]:
    """
    兼职拆分.
    将一个未被拆分过的Experience按text_rawtoken兼职拆分标记拆分成多个, 并生成各自的text和text_token以及splitnum

    Params:
        exp: 一个Experience
    """
    # splitnum不为0直接报错，这是为了整个系统的稳定着想
    if exp.splitnum != 0:
        raise ValueError("只能对splitnum为0的Experience进行兼职拆分, 若不为0说明已经拆分过了, 再次拆分将对系统带来严重错误")
    
    # 不用拆分的直接把text_rawtoken赋值给text_token，再把text_token合并赋值给text
    if (recovered_rawtoken is None) or ("|" not in recovered_rawtoken):
        new_exp = copy.deepcopy(exp)
        new_exp.splitnum = 1
        new_exp.text_token = recovered_rawtoken
        new_exp.text = None if new_exp.text_token is None else "".join([t[0:-1] for t in new_exp.text_token.split(' ')])
        return [new_exp, ]
    
    result: List[Experience] = []
    # recovered_rawtoken按"|"分开生成新的Experience，生成各自的text_token和text，按每个Experience在rawtoken中的位置设置splitnum（从1开始）
    split_token_list = recovered_rawtoken.split("|")
    for idx, split_token in enumerate(split_token_list):
        new_exp = copy.deepcopy(exp)
        new_exp.splitnum = idx+1
        new_exp.text_token = split_token
        new_exp.text = "".join([t[0:-1] for t in new_exp.text_token.split(' ')])
        result.append(new_exp)
    return result