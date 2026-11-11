#!/usr/bin/env python3
"""
個人化兒童繪本 PDF 模板 — 加大字體版（新版規格）

用法：
  1. 將每頁圖放喺 images/ ，命名 cover.webp / p1.webp / p2.webp ...
  2. 修改下面 CONFIG 同 PAGES（或者由 skill 流程自動生成）
  3. python3 build_pdf_template.py

字體規格（新版，唔好改細）：
  內文中文 24pt / 英文 23pt（舊版 19 / 13.5）
  封面中文 48pt / 英文 38pt（舊版 42 / 22）
  年齡越細字越大，見 SKILL.md 年齡對照表。
每行字數上限係硬上限：超限會出警告，要改短句，唔准縮字塞入。
"""
import os, sys, textwrap
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph

# ---------- CONFIG（按問卷填） ----------
CONFIG = {
    "child_name": "小晴",
    "age_band": "3-4",            # 0-2 / 2-3 / 3-4 / 5-6 — 決定字體大細
    "language_mode": "zh+en",     # zh / en / zh+en / yue+en / zh+en+pinyin ...
    "max_zh_chars_per_line": 12,  # 問卷第 6 題
    "max_en_words_per_line": 8,   # 問卷第 6 題
    "total_pages": 4,             # 問卷第 7 題（連封面計；呢份係試跑示範本，正式版通常 11）
}

FONT_SIZES = {  # 年齡 -> (中文pt, 英文pt, 中文行距, 英文行距)
    "0-2": (28, 26, 38, 34),
    "2-3": (26, 24, 36, 31),
    "3-4": (24, 23, 34, 30),
    "5-6": (22, 22, 31, 29),
}
COVER_ZH, COVER_EN = 48, 38  # 舊版 42 / 22

BASE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(BASE, "images")
OUT = os.path.join(BASE, "picture-book.pdf")
# 字款：繁體字形（Noto Sans TC subset .ttf 放喺同目錄就用，冇就提示）
FONT_REG = os.path.join(BASE, "NotoSansTC-Regular.ttf")
FONT_BOLD = os.path.join(BASE, "NotoSansTC-Bold.ttf")

# ---------- PAGES: (image stem, 主語言文字, 英文文字 or None, is_cover) ----------
PAGES = [
    ("cover", "小晴自己刷牙仔", "Sunny Brushes Her Teeth", True),
    ("p1", "呢個係小晴，三歲喇！", "This is Sunny. She is three!", False),
    ("p2", "唧少少牙膏，刷刷刷！", "A little toothpaste. Brush, brush!", False),
    ("p3", "刷完牙，白雪雪，好開心！", "All done! Clean, white, happy!", False),
]

W, H = landscape(A4)
NAVY = HexColor("#2B3A55")
CREAM = HexColor("#FFFBF2")


def check_lines(text, limit, kind, page):
    """每行字數上限檢查：中文數字元，英文數 words。超限只警告，唔自動縮字。"""
    if text is None:
        return
    for line in text.split("\n"):
        n = len(line.replace(" ", "")) if kind == "zh" else len(line.split())
        if n > limit:
            print(f"⚠️  {page}: {kind} 一行 {n} 超過上限 {limit}：「{line}」— 請改短句，唔好縮字", file=sys.stderr)


