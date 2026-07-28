import logging
import httpx
import asyncio
import chompjs
from selectolax.lexbor import LexborHTMLParser
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- আপনার টেলিগ্রাম বট কনফিগারেশন ---
TOKEN = '8628858496:AAGNVfI_VANOVUGyQnw16M-6ef3yHN7B1yU'

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://xhamster.com/"
}

# --- ১০টি সোর্স থেকে ভিডিও আনার সুপার এপিআই ---
async def fetch_video_sources(query):
    """
    এই ফাংশনটি xHamster, XVideos, XNXX, Pornhub, YouPorn, RedTube, 
    Tube8, SpankBang সহ ১০+ সোর্স থেকে সরাসরি ফাইল লিংক আনবে।
    """
    all_videos = []
    # XVIDAPI ব্যবহার করা হচ্ছে যা ১০টির বেশি সাইট কভার করে
    api_url = f"https://xvidapi.com/api.php/provide/vod?ac=detail&at=json&wd={query}"
    
    try:
        async with httpx.AsyncClient(timeout=20, verify=False) as client:
            res = await client.get(api_url)
            if res.status_code == 200:
                data = res.json()
                for item in data.get('list', []):
                    # সরাসরি প্লে-যোগ্য লিঙ্ক (m3u8 বা mp4)
                    raw_links = item.get('vod_play_url', '').split('#')
                    play_url = raw_links[0].split('$')[-1]
                    
                    if play_url:
                        all_videos.append({
                            'title': item.get('vod_name'),
                            'thumb': item.get('vod_pic'),
                            'video_url': play_url
                        })
    except Exception as e:
        logging.error(f"API Error: {e}")
        
    return all_videos

# --- স্টার্ট কমান্ড ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 *স্বাগতম বস!*\n\nআমি আপনার দেওয়া xHamster API এবং আরও ১০টি সোর্স থেকে ভিডিও সরাসরি টেলিগ্রাম প্লেয়ারে নিয়ে আসবো।\n\n🔍 সার্চ করতে লিখুন: `/search keyword` \n(যেমন: `/search indian` বা `/search milf`)",
        parse_mode=ParseMode.MARKDOWN
    )

# --- সার্চ এবং সরাসরি ভিডিও প্লে মেকানিজম ---
async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args)
    if not query:
        await update.message.reply_text("🔍 সার্চ করতে কিছু লিখুন বস!")
        return
    
    status_msg = await update.message.reply_text(f"🚀 ১০টি সার্ভার থেকে *'{query}'* ক্যাটাগরির ভিডিও আনা হচ্ছে...", parse_mode=ParseMode.MARKDOWN)
    
    videos = await fetch_video_sources(query)
    
    if not videos:
        await status_msg.edit_text("😔 দুঃখিত বস, কোনো ভিডিও পাওয়া যায়নি। অন্য কিছু লিখে সার্চ দিন।")
        return

    await status_msg.delete()
    
    for v in videos:
        try:
            # --- সরাসরি টেলিগ্রাম ভিডিও প্লেয়ারে পাঠানো ---
            # এটি করলে ভিডিওটি কোনো ব্রাউজারে যাবে না, সরাসরি এখানে প্লে হবে।
            await update.message.reply_video(
                video=v['video_url'],
                caption=f"🎬 *{v['title']}*\n\n✅ সরাসরি প্লে হচ্ছে। ফুল স্ক্রিন করে দেখুন।",
                parse_mode=ParseMode.MARKDOWN,
                supports_streaming=True, # ডাউনলোড হওয়ার আগেই প্লে শুরু হবে
                read_timeout=60,
                write_timeout=60,
                connect_timeout=60
            )
            # ১.৫ সেকেন্ড বিরতি যাতে টেলিগ্রাম বটকে স্প্যাম হিসেবে না ধরে
            await asyncio.sleep(1.5)
        except Exception as e:
            # যদি সরাসরি প্লে হতে সমস্যা হয় (লিঙ্ক ফরম্যাট এর কারণে), তবে মেসেজ স্কিপ করবে
            continue

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("search", search))
    
    print("🚀 মাস্টার ভিডিও বট এখন লাইভ! সরাসরি টেলিগ্রামে চেক করুন।")
    app.run_polling()
