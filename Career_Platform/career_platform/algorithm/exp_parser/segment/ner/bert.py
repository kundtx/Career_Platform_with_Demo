import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
import pandas as pd
import numpy as np
import torch
from pytorch_transformers import BertTokenizer, BertModel
from ner.utils import prepocess_data_for_lstmcrf
from ner.parser import data_process, load_data
from pytorch_transformers import BertTokenizer, BertModel
import pickle
from tqdm import tqdm

model = BertModel.from_pretrained(os.path.join(os.path.dirname(__file__), 'ckpts/chinese_L-12_H-768_A-12'))
tokenizer = BertTokenizer.from_pretrained(os.path.join(os.path.dirname(__file__), 'ckpts/chinese_L-12_H-768_A-12'))

with open(os.path.join(os.path.dirname(__file__), 'ckpts/bert_model.pkl'), 'wb') as f:
    torch.save(model, f)
    # pickle.dump(model, f, pickle.HIGHEST_PROTOCOL)

with open(os.path.join(os.path.dirname(__file__), 'ckpts/bert_tokenizer.pkl'), 'wb') as f:
    torch.save(tokenizer, f)
    # pickle.dump(tokenizer, f, pickle.HIGHEST_PROTOCOL)

all_data_X, all_data_Y, Hidden_states, Vocabulary = data_process(load_data())
bert_of_char = {}

for words in tqdm(all_data_X, desc="tuning bert"):
    for char in words:
        if char not in bert_of_char:
            input_id = torch.tensor(tokenizer.encode(char)).unsqueeze(0)
            outputs = model(input_id)
            bert_vector = outputs[0]
            bert_vector = bert_vector.reshape(768).tolist()
            bert_of_char[char] = bert_vector

with open(os.path.join(os.path.dirname(__file__), 'ckpts/bert_of_char.pkl'), 'wb') as f:
    torch.save(bert_of_char, f)
    # pickle.dump(bert_of_char, f, pickle.HIGHEST_PROTOCOL)
