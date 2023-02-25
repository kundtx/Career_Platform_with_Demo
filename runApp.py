# -*- coding: utf-8 -*-
"""
@Time ： 2022/9/20 19:51
@Auth ： luchengyue@sz.tsinghua.edu.cn
@File ：runApp.py
@IDE ：PyCharm
@Motto：ABC(Always Be Coding)
"""

from Career_API import create_app

app = create_app()

app.run(host='0.0.0.0', port=2334)
