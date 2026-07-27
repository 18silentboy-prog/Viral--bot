import logging
import httpx
import asyncio
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- আপনার টেলিগ্রাম বট টোকেন ---
TOKEN = '8628858496:AAGNVfI_VANOVUGyQnw16M-6ef3yHN7B1yU'

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- ১০+ সোর্স থেকে সরাসরি ভিডিও ডাটা আনার ফাংশন ---
async def get_multi_source_videos(query):
    # এই API টি ১০টির বেশি প্রিমিয়াম সাইটের ভিডিও সরাসরি স্ট্রিম করতে দেয়
    api_url = f"https://xvidapi.com/api.php/provide/vod?ac=detail&at=json&wd={query}"
    
    videos_list = []
    try:
        async with httpx.AsyncClient(timeout=20, verify=False) as client:
            response = await client.get(api_url)
            if response.status_code == 200:
                data = response.json()
                raw_list = data.get('list', [])
                
                for item in raw_list:
                    # ভিডিওর টাইটেল, থাম্বনেইল এবং প্লে-লিঙ্ক বের করা
                    title = item.get('vod_name', 'No Title')
                    thumb = item.get('vod_pic', '')
                    # এখানে ভিডিওর আসল ফাইল লিঙ্ক (m3u8/mp4) থাকে
                    play_url = item.get('vod_play_url', '').split('$')[-1]
                    
                    if play_url and thumb:
                        videos_list.append({
                            'title': title,
                            'thumb': thumb,
                            'url': play_url
                        })
    except Exception as e:
        logging.error(f"Search Error: {e}")
        
    return videos_list

# স্টার্ট কমান্ড
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔞 *MASTERS CLOUD X-HUB V10 — DIRECT PLAYER*\n\n"
        "বস, এই বট এখন সরাসরি টেলিগ্রামে ভিডিও প্লে করবে।\n"
        "🔍 সার্চ করতে ক্যাটাগরি বা নাম লিখুন।\n\n"
        "উদাহরণ: `/search milf` , `/search desi`",
        parse_mode=ParseMode.MARKDOWN
    )

# সার্চ রেজাল্ট এবং সরাসরি ভিডিও সেন্ডিং
async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args)
    if not query:
        await update.message.reply_text("🔍 সার্চ করতে কিছু লিখুন বস!")
        return
    
    status = await update.message.reply_text(f"⏳ ১০টি সার্ভার থেকে *'{query}'* ক্যাটাগরির ভিডিও প্রসেস হচ্ছে...", parse_mode=ParseMode.MARKDOWN)
    
    videos = await get_multi_source_videos(query)
    
    if not videos:
        await status.edit_text("😔 দুঃখিত বস, কোনো সার্ভারে ভিডিও পাওয়া যায়নি। VPN অন করে আবার ট্রাই করুন।")
        return

    await status.delete()
    
    # সিরিয়ালে ভিডিও পাঠানো
    for v in videos:
        try:
            # সরাসরি টেলিগ্রাম ভিডিও প্লেয়ারে পাঠানো
            await update.message.reply_video(
                video=v['url'],
                caption=f"🎬 *{v['title']}*\n\n✅ এটি সরাসরি টেলিগ্রামে চলবে। ফুল স্ক্রিন করে দেখুন।",
                parse_mode=ParseMode.MARKDOWN,
                supports_streaming=True, # এটি দিলে ভিডিও ডাউনলোড হওয়ার আগেই প্লে শুরু হবে
                width=1280,
                height=720
            )
            # ১ সেকেন্ডের বিরতি যাতে টেলিগ্রাম ব্লক না করে
            await asyncio.sleep(1.5)
        except Exception as e:
            # যদি কোনো লিঙ্ক টেলিগ্রাম প্লেয়ারে সরাসরি না চলে তবে সেটি স্কিপ হবে
            logging.warning(f"Skipping video due to error: {e}")
            continue

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("search", search))
    
    print("🚀 মাস্টার বট এখন সার্ভারে লাইভ! সরাসরি টেলিগ্রামে ভিডিও উপভোগ করুন।")
    app.run_polling()
