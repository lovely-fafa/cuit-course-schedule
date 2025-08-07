#!/usr/bin/python 3.8
# -*- coding: utf-8 -*- 
#
# @Time    : 2025-08-07 0:51
# @Author  : 阿发
# @Email   : fafa27182818@gmail.com
# @GitHub  : https://github.com/lovely-fafa
# @File    : 4_插入目录.py
# @Software: PyCharm
"""
可怜的 chat

使用python代码，根据pdf的书签，给我的pdf增加目录。注意，
1.你的 代码可以指定在第几页后插入目录
2.考虑中文需要字体文件
3.不需要你新增页码，我会自己用arcobat增加
4.我pdf很多页，也就是说目录肯定是不止一页的，你不能直接认为目录中第一行一定跳转目录页+1
5.目录要超链接
"""
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import math
import fitz  # PyMuPDF


def insert_toc_only(
    input_pdf: str,
    output_pdf: str,
    *,
    toc_after: int = 0,                         # 在第几页后插入目录；0=最前；1=第1页后……
    fontfile: str = r"C:\Windows\Fonts\simsun.ttc",
    fontsize: int = 12,
    header_text: str = "目录",
    header_fontsize: int = 18,
    left_margin: float = 50.0,
    right_margin: float = 50.0,
    top_margin: float = 50.0,
    bottom_margin: float = 50.0,
    indent_step: float = 20.0,
    line_leading: float = 1.35,
    show_numbers: bool = True,                  # 是否在目录右侧显示页码（只在目录页显示）
    body_start_at: int | None = None,           # 逻辑页：正文第一页的物理索引(0-based)。None=关闭逻辑页显示
    # —— 新增：点线引导配置 ——
    leader_enabled: bool = True,                # 是否启用点线引导
    leader_char: str = "·",                     # 引导字符，可改为 "."
    leader_left_gap: float = 8.0,               # 标题与点线之间的最小间隔（pt）
    leader_right_gap: float = 6.0,              # 点线与页码之间的最小间隔（pt）
):
    doc = fitz.open(input_pdf)

    # 书签：[[level, title, page1based], ...]
    toc_data = doc.get_toc(simple=True)
    if not toc_data:
        Path(output_pdf).parent.mkdir(parents=True, exist_ok=True)
        doc.save(output_pdf)
        doc.close()
        return

    # 插入位置（0-based，“在其前插入”索引）
    insert_at = max(0, min(int(toc_after), doc.page_count))

    # 页面尺寸（以首页为准）
    base_rect = doc[0].rect
    page_w, page_h = base_rect.width, base_rect.height

    # 排版参数
    line_h = fontsize * line_leading
    header_gap = fontsize * 1.2
    usable_h = page_h - top_margin - bottom_margin
    first_top_y = top_margin + header_fontsize * 1.6 + header_gap
    lines_first = max(0, int((page_h - first_top_y - bottom_margin) // line_h))
    lines_other = max(1, int(usable_h // line_h))

    total = len(toc_data)
    if total <= lines_first:
        toc_pages = 1
    else:
        remaining = total - lines_first
        toc_pages = 1 + math.ceil(remaining / lines_other)

    # 目录右侧显示数字的策略 + 计算插入后的目标新页索引（物理 0-based）
    font_for_width = fitz.Font(fontfile=fontfile)  # 测宽（不参与绘制）

    adjusted = []
    for level, title, dest_page1 in toc_data:
        p_old0 = max(0, dest_page1 - 1)  # 原目标页（物理 0-based）
        # 插入目录后的新物理页：原索引 >= insert_at 的需要整体后移 toc_pages
        p_new0 = p_old0 + toc_pages if p_old0 >= insert_at else p_old0

        # 目录页右侧显示的数字
        if body_start_at is None:
            disp = str(dest_page1) if show_numbers else ""
        else:
            if p_old0 >= body_start_at:
                disp = str((p_old0 - body_start_at) + 1) if show_numbers else ""
            else:
                disp = ""  # 正文前（前言/罗马数字部分）默认不显示

        adjusted.append((level, title, p_old0, p_new0, disp))

    # 一次性插入目录页（更稳，不会影响后续映射）
    for i in range(toc_pages):
        doc.new_page(pno=insert_at + i, width=page_w, height=page_h)

    # 在页上注册字体；成功则用 fontname，失败回退 fontfile
    def prepare_page_font(page, alias="CJK"):
        try:
            page.insert_font(fontname=alias, fontfile=fontfile)
            return True, alias
        except Exception:
            return False, alias

    # 写目录
    cur = 0
    for i in range(toc_pages):
        page = doc[insert_at + i]
        use_fontname, alias = prepare_page_font(page, alias="SimSun")

        def draw_text(x, y, text, size):
            if use_fontname:
                page.insert_text(fitz.Point(x, y), text, fontsize=size, fontname=alias)
            else:
                page.insert_text(fitz.Point(x, y), text, fontsize=size, fontfile=fontfile)

        # 标题（仅第一页）
        y = top_margin
        if i == 0:
            draw_text(left_margin, y, header_text, header_fontsize)
            y += header_fontsize * 1.6 + header_gap
            cap = lines_first
        else:
            cap = lines_other

        for _ in range(cap):
            if cur >= total:
                break

            level, title, p_old0, p_new0, disp = adjusted[cur]
            x_left = left_margin + max(0, level) * indent_step
            y += line_h

            # ==== 左侧标题 ====
            draw_text(x_left, y, title, fontsize)

            # ==== 右侧页码（测宽右对齐；不使用 align） ====
            x_num = None
            if disp:
                w_num = font_for_width.text_length(disp, fontsize)
                x_num = page_w - right_margin - w_num
                draw_text(x_num, y, disp, fontsize)

            # ==== 点线引导（仅在存在页码时绘制） ====
            if leader_enabled and disp:
                # 标题宽度
                w_title = font_for_width.text_length(title, fontsize)
                # 点线区域的起止 X
                lead_start_x = x_left + w_title + leader_left_gap
                lead_end_x = x_num - leader_right_gap
                available = max(0.0, lead_end_x - lead_start_x)

                if available > 0:
                    # 单个引导字符的宽度
                    dot_w = max(0.1, font_for_width.text_length(leader_char, fontsize))
                    # 计算可放置的数量
                    n = int(available // dot_w)
                    if n > 0:
                        dots = leader_char * n
                        draw_text(lead_start_x, y, dots, fontsize)

            # ==== 整行点击区域（更容易点中） ====
            link_rect = fitz.Rect(
                left_margin,
                y - line_h * 0.8,
                page_w - right_margin,
                y + line_h * 0.3
            )
            page.insert_link({
                "kind": fitz.LINK_GOTO,
                "from": link_rect,
                "page": p_new0,          # 0-based 目标物理页（已包含目录偏移）
                "to": fitz.Point(0, 0),
                "zoom": 0,
            })

            cur += 1

    # === 重写书签页码（把原书签全部映射到“新物理页”） ===
    new_toc = [[level, title, p_new0 + 1] for (level, title, _p_old0, p_new0, _disp) in adjusted]
    try:
        doc.set_toc(new_toc)          # 新接口
    except AttributeError:
        try:
            doc.setToC(new_toc)       # 旧接口
        except Exception as e:
            print(f"警告：未能更新书签页码：{e}")

    # 保存
    Path(output_pdf).parent.mkdir(parents=True, exist_ok=True)
    doc.save(output_pdf)
    doc.close()
    print(f"完成：目录已插入到第 {toc_after} 页后（物理），共 {toc_pages} 页；书签已同步；输出：{output_pdf}")


if __name__ == "__main__":
    # 示例
    insert_toc_only(
        input_pdf=r"成信大课程表.pdf",
        output_pdf=r"成信大课程表-带目录.pdf",
        toc_after=0,  # 0=最前插；2=在第2页后插
        fontfile=r"C:\Windows\Fonts\simsun.ttc",
        header_text="目录",
        show_numbers=True,  # 目录右侧显示目标页码（不影响你后续用 Acrobat 加页码）
    )
