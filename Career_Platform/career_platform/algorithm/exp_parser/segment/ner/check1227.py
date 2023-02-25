# from utils import load_model
# from evaluating import Metrics
# import torch
# from pyhanlp import *
# from parser_check import parser,prepocess_data_for_lstmcrf
import os

from .utils import load_model
from pyhanlp import *
from .parser_check import parser, prepocess_data_for_lstmcrf
import jieba.posseg as pseg

# '''testing'''
crf_word2id = load_model(os.path.join(os.path.dirname(__file__), 'ckpts/crf_word2id.pkl'))
crf_tag2id = load_model(os.path.join(os.path.dirname(__file__), 'ckpts/crf_tag2id.pkl'))
BiLSTMCRF_MODEL_PATH = os.path.join(os.path.dirname(__file__), 'ckpts/bilstm_crf.pkl')
print("加载并使用bilstm+crf模型...")
bilstm_model = load_model(BiLSTMCRF_MODEL_PATH)
bilstm_model.model.bilstm.bilstm.flatten_parameters()  # remove warning
print(crf_tag2id)
# bilstm_model.best_model.check_transmat(prohibitions, restrictions, crf_tag2id)


# func: 查找list包含指定word的全部位置，以列表形式返回
def index_str(word_list, word):
    index_list = []
    # 查找指定字符串str1包含指定子字符串str2的全部位置，以列表形式返回
    for i in range(len(word_list)):
        if word_list[i] == word:
            index_list.append(i)
    return index_list

def get_tag_index(first_job_pred, tag):
    for i in range(len(first_job_pred)):
        if first_job_pred[i] == tag:
            return i
    return -1

def check_each_job(job):
    word_list = []
    tmp = ''
    for i in range(len(job)):

        if job[i] != '|':
            tmp = tmp + job[i]
            if i == len(job) - 1:
                word_list.append(tmp)
        else:
            word_list.append(tmp)
            tmp = ''
    word_lists = prepocess_data_for_lstmcrf(word_list)
    pred_tag_lists = bilstm_model.predict(word_lists, crf_word2id, crf_tag2id)

    # print("=============1.分段分词结果=============")
    for i in range(len(pred_tag_lists)):
        result = parser(pred_tag_lists[i], word_lists[i])
        # print(result)

    adjunct_list = []

    first_job = word_lists[0]
    first_job_pred = pred_tag_lists[0]
    adjunct_list.append(parser(first_job_pred, first_job))

    for adj in range(1,len(word_lists)):
                    next_job = word_lists[adj]
                    next_pred = pred_tag_lists[adj]
                    next_result = parser(next_pred, next_job)
                    # ['市', '长', '候', '选', '人', '<end>']
                    # ['BP', 'EP', 'BP', 'MP', 'EP']
                    root_word = []
                    root_pred = []
                    root_result = ""

                    first_es_i = get_tag_index(first_job_pred, "ES")
                    first_eo_i = get_tag_index(first_job_pred, "EO")
                    first_el_i = get_tag_index(first_job_pred, "EL")

                    # P找S或者O
                    if next_pred[0] == "BP" or next_pred[0] == "MP" or next_pred[0] == "EP":
                        print("P找S或者O")

                        if first_es_i != -1:
                            root_word = first_job[:first_es_i+1]
                            root_pred = first_job_pred[:first_es_i+1]
                        elif first_es_i == -1 and first_eo_i != -1:
                            root_word = first_job[:first_eo_i+1]
                            root_pred = first_job_pred[:first_eo_i+1]
                        elif first_es_i == -1 and first_eo_i == -1 and first_el_i != -1:
                            root_word = first_job[:first_el_i+1]
                            root_pred = first_job_pred[:first_el_i+1]
                        else:  # 没找到L O S
                            root_word = first_job
                            root_pred = first_job_pred
                        root_result = parser(root_pred, root_word)
                    # S找O
                    elif next_pred[0] == "BS" or next_pred[0] == "MS":
                        print("S找O")
                        # first job有O无S  接在O后
                        if first_eo_i != -1 and first_es_i == -1:
                            root_word = first_job[:first_eo_i+1]
                            root_pred = first_job_pred[:first_eo_i+1]
                        # first job无O     接在L后
                        elif first_eo_i == -1 and first_el_i != -1:
                            root_word = first_job[:first_el_i+1]
                            root_pred = first_job_pred[:first_el_i+1]
                        else:  # 没找到L O
                            pass
                        root_result = parser(root_pred, root_word)

                    # O找L
                    elif next_pred[0] == "BO" or next_pred[0] == "MO":
                        print("O找L")
                        if first_el_i != -1:
                            root_word = first_job[:first_el_i+1]
                            root_pred = first_job_pred[:first_el_i+1]
                        else:  # 没找到L
                            pass
                        root_result = parser(root_pred, root_word)

                    # L 改L找L
                    elif next_pred[0] == "BL" or next_pred[0] == "EL":
                        print("L找L")
                        if first_el_i != -1:
                            root_word = first_job[:first_el_i + 1]
                            root_pred = first_job_pred[:first_el_i + 1]
                        root_result = parser(root_pred, root_word)

                    adjunct_list.append(root_result + next_result)
    # print("==============2.最终分词分句结果=============")
    # print(adjunct_list)

    final = []
    for adjunct in adjunct_list:
        entity_list = adjunct.strip().split(" ")
        tmp = ""
        for i in range(len(entity_list)):

            terms = HanLP.segment(entity_list[i])
            if str(terms[-2].nature)[0] == 'n':
                tmp = tmp + entity_list[i] + " "
        final.append(tmp)
    return final[-1]


def check(job):
        word_lists = pseg.cut(job)
        position = ''
        for i in word_lists:
            if str(i.flag) != 'c' and str(i.flag) != 'd':
                position = position + i.word
        position = position.replace("，任","").replace(",任","").replace(",历任","").replace("，历任","")
        position = position.replace("兼职", "").replace("，兼", "兼").replace(",兼", "兼")

        position = position.replace("兼任", "兼").replace(",", "兼").replace("，", "兼"). \
            replace("。", "兼").replace("、", "兼").replace("及", "兼")

        index_list = index_str(position, "兼")

        ini_list = []
        if len(index_list) == 0:
            ini_list.append(position)
        # 处理兼词情况
        # 第一个字是兼
        elif index_list[0] == 0:
            ini_list.append(position[1:])
        else:
            index_list.append(len(position))
            ini_list = []
            ini_job = position[:index_list[0]]
            ini_list.append(ini_job)
            for i in range(0, len(index_list) - 1):
                i_index = index_list[i] + 1
                j_index = index_list[i + 1]
                tmp = ini_job + "|" + position[i_index:j_index]
                ini_list.append(tmp)

        end_job = HanLP.segment(ini_list[-1])[-1]
        final_result = []
        for i in range(len(ini_list)):
            if ini_list[i].find('|') != -1:
                # 判断每一个词的倒数第一个词语的词性
                end_word_nature = HanLP.segment(ini_list[i])[-1].nature
                if not (str(end_word_nature)).startswith('nn'):
                    ini_list[i] = ini_list[i] + end_job.word
            # print("=============0.原句是=============")
            # print(ini_list[i])
            result = check_each_job(ini_list[i])
            final_result.append(result)
        return final_result

if __name__ == '__main__':
    input_str = "深圳市教育局局长兼书记"
    result = check(input_str)
    print(result)
