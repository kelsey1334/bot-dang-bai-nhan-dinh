import logging
import os
import re
import traceback
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
import pandas as pd
from excel_reader import read_excel
from content_writer import generate_post, paraphrase_caption
from image_generator import compose_image, slugify
from wp_poster import post_to_wordpress, upload_image_to_wp
from gemini_extract_team import extract_teams_from_url
from bs4 import BeautifulSoup

load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

logging.basicConfig(level=logging.INFO)

def create_wp_figure_html(img_url, alt, caption, width=800, height=450, img_id=None):
    img_class = f"size-full wp-image-{img_id}" if img_id else "size-full"
    figure_id = f'attachment_{img_id}' if img_id else ""
    cap_id = f'caption-attachment-{img_id}' if img_id else ""
    height_attr = f' height="{height}"' if height else ""
    figcaption = f'<figcaption id="{cap_id}" class="wp-caption-text">{caption}</figcaption>' if caption else ""
    html_fig = (
        f'<figure id="{figure_id}" aria-describedby="{cap_id}" style="width: {width}px" class="wp-caption aligncenter">'
        f'<img loading="lazy" decoding="async" class="{img_class}" src="{img_url}" alt="{alt}" width="{width}"{height_attr}>'
        f'{figcaption}'
        f'</figure>'
    )
    return html_fig

def remove_all_entities(raw_html):
    return re.sub(r'&[a-zA-Z0-9#]+;', '', raw_html)

def insert_figures_after_h2s(html_content, img2_html, img3_html, bot=None, chat_id=None):
    try:
        html_content = remove_all_entities(html_content)
        soup = BeautifulSoup(html_content, "lxml")
        h2s = soup.find_all('h2')
        if len(h2s) >= 2 and img2_html:
            h2s[1].insert_after(BeautifulSoup(img2_html, "lxml"))
        if h2s and img3_html:
            h2s[-1].insert_after(BeautifulSoup(img3_html, "lxml"))
        if soup.body:
            return soup.body.decode_contents()
        return str(soup)
    except Exception as e:
        error_msg = f"[ERROR] insert_figures_after_h2s: {e}\n"
        error_msg += traceback.format_exc()
        error_msg += f"\n------\n[INPUT HTML]:\n{html_content}\n------\n"
        print(error_msg)
        if bot and chat_id:
            short_err = error_msg[:4000]
            bot.send_message(chat_id, f"❌ [DEBUG] Lỗi BeautifulSoup:\n<pre>{short_err}</pre>", parse_mode="HTML")
        return f"[ERROR] insert_figures_after_h2s: {e}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🐣 Gửi file Excel chứa dữ liệu để đăng bài nhé~")

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = update.message.document
    chat_id = update.effective_chat.id
    if file.file_name.endswith('.xlsx'):
        file_obj = await file.get_file()
        os.makedirs("tmp", exist_ok=True)
        local_path = f"tmp/{file.file_name}"
        await file_obj.download_to_drive(local_path)
        await context.bot.send_message(chat_id, "📦 Đã nhận file, bắt đầu xử lý nhé! 💪")
        await process_excel(local_path, update, context)
    else:
        await context.bot.send_message(chat_id, "⚠️ Chỉ nhận file .xlsx thôi nha~ 😽")

