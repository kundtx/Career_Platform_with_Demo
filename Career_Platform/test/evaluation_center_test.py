import datetime
import os, sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../"))

import career_platform as CP


# @scheduled_job('cron', id='syncEvaluationData', hour='22')
async def syncEvaluationData(self):
    """
    干部评价数据同步[Evaluation(数据中心表名：ods.ZSSR_A_GBPJ)]
    按更新时间进行的同步
    获取最新评价数据 DataCenter->Career_dev
    返回获取的最新评价数据
    本方法应用于 Career_API 工程，定时运行
    """
    # import Career_Platform.career_platform as CP
    dem = CP.persistent.mapper.DatacenterEvaluationMapper()
    cem = CP.persistent.mapper.CareerDBEvaluationMapper()

    data = dem.getByUpdatetime(cem.getUpdateLastTime())
    size = cem.save(replace_by="id", eva_list=data)
    print("syncData size ==> {}", size)

    return data


"""
以下为单元测试方法
"""

evaluation = CP.common.Evaluation(uuid="88615C22-FB76-3A1D-8BE1-CAA2C369B045",
                        person_uuid="671430B6-8D28-3175-B87D-E81F2F5978C6",
                        text="爱读书、爱岗敬业,爱好广泛,爱好写诗,爱学习善钻研,爱憎分明,把好选人用人关,把控大局能力较强,把握工作主动性,把握全局能力较强,把握上级政策精准",
                        ordernum=1,
                        effective="1",
                        ismatch="1",
                        time_start=datetime.date(2012, 12, 1))
#print(evaluation)

print("save ============> ")
# save test
cem = CP.persistent.mapper.DatacenterEvaluationMapper()
size = cem.save(replace_by="id", eval_list=[evaluation])
print(size)

size = cem.save(replace_by="person_uuid", eval_list=[evaluation])
print(size)

print("getById ============> ")
print(cem.getById(id="88615C22-FB76-3A1D-8BE1-CAA2C369B045"))

print("getAll ============> ")
for eval in cem.getAll():
    print(eval)

