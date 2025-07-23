import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import re
import unicodedata
import os
import textwrap

FONT_PATH = "assets/NotoSans-Regular.ttf"

def slugify(text):
    # Chuyển đ/Đ thành d/D để slug chuẩn SEO
    text = text.replace('đ', 'd').replace('Đ', 'D')
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    text = re.sub(r"[^\w\s-]", '', text.lower())
    text = re.sub(r"[\s]+", '-', text)
    text = text.strip('-')
    if not text:
        text = "image"
    return text

def download_image(url):
    response = requests.get(url)
    return Image.open(BytesIO(response.content)).convert("RGB")  # JPG là RGB

def compose_image(bg_url, text, out_name, max_width_ratio=0.82, max_height_ratio=0.55):
    import requests
    import textwrap
    from io import BytesIO

    # Làm sạch text
    text = text.lstrip("#* ").strip()

    response = requests.get(bg_url)
    bg = Image.open(BytesIO(response.content)).resize((800, 450))
    draw = ImageDraw.Draw(bg)

    img_w, img_h = bg.size
    max_text_width = int(img_w * max_width_ratio)
    max_text_height = int(img_h * max_height_ratio)

    # Bắt đầu thử font size lớn rồi giảm dần
    font_size = 64
    font = ImageFont.truetype(FONT_PATH, font_size)
    lines = [text]
    while font_size > 24:
        # Tự wrap text lại cho dòng dài hơn
        wrap_width = 24
        lines = textwrap.wrap(text, width=wrap_width)
        max_line_w = max(draw.textlength(line, font=font) for line in lines)
        total_text_h = len(lines) * (font.getbbox("A")[3] - font.getbbox("A")[1] + 14)
        if max_line_w <= max_text_width and total_text_h <= max_text_height:
            break
        font_size -= 2
        font = ImageFont.truetype(FONT_PATH, font_size)
        # Nới wrap width cho font nhỏ hơn
        wrap_width = min(36, wrap_width + 1)

    # Tính toạ độ block text để căn giữa
    total_text_h = len(lines) * (font.getbbox("A")[3] - font.getbbox("A")[1] + 14)
    y_text = (img_h - total_text_h) // 2

    for line in lines:
        line_w = draw.textlength(line, font=font)
        x_text = (img_w - line_w) // 2
        # Đổ bóng cho chữ (shadow)
        shadow_xy = [(x_text+2, y_text+2), (x_text-2, y_text-2), (x_text+2, y_text-2), (x_text-2, y_text+2)]
        for sx, sy in shadow_xy:
            draw.text((sx, sy), line, font=font, fill="black")
        # Chữ chính màu trắng
        draw.text((x_text, y_text), line, font=font, fill="white")
        y_text += (font.getbbox("A")[3] - font.getbbox("A")[1] + 14)

    bg.save(out_name, "JPEG", quality=95)
    return out_name
