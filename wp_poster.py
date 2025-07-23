import requests
import os
from requests.auth import HTTPBasicAuth

def upload_featured_image(wp_url, username, password, img_path, alt_text):
    media_api = wp_url.rstrip('/') + "/wp-json/wp/v2/media"
    with open(img_path, 'rb') as img_file:
        files = {'file': (os.path.basename(img_path), img_file, 'image/jpeg')}
        data = {'alt_text': alt_text}
        resp = requests.post(media_api, files=files, data=data, auth=(username, password))
    resp.raise_for_status()
    resp_json = resp.json()
    return resp_json['id']   # Trả về media ID

def post_to_wordpress(url, username, password, html_content, category_id, title, featured_media_id=None):
    post = {
        "title": title,
        "content": html_content,
        "status": "publish",
        "categories": [int(category_id)]
    }
    if featured_media_id:
        post["featured_media"] = featured_media_id
    api_url = url.rstrip('/') + "/wp-json/wp/v2/posts"
    response = requests.post(api_url, auth=HTTPBasicAuth(username, password), json=post)
    response.raise_for_status()
    return response.json().get('link')
