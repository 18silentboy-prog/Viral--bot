import logging
import httpx
import asyncio
import chompjs
import re
from selectolax.lexbor import LexborHTMLParser
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- আপনার টেলিগ্রাম বট টোকেন ---
TOKEN = '8628858496:AAGNVfI_VANOVUGyQnw16M-6ef3yHN7B1yU'

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://xhamster.com/"
}

# --- ১. Eporner থেকে ভিডিও খোঁজা (এটি সবচেয়ে সচল) ---
async def search_eporner(query):
    url = f"https://www.eporner.com/api/v2/video/search/?query={query}&per_page=5&format=json"
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            res = await client.get(url)
            if res.status_code == 200:
                data = res.json()
                videos = []
                for v in data.get('videos', []):
                    videos.append({
                        'title': v['title'],
                        'thumb': v['default_thumb']['src'],
                        'play_url': f"https://www.eporner.com/embed/{v['id']}/",
                        'source': 'Eporner'
                    })
                return videos
    except: return []

# --- ২. xHamster থেকে ভিডিও খোঁজা (আপনার দেওয়া লজিক অনুযায়ী) ---
async def search_xhamster(query):
    search_url = f"https://xhamster.com/search/{query.replace(' ', '+')}"
    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=15, follow_redirects=True) as client:
            res = await client.get(search_url)
            if res.status_code != 200: return []
            
            parser = LexborHTMLParser(res.text)
            nodes = parser.css("div.video-thumb")[:5]
            
            videos = []
            for node in nodes:
                a_tag = node.css_first("a.video-thumb__image-container")
                title_tag = node.css_first("div.video-thumb__title")
                if a_tag and title_tag:
                    v_url = a_tag.attributes.get('href')
                    title = title_tag.text(strip=True)
                    img = a_tag.css_first("img").attributes.get('src')
                    # এমবেড লিংক তৈরি
                    v_id = v_url.split('-')[-1]
                    play_url = f"https://xhamster.com/embed/{v_id}"
                    
                    videos.append({
                        'title': title,
                        'thumb': img,
                        'play_url': play_url,
                        'source': 'xHamster'
                    })
            return videos
    except: return []

# --- স্টার্ট কমান্ড ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔞 *MASTERS X-HUB — REAL VIDEO PLAYER*\n\n"
        "বস, আমি এখন xHamster এবং Eporner থেকে সরাসরি ভিডিও আনবো।\n"
        "🔍 সার্চ করতে ক্যাটাগরির নাম লিখুন।\n\n"
        "উদাহরণ: `/search indian` বা `/search milf`",
        parse_mode=ParseMode.MARKDOWN
    )

# --- সার্চ ফাংশন ---
async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args)
    if not query:
        await update.message.reply_text("🔍 সার্চ করতে কিছু লিখুন বস!")
        return
    
    status = await update.message.reply_text(f"⏳ সার্ভার থেকে *'{query}'* ভিডিও খোঁজা হচ্ছে...", parse_mode=ParseMode.MARKDOWN)
    
    # দুটি সোর্স থেকেই ডাটা আনা
    ep_videos = await search_eporner(query)
    xh_videos = await search_xhamster(query)
    all_videos = ep_videos + xh_videos
    
    if not all_videos:
        await status.edit_text("😔 দুঃখিত বস, কোনো ভিডিও পাওয়া যায়নি। VPN অন করে আবার চেষ্টা করুন।")
        return

    await status.delete()
    
    for v in all_videos:
        # বাটন তৈরি (টেলিগ্রামের ভেতরে প্লে করার জন্য)
        # url অপশনে ক্লিক করলে টেলিগ্রামের ইন-অ্যাপ ব্রাউজারে ফুল স্ক্রিন প্লে হবে
        keyboard = [[InlineKeyboardButton("▶️ Play Directly in Telegram", url=v['play_url'])]]
        
        try:
            await update.message.reply_photo(
                photo=v['thumb'],
                caption=f"🎬 *{v['title']}*\n🌐 *Source:* {v['source']}",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN
            )
            await asyncio.sleep(1) # টেলিগ্রাম স্প্যাম ফিল্টার এড়াতে
        except:
            continue

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("search", search))
    print("🚀 বট অনলাইন!")
    app.run_polling()
