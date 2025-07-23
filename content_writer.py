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
    prompt = f"""Viết lại một câu mô tả ngắn (~15-20 từ) từ tiêu đề: "{h2_text}" để dùng làm caption và alt ảnh bài nhận định bóng đá. Không trùng lặp với tiêu đề gốc, giữ đúng ý, không nhắc đến 'H2' hay 'ảnh'. Viết bằng tiếng Việt."""
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content([prompt])
        return response.text.strip().replace('\n', ' ')
    except Exception:
        return h2_text

def generate_post(source_url, anchor_text, anchor_url):
    prompt = f"""Bạn là một chuyên gia viết nội dung nhận định và soi kèo dự đoán kết quả bóng đá chuẩn SEO. Viết một bài blog dài khoảng 700 đến 800 từ chuẩn SEO, hãy vào url {source_url} để lấy dữ liệu từ url này để viết bài, yêu cầu lấy đúng toàn bộ thông tin về phân tích kèo trong url để viết.
Trong bài viết, hãy tự nhiên chèn một liên kết nội bộ (internal link) với anchor text: "{anchor_text}" và url là: {anchor_url} ở một vị trí phù hợp (không phải ở đầu hoặc cuối bài, không được lặp lại).

Yêu cầu:
1. Viết ra đúng định dạng markdown chuẩn:
    - H1: # Tiêu đề bài viết
    - H2: ## Tiêu đề phụ
    - H3: ### Mục nhỏ
    - Đoạn bôi đậm dùng **text** chuẩn markdown.
    - Bảng dùng markdown table.
2. Không dùng code block, không dùng các ký tự rác, không sinh thêm dấu * hoặc # thừa.
3. Chỉ trả về nội dung bài viết, không thêm mô tả hoặc note gì.

⚠️Lưu ý: Viết bằng tiếng Việt, bắt đầu bài viết ngay, không có lời nói đầu và kết bài không thêm bất kỳ trích dẫn hoặc đường link nào, chỉ trả về nội dung bài viết.
"""
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content([prompt])
        raw_md = response.text.strip()
        cleaned_md = clean_markdown(raw_md)
        h1_title, markdown_no_h1 = extract_h1_and_remove(cleaned_md)
        h2s_list = extract_h2_list(markdown_no_h1)
        html = markdown2.markdown(markdown_no_h1, extras=["tables", "fenced-code-blocks", "strike", "cuddled-lists"])
        html = re.sub(r'<p>(\s*<h[1-6][^>]*>.*?</h[1-6]>)\s*</p>', r'\1', html, flags=re.DOTALL)
        return h1_title, h2s_list, html
    except Exception as e:
        import traceback
        print("[ERROR] generate_post:", e)
        print(traceback.format_exc())
        return "", [], f"Lỗi khi gọi Gemini: {e}"
