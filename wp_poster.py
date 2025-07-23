import os
from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods.posts import NewPost
from wordpress_xmlrpc.methods.media import UploadFile
import mimetypes

def get_wp_client(wp_url, wp_user, wp_pass):
    return Client(wp_url, wp_user, wp_pass)

def upload_image_to_wp(client, image_path, title, alt, caption):
    with open(image_path, "rb") as img_file:
        data = {
            'name': os.path.basename(image_path),
            'type': mimetypes.guess_type(image_path)[0] or 'image/jpeg',
            'bits': img_file.read(),
        }
    response = client.call(UploadFile(data))
    return {
        "url": response.url,
        "id": response.id,
        "title": title,
        "alt": alt,
        "caption": caption
    }

def post_to_wordpress(wp_url, wp_user, wp_pass, title, html_content, cat_id, img_list):
    client = get_wp_client(wp_url, wp_user, wp_pass)
    post = WordPressPost()
    post.title = title
    post.content = html_content
    if img_list and img_list[0].get("id"):
        post.thumbnail = img_list[0]["id"]
    post.terms_names = {'category': [str(cat_id)]}
    post.post_status = 'publish'
    post_id = client.call(NewPost(post))
    return post_id
