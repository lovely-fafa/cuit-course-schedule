#!/usr/bin/python 3.8
# -*- coding: utf-8 -*- 
#
# @Time    : 2025-07-27 1:14
# @Author  : 阿发
# @Email   : fafa27182818@gmail.com
# @GitHub  : https://github.com/lovely-fafa
# @File    : 1_爬取.py
# @Software: PyCharm

import re
from copy import deepcopy
from pathlib import Path

import feapder
from feapder import Response

from feapder_utils import progress, get_s_from_xpath_selector
from cookies import cookies


class Main(feapder.AirSpider):
    __custom_setting__ = dict(
        LOG_LEVEL='INFO',
        PLAYWRIGHT=dict(
            user_agent=None,  # 字符串 或 无参函数，返回值为user_agent
            proxy=None,  # xxx.xxx.xxx.xxx:xxxx 或 无参函数，返回值为代理地址
            headless=True,  # 是否为无头浏览器
            driver_type="chromium",  # chromium、firefox、webkit
            timeout=30,  # 请求超时时间
            window_size=(1024, 800),  # 窗口大小
            executable_path=None,  # 浏览器路径，默认为默认路径
            download_path=None,  # 下载文件的路径
            render_time=0.5,  # 渲染时长，即打开网页等待指定时间后再获取源码
            wait_until="networkidle",  # 等待页面加载完成的事件,可选值："commit", "domcontentloaded", "load", "networkidle"
            use_stealth_js=False,  # 使用stealth.min.js隐藏浏览器特征
            page_on_event_callback=None,
            # page.on() 事件的回调 如 page_on_event_callback={"dialog": lambda dialog: dialog.accept()}
            storage_state_path=None,  # 保存浏览器状态的路径
            url_regexes=None,  # 拦截接口，支持正则，数组类型
            save_all=False,  # 是否保存所有拦截的接口, 配合url_regexes使用，为False时只保存最后一次拦截的接口
        ),
        RENDER_DOWNLOADER="feapder.network.downloader.PlaywrightDownloader",

    )

    def __init__(self, thread_count=None):
        super().__init__(thread_count)
        self.html = Path('html')

    def start_requests(self):

        for semester_id, semester_name in zip(['905', '906'], ['2024-2025学年2学期', '2025-2026学年1学期']):
            progress.add_task()
            yield feapder.Request(
                'http://jwgl-cuit-edu-cn.webvpn.cuit.edu.cn:8118/eams/courseTableSecondForStd.action',
                params={
                    "sf_request_type": "ajax"
                },
                data={
                    "courseTableType": "class",
                    "project.id": "1",
                    "semester.id": semester_id
                },
                semester_name=semester_name,
                semester_id=semester_id
            )

    def download_midware(self, request):
        request.headers = {
            "Accept": "*/*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": "http://jwgl-cuit-edu-cn.webvpn.cuit.edu.cn:8118",
            "Pragma": "no-cache",
            "$Referer": "http://jwgl-cuit-edu-cn.webvpn.cuit.edu.cn:8118/eams/courseTableSecondForStd\\u0021search.action?semester.id=904&courseTableType=class&enabled=1&pageNo=1&pageSize=100",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest"
        }
        request.cookies = cookies

    def validate(self, request, response):
        if response.status_code != 200:
            raise Exception(f'校验不通过 | callback={request.callback} url={request.url} text={response.text[:100]}')

    def parse(self, request, response):
        semester_name = request.semester_name
        semester_id = request.semester_id
        for college_item in response.xpath('.//*[@name="departmentId"]/option'):
            college_name = college_item.xpath('./text()').extract_first()
            if not college_name:
                continue
            progress.add_task()
            yield feapder.Request(
                url="http://jwgl-cuit-edu-cn.webvpn.cuit.edu.cn:8118/eams/courseTableSecondForStd!search.action",
                params={
                    "sf_request_type": "ajax"
                },
                data={
                    "adminclass.project.id": "1",
                    "adminclass.code": "",
                    "adminclass.name": "",
                    "adminclass.campus.id": "",
                    "adminclass.grade": "",
                    "adminclass.education.id": "",
                    "adminclass.stdType.id": "",
                    "departmentId": college_item.xpath('./@value').extract_first(),
                    "majorId": "",
                    "directionId": "",
                    "enabled": "1",
                    "semester.id": semester_id,
                    "courseTableType": "class",
                    "pageNo": "1",
                    "pageSize": "100"
                },
                semester_name=semester_name,
                semester_id=semester_id,
                is_first_request=True,
                college_name=college_name,
                callback=self.parse_page_query
            )

    def parse_page_query(self, request, response):
        semester_name = request.semester_name
        semester_id = request.semester_id
        match = re.search(r'pageInfo\(\d+,100,(.*?)\);', response.text)
        if not match:
            print(request.to_dict, response.text)
            return
        total = eval(match.group(1))
        if total == 0:
            return
        if hasattr(request, 'is_first_request'):
            for page in range(2, int(total / 100) + 2):
                data = deepcopy(request.data)
                data['pageNo'] = page
                progress.add_task()
                yield feapder.Request(
                    request.url,
                    data=data,
                    params=request.params,
                    semester_id=semester_id,
                    semester_name=semester_name,
                    college_name=request.college_name,
                    callback=self.parse_page_query,
                )
        trs = response.xpath('//*[@class="gridtable"]/tbody/tr')
        for tr in trs:
            tds = [get_s_from_xpath_selector(td.xpath('.//text()')) for td in tr.xpath('./td')]
            college = tds[6]
            if college in ['物流学院', '管理学院', '文化艺术学院', '统计学院']:
                college = f'龙泉_{college}'
            else:
                college = f'航空港_{college}'
            file_path = self.html / semester_name / college / f'{tds[3]}_{tds[2]}.html'
            if file_path.exists():
                continue
            file_path.parent.mkdir(parents=True, exist_ok=True)
            progress.add_task()
            yield feapder.Request(
                tr.xpath('.//a/@href').extract_first(),
                file_path=file_path,
                callback=self.parse_page,
                render=True
            )

    def parse_page(self, request, response: Response):
        response.make_absolute_links = True
        with open(request.file_path, encoding='utf-8', mode='w') as f:
            f.write(response.text)


if __name__ == '__main__':
    Main(thread_count=4).start()
