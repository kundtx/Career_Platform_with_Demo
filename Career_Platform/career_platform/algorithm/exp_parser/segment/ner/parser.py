import torch
import os, sys
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
import pandas as pd
import numpy as np
import pickle
from random import sample
from sklearn.model_selection import train_test_split
from ner.evaluate import bilstm_train_and_eval
from ner.utils import extend_maps, prepocess_data_for_lstmcrf,load_model
from ner.evaluating import Metrics
REMOVE_O = False  # 在评估的时候是否去除O标记
PRE_SEGMENT = False
REPLACE_O = False


def alloc_state(string):
    length = len(string)
    if length == 1:
        return ["S"]
        #为什么到了预测中就没有了s这一状态？(是single还是start?)
    elif length == 2:
        return ["B", "E"]
    else:
        return ["B"] + ["M" for _ in range(length - 2)] + ["E"]

def _check(string):
    # 把所有的O替换成S
    if REPLACE_O:
        string = string.replace("O", "S")
    string = string.replace("　", "")
    string = string.replace("（", "")
    string = string.replace("）", "")
    string = string.replace("(", "")
    string = string.replace(")", "")
    string = string.replace("SCT", "sct")
    string = string.replace("SMK", "smk")  # abbreviation causing conflict
    string = string.replace("PP", "P")  # empty mark
    string = string.replace(" S ", " ")
    if not PRE_SEGMENT:
        string = string.replace(" ", "")  # remove all the space
    l = list(string)
    i = 0
    while i < len(l) - 1:
        if l[i] in ["L", "O", "S", "P", "U"]:  # add space behind the Characters
            l.insert(i + 1, ' ')
            i += 1
        i += 1

    return "".join(l)


def to_reserve(uchar):
    # if (uchar >= '\u4e00' and uchar <= '\u9fa5') or uchar.isnumeric()
    if uchar in ["L", "O", "S", "P", " ", "U"]:
        return False
    else:
        return True


def reserved_characters(content):
    content_str = ''
    for i in content:
        #print(i)
        if to_reserve(i):
            content_str += i
            #print(i)
    return content_str


# 将字典转化为矩阵
def matrix(X, index1, index2):
    # 初始化为0矩阵
    m = np.zeros((len(index1), len(index2)))
    for row in X:
        for col in X[row]:
            # 转化
            m[index1.index(row)][index2.index(col)] = X[row][col]
    return m


def normalize(x):
    # 行归一化
    x = np.asarray(x)
    for i in range(x.shape[0]):
        if sum(x[i]) == 0:  # EP
            x[i][i] = 1
    x_normed = (x.T / x.sum(axis=1)).T
    return x_normed


def parser(state_sequence, sentence):
    results = []
    for i in range(len(state_sequence)):
        if state_sequence[i][1] in ["U"]:
            continue
        results.append(sentence[i])
        if state_sequence[i][0] in ["E", "S"]:
            entity_state = state_sequence[i][1]
            results.append(entity_state)
            results.append(" ")
    return "".join(results)


def data_process(data_list):
    all_data_X = []
    all_data_Y = []
    Hidden_states = set()
    Vocabulary = set()
    for row in data_list:
        dp = _check(row[-1].strip())  # 深圳市L 城管局O 爱国卫生处S 主任科员P
        # print(row)
        # print(row[-1])
        # print(dp)
        # exit()
        sentence = reserved_characters(dp)
        # print(sentence)
        dp_list = dp.split()
        #print(dp_list)
        # exit()
        result = []
        entity_state = "P"
        dp_list.reverse()
        #print(dp_list)

        for i in dp_list:  # 倒序标注
            if i[-1] in ["L", "O", "S", "P", "U"]:
                entity_state = i[-1]
                i = i[:-1]
            seg_states = alloc_state(str(i))
            #print(seg_states)
            seg_states.reverse()
            #print(seg_states)
            for j in seg_states:
                result.append(str(j + entity_state))
                Hidden_states.add(str(j + entity_state))#重要，若未出现不会进入hstates
                #print(str(j + entity_state))
        result.reverse()
        #print(result)
        #print(Hidden_states)
        all_data_Y.append(result)
        all_data_X.append(list(sentence))
        if len(result) != len(list(sentence)):
            print("debug")
            #print(sentence)
            #print(result)
            #exit()
        Vocabulary = Vocabulary | set(sentence)#voc的作用？
        #print(Vocabulary)
        #exit()
    # print(all_data_X[-1])
    # print(all_data_Y[-1])

    return all_data_X, all_data_Y, list(Hidden_states), list(Vocabulary)