def main():
    if not (os.path.exists(FONT_REG) and os.path.exists(FONT_BOLD)):
        sys.exit("欠字款：請將 NotoSansTC-Regular.ttf 同 NotoSansTC-Bold.ttf 放喺本檔案同目錄")
    pdfmetrics.registerFont(TTFont("NotoSansTC", FONT_REG))
    pdfmetrics.registerFont(TTFont("NotoSansTC-Bold", FONT_BOLD))
    zh_pt, en_pt, zh_lead, en_lead = FONT_SIZES[CONFIG["age_band"]]

    zh_style = ParagraphStyle("zh", fontName="NotoSansTC-Bold", fontSize=zh_pt,
                              leading=zh_lead, textColor=NAVY, alignment=1, wordWrap="CJK")
    en_style = ParagraphStyle("en", fontName="NotoSansTC", fontSize=en_pt,
                              leading=en_lead, textColor=NAVY, alignment=1, wordWrap="CJK")
    zh_cover = ParagraphStyle("zhc", fontName="NotoSansTC-Bold", fontSize=COVER_ZH,
                              leading=60, textColor=NAVY, alignment=1, wordWrap="CJK")
    en_cover = ParagraphStyle("enc", fontName="NotoSansTC", fontSize=COVER_EN,
                              leading=46, textColor=NAVY, alignment=1, wordWrap="CJK")
    num_style = ParagraphStyle("num", fontName="NotoSansTC", fontSize=13,
                               leading=15, textColor=HexColor("#8A8A8A"), alignment=2)

    def band(c, x, y, w, h, r=14):
        c.saveState(); c.setFillAlpha(0.92); c.setFillColor(CREAM)
        c.setStrokeColor(HexColor("#E8DCC8")); c.setLineWidth(1.2)
        c.roundRect(x, y, w, h, r, stroke=1, fill=1); c.restoreState()

    def full_image(c, path, tag):
        from PIL import Image
        im = Image.open(path); iw, ih = im.size
        pr, ir = W / H, iw / ih
        if ir > pr:
            cw = int(ih * pr); x0 = (iw - cw) // 2; box = (x0, 0, x0 + cw, ih)
        else:
            ch = int(iw / pr); y0 = (ih - ch) // 2; box = (0, y0, iw, y0 + ch)
        tmp = f"/tmp/pb_crop_{tag}.jpg"
        im.crop(box).save(tmp, "JPEG", quality=92)
        c.drawImage(tmp, 0, 0, width=W, height=H)

    if len(PAGES) != CONFIG["total_pages"]:
        print(f"⚠️  PAGES 有 {len(PAGES)} 頁，問卷總頁數係 {CONFIG['total_pages']}，請對返", file=sys.stderr)

    c = canvas.Canvas(OUT, pagesize=landscape(A4))
    c.setTitle(PAGES[0][1]); c.setAuthor("Family")
    for i, (stem, main_text, en_text, is_cover) in enumerate(PAGES):
        check_lines(main_text, CONFIG["max_zh_chars_per_line"], "zh", stem)
        check_lines(en_text, CONFIG["max_en_words_per_line"], "en", stem)
        full_image(c, os.path.join(IMG, f"{stem}.webp"), i)
        if is_cover:
            zp = Paragraph(main_text, zh_cover); ep = Paragraph(en_text, en_cover) if en_text else None
            zw, zh_h = zp.wrap(W - 260, H)
            ew, en_h = ep.wrap(W - 260, H) if ep else (0, 0)
            bh = zh_h + en_h + 44; bw = max(zw, ew) + 90
            bx, by = (W - bw) / 2, H - bh - 42
            band(c, bx, by, bw, bh, r=20)
            zp.drawOn(c, bx + 45, by + en_h + 26)
            if ep: ep.drawOn(c, bx + 45, by + 22)
        else:
            zp = Paragraph(main_text, zh_style)
            ep = Paragraph(en_text, en_style) if en_text else None
            zw, zh_h = zp.wrap(W - 220, H)
            ew, en_h = ep.wrap(W - 220, H) if ep else (0, 0)
            bh = zh_h + en_h + 34; bw = max(zw, ew) + 80
            bx, by = (W - bw) / 2, 26
            band(c, bx, by, bw, bh)
            zp.drawOn(c, bx + 40, by + en_h + 20)
            if ep: ep.drawOn(c, bx + 40, by + 16)
            np_ = Paragraph(str(i), num_style); nw, nh = np_.wrap(60, 30)
            np_.drawOn(c, W - nw - 22, H - nh - 18)
        c.showPage()
    c.save()
    print("saved:", OUT, os.path.getsize(OUT), "bytes | 字體: 中文", zh_pt, "pt / 英文", en_pt, "pt")


if __name__ == "__main__":
    main()
