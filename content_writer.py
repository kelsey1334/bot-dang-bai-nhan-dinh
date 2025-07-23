import google.generativeai as genai
import os
import markdown2
import re

genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

def clean_markdown(md):
    lines = md.splitlines()
    cleaned = []
    for line in lines:
        if line.strip() in {'#', '##', '###', '####', '#####', '######', '*', '**', '***'}:
            continue
        if re.fullmatch(r'[#\*\s]+', line.strip()):
            continue
        cleaned.append(line)
    return "\n".join(cleaned).strip()

def extract_h1_and_remove(md):
    lines = md.splitlines()
    h1_line = ""
    rest = []
    for line in lines:
        if not h1_line and line.strip().startswith("# "):
            h1_line = line.strip()[2:].strip()
        else:
            rest.append(line)
    cleaned_md = "\n".join(rest).strip()
    return h1_line, cleaned_md

def extract_h2_list(md):
    return re.findall(r'^\s*##\s*(.+)$', md, re.MULTILINE)

def paraphrase_caption(h2_text):
    prompt = (
        f'Viết lại tiêu đề "{h2_text}" thành một câu mô tả ngắn, dùng làm caption và alt ảnh nhận định bóng đá. '
        'Chỉ trả về đúng một câu duy nhất, không giải thích, không đánh số, không in lại tiêu đề gốc.'
    )
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content([prompt])
        text = response.text.strip()
        text = re.sub(r"^[-\d. ]+", "", text).strip()
        text = text.split('\n')[0].strip()
        return text
    except Exception:
        return h2_text

def ensure_internal_link(content, anchor_text, anchor_url):
    # Nếu đã có internal link với bôi đậm, giữ nguyên
    if f'<a href="{anchor_url}"><strong>{anchor_text}</strong></a>' in content \
        or f'<a href="{anchor_url}"><b>{anchor_text}</b></a>' in content:
        return content
    # Thay anchor_text đầu tiên thành internal link có strong bôi đậm
    def replacer(match):
        return f'<a href="{anchor_url}"><strong>{anchor_text}</strong></a>'
    # Không thay trong tag đã có link
    pattern = rf'(?<![">])({re.escape(anchor_text)})(?!<\/a>)'
    return re.sub(pattern, replacer, content, count=1)

def generate_post(source_url, anchor_text, anchor_url):
    prompt = f"""Bạn là một chuyên gia viết nội dung nhận định và soi kèo dự đoán kết quả bóng đá chuẩn SEO. 
Viết một bài blog dài khoảng 700 đến 800 từ chuẩn SEO, hãy vào url {source_url} để lấy dữ liệu từ url này để viết bài, yêu cầu lấy đúng toàn bộ thông tin về phân tích kèo trong url để viết.

⚠️ Trong bài viết, bạn phải **chèn một liên kết nội bộ (internal link) với dạng HTML, với anchor text: "{anchor_text}" và url: {anchor_url}** vào một vị trí phù hợp trong thân bài (không ở đầu hoặc cuối bài, không lặp lại). 

Ví dụ chèn đúng dạng HTML:  
<a href="{anchor_url}">{anchor_text}</a>

Yêu cầu:
1. Viết đúng định dạng markdown:
    - H1: # Tiêu đề bài viết và Hãy đặt tiêu đề theo H1 là Nhận Định Bóng Đá: Đội A vs Đội B ngày 25/12/2025
    - H2: ## Tiêu đề phụ
    - H3: ### Mục nhỏ
    - Đoạn bôi đậm dùng **text** chuẩn markdown.
    - Bảng dùng markdown table.
2. Không dùng code block, không sinh thêm dấu * hoặc # thừa.
3. Không giải thích, chỉ trả về nội dung bài viết.

Lưu ý: Bài viết bằng tiếng Việt, bắt đầu bài viết ngay, không có lời nói đầu hoặc kết bài.
"""
    try:
        model = genai.GenerativeModel('gemini-2.5-pro')
        response = model.generate_content([prompt])
        raw_md = response.text.strip()
        cleaned_md = clean_markdown(raw_md)
        h1_title, markdown_no_h1 = extract_h1_and_remove(cleaned_md)
        h2s_list = extract_h2_list(markdown_no_h1)
        html = markdown2.markdown(markdown_no_h1, extras=["tables", "fenced-code-blocks", "strike", "cuddled-lists"])
        html = re.sub(r'<p>(\s*<h[1-6][^>]*>.*?</h[1-6]>)\s*</p>', r'\1', html, flags=re.DOTALL)
        html = ensure_internal_link(html, anchor_text, anchor_url)
        return h1_title, h2s_list, html
    except Exception as e:
        import traceback
        print("[ERROR] generate_post:", e)
        print(traceback.format_exc())
        return "", [], f"Lỗi khi gọi Gemini: {e}"
