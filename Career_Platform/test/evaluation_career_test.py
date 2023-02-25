import datetime
import os, sys
import json
sys.path.append(os.path.join(os.path.dirname(__file__), "../"))

import career_platform as CP

# print("EvaluationService.syncData ====> ")
# ces = CP.persistent.service.EvaluationService()
# for eval in ces.syncData():
#     print(eval)


data=[]
evaluation = CP.common.Evaluation(uuid="88615C22-FB76-3A1D-8BE1-CAA2C369B045",
                        person_uuid="671430B6-8D28-3175-B87D-E81F2F5978C6",
                        text="爱读书、爱岗敬业,爱好广泛,爱好写诗,爱学习善钻研,爱憎分明,把好选人用人关,把控大局能力较强,把握工作主动性,把握全局能力较强,把握上级政策精准",
                        ordernum=1,
                        effective="1",
                        ismatch="1",
                        time_start=datetime.date(2012, 11, 16),
                        time_update=datetime.date(2022, 11, 16))
data.append(evaluation)
evaluation = CP.common.Evaluation(uuid="88615C22-FB76-3A1D-8BE1-CAA2C369B046",
                        person_uuid="671430B6-8D28-3175-B87D-E81F2F5978C6",
                        text="爱读书2、爱岗敬业2,爱好广泛2,爱好写诗2,爱学习善钻研2,爱憎分明,把好选人用人关,把控大局能力较强,把握工作主动性,把握全局能力较强,把握上级政策精准",
                        ordernum=2,
                        effective="1",
                        ismatch="1",
                        time_start=datetime.date(2021, 11, 17),
                        time_update=datetime.date(2022, 11, 17))
data.append(evaluation)

with open("E:\Repo\TBSI\Career_Platform\demo\sample_data\sample_data_evaluation.json", "r", encoding='utf-8') as f:
    sample_data = json.load(f)
for i in sample_data:
    data.append(CP.common.Evaluation(uuid=i["eval_uuid"], person_uuid=i["person_uuid"], text=i["eval_text"]))

print("save ============> ")
# save test
cem = CP.persistent.mapper.CareerDBEvaluationMapper()
size = cem.save(replace_by="id", eval_list=data)
print(size)

size = cem.save(replace_by="person_uuid", eval_list=data)
print(size)

print("getUpdateLastTime ============> ")
print(cem.getUpdateLastTime())

print("getById ============> ")
print(cem.getById(id="88615C22-FB76-3A1D-8BE1-CAA2C369B045"))

print("getByIdList ============> ")
res = cem.getByIdList(id_list=["88615C22-FB76-3A1D-8BE1-CAA2C369B045"])
for eval in res:
    print(eval)

print("getByPersonuuidList ============> ")
res = cem.getByPersonuuidList(person_uuid_list=["671430B6-8D28-3175-B87D-E81F2F5978C6"])
for eval in res:
    print(eval)

print("getByUpdatetime ============> ")
for eval in cem.getByUpdatetime(time_update=datetime.date(2022, 11, 17)):
    print(eval)

print("getAll ============> ")
for eval in cem.getAll():
    print(eval)

