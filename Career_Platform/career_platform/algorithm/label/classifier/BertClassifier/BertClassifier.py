import os, sys
from .process_data import SpanClDataset
from torch.utils.data import DataLoader
import torch
import numpy as np
import tqdm
from typing import List
location = os.path.abspath(os.path.dirname(__file__))
sys.path.append(location)


class BertClassifier():
    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model_path = os.path.join(os.path.dirname(__file__), "model/model_Albert.pkl")
        self.batch_size = 100
        self.label_map = ['教育','财务','文化旅游','科技','国防军事','交通','政法','政法','纪检监察','卫生','环境','学生']
        # self.label_map_old = ['教育','财务','文化','技术','军队军工','交通运输','公安消防','法律','监督检查','医疗','环境','学生']

    def get_predict(self,output):
            output = output.detach().cpu().numpy()
            predict = np.zeros((output.shape[0],12))
            for i in range(len(output)):
                threshold = 0
                for col in range(len(output[i])):
                    if output[i,col] > threshold:
                        predict[i,col] = 1
            return torch.Tensor(predict).to(self.device)

    def dev(self,model,dev_loader):
        model.eval()
        predicts = []
        with torch.no_grad():
            if len(dev_loader)>5:
                dev_loader = tqdm.tqdm(dev_loader, desc="Bert Predict")
            for (indextokens_a, input_mask_a, indextokens_b, input_mask_b, label) in dev_loader:
                indextokens_a, input_mask_a = indextokens_a.to(self.device), input_mask_a.to(self.device)
                indextokens_b, input_mask_b, label = indextokens_b.to(self.device), input_mask_b.to(self.device), label.to(self.device)
                out_put = model(indextokens_a,input_mask_a,indextokens_b,input_mask_b)
                predict = self.get_predict(out_put)
                predict = predict.detach().cpu().numpy()
                predicts.append(predict)

            return predicts

    def get_result(self,li):
            result = []
            for i in li:
                result1 = []
                for j in range(12):
                    if i[j] == 1:
                        result1  = result1 + [self.label_map[j]]
                result.append(result1)
            return result

    def classify(self, data:List[str]) -> List[str]:
        output = []
        result = {}
        test_data = SpanClDataset(data)
        data_1 = test_data.data_list
        test_loader = DataLoader(dataset=test_data, batch_size=self.batch_size, shuffle=False)
        path = self.model_path
        model1 = torch.load(path,map_location="cpu").to(self.device)
        predicts = self.dev(model1,test_loader)
        predict_final = []
        for i in predicts:
            predict_final = predict_final + i.tolist()
        result = self.get_result(predict_final)
        for i in range(len(data_1)):
            output.append(result[i])
        return output