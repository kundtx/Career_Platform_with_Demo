import os,sys
import json
import ahocorasick
from typing import *
import numpy as np
import re
__all__ = ["location_recover"]


DATA_DIR = os.path.dirname(__file__)

def location_recover(token:str) -> str:
    """
    将输入的token字符串中地点L标签补齐, 返回补齐后的token字符串. 
    
    例1: 深圳L 审计局O 政府投资审计专业局O 干部P ——> 广东省L 深圳市L 审计局O 政府投资审计专业局O 干部P
    例2: 清华大学O 计算机系S 教授P ——> 北京市L 北京市L 清华大学O 计算机系O 教授P

    Params:
        token: 待补齐地点的token字符串
    """
    
    if (token is None) or (re.search("[SOL]", token) is None):
        return token

    helper = LocDetHelper()

    token_list = token.split(" ")
    full_text = "".join([token[0:-1] for token in token_list])
    
    L_tokens = [token[0:-1] for token in token_list if token[-1]=='L']
    L_tokens_nosuffix = [helper.remove_loc_suffix(token) for token in L_tokens]
    L_text = "".join(L_tokens)

    O_tokens = [token[0:-1] for token in token_list if token[-1] in ['O', 'S']]
    O_text = "".join(O_tokens)


    explicit_prov:List[str] = []
    explicit_city:List[Tuple[str, str]] = []
    O_inferenced_city:List[Tuple[int, str, Tuple[str, str]]] = []
    L_inferenced_city:List[Tuple[str, str]] = []

    # 1. 在L tokens里检测显式给出的省份
    for t in range(len(L_tokens)):
        if helper.prov2p_dict.get(L_tokens[t], False):
            explicit_prov.append(helper.prov2p_dict[L_tokens[t]])
        if helper.prov2p_dict.get(L_tokens_nosuffix[t], False):
            explicit_prov.append(helper.prov2p_dict[L_tokens_nosuffix[t]])

    # 2. 在L tokens里检测显式给出的市级行政区
    explicit_city.extend(helper.detect_by_city2pc_dict(L_tokens, L_tokens_nosuffix))
    explicit_city.extend([e[2] for e in helper.detect_by_city2pc_AC(L_text)])

    # 3. 如果没找到L中显式的省份和市级行政区，则尝试从O和S中找
    if len(explicit_city) == 0:
        O_inferenced_city.extend(helper.detect_by_school2pc_AC(full_text))
        O_inferenced_city.extend(helper.detect_by_city2pc_AC(O_text))
        O_inferenced_city.sort(key=lambda x:x[0])   # 按匹配的位置排序

    # 4. 如果上述步骤都没有找到市级行政区，则尝试用L匹配区县一级，反推省市
    if (len(explicit_city)==0)  and (len(O_inferenced_city)==0):
        L_inferenced_city.extend(helper.detect_by_dist2pc_dict(L_tokens, L_tokens_nosuffix))

    # 5. 在所有检测出的结果中确定最终的(省, 市)
    prov, city = None, None
    if len(explicit_prov) > 0:  # 省份被显示给出的情况
        prov = explicit_prov[0]
        for i in explicit_city:
            if i[0] == prov:
                city = i[1]
                break
        if city is None:
            for i in O_inferenced_city:
                if i[2][0] == prov:
                    city = i[2][1]
                    break
    elif len(explicit_city) > 0:   # 省份没给出的情况
        prov, city = explicit_city[0]
    elif len(O_inferenced_city) > 0:
        prov, city = O_inferenced_city[-1][2]
    elif len(L_inferenced_city) > 0:
        prov, city = L_inferenced_city[-1]

    # 6. 重建token
    token_list_new = []
    if prov:
        token_list_new.append(prov+'L')
    if city:
        token_list_new.append(city+'L')
    for i in range(len(token_list)):
        cur_token = token_list[i]
        if cur_token[-1] == 'L':
            # 如果是区县一级的L就加入新的token_list_new
            if helper.dist2pc_dict.get(cur_token[0:-1], False) or helper.dist2pc_dict_nosuffix.get(helper.remove_loc_suffix(cur_token[0:-1]), False):
                token_list_new.append(cur_token)
        if cur_token[-1] != 'L':    # 第一次遇到不是L的就把之后的全拼进新的token_list_new, 然后跳出循环
            rest_list = token_list[i:]
            rest_list = " ".join(rest_list).replace("L ", "").split(" ")
            token_list_new.extend(rest_list)
            break

    token_new = " ".join(token_list_new)
    return token_new


