# from utils import load_model
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from ner.utils import load_model
# from evaluating import Metrics
from ner.evaluating import Metrics
import torch


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


def prepocess_data_for_lstmcrf(data_lists):
    word_lists = [list(i) for i in data_lists]
    for i in range(len(data_lists)):
        word_lists[i].append("<end>")
    return word_lists

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




REMOVE_O = False  # 在评估的时候是否去除O标记


def main():
    # '''testing'''
    crf_word2id = load_model(os.path.join(os.path.dirname(__file__), 'ckpts/crf_word2id.pkl'))
    crf_tag2id = load_model(os.path.join(os.path.dirname(__file__), 'ckpts/crf_tag2id.pkl'))
    BiLSTMCRF_MODEL_PATH = os.path.join(os.path.dirname(__file__), 'ckpts/bilstm_crf.pkl')
    print("加载并使用bilstm+crf模型...")
    bilstm_model = load_model(BiLSTMCRF_MODEL_PATH)
    bilstm_model.model.bilstm.bilstm.flatten_parameters()  # remove warning
    print(crf_tag2id)
    # bilstm_model.best_model.check_transmat(prohibitions, restrictions, crf_tag2id)
    word_lists = ["广东省第八建筑工程公司发电分公司技术员",
                  "广东省第八建筑工程公司深圳公司技术员",
                  "广东省第八建筑工程公司深圳分公司技术员",
                  "致公党深圳市委会副主委",
                  "深圳市司法局社区矫正和安置帮教工作处副处长",
                  "深能国际有限公司董事副总经理",
                  "深能国际有限公司董事会副总经理",
                  "深能国际有限公司董事会总经理",
                  "深能国际有限公司董事会总经理助理",
                  "深圳市深水水务咨询有限公司监理总经理助理",
                  "加纳风电项目加纳阿达风电有限公司董事长",
                  "长沙电力学院地理学专业本科学习",
                  "哈尔滨工业大学深圳研究生院博士生导师",
                  "清华大学电子工程系学生",
                  "深圳市教育局高等教育处处长",
                  "深圳市罗湖区人民检察院监查局局长",
                  '市委卫生工委委员',
                  "中国平安人寿保险股份有限公司河北分公司机关党支部书记",
                  '中共深圳创维-RGB电子有限公司重庆分公司支部书记',
                  '哈尔滨工业大学深圳研究生院博士生导师',
                  '哈尔滨工业大学深圳研究生院管理科学与工程专业博士研究生学习',
                  '深圳市人力资源和社会保障局职员与雇员管理处主任科员',
                  '河南省郑州磨料磨具磨削研究所理化室助理工程师',
                  '深圳市皇岗公园管理处普通工人',
                  '深圳市皇岗公园管理处初级工人',
                  '厦门大学环境科学专业研究生硕士',
                  '江西吉安师范学校教师',
                  '暨南大学管理学院产业经济学专业硕士研究生',
                  '北京农业工程大学应用电子技术专业大学本科学习',
                  '哈尔滨船舶工程学院动力工程系本科',
                  '河南省郑州磨料磨具磨削研究所理化室助理工程师',
                  '深圳市人力资源和社会保障局职员与雇员管理处主任科员',
                  '河南省信阳市药厂会计师',
                  '总参三部三局二处二科助理翻译',
                  '北京轻工业学院外语系科技英语专业学习',
                  '对外经济贸易大学研究生院国际商务英语专业硕士研究生']
    word_lists = prepocess_data_for_lstmcrf(word_lists)
    print(word_lists)
    #exit()
    pred_tag_lists = bilstm_model.predict(word_lists, crf_word2id, crf_tag2id)

    for i in range(len(word_lists)):
        # print(word_lists[i])
        # print(pred_tag_lists[i])
        print(parser(pred_tag_lists[i], word_lists[i]))

    word_lists = input("输入例句\n")
    #print(word_lists)
    word_lists = [word_lists]
    while word_lists[0]:
        word_lists = prepocess_data_for_lstmcrf(word_lists)
        #print(word_lists)
        # exit()
        pred_tag_lists = bilstm_model.predict(word_lists, crf_word2id, crf_tag2id)

        for i in range(len(word_lists)):
            # print(word_lists[i])
            print("单字标签")
            print(pred_tag_lists[i])
            print("分词结果")
            print(parser(pred_tag_lists[i], word_lists[i]))
        word_lists = input("输入例句\n")
        word_lists = [word_lists]
        #print(word_lists)


if __name__ == '__main__':
    main()
