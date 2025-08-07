#!/usr/bin/python 3.8
# -*- coding: utf-8 -*- 
#
# @Time    : 2025-08-07 3:06
# @Author  : 阿发
# @Email   : fafa27182818@gmail.com
# @GitHub  : https://github.com/lovely-fafa
# @File    : 5_页码.py
# @Software: PyCharm

from tqdm import tqdm
import fitz
import os

def add_page_numbers(
    input_pdf: str,
    output_pdf: str,
    start_page: int = 1,
    fontfile: str = r"C:\Windows\Fonts\simsun.ttc",
    fontsize: int = 12,
    x_offset: float = 120,
    y_offset: float = 30,
):
    """
    为 PDF 添加页码：第 x 页 共 y 页

    参数：
      input_pdf  - 输入 PDF 路径
      output_pdf - 输出 PDF 路径
      start_page - 从第几页开始添加页码（1 为首页）
      fontfile   - 字体文件路径，用于显示中文
      fontsize   - 字号
      x_offset   - 距页面右侧的水平偏移（pt）
      y_offset   - 距页面底部的垂直偏移（pt）
    """
    if not os.path.isfile(input_pdf):
        raise FileNotFoundError(f"找不到输入文件：{input_pdf}")

    doc = fitz.open(input_pdf)
    total_pages = doc.page_count
    # 有效页数 = 总页数 - (start_page - 1)
    numbered_pages = total_pages - (start_page - 1)
    if numbered_pages <= 0:
        raise ValueError(f"start_page={start_page} 超出文档总页数 {total_pages}")

    # 遍历要添加页码的每一页
    for idx in tqdm(range(start_page - 1, total_pages)):
        page = doc[idx]
        # 插入外部字体（一次即可，但多次插入也不会重复）
        page.insert_font(fontname="CustomFont", fontfile=fontfile)

        # 计算当前页码
        current = idx - (start_page - 1) + 1
        text = f"第{current}页 共{numbered_pages}页"

        # 页面尺寸
        rect = page.rect
        # 文字位置：右下角偏移
        x = rect.width - x_offset
        y = rect.height - y_offset

        page.insert_text(
            (x, y),
            text,
            fontname="CustomFont",
            fontsize=fontsize,
            color=(0, 0, 0),
            rotate=0,
            render_mode=0,  # 填充模式
        )

    # 保存并压缩（可选）
    doc.save(output_pdf, garbage=4, deflate=True)
    doc.close()
    print(f"✅ 已完成页码添加：从第 {start_page} 页开始，共 {numbered_pages} 页，输出到 {output_pdf}")


if __name__ == "__main__":
    add_page_numbers(
        '合并.pdf',
        '成信大课程表2025版V1.1.pdf',
        26
    )
