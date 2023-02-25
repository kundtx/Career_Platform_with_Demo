import datetime
import os, sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../career_platform"))

import career_platform as CP

"""
以下为单元测试方法
"""

cem = CP.persistent.mapper.CareerDBRelativeMapper()

print("getUpdateLastTime =======>", cem.getUpdateLastTime())
print("updateRelativeUuid ======>", cem.updateRelativeUuid())

ced = CP.persistent.mapper.DatacenterRelativeMapper()
print("getByUpdatetime ============> ")

relas = ced.getByUpdatetime(time_update=datetime.date(2022, 11, 17))
cem.save(Relative_list=relas)
for rela in relas:
    print(rela)
