#!/usr/bin/python 3.10
# -*- coding: utf-8 -*- 
#
# @Time    : 2024/02/13 0:24
# @Author  : 阿发
# @File    : process.py
# @Software: PyCharm

from time import time

from feapder.network.selector import Selector
from feapder import Request, Response
from feapder.utils.log import log
from tqdm import tqdm


class Progress(object):
    TOTAL_AMOUNT = 0
    FINISH_AMOUNT = 0
    LAST_LOG_TIME = time()
    START_TIME = time()

    def add_task(self):
        self.TOTAL_AMOUNT += 1

    def add_tasks(self, task_amount: int):
        self.TOTAL_AMOUNT += task_amount

    def finish_task(self):
        self.FINISH_AMOUNT += 1
        now = time()
        if self.TOTAL_AMOUNT != 0 and now - self.LAST_LOG_TIME > 3:
            self.__log_progress(now - self.START_TIME)
            self.LAST_LOG_TIME = time()

    def __log_progress(self, consume):
        rate = round(self.FINISH_AMOUNT / self.TOTAL_AMOUNT * 100, 4)
        amount = f'{self.FINISH_AMOUNT}/{self.TOTAL_AMOUNT}'
        pre_time = (self.TOTAL_AMOUNT - self.FINISH_AMOUNT) * (consume / self.FINISH_AMOUNT)
        ti = f'{tqdm.format_interval(consume)}<{tqdm.format_interval(pre_time)}'
        log.info(f'{rate}% | {amount} | [{ti}]')


progress = Progress()
Request.__del__ = progress.finish_task


def download_file(request_or_filepath, response: Response):
    if isinstance(request_or_filepath, Request):
        file_path = request_or_filepath.file_path
    else:
        file_path = request_or_filepath
    with open(file_path, mode='wb') as f:
        f.write(response.content)


def get_s_from_xpath_selector(ele: Selector, sep: str = '') -> str:
    return sep.join([i.strip() for i in ele.extract() if i.strip()])
