from ...common import Label, Experience
from .classifier import BertClassifier, ExpRuleClassifier
from typing import *
from tqdm import tqdm

__all__ = ["label_exp"]



def label_exp(exp_list:List[Experience]) -> List[Label]:
    """
    对输入的exp_list中的每一个Experience进行标签预测, 返回结果Label列表.
    """
    text_list = [(i.text if i.text else "") for i in exp_list] # None值替换为空字符串

    # 1. 用BertClassifier做分类
    bertCls = BertClassifier()
    bert_pred = bertCls.classify(text_list)

    label_result = []
    for i in range(len(exp_list)):
        if bert_pred[i] is None:
            continue
        for label_text in bert_pred[i]:
            if label_text == "学生":
                continue
            label_result.append(Label(label_text=label_text, 
                                      label_category=1, 
                                      label_source=202, 
                                      person_uuid=exp_list[i].person_uuid,
                                      exp_uuid=exp_list[i].uuid,
                                      time_start=exp_list[i].time_start,
                                      time_end=exp_list[i].time_end
                                      ))
    
    # 2. 用ExpRuleClassifier做分类
    expRuleCls = ExpRuleClassifier()
    ignore_set = ('深圳','深圳市外1','龙华','罗湖','福田','南山','宝安','龙岗','盐田','坪山','光明','深汕特别合作区','大鹏新区','市委直属','市人大直属','市政协直属','市政府直属')

    expRule_pred = []
    for txt in tqdm(text_list, desc="ExpRule Predict"):
        expRule_pred.append(expRuleCls.classify(txt, Hybrid=False))
    for i in range(len(exp_list)):
        if expRule_pred[i] is None:
            continue
        for label_text in expRule_pred[i]:
            if label_text in ignore_set:
                continue
            label_result.append(Label(label_text=label_text, 
                                      label_category=1, 
                                      label_source=201, 
                                      person_uuid=exp_list[i].person_uuid,
                                      exp_uuid=exp_list[i].uuid,
                                      time_start=exp_list[i].time_start,
                                      time_end=exp_list[i].time_end
                                      ))


    # 3. 对label_result进行去重
    label_dict:Dict[str, Label] = {}    # 用于去重的标签字典，key为exp_uuid
    for lb in label_result:
        if label_dict.get(lb.exp_uuid, False):
            duplicate = False
            # 如果找到label_dict中已有exp_uuid和label_text相同的，则丢弃，否则插入
            for lb_in_dict in label_dict[lb.exp_uuid]: 
                if lb.label_text == lb_in_dict.label_text:
                    duplicate = True
                    break
            if not duplicate:
                label_dict[lb.exp_uuid].append(lb)
        else:
            label_dict[lb.exp_uuid] = [lb, ]
    
    label_result = []
    for lb_list in label_dict.values():
        label_result.extend(lb_list)

    return label_result