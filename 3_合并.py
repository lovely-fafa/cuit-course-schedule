#!/usr/bin/python 3.8
# -*- coding: utf-8 -*- 
#
# @Time    : 2025-07-27 2:32
# @Author  : 阿发
# @Email   : fafa27182818@gmail.com
# @GitHub  : https://github.com/lovely-fafa
# @File    : 3_合并.py
# @Software: PyCharm

import os
from pathlib import Path

from PyPDF2 import PdfMerger, PdfReader


def merge_pdfs_with_bookmarks(root_dir: str, output_path: str):
    merger = PdfMerger()
    bookmark_parents = {}  # 存放 “相对路径 → 书签引用对象”
    current_page = 0

    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames.sort()
        pdfs = sorted(f for f in filenames if f.lower().endswith('.pdf'))
        for pdf_name in pdfs:
            full_path = os.path.join(dirpath, pdf_name)
            reader = PdfReader(full_path)
            num_pages = len(reader.pages)
            if num_pages > 1:
                print(f'文件大于1页，已经删除 调整转pdf时的高度后重新跑一遍 | full_path={full_path}')
                Path(full_path).unlink()
                continue
            # 构建多级文件夹书签
            rel_dir = os.path.relpath(dirpath, root_dir)
            parts = [] if rel_dir == "." else rel_dir.split(os.sep)
            parent = None
            accum = ""
            for part in parts:
                accum = os.path.join(accum, part) if accum else part
                if accum not in bookmark_parents:
                    # 新建一级/二级…书签，返回 outline_item 对象
                    outline = merger.add_outline_item(part, current_page, parent=parent)
                    bookmark_parents[accum] = outline
                parent = bookmark_parents[accum]

            # 文件本身的书签（不带 .pdf）
            title = os.path.splitext(pdf_name)[0]
            merger.add_outline_item(title, current_page, parent=parent)

            # 合并 PDF
            merger.append(full_path)
            current_page += num_pages

    # 写出结果
    with open(output_path, "wb") as f_out:
        merger.write(f_out)
    merger.close()
    print(f"合并完成：{output_path}")


if __name__ == "__main__":
    ROOT = r"pdf"  # 改成你的多级文件夹路径
    OUT = r"成信大课程表.pdf"  # 改成你想要的输出文件
    merge_pdfs_with_bookmarks(ROOT, OUT)