class LocDetHelper():
    """
    地点检测时需要用到的工具集, 只在第一次实例化时加载, 全局单例

    Attributes:
        prov2p_dict:              省级行政区回查标准省名词典
        city2pc_dict:             市级行政区回查[省,市]词典, 有后缀
        city2pc_dict_nosuffix:    市级行政区回查[省,市]词典, 无后缀
        dist2pc_dict:             区县级行政区回查[省,市]词典, 有后缀
        dist2pc_dict_nosuffix:    区县级行政区回查[省,市]词典, 无后缀
        school2pc_dict:           高校名回查[省,市]词典, 有后缀

    Function:
        remove_loc_suffix(): 去除地名里的后缀, 返回无后缀的地名
        detect_by_school2pc_AC(): 用高校AC自动机检测句子中的高校名, 以推断地点, 返回所有匹配位置和对应[省市]
        detect_by_city2pc_AC(): 用市级行政区AC自动机检测句子中的地名, 以推断地点, 返回所有匹配位置和对应[省市]
    """

    # 类变量
    loc_dict = None                 # loc.json中的数据

    prov2p_dict = None              # 省级行政区回查标准省名词典
    city2pc_dict = None             # 市级行政区回查[省,市]词典, 有后缀
    city2pc_dict_nosuffix = None    # 市级行政区回查[省,市]词典, 无后缀
    dist2pc_dict = None             # 区县级行政区回查[省,市]词典, 有后缀
    dist2pc_dict_nosuffix = None    # 区县级行政区回查[省,市]词典, 无后缀
    school2pc_dict = None           # 高校名回查[省,市]词典, 有后缀

    city2pc_AC = None               # 市级行政区回查[省,市]AC自动机
    school2pc_AC = None             # 高校名回查[省,市]AC自动机, 用于对包含高校名的字符串进行多模匹配    


    def __init__(self):
        # 只需初次实例化时初始化各类变量, 之后就不用了
        if self.loc_dict is None:
            self.__init_loc_dict()
            self.__init_prov2p_dict()
            self.__init_city2pc_dict()
            self.__init_dist2pc_dict()
            self.__init_school2pc_dict()

            self.__init_school2pc_AC()
            self.__init_city2pc_AC()
    
    def detect_by_city2pc_dict(self, tokens:str, tokens_nosuffix:str) -> List[Tuple[str, str]]:
        """
        查看tokens中每一个token是否在city2pc词典中, 返回所有的匹配
        """
        results = []
        for t in tokens:
            if self.city2pc_dict.get(t, False):
                results.append(self.city2pc_dict[t])
        if len(results) > 0:
            return results

        # 如果没检测出来就去掉后缀再找一次
        for t in tokens_nosuffix:
            if self.city2pc_dict_nosuffix.get(t, False):
                results.append(self.city2pc_dict_nosuffix[t])
        return results

    def detect_by_dist2pc_dict(self, tokens:str, tokens_nosuffix:str) -> List[Tuple[str, str]]:
        """
        查看tokens中每一个token是否在dist2pc词典中, 返回所有的匹配
        """
        results = []
        for t in tokens:
            if self.dist2pc_dict.get(t, False):
                results.extend(self.dist2pc_dict[t])
        if len(results) > 0:
            return results

        # 如果没检测出来就去掉后缀再找一次
        for t in tokens_nosuffix:
            if self.dist2pc_dict_nosuffix.get(t, False):
                results.extend(self.dist2pc_dict_nosuffix[t])
        return results

    def detect_by_school2pc_AC(self, text:str) -> List[Tuple[int, str, Tuple[str, str]]]:
        """
        用高校AC自动机检测句子中的高校名, 以推断地点, 返回所有匹配位置和对应[省, 市]
        """
        results = []
        for res in self.school2pc_AC.iter_long(text):
            results.append((res[0], res[1][0], res[1][1]))
            break
        return results

    def detect_by_city2pc_AC(self, text:str) -> List[Tuple[int, str, Tuple[str, str]]]:
        """
        用市级行政区AC自动机检测句子中的地名, 以推断地点, 返回所有匹配位置和对应[省, 市]
        """
        results = []
        for res in self.city2pc_AC.iter_long(text):
            results.append((res[0], res[1][0], res[1][1]))
        return results
    
    # remove_loc_suffix的一些辅助变量，只初始化一次
    __MINORS = ['壮族', '回族', '满族', '维吾尔', '苗族', '彝族', '土家', '藏族', '蒙古', '侗族', 
                '布依', '瑶族', '白族', '朝鲜', '哈尼', '黎族', '哈萨克', '傣族', '畲族', '傈僳', 
                '东乡', '仡佬', '拉祜', '佤族', '水族', '纳西', '羌族', '土族', '仫佬', '锡伯', 
                '柯尔克孜', '景颇', '达斡尔', '撒拉', '布朗', '毛南', '塔吉克', '普米', '阿昌', 
                '怒族', '鄂温克', '京族', '基诺', '德昂', '保安', '俄罗斯', '裕固', '乌孜别克', 
                '门巴', '鄂伦春', '独龙', '赫哲', '高山', '珞巴', '塔塔尔']  # 56个少数民族, 超过两个字的民族去掉"族"
    __LOC_SUFFIX = ["州", "省", '市', '县', '盟', '地区', '区',
                    "(?:(?:(?:[左右]翼)?[前中后左右])|(?:联合))?旗",
                    "(?:(?:{})族?){{0,4}}?自治[区州县旗]".format("|".join(["(?:{})".format(m) for m in __MINORS+["各"]]))]
    __RE_OBJ = re.compile("({})$".format("|".join(__LOC_SUFFIX)))

    @classmethod
    def remove_loc_suffix(cls, loc_str:str) -> str:
        """
        去除地名里的后缀, 返回无后缀的地名
        """
        loc_str_new = cls.__RE_OBJ.sub(repl="", string=loc_str, count=1)

        # 太短就不去后缀了
        if len(loc_str_new) < 2:    
            # 几千个行政区地名里内蒙古竟是如此的特别, 巧妙地与我们的规则冲突
            if loc_str == "内蒙古自治区":
                loc_str_new = "内蒙古"
            else:
                loc_str_new = loc_str

        return loc_str_new

    @classmethod
    def __init_loc_dict(cls, file_path:str=DATA_DIR+"/loc.json"):
        """
        加载loc.json中的数据到loc_dict
        """
        cls.loc_dict = {}
        with open(file_path, "r", encoding="utf-8") as f:
            loc_json = json.load(f)
        for prov, city_dict in loc_json.items():
            cls.loc_dict[prov] = {}
            for city, dist_dict in city_dict.items():
                city = prov if city in ['市辖区','县'] else city
                cls.loc_dict[prov][city] = list(dist_dict.keys())

    @classmethod
    def __init_prov2p_dict(cls):
        """
        加载省级行政区回查标准省名词典
        """
        cls.prov2p_dict:Dict[str, str] = {}
        for prov in cls.loc_dict.keys():
            cls.prov2p_dict[prov] = prov
            cls.prov2p_dict[cls.remove_loc_suffix(prov)] = prov

    @classmethod
    def __init_city2pc_dict(cls):
        """
        加载市级行政区回查[省,市]的词典（两个，一个有后缀一个无后缀）
        """
        cls.city2pc_dict:Dict[str, Tuple[str, str]] = {}    # 有后缀
        cls.city2pc_dict_nosuffix:Dict[str, Tuple[str, str]] = {}   # 无后缀

        for prov, city_dict in cls.loc_dict.items():
            for city, dist_list in city_dict.items():
                if '直辖县级行政区划' in city:
                    for dist in dist_list:
                        cls.city2pc_dict[dist] = (prov, dist)
                else:
                    cls.city2pc_dict[city] = (prov, city)
                    city_nosuffix = cls.remove_loc_suffix(city)
                    cls.city2pc_dict_nosuffix[city_nosuffix] = (prov, city)
    
    @classmethod
    def __init_dist2pc_dict(cls):
        """
        加载区县级行政区回查[省,市]的词典, 有部分区县级行政区在全国范围内重名, 因此dist2pc_dict的值是一个list包含了所有可能的省市
        """
        cls.dist2pc_dict:Dict[str, List[Tuple[str, str]]] = {}  # 有后缀
        cls.dist2pc_dict_nosuffix:Dict[str, List[Tuple[str, str]]] = {}  # 无后缀

        for prov, city_dict in cls.loc_dict.items():
            for city, dist_list in city_dict.items():
                if '直辖县级行政区划' in city:
                    continue
                for dist in dist_list:
                    if dist in ["郊区", "城区", "新城区", "矿区"]:
                        continue
                    # 插入有后缀词典
                    if cls.dist2pc_dict.get(dist, False):
                        cls.dist2pc_dict[dist].append((prov, city))
                    else:
                        cls.dist2pc_dict[dist] = [(prov, city), ]
                    # 插入无后缀词典
                    dist_nosuffix = cls.remove_loc_suffix(dist)
                    if cls.dist2pc_dict_nosuffix.get(dist_nosuffix, False):
                        cls.dist2pc_dict_nosuffix[dist_nosuffix].append((prov, city))
                    else:
                        cls.dist2pc_dict_nosuffix[dist_nosuffix] = [(prov, city), ]

    @classmethod
    def __init_school2pc_dict(cls):
        """
        加载高校名称回查[省, 市]的词典
        """
        cls.school2pc_dict:Dict[str, List[Tuple[str, str]]] = {}
        pugao_csv = np.loadtxt(DATA_DIR + "/全国普通高等学校名单_2021.csv", dtype=str, delimiter=",", encoding="utf-8")
        # supplement_csv = np.loadtxt(DATA_DIR + "/高校补充名单.csv", dtype=str, delimiter=",", encoding="utf-8")

        for school in pugao_csv:
            school_loc = None
            if cls.city2pc_dict.get(school[3], False):                                      # 先找市级
                school_loc = cls.city2pc_dict[school[3]]
            elif cls.city2pc_dict_nosuffix.get(cls.remove_loc_suffix(school[3]), False):      # 去掉后缀再找市级
                school_loc = cls.city2pc_dict_nosuffix[cls.remove_loc_suffix(school[3])]
            elif cls.dist2pc_dict.get(school[3], False):                                    # 没有再找区级
                ents = cls.dist2pc_dict[school[3]]
                for ent in ents:
                    if ent[0] in school[2]:
                        school_loc = ent
            elif cls.dist2pc_dict_nosuffix.get(cls.remove_loc_suffix(school[3]), False):      # 去掉后缀再找区级
                ents = cls.dist2pc_dict_nosuffix[cls.remove_loc_suffix(school[3])]
                for ent in ents:
                    if ent[0] in school[2]:
                        school_loc = ent
            
            if school_loc:
                for name in school[0].split("/"):
                    cls.school2pc_dict[name] = school_loc

    @classmethod
    def __init_school2pc_AC(cls):
        """
        初始化高校AC自动机
        """
        cls.school2pc_AC = ahocorasick.Automaton()
        for name, pc in cls.school2pc_dict.items():
            cls.school2pc_AC.add_word(name, (name, pc))
        cls.school2pc_AC.make_automaton()

    @classmethod
    def __init_city2pc_AC(cls):
        """
        初始化市级行政区AC自动机
        """
        cls.city2pc_AC = ahocorasick.Automaton()

        for city, pc in cls.city2pc_dict.items():
            cls.city2pc_AC.add_word(city, (city, pc))
        for city, pc in cls.city2pc_dict_nosuffix.items():
            cls.city2pc_AC.add_word(city, (city, pc))

        cls.city2pc_AC.make_automaton()