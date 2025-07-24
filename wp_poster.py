import requests
import os
from requests.auth import HTTPBasicAuth

def upload_featured_image(wp_url, username, password, img_path, alt_text):
    """
    Upload ảnh lên WP, trả về ID (dùng cho featured_media) và URL (để chèn vào bài viết)
    """
    media_api = wp_url.rstrip('/') + "/wp-json/wp/v2/media"
    with open(img_path, 'rb') as img_file:
        files = {'file': (os.path.basename(img_path), img_file, 'image/jpeg')}
        data = {'alt_text': alt_text}
        resp = requests.post(
            media_api, 
            files=files, 
            data=data, 
            auth=(username, password)
        )
    resp.raise_for_status()
    resp_json = resp.json()
    return resp_json['id']

def get_media_url(wp_url, media_id, username=None, password=None):
    """
    Lấy URL của media (dùng ID vừa upload)
    """
    media_api = wp_url.rstrip('/') + f"/wp-json/wp/v2/media/{media_id}"
    if username and password:
        resp = requests.get(media_api, auth=(username, password))
    else:
        resp = requests.get(media_api)
    resp.raise_for_status()
    resp_json = resp.json()
    return resp_json.get('source_url')

def post_to_wordpress(wp_url, username, password, html_content, category_id, title, featured_media_id=None):
    """
    Đăng bài lên WP. Trả về link bài viết
    """
    api_url = wp_url.rstrip('/') + "/wp-json/wp/v2/posts"
    post = {
        "title": title,
        "content": html_content,
        "status": "publish",
        "categories": [int(category_id)]
    }
    if featured_media_id:
        post["featured_media"] = featured_media_id
    resp = requests.post(api_url, auth=HTTPBasicAuth(username, password), json=post)
    resp.raise_for_status()
    return resp.json().get('link')
