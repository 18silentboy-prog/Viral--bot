import logging
import httpx
import asyncio
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# --- আপনার টেলিগ্রাম বট টোকেন ---
TOKEN = '8628858496:AAGNVfI_VANOVUGyQnw16M-6ef3yHN7B1yU'

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- ভিডিও ফাইল লিঙ্ক বের করার এপিআই (১০+ সোর্স সাপোর্ট করে) ---
async def fetch_direct_videos(query, page=1):
    # এই এপিআই টি একাই xHamster, XVideos, XNXX সহ সব বড় সাইটের ডিরেক্ট ফাইল লিঙ্ক দেয়
    api_url = f"https://xvidapi.com/api.php/provide/vod?ac=detail&at=json&wd={query}&pg={page}"
    
    video_files = []
    try:
        async with httpx.AsyncClient(timeout=20, verify=False) as client:
            res = await client.get(api_url)
            if res.status_code == 200:
                data = res.json()
                for item in data.get('list', []):
                    # ভিডিওর আসল স্ট্রিম লিঙ্ক বের করা (এটিই সরাসরি প্লে করতে সাহায্য করবে)
                    play_url_raw = item.get('vod_play_url', '')
                    if play_url_raw:
                        # অনেক সময় লিঙ্কে অনেক কিছু থাকে, আমরা মেইন লিঙ্কটি নিচ্ছি
                        direct_url = play_url_raw.split('$')[-1]
                        if direct_url.startswith('http'):
                            video_files.append({
                                'title': item.get('vod_name'),
                                'file_url': direct_url,
                                'thumb': item.get('vod_pic')
                            })
    except Exception as e:
        logging.error(f"Error fetching data: {e}")
        
    return video_files

# --- স্টার্ট কমান্ড ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 *MASTERS DIRECT VIDEO PLAYER*\n\n"
        "বস, এখন ভিডিও সরাসরি টেলিগ্রাম প্লেয়ারে আসবে!\n"
        "🔍 সার্চ করতে লিখুন: `/search milf` বা যেকোনো নাম।\n\n"
        "✅ ভিডিও টেনে দেখতে পারবেন\n"
        "✅ ফুল স্ক্রিন করতে পারবেন\n"
        "✅ সরাসরি সেভ করতে পারবেন",
        parse_mode=ParseMode.MARKDOWN
    )

# --- সার্চ হ্যান্ডলার ---
async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args)
    if not query:
        await update.message.reply_text("🔍 সার্চ করতে কিছু লিখুন বস!")
        return
    
    await load_videos(update, context, query, page=1)

# --- সরাসরি ভিডিও পাঠানোর ফাংশন ---
async def load_videos(update, context, query, page):
    if update.callback_query:
        msg = update.callback_query.message
        await update.callback_query.answer()
    else:
        msg = await update.message.reply_text(f"🚀 *'{query}'* এর ভিডিওগুলো প্রসেস হচ্ছে... একটু সময় দিন।", parse_mode=ParseMode.MARKDOWN)

    videos = await fetch_direct_videos(query, page)
    
    if not videos:
        await msg.edit_text("😔 কোনো ভিডিও পাওয়া যায়নি। অন্য কিছু লিখে সার্চ দিন।")
        return

    if not update.callback_query:
        await msg.delete()

    for v in videos[:10]: # একবারে ১০টি করে ভিডিও পাঠাবে
        try:
            # সরাসরি টেলিগ্রাম প্লেয়ারে ভিডিও পাঠানো
            # supports_streaming=True দিলে ডাউনলোড হওয়ার আগেই ভিডিও প্লে শুরু হবে
            await context.bot.send_video(
                chat_id=update.effective_chat.id,
                video=v['file_url'],
                caption=f"🎬 *{v['title']}*",
                parse_mode=ParseMode.MARKDOWN,
                supports_streaming=True,
                timeout=120 # বড় ফাইলের জন্য সময় বাড়িয়ে দেওয়া হয়েছে
            )
            await asyncio.sleep(1) 
        except:
            continue

    # আনলিমিটেড লোড করার জন্য নেক্সট বাটন
    keyboard = [[InlineKeyboardButton("➡️ Load More (Next Page)", callback_data=f"p|{query}|{page+1}")]]
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"✅ Page {page} শেষ। আরও ভিডিও দেখতে চাইলে নিচের বাটনে ক্লিক করুন।",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# --- বাটন ক্লিক হ্যান্ডলার ---
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = update.callback_query.data
    if data.startswith("p|"):
        _, query, page = data.split("|")
        await load_videos(update, context, query, int(page))

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("search", search))
    app.add_handler(CallbackQueryHandler(button))
    print("🚀 বট এখন লাইভ! সরাসরি টেলিগ্রামে চেক করুন।")
    app.run_polling()
