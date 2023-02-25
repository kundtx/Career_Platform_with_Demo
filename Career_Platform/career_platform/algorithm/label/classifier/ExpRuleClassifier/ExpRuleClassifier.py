import re
import json
from graphviz import Digraph
import os

LABEL_DIR = os.path.realpath(os.path.dirname(__file__))

class ExpRuleClassifier():
    def __init__(self, rule_label_path=LABEL_DIR+'/config/rule_label.json', hybrid_label_path=LABEL_DIR+'/config/hybrid_rule_label.json'):
        f = open(rule_label_path,encoding='utf-8')
        self.label_dic = json.load(f)
        f.close()
        self.groupkeys = list(self.label_dic.keys())
        f = open(hybrid_label_path,encoding='utf-8')
        self.hylabel_dic = json.load(f)
        f.close()
        self.hybridkeys = list(self.hylabel_dic.keys())
        self.hybrid_dict = {}
        for label in self.hybridkeys:
            self.hybrid_dict[label] = False
        self.ltree = logictree()
        
    def classify(self,text,Hybrid=True):
        if text is None:
            return None
        final = {}
        for groupname in self.groupkeys:
            res = self.groupclassify(groupname,text)
            final = {**final,**res}
        if Hybrid:
            final = {**final,**self.hybrid_dict}
            pre_dict_state = final
            self.ltree.update_basicdict(final)
            while True:
                final = self.addhybridlabel(final)
                if final == pre_dict_state:
                    break
                pre_dict_state = final
        final = [key for key in final.keys() if final[key]==True]
        return final
    
    def groupclassify(self,groupname,text,f=1):
        jsondict = self.label_dic
        group = jsondict[groupname]
        innerkeys = list(group.keys())
        addition = innerkeys[3:]
        
        result = {group['default']:False}
        for label in addition:
            result[label] = False
        
        if f==1:
            f = self.method1
        elif f==2:
            f = self.method2
        flag = f(text,group['isexist'])
        if f(text,group['remove']):
            flag = False
        if flag:
            for label in addition:
                temp = group[label]
                if f(text,temp):
                    result[label] = True
                    if result.get('')!=None:
                        del result['']
                    return result
            result[group['default']] = True
        if result.get('')!=None:
            del result['']
        return result
    
    def hybridclassify(self,labelname):
        jsondict = self.hylabel_dic[labelname]
        self.ltree(jsondict['tree'])
        value = self.ltree.getvalue()
        expect = jsondict['expect']
        if expect == 'any':
            return {labelname:value}
        if value == expect:
            return {labelname:expect}
        else:
            return {}
    
    def addhybridlabel(self,result_dict):
        for labelname in self.hybridkeys:
            # print(labelname, result_dict)
            res = self.hybridclassify(labelname)
            result_dict = {**result_dict, **res}
            self.ltree.update_basicdict(result_dict)
        return result_dict
    '''存在性判断'''
    def method1(self,text,D):
        for item in D['keyword']:
            if item in text:
                return True
        for reg in D['regular']:
            if re.search(reg,text) != None:
                return True
        return False
    '''任意性判断'''
    def method2(self,text,D):
        for item in D['keyword']:
            if item not in text:
                return False
        return True
    '''简单的Hybrid Label生成法'''
    def method3(self,text,L,n=2):
        count = 0
        for item in L:
            if item in text:
                count += 1
                if count>=n:
                    return True
        return False


