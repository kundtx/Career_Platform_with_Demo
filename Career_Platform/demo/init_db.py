import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import career_platform as CP

# 初始化CAREER数据库
CP.persistent.init_CareerDB()