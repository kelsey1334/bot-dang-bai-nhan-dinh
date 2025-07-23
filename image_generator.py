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

def compose_image(bg_url, text, out_name, max_width_ratio=0.75, max_height_ratio=0.5):
    import requests
    import textwrap
    from io import BytesIO

    # Tải background
    response = requests.get(bg_url)
    bg = Image.open(BytesIO(response.content)).resize((800, 450))
    draw = ImageDraw.Draw(bg)

    # Thiết lập max width (chiếm 70-75% ảnh)
    img_w, img_h = bg.size
    max_text_width = int(img_w * max_width_ratio)
    max_text_height = int(img_h * max_height_ratio)

    # Tìm kích thước font tối ưu (giảm dần)
    font_size = 56  # thử với cỡ lớn trước
    lines = []
    while font_size > 18:
        font = ImageFont.truetype(FONT_PATH, font_size)
        lines = textwrap.wrap(text, width=40)
        # Tính max chiều rộng dòng
        max_line_w = max(draw.textlength(line, font=font) for line in lines)
        total_text_h = len(lines) * (font.getbbox("A")[3] - font.getbbox("A")[1] + 10)
        if max_line_w <= max_text_width and total_text_h <= max_text_height:
            break
        font_size -= 2

    # Nếu còn dài quá thì chia dòng nhỏ hơn nữa
    while True:
        lines = textwrap.wrap(text, width=max(10, int(1.2 * max_text_width // font.getbbox("A" * 8)[2])))
        max_line_w = max(draw.textlength(line, font=font) for line in lines)
        total_text_h = len(lines) * (font.getbbox("A")[3] - font.getbbox("A")[1] + 10)
        if max_line_w <= max_text_width and total_text_h <= max_text_height:
            break
        if font_size <= 18 or len(lines) >= 8:
            break
        font_size -= 2
        font = ImageFont.truetype(FONT_PATH, font_size)

    # Tính vị trí vẽ căn giữa block text
    total_text_h = len(lines) * (font.getbbox("A")[3] - font.getbbox("A")[1] + 10)
    y_text = (img_h - total_text_h) // 2
    for line in lines:
        line_w = draw.textlength(line, font=font)
        x_text = (img_w - line_w) // 2
        draw.text((x_text, y_text), line, font=font, fill="white", stroke_width=3, stroke_fill="black")
        y_text += (font.getbbox("A")[3] - font.getbbox("A")[1] + 10)

    bg.save(out_name, "JPEG", quality=92)
    return out_name
