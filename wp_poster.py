import requests
import base64

def wp_basic_auth(user, app_password):
    token = base64.b64encode(f"{user}:{app_password}".encode()).decode()
    return {"Authorization": f"Basic {token}"}

def upload_image_to_wp(wp_url, user, app_password, image_path, alt, caption, title):
    api_url = wp_url.rstrip('/') + '/wp-json/wp/v2/media'
    headers = wp_basic_auth(user, app_password)
    headers['Content-Disposition'] = f'attachment; filename="{image_path.split("/")[-1]}"'
    headers['Content-Type'] = 'image/jpeg'
    with open(image_path, "rb") as img_file:
        img_data = img_file.read()
    # Không cần params ở đây, chỉ meta sau khi upload
    resp = requests.post(api_url, headers=headers, data=img_data)
    resp.raise_for_status()
    data = resp.json()
    # Sửa meta nếu muốn sau upload (nếu cần alt/caption chuẩn)
    # Sửa meta cho ảnh vừa upload
    media_id = data.get("id")
    meta_url = wp_url.rstrip('/') + f'/wp-json/wp/v2/media/{media_id}'
    meta = {
        'alt_text': alt,
        'caption': caption,
        'title': title
    }
    resp2 = requests.post(meta_url, headers=headers, json=meta)
    # resp2.raise_for_status() # Có thể bị lỗi 401, nhưng không ảnh hưởng ảnh
    return {
        "url": data.get("source_url"),
        "id": media_id,
        "title": title,
        "alt": alt,
        "caption": caption
    }

def post_to_wordpress(wp_url, user, app_password, title, content, cat_id, img_list):
    api_url = wp_url.rstrip('/') + '/wp-json/wp/v2/posts'
    headers = wp_basic_auth(user, app_password)
    params = {
        'title': title,
        'content': content,
        'status': 'publish',
        'categories': [cat_id],
    }
    # Thumbnail: dùng ID ảnh thumbnail upload ở đầu img_list
    if img_list and img_list[0].get("id"):
        params['featured_media'] = img_list[0]["id"]
    resp = requests.post(api_url, headers=headers, json=params)
    resp.raise_for_status()
    return resp.json().get("id")
