import logging
import httpx
import asyncio
from selectolax.lexbor import LexborHTMLParser
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

# --- আপনার টেলিগ্রাম বট টোকেন ---
TOKEN = '8628858496:AAGNVfI_VANOVUGyQnw16M-6ef3yHN7B1yU'

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://google.com"
}

# --- ১. Eporner সার্চ ফাংশন (৩০টি করে ভিডিও দিবে) ---
async def search_eporner(query, page=1):
    url = f"https://www.eporner.com/api/v2/video/search/?query={query}&per_page=30&page={page}&thumbsize=big&format=json"
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

# --- ২. xHamster সার্চ ফাংশন (উন্নত মেথড) ---
async def search_xhamster(query, page=1):
    url = f"https://xhamster.com/search/{query}/{page}"
    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=15, follow_redirects=True) as client:
            res = await client.get(url)
            parser = LexborHTMLParser(res.text)
            nodes = parser.css("div.video-thumb")
            videos = []
            for node in nodes:
                a_tag = node.css_first("a.video-thumb__image-container")
                t_tag = node.css_first("div.video-thumb__title")
                if a_tag and t_tag:
                    v_url = a_tag.attributes.get('href')
                    v_id = v_url.split('-')[-1].split('?')[0] if v_url else ""
                    img = a_tag.css_first("img").attributes.get('src')
                    if v_id:
                        videos.append({
                            'title': t_tag.text(strip=True),
                            'thumb': img,
                            'play_url': f"https://xhamster.com/embed/{v_id}",
                            'source': 'xHamster'
                        })
            return videos
    except: return []

# --- স্টার্ট কমান্ড ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔞 *MASTERS X-HUB UNLIMITED V11*\n\n"
        "বস, এখন আপনি আনলিমিটেড ভিডিও পাবেন।\n"
        "🔍 সার্চ করতে লিখুন: `/search milf` বা যেকোনো নাম।",
        parse_mode=ParseMode.MARKDOWN
    )

# --- সার্চ রেজাল্ট হ্যান্ডলার ---
async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args)
    if not query:
        await update.message.reply_text("🔍 সার্চ করতে কিছু লিখুন বস!")
        return
    
    await send_video_results(update, query, page=1)

# --- ভিডিও রেজাল্ট পাঠানোর মূল ফাংশন ---
async def send_video_results(update, query, page):
    if hasattr(update, 'callback_query') and update.callback_query:
        msg = update.callback_query.message
        chat_id = msg.chat_id
    else:
        chat_id = update.effective_chat.id
        msg = await update.message.reply_text(f"🔎 *'{query}'* এর রেজাল্ট আনা হচ্ছে (Page {page})...", parse_mode=ParseMode.MARKDOWN)

    # দুটি সোর্স থেকে ডাটা আনা (৩০+ ভিডিও)
    ep_videos = await search_eporner(query, page)
    xh_videos = await search_xhamster(query, page)
    all_videos = ep_videos + xh_videos
    
    if not all_videos:
        await msg.edit_text("😔 কোনো ভিডিও পাওয়া যায়নি। VPN চেক করুন।")
        return

    # প্রথম মেসেজটি ডিলিট করে ভিডিও পাঠানো শুরু করা
    if not hasattr(update, 'callback_query'):
        await msg.delete()

    for v in all_videos:
        keyboard = [[InlineKeyboardButton("▶️ Play Directly in Telegram", url=v['play_url'])]]
        try:
            await update.get_bot().send_photo(
                chat_id=chat_id,
                photo=v['thumb'],
                caption=f"🎬 *{v['title']}*\n🌐 *Source:* {v['source']}",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN
            )
            await asyncio.sleep(0.5) 
        except: continue

    # আনলিমিটেড লোড করার জন্য নেক্সট বাটন
    next_kb = [[InlineKeyboardButton("➡️ Load More Videos (Next Page)", callback_data=f"next|{query}|{page+1}")]]
    await update.get_bot().send_message(
        chat_id=chat_id,
        text=f"✅ Page {page} লোড হয়েছে। আরও দেখতে নিচের বাটনে ক্লিক করুন।",
        reply_markup=InlineKeyboardMarkup(next_kb)
    )

# --- নেক্সট পেজ হ্যান্ডলার ---
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query_data = update.callback_query.data
    await update.callback_query.answer()
    
    if query_data.startswith("next"):
        _, query, page = query_data.split("|")
        await send_video_results(update, query, int(page))

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("search", search))
    app.add_handler(CallbackQueryHandler(button_click))
    print("🚀 বট সার্ভারে লাইভ!")
    app.run_polling()
