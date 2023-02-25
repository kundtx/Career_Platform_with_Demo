from re import L
import torch
import torch.nn as nn
from torch.nn.utils.rnn import pad_packed_sequence, pack_padded_sequence
from .config import LSTMConfig

class BiLSTM(nn.Module):
    def __init__(self, vocab_size, emb_size, hidden_size, out_size, weight):
        """初始化参数：
            vocab_size:字典的大小
            emb_size:词向量的维数
            hidden_size：隐向量的维数
            out_size:标注的种类
        """
        super(BiLSTM, self).__init__()
        # 采用 bert 预训练的 embedding
        if (LSTMConfig.bert_pre_trained == True):
            self.embedding_1 = nn.Embedding.from_pretrained(weight) # weight: [vocab_size, 768] 768是bert的默认维度
            self.embedding_2 = nn.Embedding(vocab_size, emb_size)
            self.red = nn.Linear(768, emb_size)
        else:
            self.embedding = nn.Embedding(vocab_size, emb_size)
        self.dropout = nn.Dropout(p = 0.2)
        self.bilstm = nn.LSTM(emb_size, hidden_size,
                              batch_first=True,
                              bidirectional=True)

        self.lin = nn.Linear(2*hidden_size, out_size)

    # sents_tensor [B, L] nn.embedding 把 sents_tensor[i][j] 对应的 word 映射到一个 emb_size 的向量
    def forward(self, sents_tensor, lengths):
        if (LSTMConfig.bert_pre_trained == True):
            emb_1 = self.embedding_1(sents_tensor)
            emb_2 = self.embedding_2(sents_tensor)
            ber = self.red(emb_1)
            emb = emb_2 + ber
        else:
            emb = self.embedding(sents_tensor)  # [B, L, emb_size]   L: 最长的序列长度 ?
        # 可以在 emb 层修改载入预训练的 word2vec 比如说加上？
        emb = self.dropout(emb)
        packed = pack_padded_sequence(emb, lengths, batch_first=True)
        rnn_out, _ = self.bilstm(packed)
        # rnn_out:[B, L, hidden_size*2]
        rnn_out, _ = pad_packed_sequence(rnn_out, batch_first=True)

        scores = self.lin(rnn_out)  # [B, L, out_size]

        return scores

    def test(self, sents_tensor, lengths, _):
        """第三个参数不会用到，加它是为了与BiLSTM_CRF保持同样的接口"""
        logits = self.forward(sents_tensor, lengths)  # [B, L, out_size]
        _, batch_tagids = torch.max(logits, dim=2)

        return batch_tagids   # [B, L] ?


class Bert_BiLSTM(BiLSTM): # pre-trained bert-base-chinese instead of nn.Embedding(vocab_size, emb_size)
    def __init__(self, vocab_size, emb_size, hidden_size, out_size):
        """初始化参数：
            vocab_size:字典的大小
            emb_size:词向量的维数
            hidden_size：隐向量的维数
            out_size:标注的种类
        """
        super(Bert_BiLSTM, self).__init__(vocab_size, emb_size, hidden_size, out_size)
        self.embedding = nn.Embedding(vocab_size, emb_size)

    def forward(self, sents_tensor, lengths):   # 这里加 pre_trained_weight
        emb = self.embedding(sents_tensor)  # [B, L, emb_size]

        packed = pack_padded_sequence(emb, lengths, batch_first=True)
        rnn_out, _ = self.bilstm(packed)
        # rnn_out:[B, L, hidden_size*2]
        rnn_out, _ = pad_packed_sequence(rnn_out, batch_first=True)

        scores = self.lin(rnn_out)  # [B, L, out_size]

        return scores

    def test(self, sents_tensor, lengths, _):
        """第三个参数不会用到，加它是为了与BiLSTM_CRF保持同样的接口"""
        logits = self.forward(sents_tensor, lengths)  # [B, L, out_size]
        _, batch_tagids = torch.max(logits, dim=2)

        return batch_tagids