async def process_excel(file_path, update, context):
    chat_id = update.effective_chat.id
    try:
        await context.bot.send_message(chat_id, "📖 Đang đọc file Excel... ⏳")
        accounts, keywords = read_excel(file_path)
        await context.bot.send_message(chat_id, "🍀 Đã đọc xong file Excel. Bắt đầu xử lý từng dòng key_word! 🚀")

        for idx, row in keywords.iterrows():
            try:
                await context.bot.send_message(
                    chat_id,
                    f"\n---\n📝 Xử lý dòng {idx+2}:\n<code>{dict(row)}</code>",
                    parse_mode="HTML"
                )

                src_url = row['url bài viết nguồn']
                website = row['website cần đăng']
                cat_id = int(row['id chuyên mục cần đăng'])
                anchor_text = row['anchor text']
                anchor_url = row['url anchor text']

                await context.bot.send_message(chat_id, "🔎 Đang dùng Gemini để xác định hai đội bóng...")
                try:
                    team_home, team_away = extract_teams_from_url(src_url)
                    await context.bot.send_message(
                        chat_id,
                        f"✅ Hai đội xác định: <b>{team_home}</b> vs <b>{team_away}</b>",
                        parse_mode="HTML"
                    )
                except Exception as e:
                    await context.bot.send_message(
                        chat_id,
                        f"😢 Lỗi dùng Gemini lấy tên hai đội: <code>{e}</code>",
                        parse_mode="HTML"
                    )
                    continue

                await context.bot.send_message(chat_id, "🔍 Đang tìm tài khoản website cần đăng... 🕵️‍♂️")
                acc_row = accounts[accounts['website'] == website]
                if acc_row.empty:
                    await context.bot.send_message(
                        chat_id,
                        f"😥 Lỗi: Không tìm thấy account cho website <b>{website}</b> ở dòng {idx+2}",
                        parse_mode="HTML"
                    )
                    continue
                acc_row = acc_row.iloc[0]
                wp_url = acc_row['website']
                wp_user = acc_row['tài khoản']
                wp_pass = acc_row['mật khẩu']
                logo_bg = acc_row['background ảnh']

                await context.bot.send_message(
                    chat_id,
                    f"🤖 Gọi Gemini viết bài và lấy H1, H2, anchor: <b>{anchor_text}</b> 🪄",
                    parse_mode="HTML"
                )
                try:
                    h1_title, h2s_list, post_content = generate_post(src_url, anchor_text, anchor_url)
                    if not h1_title:
                        await context.bot.send_message(
                            chat_id,
                            "⚠️ Không tìm thấy tiêu đề 1 (H1) trong bài viết của Gemini!",
                            parse_mode="HTML"
                        )
                        continue
                    await context.bot.send_message(
                        chat_id,
                        f"🌸 Đã tách tiêu đề 1: <b>{h1_title}</b> và H2s: <b>{h2s_list}</b>!",
                        parse_mode="HTML"
                    )
                except Exception as e:
                    await context.bot.send_message(
                        chat_id,
                        f"💔 Lỗi khi gọi Gemini hoặc tách tiêu đề 1: <code>{e}</code>",
                        parse_mode="HTML"
                    )
                    continue

                img_list = []
                await context.bot.send_message(chat_id, "🖼️ Đang tạo ảnh thumbnail & 2 ảnh phụ... 🎨")
                img1_name = f"tmp/{slugify(h1_title)}.jpg"
                img2_name, img3_name = None, None
                img2_text, img3_text = "", ""
                try:
                    compose_image(logo_bg, h1_title, img1_name)
                    img_list.append({'path': img1_name, 'title': h1_title, 'alt': h1_title, 'caption': h1_title})
                    await context.bot.send_message(
                        chat_id,
                        f"🌷 Đã tạo xong ảnh thumbnail: <code>{img1_name}</code> 🏆",
                        parse_mode="HTML"
                    )
                    if len(h2s_list) >= 2:
                        img2_text = h2s_list[1]
                        img2_name = f"tmp/{slugify(img2_text)}.jpg"
                        compose_image(logo_bg, img2_text, img2_name)
                    if len(h2s_list) >= 1:
                        img3_text = h2s_list[-1]
                        img3_name = f"tmp/{slugify(img3_text)}.jpg"
                        compose_image(logo_bg, img3_text, img3_name)
                except Exception as e:
                    await context.bot.send_message(
                        chat_id,
                        f"🧩 Lỗi tạo ảnh: <code>{e}</code>",
                        parse_mode="HTML"
                    )
                    continue

                img2_url, img3_url = None, None
                img2_id, img3_id = None, None
                img2_width, img2_height = 800, 450
                img3_width, img3_height = 800, 450

                # UPLOAD ẢNH = REST API
                if img2_name:
                    img2_info = upload_image_to_wp(wp_url, wp_user, wp_pass, img2_name, img2_text, img2_text, img2_text)
                    img2_url = img2_info.get("url")
                    img2_id = img2_info.get("id")
                if img3_name:
                    img3_info = upload_image_to_wp(wp_url, wp_user, wp_pass, img3_name, img3_text, img3_text, img3_text)
                    img3_url = img3_info.get("url")
                    img3_id = img3_info.get("id")

                # Caption & alt sử dụng AI bám sát ngữ cảnh
                alt2 = caption2 = paraphrase_caption(img2_text, team_home, team_away) if img2_text else ""
                alt3 = caption3 = paraphrase_caption(img3_text, team_home, team_away) if img3_text else ""

                img2_html = create_wp_figure_html(img2_url, alt2, caption2, img2_width, img2_height, img2_id) if img2_url else ""
                img3_html = create_wp_figure_html(img3_url, alt3, caption3, img3_width, img3_height, img3_id) if img3_url else ""

                try:
                    html_with_figures = insert_figures_after_h2s(
                        post_content, img2_html, img3_html, context.bot, chat_id
                    )
                except Exception as e:
                    await context.bot.send_message(
                        chat_id,
                        f"❌ [DEBUG] Lỗi chèn ảnh vào bài: <code>{e}</code>",
                        parse_mode="HTML"
                    )
                    html_with_figures = post_content

                await context.bot.send_message(chat_id, "🚀 Bắt đầu đăng bài lên WordPress... 📝")
                try:
                    post_id = post_to_wordpress(wp_url, wp_user, wp_pass, h1_title, html_with_figures, cat_id, img_list)
                    await context.bot.send_message(
                        chat_id,
                        f"🎉✅ Đăng bài thành công cho <b>{h1_title}</b> lên <b>{website}</b>!\n🆔 Post ID: <code>{post_id}</code> 🦄",
                        parse_mode="HTML"
                    )
                except Exception as e:
                    await context.bot.send_message(
                        chat_id,
                        f"💣 Lỗi đăng bài lên WordPress: <code>{e}</code>",
                        parse_mode="HTML"
                    )
                    continue

            except Exception as e:
                err_msg = f"❌ Lỗi không xác định dòng {idx+2}: {e}\n{traceback.format_exc()}"
                await context.bot.send_message(chat_id, err_msg[:4000], parse_mode="HTML")
                print(err_msg)

        await context.bot.send_message(chat_id, "✨ Đã xử lý xong toàn bộ file. Cảm ơn bạn! 🥰")
    except Exception as e:
        err_msg = f"❌ Lỗi tổng khi xử lý file: {e}\n{traceback.format_exc()}"
        await context.bot.send_message(chat_id, err_msg[:4000], parse_mode="HTML")
        print(err_msg)

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    app.run_polling()

if __name__ == "__main__":
    main()
