# -*- coding: utf-8 -*-
"""
@Time ： 2022/9/20 19:52
@Auth ： luchengyue@sz.tsinghua.edu.cn
@File ：utils.py
@IDE ：PyCharm
@Motto：ABC(Always Be Coding)
"""
import pytz
import traceback
from functools import wraps
from quart.utils import run_sync
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from typing import Any, List, Dict, Tuple, Union, Callable, Awaitable

LOCK_OCTREE = None

# APSCHEDULER_CONFIG: Dict[str, Any] = {'apscheduler.timezone': 'Asia/Shanghai'}
# scheduler = AsyncIOScheduler()


def replace_seg(seg):
    seg = seg.replace('L', '').replace('S', '').replace('P', '').replace('O', '').replace(' ', '')
    return seg


def check_contain_chinese(check_str):
    for ch in check_str:
        if u'\u4e00' <= ch <= u'\u9fff':
            return True
    return False


# def scheduled_job(*args, **kwargs) -> Callable:
#     kwargs.setdefault('timezone', pytz.timezone('Asia/Shanghai'))
#     kwargs.setdefault('misfire_grace_time', 60)
#     kwargs.setdefault('coalesce', True)

#     def deco(func: Callable[[], Any]) -> Callable:
#         @wraps(func)
#         async def wrapper():
#             try:
#                 print(f'Scheduled job {func.__name__} start.')
#                 ret = await func()
#                 print(f'Scheduled job {func.__name__} completed.')
#                 return ret
#             except Exception as e:
#                 print(traceback.format_exc())

#         return scheduler.scheduled_job(*args, **kwargs)(wrapper)

#     return deco
