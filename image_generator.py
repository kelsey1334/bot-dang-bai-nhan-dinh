import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import re
import unicodedata
import os

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

def compose_image(bg_url, text, out_name):
    bg = download_image(bg_url).resize((800, 450))
    out = bg.copy()
    draw = ImageDraw.Draw(out)
    # Load font Việt hóa, fallback mặc định nếu thiếu
    try:
        font_text = ImageFont.truetype(FONT_PATH, 48)
    except Exception:
        font_text = ImageFont.load_default()
    # Tính toán vị trí căn giữa
    bbox = draw.textbbox((0, 0), text, font=font_text)
    text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    w, h = out.size
    x = (w - text_w) // 2
    y = (h - text_h) // 2
    draw.text((x, y), text, font=font_text, fill="black", stroke_width=2, stroke_fill="white")
    out.save(out_name, "JPEG", quality=92)
    return out_name
