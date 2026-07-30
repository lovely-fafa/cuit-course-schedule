#!/usr/bin/python 3.12
# -*- coding: utf-8 -*- 
#
# @Time    : 2026-06-27 21:39
# @Author  : 笨阿发
# @File    : 2_pdf清洗.py
# @Software: PyCharm

from pathlib import Path

import fitz  # PyMuPDF
from loguru import logger
from tqdm import tqdm


def clean_pdf_vector(input_path, output_path, top_cut_px1: int, top_cut_px2: int) -> bool:
    """
    矢量裁剪 PDF。

    参数：
        input_path: 输入 PDF 路径
        output_path: 输出 PDF 路径
        top_cut_px: 从页面顶部裁掉的高度，单位按 px 传入；默认按 96 DPI 换算为 PDF point

    规则：
        1. 如果页数 > 1：warning，删除输入 PDF，return False
        2. 如果页数 == 1：
            - 裁掉顶部 top_cut_px 高度
            - 自动识别下面最后有内容的位置
            - 内容底部 + 10px 后的空白全部裁掉
            - 保持矢量内容，不转图片
    """

    if not input_path.exists():
        logger.error(f"PDF 不存在：{input_path}")
        return False

    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        doc = fitz.open(str(input_path))

        if doc.page_count > 1:
            doc.close()
            logger.warning(f"PDF 页数大于 1，删除：{input_path}")
            input_path.unlink(missing_ok=True)
            return False

        page = doc[0]

        page_rect = page.rect

        content_rect = _get_page_content_rect(page)

        if content_rect is None:
            doc.close()
            logger.warning(f"PDF 未检测到内容，删除：{input_path}")
            input_path.unlink(missing_ok=True)
            return False

        new_top = page_rect.y0 + (top_cut_px1 if '课程表(1个)' in page.get_text() else top_cut_px2)

        # 内容底部 + 10px
        new_bottom = content_rect.y1 + 40

        # 防止异常越界
        new_top = max(page_rect.y0, min(new_top, page_rect.y1))
        new_bottom = max(new_top + 1, min(new_bottom, page_rect.y1))

        new_cropbox = fitz.Rect(
            page_rect.x0,
            new_top,
            page_rect.x1,
            new_bottom,
        )

        page.set_cropbox(new_cropbox)

        doc.save(
            str(output_path),
            garbage=4,
            deflate=True,
            clean=True,
        )
        doc.close()
        return True

    except Exception:
        logger.exception(f"PDF 清理失败：{input_path}")
        return False


def _get_page_content_rect(page) -> fitz.Rect | None:
    """
    获取页面实际内容边界。
    包含：
        - 文本
        - 图片
        - 矢量绘图，包括表格线、边框等
    """
    rects = []

    # 1. 文本块和图片块
    page_dict = page.get_text("dict")

    for block in page_dict.get("blocks", []):
        bbox = block.get("bbox")
        if not bbox:
            continue

        rect = fitz.Rect(bbox)

        if rect.is_empty or rect.is_infinite:
            continue

        # block type:
        # 0 = text
        # 1 = image
        rects.append(rect)

    # 2. 矢量绘图，比如表格线、边框、背景块
    for drawing in page.get_drawings():
        rect = drawing.get("rect")

        if not rect:
            continue

        rect = fitz.Rect(rect)

        if rect.is_empty or rect.is_infinite:
            continue

        rects.append(rect)

    if not rects:
        return None

    content_rect = rects[0]

    for rect in rects[1:]:
        content_rect |= rect

    return content_rect


def miao():
    for pdf in tqdm(list(Path('pdf').rglob('*.pdf'))[:]):
        out = Path('clean_pdf', *pdf.parts[-3:])
        if out.exists():
            continue
        clean_pdf_vector(pdf, out, 105, 43)


if __name__ == '__main__':
    miao()
