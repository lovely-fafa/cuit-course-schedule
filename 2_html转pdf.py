#!/usr/bin/python 3.8
# -*- coding: utf-8 -*- 
#
# @Time    : 2025-07-27 2:17
# @Author  : 阿发
# @File    : 2_html转pdf.py
# @Software: PyCharm
# python -m http.server 8000

import traceback
from pathlib import Path
import asyncio

import pdfkit
from playwright.async_api import async_playwright
from PIL import Image
from tqdm import tqdm


async def html_to_pdf_via_screenshot():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)
        page = await browser.new_page()
        for file in tqdm(
                list(Path('html', '2025-2026学年2学期').rglob('*.html')) +
                list(Path('html', '2026-2027学年1学期').rglob('*.html'))
        ):
            try:
                pdf_folder = Path('pdf') / Path(*list(file.parts[1:-1]))
                pdf_folder.mkdir(exist_ok=True, parents=True)
                if (pdf_folder / f'{file.stem}.pdf').exists():
                    continue
                await page.goto(f'file://{str(file.absolute())}', wait_until='networkidle')
                img_path = "fullpage.png"
                await page.screenshot(path=img_path, full_page=True)
                # Python 端打开测高
                img = Image.open(img_path)
                pixel_height = img.height  # 真实物理像素数
                img.close()
                Path(img_path).unlink()
                # 假设用 96 DPI 输出 PDF：
                mm_per_px = 25.4 / 96
                height_mm = pixel_height * mm_per_px + 300
                # fullPage 截图
                # 最后，调用 Playwright 或 pdfkit 生成 PDF：
                # 这里示例用 pdfkit
                options = {
                    "print-media-type": "",
                    "page-width": "209.9mm",
                    "page-height": f"{height_mm:.2f}mm",
                    "margin-top": "10mm",
                    "margin-bottom": "10mm",
                    "margin-left": "10mm",
                    "margin-right": "10mm",
                    "enable-local-file-access": "",
                    "load-error-handling": "ignore",
                    "load-media-error-handling": "ignore",
                    "encoding": "UTF-8",
                    "quiet": "",
                }
                pdfkit.from_file(
                    str(file),
                    str(pdf_folder / f'{file.stem}.pdf'),
                    options=options
                )
            except Exception as e:
                print(file, traceback.format_exc())
        await browser.close()


asyncio.run(html_to_pdf_via_screenshot())
