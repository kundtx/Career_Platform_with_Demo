from torch.utils.data import DataLoader,Dataset
from transformers import BertModel,BertTokenizer,AutoTokenizer
from allennlp.data.dataset_readers.dataset_utils import enumerate_spans
import torch
from tqdm import tqdm
import time
import pandas as pd
import os
 
class SpanClDataset(Dataset):
    def __init__(self,filename,repeat=1):
        self.max_sentence_length = 128
        self.max_spans_num = len(enumerate_spans(range(self.max_sentence_length),max_span_width=3))
        self.repeat = repeat
        self.tokenizer = AutoTokenizer.from_pretrained(pretrained_model_name_or_path=os.path.join(os.path.dirname(__file__),"albert_model"))# this is where bert come from
        # self.tokenizer = BertTokenizer.from_pretrained(pretrained_model_name_or_path='Bert_model')
        self.data_list = self.read_file(filename)# this is where the read file method works
        self.len = len(self.data_list)
        self.process_data_list = self.process_data()
        
 
    def convert_into_indextokens_and_segment_id(self,text):
        tokeniz_text = self.tokenizer.tokenize(text)
        indextokens = self.tokenizer.convert_tokens_to_ids(tokeniz_text)
        input_mask = [1] * len(indextokens)
 
        pad_indextokens = [0]*(self.max_sentence_length-len(indextokens))
        indextokens.extend(pad_indextokens)
        input_mask_pad = [0]*(self.max_sentence_length-len(input_mask))
        input_mask.extend(input_mask_pad)
 
        segment_id = [0]*self.max_sentence_length
        return indextokens,segment_id,input_mask

 
    def read_file(self,data):# this is a read file method this will output different data respect to different classifiers.
        def eliminate_the_letter(string):
            eliminating_string = ['P','O','S','L','U',' ','\t','1','2','3','4','5','6','7','8','9','0','\n']
            new_string = ''
            for i in string:
                if i not in eliminating_string:
                    new_string = new_string + i
            return new_string 
        li_final = []
        for i in data:
            li_final.append((eliminate_the_letter(i)," ",[0 for _ in range(12)]))
        return li_final


    def process_data(self):
        process_data_list = []
        for ele in self.data_list:
            res = self.do_process_data(ele)
            process_data_list.append(res)
        return process_data_list

 
    def do_process_data(self,params):
 
        res = []
        sentence_a = params[0]
        sentence_b = params[1]
        label = params[2]
 
        indextokens_a,segment_id_a,input_mask_a = self.convert_into_indextokens_and_segment_id(sentence_a)
        indextokens_a = torch.tensor(indextokens_a,dtype=torch.long)
        segment_id_a = torch.tensor(segment_id_a,dtype=torch.long)
        input_mask_a = torch.tensor(input_mask_a,dtype=torch.long)
 
        indextokens_b, segment_id_b, input_mask_b = self.convert_into_indextokens_and_segment_id(sentence_b)
        indextokens_b = torch.tensor(indextokens_b, dtype=torch.long)
        segment_id_b = torch.tensor(segment_id_b, dtype=torch.long)
        input_mask_b = torch.tensor(input_mask_b, dtype=torch.long)
 
        label = torch.FloatTensor(label)
 
        res.append(indextokens_a)
        res.append(segment_id_a)
        res.append(input_mask_a)
 
 
        res.append(indextokens_b)
        res.append(segment_id_b)
        res.append(input_mask_b)
 
 
        res.append(label)
 
        return res
    
    def __getitem__(self, i):
        item = i
 
        indextokens_a = self.process_data_list[item][0]
        segment_id_a = self.process_data_list[item][1]
        input_mask_a = self.process_data_list[item][2]
 
 
 
        indextokens_b = self.process_data_list[item][3]
        segment_id_b = self.process_data_list[item][4]
        input_mask_b = self.process_data_list[item][5]
 
 
        label = self.process_data_list[item][6]
 
 
        return indextokens_a,input_mask_a,indextokens_b,input_mask_b,label
 
    def __len__(self):
        if self.repeat == None:
            data_len = 10000000
        else:
            data_len = len(self.process_data_list)
        return data_len
 
