#!/usr/bin/python 3.8
# -*- coding: utf-8 -*- 
#
# @Time    : 2025-07-27 2:32
# @Author  : 阿发
# @File    : 3_合并.py
# @Software: PyCharm

import os
from pathlib import Path
import re
from collections import defaultdict
from itertools import chain

import fitz
from pypdf import PdfWriter
from tqdm import tqdm

TMP_FOLDER = Path('tmp')
SEQ = list(chain.from_iterable([[f'{i}上', f'{i}下'] for i in ['大一', '大二', '大三', '大四']]))
LEVEL_MAPPING = {
    ('26', '1学期'): '大一上',
    ('25', '2学期'): '大一下',
    ('25', '1学期'): '大二上',
    ('24', '2学期'): '大二下',
    ('24', '1学期'): '大三上',
    ('23', '2学期'): '大三下',
    ('23', '1学期'): '大四上',
    ('22', '2学期'): '大四下',
}

FONT_FILE = "Alibaba-PuHuiTi-Regular.ttf"
FONT = fitz.Font(fontfile=FONT_FILE)


def add_right_text(pdf_path: Path, text) -> str:
    doc = fitz.open(pdf_path)
    assert doc.page_count == 1, '你应该运行 2_pdf清洗.py'

    page = doc[0]
    fontsize = 8
    font = fitz.Font("china-s")
    text_width = font.text_length(text, fontsize=fontsize)

    x = page.rect.width - text_width - 33
    y = 20

    page.insert_text(
        (x, y),
        text,
        fontname="china-s",
        fontsize=fontsize,
        color=(0, 0, 0),
    )

    tmp_path = TMP_FOLDER.joinpath(pdf_path)
    tmp_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(
        tmp_path,
        garbage=4,
        deflate=True
    )
    doc.close()
    return str(tmp_path.absolute())


def build_structure(root_dir):
    structure = defaultdict(lambda: defaultdict(list))
    for file in Path(root_dir).rglob("*.pdf"):
        parts = file.parts
        match = re.search(r'^(.*?(\d{3}).*?)_', file.stem)
        year = match.group(2)[:-1]
        assert match.group(1).count(year) == 1, '哦豁又要写代码了'
        class_name = match.group(1).replace(year, '')
        structure[parts[-2]][class_name].append((
            LEVEL_MAPPING[(year, re.search(r'(\d学期)', parts[-3]).group(1))], file
        ))
    for _, items in structure.items():
        for key, data in items.items():
            assert len(set(i[0] for i in data)) == len([i[0] for i in data]), '哈？怎么会有重复的'
            items[key] = sorted(data, key=lambda x: SEQ.index(x[0]))
    return structure


def merge_pdfs_with_bookmarks(root_dir: str, output_path: str):
    writer = PdfWriter()
    bookmark_parents = {}  # 存放 “相对路径 → 书签引用对象”
    current_page = 0

    for collee_name, items in tqdm(sorted(list(build_structure(root_dir).items()), key=lambda x: x[0], reverse=True)):
        for class_name, classs in items.items():
            for level, path in classs:
                # 构建多级文件夹书签
                parent = None
                accum = ""
                paets = [collee_name, class_name, level]
                for part in paets:
                    accum = os.path.join(accum, part) if accum else part
                    if accum not in bookmark_parents:
                        # 新建一级/二级…书签，返回 outline_item 对象
                        outline = writer.add_outline_item(part, current_page, parent=parent, is_open=False)
                        bookmark_parents[accum] = outline
                    parent = bookmark_parents[accum]

                full_path = add_right_text(path, '_'.join(paets))
                # 合并 PDF
                writer.append(full_path)
                current_page += 1  # add_right_text 确保了必须是一页
    # 写出结果
    with open(output_path, "wb") as f_out:
        writer.write(f_out)
    writer.close()
    print(f"合并完成：{output_path}")


if __name__ == "__main__":
    ROOT = r"clean_pdf"  # 改成你的多级文件夹路径
    OUT = r"tmp.pdf"  # 改成你想要的输出文件
    merge_pdfs_with_bookmarks(ROOT, OUT)