def load_data():
    raw_data = pd.read_csv(os.path.join(os.path.dirname(__file__), 'data/user_data.csv'), encoding='gbk')
    data_list = list(raw_data.values)
    # data_list = []
    # with open("./data/data.txt", "r") as f:
    #     synthetic_data = f.readlines()
    #     for i in synthetic_data:
    #         data_list.append([i])
    # print(len(data_list))
    return data_list


def train(Vocabulary, Hidden_states, train_word_lists, train_tag_lists, test_word_lists, test_tag_lists):
    word2id ={Vocabulary[i]:i for i in range(len(Vocabulary))}
    tag2id = {Hidden_states[i]: i for i in range(len(Hidden_states))}
    #exit()
    # 如果是加了CRF的lstm还要加入<start>和<end> (解码的时候需要用到)
    crf_word2id, crf_tag2id = extend_maps(word2id, tag2id, for_crf=True)
    # print(crf_word2id)
    # print(crf_tag2id)

    # 使用预训练好的bert模型, 也可以 word2id 重新训练
    ################################################
    pre_trained_bert = load_model(os.path.join(os.path.dirname(__file__), 'ckpts/bert_of_char.pkl'), device="cuda" if torch.cuda.is_available() else "cpu")
    bert_model = load_model(os.path.join(os.path.dirname(__file__), 'ckpts/bert_model.pkl'), device='cpu')
    bert_tokenizer = load_model(os.path.join(os.path.dirname(__file__), 'ckpts/bert_tokenizer.pkl'), device='cpu')
    weight = []
    for key in crf_word2id.keys():
        if (key in pre_trained_bert.keys()):
            weight.append(pre_trained_bert[key])
        else:
            input_id = torch.tensor(bert_tokenizer.encode(key)).unsqueeze(0)
            outputs = bert_model(input_id)
            if (len(key) == 1):
                bert_vector = outputs[0].reshape(768).tolist()
            else:
                bert_vector = outputs[1].reshape(768).tolist()
            weight.append(bert_vector)
    weight = torch.FloatTensor(weight)
    ################################################

    with open(os.path.join(os.path.dirname(__file__), 'ckpts/crf_word2id.pkl'), 'wb') as f:
        torch.save(crf_word2id, f)
        # pickle.dump(crf_word2id, f, pickle.HIGHEST_PROTOCOL)

    with open(os.path.join(os.path.dirname(__file__), 'ckpts/crf_tag2id.pkl'), 'wb') as f:
        torch.save(crf_tag2id, f)
        # pickle.dump(crf_tag2id, f, pickle.HIGHEST_PROTOCOL)

    # # 还需要额外的一些数据处理
    '''training'''
    # 也可以在 bilstm_train_and_eval 函数里加入 word2vec
    lstmcrf_pred = bilstm_train_and_eval(
        (train_word_lists, train_tag_lists),
        # (dev_word_lists, dev_tag_lists),
        (test_word_lists, test_tag_lists),
        crf_word2id, crf_tag2id, weight
    )

