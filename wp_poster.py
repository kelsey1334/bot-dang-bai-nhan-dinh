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
    params = {
        'alt_text': alt,
        'caption': caption,
        'title': title
    }
    resp = requests.post(api_url, headers=headers, data=img_data, params=params)
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
    api_url = wp_url.rstrip('/') + '/wp-json/wp/v2/posts'
    headers = wp_basic_auth(user, app_password)
    params = {
        'title': title,
        'content': content,
        'status': 'publish',
        'categories': [cat_id],
    }
    if img_list and img_list[0].get("id"):
        params['featured_media'] = img_list[0]["id"]
    resp = requests.post(api_url, headers=headers, json=params)
    resp.raise_for_status()
    return resp.json().get("id")
