import requests
import os

def upload_image_to_wp(wp_url, user, app_password, image_path, alt, caption, title):
    """
    Upload ảnh lên WordPress (REST API) và trả về dict {url, id, title, alt, caption}
    """
    api_url = wp_url.rstrip('/') + '/wp-json/wp/v2/media'
    with open(image_path, 'rb') as img_file:
        files = {'file': (os.path.basename(image_path), img_file, 'image/jpeg')}
        data = {'alt_text': alt}
        resp = requests.post(api_url, files=files, data=data, auth=(user, app_password))
    resp.raise_for_status()
    data = resp.json()
    return {
        "url": data.get("source_url"),
        "id": data.get("id"),
        "title": title,
        "alt": alt,
        "caption": caption
    }

def post_to_wordpress(wp_url, user, app_password, title, content, cat_id, img_list):
    """
    Đăng bài viết lên WordPress, set thumbnail bằng ID ảnh thumbnail đã upload.
    """
    api_url = wp_url.rstrip('/') + '/wp-json/wp/v2/posts'
    params = {
        'title': title,
        'content': content,
        'status': 'publish',
        'categories': [cat_id],
    }
    if img_list and img_list[0].get("id"):
        params['featured_media'] = img_list[0]["id"]
    resp = requests.post(api_url, json=params, auth=(user, app_password))
    resp.raise_for_status()
    return resp.json().get("id")
