import google.generativeai as genai
import os

genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

def extract_teams_from_url(source_url):
    prompt = f"""
Bạn là AI chuyên phân tích dữ liệu bóng đá. Hãy vào url {source_url} và chỉ trả về đúng 2 tên đội bóng đang thi đấu (ghi đúng tên tiếng Anh chuẩn của mỗi đội để dùng API quốc tế, không thêm mô tả, không thêm ký tự nào khác, không chèn từ "vs", "and", chỉ in hoa chữ cái đầu, mỗi tên 1 dòng). Định dạng output:

Đội 1:
Đội 2:

Chỉ trả về tên hai đội, không thêm gì khác.
    """
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content([prompt])
    text = response.text.strip()
    # Xử lý output chuẩn, loại bỏ rác và tách 2 dòng
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    team_home, team_away = None, None
    for line in lines:
        if not team_home:
            team_home = line.replace("Đội 1:", "").strip()
        elif not team_away:
            team_away = line.replace("Đội 2:", "").strip()
            break
    if not team_home or not team_away:
        raise Exception(f"Không extract được tên hai đội: {text}")
    return team_home, team_away