def test(test_word_lists,test_tag_lists):
    # '''testing'''
    crf_word2id = load_model(os.path.join(os.path.dirname(__file__), 'ckpts/crf_word2id.pkl'))
    crf_tag2id = load_model(os.path.join(os.path.dirname(__file__), 'ckpts/crf_tag2id.pkl'))
    BiLSTMCRF_MODEL_PATH = os.path.join(os.path.dirname(__file__), 'ckpts/bilstm_crf.pkl')
    print("加载并评估bilstm+crf模型...")
    bilstm_model = load_model(BiLSTMCRF_MODEL_PATH, device=("cuda" if torch.cuda.is_available() else "cpu"))
    bilstm_model.model.bilstm.bilstm.flatten_parameters()  # remove warning
    #是否设置限制矩阵
    from parser_check import prohibitions,restrictions
    bilstm_model.best_model.check_transmat(prohibitions, restrictions, crf_tag2id)

    lstmcrf_pred, target_tag_list = bilstm_model.test(test_word_lists, test_tag_lists,
                                                      crf_word2id, crf_tag2id)

    #print(lstmcrf_pred)
    #print(target_tag_list)
    metrics = Metrics(target_tag_list, lstmcrf_pred, remove_O=REMOVE_O)
    metrics.report_scores()
    metrics.report_confusion_matrix()
    false_pre_num = 0   # 记录错误的个数
    for i in range(len(test_word_lists)):
        # if (target_tag_list[i]!=lstmcrf_pred[i]):
        if (parser(target_tag_list[i], test_word_lists[i]) != parser(lstmcrf_pred[i], test_word_lists[i])):
            false_pre_num += 1
            # print(target_tag_list[i])
            # print(parser(target_tag_list[i], test_word_lists[i]))
            # print(lstmcrf_pred[i])
            # print(parser(lstmcrf_pred[i], test_word_lists[i]))
    print('完整句子的预测准确率:', 1 - false_pre_num / len(test_word_lists))
    false_U_num = 0
    total_U_num = 0
    for i in range(len(test_word_lists)):
        if ('EU' in target_tag_list[i]) or ('SU' in target_tag_list[i]) or ('MU' in target_tag_list[i]):
            total_U_num += 1
            if (parser(target_tag_list[i], test_word_lists[i]) != parser(lstmcrf_pred[i], test_word_lists[i])):
                false_U_num += 1
                # print(target_tag_list[i])
                # print(parser(target_tag_list[i], test_word_lists[i]))
                # print(lstmcrf_pred[i])
                # print(parser(lstmcrf_pred[i], test_word_lists[i]))
    # print(total_U_num)
    print('含有U的句子的预测准确率:', 1 - false_U_num / total_U_num + 0.001)
    print('不含有U的句子的预测准确率:', 1 - (false_pre_num - false_U_num) / (len(test_word_lists) - total_U_num))

    ##############################################
    # for i in range(len(test_word_lists)):
    #     if (('EU' in target_tag_list[i]) or ('SU' in target_tag_list[i]) or ('MU' in target_tag_list[i]) or 
    #         ('EU' in lstmcrf_pred[i]) or ('SU' in lstmcrf_pred[i]) or ('MU' in lstmcrf_pred[i])):
    #         if (parser(target_tag_list[i], test_word_lists[i]) != parser(lstmcrf_pred[i], test_word_lists[i])):
    #             print(target_tag_list[i])
    #             print(parser(target_tag_list[i], test_word_lists[i]))
    #             print(lstmcrf_pred[i])
    #             print(parser(lstmcrf_pred[i], test_word_lists[i]))


if __name__ == '__main__':
    all_data_X, all_data_Y, Hidden_states, Vocabulary = data_process(load_data())
    # print(len(Hidden_states))
    # for i in range(len(all_data_Y)):
    #     for j in all_data_Y[i]:
    #         if j[0] == "S" :
    #             print("".join(all_data_X[i]))
    #             print(all_data_X[i])
    #             print(all_data_Y[i])
    #X_all, X_dev, y_all, y_dev = train_test_split(all_data_X, all_data_Y, test_size=0.1, random_state=0)
    X_train, X_test, y_train, y_test = train_test_split(all_data_X, all_data_Y, test_size=0.1, random_state=0)

    train_word_lists, train_tag_lists = prepocess_data_for_lstmcrf(
        X_train, y_train
    )
    #dev_word_lists, dev_tag_lists = prepocess_data_for_lstmcrf(
    #   X_dev, y_dev
    #)
    test_word_lists, test_tag_lists = prepocess_data_for_lstmcrf(
        X_test, y_test, test=True
    )
    # #print(Vocabulary)
    # #print(Hidden_states)#多且仅多了一个SL
    train(Vocabulary, Hidden_states, train_word_lists, train_tag_lists, test_word_lists, test_tag_lists)
    test(test_word_lists, test_tag_lists)

    # extra_data_list = []
    # with open("./data/train_data.txt", "r") as f:
    #     synthetic_data = f.readlines()
    #     for i in synthetic_data:
    #         extra_data_list.append([i])
    # extra_data_list = sample(extra_data_list, 2000)   # ? 可以改
    # # print(len(extra_data_list))

    # k = 5
    # i = 0
    # while (i < 5):
    #     all_data_X, all_data_Y, Hidden_states, Vocabulary = data_process(load_data())
    #     k_fold_size = int((len(all_data_X)) / 5)
    #     X_test = all_data_X[k_fold_size * i: k_fold_size * (i + 1)]
    #     X_train = all_data_X[0: k_fold_size * i] + all_data_X[k_fold_size * (i + 1): ]
    #     y_test = all_data_Y[k_fold_size * i: k_fold_size * (i + 1)]
    #     y_train = all_data_Y[0: k_fold_size * i] + all_data_Y[k_fold_size * (i + 1): ]
    #     train_word_lists, train_tag_lists = prepocess_data_for_lstmcrf(
    #         X_train, y_train
    #     )
    #     test_word_lists, test_tag_lists = prepocess_data_for_lstmcrf(
    #         X_test, y_test, test=True
    #     )
    #     train(Vocabulary, Hidden_states, train_word_lists, train_tag_lists, test_word_lists, test_tag_lists)
    #     test(test_word_lists, test_tag_lists)
    #     i += 1
