# coding=utf-8
# from __init__ import *
import signal
import time
import inspect
import ctypes
import logging
from functools import wraps


def count_down(duration):
    '''
    闹钟-倒计时
    :param duration: 时长 单位秒
    :return:
    '''

    def wrapper(func):
        def inner(*args, **kwargs):
            global res
            start = time.time()
            while time.time() - start < duration:
                res = func(*args, **kwargs)
            return res

        return inner

    return wrapper


def set_timeout(num, callback=''):
    def wrap(func):
        def handle(signum, frame):  # 收到信号 SIGALRM 后的回调函数，第一个参数是信号的数字，第二个参数是the interrupted stack frame.
            # signal.alarm(1)
            raise RuntimeError

        @wraps(func)
        def to_do(self, *args, **kwargs):
            try:
                signal.signal(signal.SIGALRM, handle)  # 设置信号和回调函数
                signal.alarm(num)  # 设置 num 秒的闹钟
                r = func(self, *args, **kwargs)
                signal.alarm(0)  # 关闭闹钟
                return r
            except RuntimeError as e:
                if callback:
                    callback(self)

        return to_do

    return wrap


def _async_raise(tid, exctype):
    """raises the exception, performs cleanup if needed"""
    logging.debug('try to stop thread')
    tid = ctypes.c_long(tid)
    if not inspect.isclass(exctype):
        exctype = type(exctype)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
    if res == 0:
        raise ValueError("invalid thread id")
    elif res != 1:
        # """if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect"""
        ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
        raise SystemError("PyThreadState_SetAsyncExc failed")


def stop_thread(thread):
    '''
    停止进程
    :param thread:
    :return:
    '''
    _async_raise(thread.ident, SystemExit)


def singleton(cls):
    '''
    单例
    :param cls:
    :return:
    '''
    _instance = {}

    def _singleton(*args, **kargs):
        if cls not in _instance:
            _instance[cls] = cls(*args, **kargs)
        return _instance[cls]

    return _singleton


def lazy_proerty(func):
    attr_name = '_lazy_' + func.__name__

    @property
    def _lazy_proerty(self):
        if not hasattr(self, attr_name):
            setattr(self, attr_name, func(self))
        return getattr(self, attr_name)

    return _lazy_proerty