class logictree():
    def __init__(self,ltree={},result_dict={}):
        self.tree = ltree
        self.result_dict = result_dict
    def __call__(self,ltree):
        self.tree = ltree
    def update_basicdict(self,resD):
        self.result_dict = resD
        
    def getvalue(self,nodeid='0'):
        # print(nodeid)
        # node_id:[activation,input_id_list(or a label),output_reverse,logic(and,or,None)]
        node = self.tree[nodeid]
        if node[2] == False:
            f = lambda x:x
        else:
            f = lambda x:(not x)
        if node[3]==None: # indicates this is a leaf node/ label node
            return f(self.result_dict.get(node[1],False))
        if node[3]=='and':
            for id in node[1]:
                if self.getvalue(str(id))==False:
                    return f(False)
            return f(True)
        if node[3]=='or':
            for id in node[1]:
                if self.getvalue(str(id))==True:
                    return f(True)
            return f(False)
        return None
    def show(self):
        g = Digraph(name='logic tree',format="png")
        #g.attr('node',shape='doublecircle')
        for id in self.tree.keys():
            node = self.tree[str(id)]
            if node[3]==None:
                g.node(name=str(id),label=node[1],fontname="Microsoft YaHei")
            else:
                g.node(name=str(id),label=node[3],fontname="Microsoft YaHei")
        #g.attr('node', shape='circle')
        for outid in self.tree.keys():
            if self.tree[outid][3] == None:
                continue
            for inid in self.tree[outid][1]:
                cl = 'green' if self.tree[str(inid)][2]==False else 'red'
                g.edge(str(inid),str(outid),color=cl)
        g.node(name='output',fontname="Microsoft YaHei")
        cl = 'green' if self.tree['0'][2]==False else 'red'
        g.edge('0','output',color=cl)
        # g.view()
        return g
    
    def tree2exp(self,dictname='result_dict',nodeid='0'):
        # node_id:[activation,input_id_list(or a label),output_reverse,logic(and,or,None)]
        node = self.tree[nodeid]
        if node[2] == False:
            f = lambda x:x
        else:
            f = lambda x:('(not '+x+')')
        if node[3]==None:
            exp = dictname+'["'+node[1]+'"]'
            return f(exp)
        unit = [self.tree2exp(dictname,str(id)) for id in node[1]]
        exp = (' '+node[3]+' ').join(unit)
        exp = '('+exp+')'
        return f(exp)
    
    def exp2tree(self,expression):
        print('Warning:请合理使用小括号，同一小括号内，and、or、not三类关键字仅出现其中一类；not运算符请贴近底层条件')
        print('正确实例 ：("教育" and (not "科技") and ("经济" or "行政"))')
        print('错误示例1：("教育" and not "科技" and ("经济" or "行政"))')
        print('错误示例2：("教育" and (not "科技") and (("经济" or "行政")))')
        if not expression.startswith('('):
            expression = '('+expression+')'
        Llist = []
        grade,maxgrade = 0,0
        allnode = []
        for i,ch in enumerate(expression):
            if ch=='(':
                Llist.append(i)
                grade += 1
            elif ch==')':
                maxgrade = max(grade,maxgrade)
                allnode.append([grade,expression[Llist.pop():i+1]])
                grade -= 1
        allnode.reverse()
        # allnode get, now depth tree
        depthtree = {}
        for i in range(1,maxgrade+1):
            depthtree[str(i)] = []
        for i,node in enumerate(allnode):
            depthtree[str(node[0])].append([i,[],node[1]])
        # depthtree
        for dep in range(1,maxgrade):
            for par in depthtree[str(dep)]:
                for chi in depthtree[str(dep+1)]:
                    if chi[2] in par[2]:
                        par[1].append(chi[0])
                        par[2] = par[2].replace(chi[2],'',1)             
        # Real tree
        nodelist = []
        for L in depthtree.values():
            nodelist.extend(L)
        nodenum = len(nodelist)
        tree = {}
        for node in nodelist:
            node[2] = node[2][1:-1]
            parsed = node[2].split()
            notflag = False
            for operator in ['and','or']:
                if operator in parsed:
                    logic = operator
                    childL = node[2].split(' '+operator+' ')
            if 'not' in parsed:
                logic = 'None'
                notflag = True
                childL = node[2].split('not ')
            childL = [item.strip() for item in childL]
            childL = list(set(childL))
            if '' in childL:
                childL.remove('')
            if notflag == True:
                tree[str(node[0])] = [True,childL[0],notflag,None]
                continue
            tree[str(node[0])] = [True,node[1],notflag,logic]
            for source in childL:
                tree[str(node[0])][1].append(nodenum)
                tree[str(nodenum)] = [True,source,notflag,None]
                nodenum += 1
        return tree
    
    def exp2tree2(self,expression):
        # 1.Preprocessing
        expression = re.sub('[ ]+',' ',expression)
        expression = re.sub('\(','（',expression)
        expression = re.sub('\)','）',expression)
        if not expression.startswith('（'):
            expression = '（'+expression+'）'
        # 2.global var
        tree = {}
        current_id = 99
        pattern = re.compile('[\u4e00-\u9fff]+')
        leaf_list = pattern.findall(expression)
        # 3.find leaf nodes in the tree
        for ind,label in enumerate(leaf_list):
            if 'not '+label in expression:
                tree[str(current_id)] = [True,label,True,None]
                expression = re.sub('（'+' *'+'not '+label+' *'+'）',str(current_id),expression)
                expression = re.sub('not '+label,str(current_id),expression)
                current_id -= 1
            if label in expression:
                tree[str(current_id)] = [True,label,False,None]
                expression = re.sub(label,str(current_id),expression)
                current_id -= 1
        print(tree,'\n')
        #print(expression)
        # 4.
        while True:
            allnode = []
            L = []
            for i,ch in enumerate(expression):
                if ch=='（':
                    L.append(i)
                elif ch=='）':
                    allnode.append(expression[L.pop():i+1])
            #print('expression:',expression)
            #print('allnode:',allnode)
            if len(allnode) == 0:# to deal with exp like '(not (…))'
                break
            subexp = allnode[0]
            subexpL = list(set(subexp[1:-1].split()))
            #print('subexp,subexpL:',subexp,subexpL)
            if 'or' in subexpL:
                logic = 'or'
            elif 'and' in subexpL:
                logic = 'and'
            #print(logic)
            subexpL.remove(logic)
            if 'not '+subexp in expression:
                tree[str(current_id)] = [True,[eval(x) for x in subexpL],True,logic]
                expression = re.sub('（'+' *'+'not '+subexp+' *'+'）',str(current_id),expression)
                expression = re.sub('not '+subexp,str(current_id),expression)
            else:
                tree[str(current_id)] = [True,[eval(x) for x in subexpL],False,logic]
                expression = re.sub(subexp,str(current_id),expression)
            current_id -= 1
            #print('tree:',tree,'\n')
            if len(allnode) == 1:
                break
        key = min([eval(key) for key in tree.keys()])
        tree['0'] = tree[str(key)]
        tree.pop(str(key))
        return tree