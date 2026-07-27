import logging
import httpx
import asyncio
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- আপনার টেলিগ্রাম বট টোকেন ---
TOKEN = '8628858496:AAGNVfI_VANOVUGyQnw16M-6ef3yHN7B1yU'

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- ভিডিও সোর্স এপিআই লিস্ট (এখানে ১০টি বা তার বেশি সোর্স যোগ করা হয়েছে) ---
# নোট: কিছু API একই ফরম্যাট ফলো করে, কিছু আলাদা। এখানে জেনেরিক স্ট্রাকচার দেওয়া হলো।
API_SOURCES = [
    "https://xvidapi.com/api.php/provide/vod?ac=detail&at=json&wd=",
    "https://api.xfantasy.tv/v1/search?keyword=", # উদাহরণ API
    "https://avtop.cc/api.php/provide/vod?ac=detail&at=json&wd=",
    "https://www.heimatuer.com/api.php/provide/vod/at/json/?wd=",
    "https://toptv.com/api.php/provide/vod?ac=detail&at=json&wd=",
    # আরও সোর্স এখানে যোগ করতে পারেন...
]

async def fetch_from_source(client, url, query):
    try:
        response = await client.get(f"{url}{query}", timeout=15)
        if response.status_code == 200:
            data = response.json()
            # বেশিরভাগ এশিয়ান এবং অ্যাডাল্ট CMS (AppleCMS) এই ফরম্যাট ফলো করে
            return data.get('list', [])
    except Exception as e:
        logging.error(f"Source Error ({url}): {e}")
    return []

async def get_all_videos(query):
    videos_list = []
    async with httpx.AsyncClient(verify=False) as client:
        # সবগুলো এপিআই থেকে একসাথে ডাটা ফেচ করা (Concurrency)
        tasks = [fetch_from_source(client, url, query) for url in API_SOURCES]
        results = await asyncio.gather(*tasks)
        
        for result in results:
            for item in result:
                title = item.get('vod_name', 'No Title')
                thumb = item.get('vod_pic', '')
                
                # অনেক সময় প্লে লিঙ্কে একাধিক কোয়ালিটি থাকে, আমরা শেষ অংশটি নিব
                raw_url = item.get('vod_play_url', '')
                if not raw_url: continue
                
                # ডাইরেক্ট লিঙ্ক এক্সট্রাক্ট করা
                play_url = raw_url.split('$')[-1]
                
                if play_url.startswith('http'):
                    videos_list.append({
                        'title': title,
                        'thumb': thumb,
                        'url': play_url
                    })
    
    # ডুপ্লিকেট ভিডিও রিমুভ করা (টাইটেল দিয়ে)
    unique_videos = {v['title']: v for v in videos_list}.values()
    return list(unique_videos)[:20] # প্রথম ২০টি রেজাল্ট দেখাবে

# স্টার্ট কমান্ড
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 **MASTERS CLOUD X-HUB V10 ONLINE**\n\n"
        "এখন সরাসরি টেলিগ্রামে ভিডিও প্লে হবে!\n"
        "🔍 সার্চ করতে লিখুন: `/search desi`",
        parse_mode=ParseMode.MARKDOWN
    )

# ভিডিও সেন্ডিং ফাংশন
async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args)
    if not query:
        await update.message.reply_text("❌ সার্চ করার জন্য কিছু লিখুন!")
        return
    
    status = await update.message.reply_text(f"🔎 ১০টি সার্ভারে **'{query}'** খোঁজা হচ্ছে...", parse_mode=ParseMode.MARKDOWN)
    
    videos = await get_all_videos(query)
    
    if not videos:
        await status.edit_text("😔 দুঃখিত, কোনো ভিডিও পাওয়া যায়নি। অন্য কিছু লিখে সার্চ করুন।")
        return

    await status.delete()
    
    for v in videos:
        try:
            # সরাসরি ভিডিও হিসেবে পাঠানো
            # supports_streaming=True দিলে টেলিগ্রাম প্লেয়ারে সাথে সাথে চালু হয়
            await update.message.reply_video(
                video=v['url'],
                thumbnail=v['thumb'], # থাম্বনেইল সরাসরি ইউআরএল থেকে নিবে
                caption=f"🎬 **{v['title']}**\n\n✅ সরাসরি প্লে হবে | ফুল স্ক্রিন করুন",
                parse_mode=ParseMode.MARKDOWN,
                supports_streaming=True,
                width=1280,
                height=720
            )
            await asyncio.sleep(1) # টেলিগ্রাম ফ্লাড কন্ট্রোল
        except Exception as e:
            # যদি ভিডিও ডাইরেক্ট প্লে না হয়, তবে লিঙ্ক হিসেবে পাঠানো
            logging.warning(f"Failed to send video: {e}")
            await update.message.reply_text(
                f"🔗 **{v['title']}**\n\nএই ভিডিওটি সরাসরি প্লে হচ্ছে না, লিঙ্কে ক্লিক করুন:\n[প্লে ভিডিও]({v['url']})",
                parse_mode=ParseMode.MARKDOWN
            )

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("search", search))
    
    print("✅ বট এখন অনলাইন। সরাসরি ভিডিও লোড করার জন্য প্রস্তুত।")
    app.run_polling()
