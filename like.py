import telebot
import requests
import time
import threading
import os
from flask import Flask
from threading import Thread

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running ✅"

def run():
    app.run(host='0.0.0.0', port=10000)

def keep_alive():
    t = Thread(target=run)
    t.start()
# Configurat
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found!")

bot = telebot.TeleBot(BOT_TOKEN)
ALLOWED_GROUP_ID =-1003789754832
VIP_USERS = {8550650269}
BOT_ACTIVE = True
ADMIN_ID = 8550650269
API_URL = os.getenv("API_URL")
# Tracker for daily limits
like_request_tracker = {}

bot = telebot.TeleBot(BOT_TOKEN)

def call_api(region, uid):
    url = f"{API_URL}?uid={uid}&server={region}"
    try:
        response = requests.get(url, timeout=15) # Increased timeout
        if response.status_code == 200:
            return response.json()
        return "API_ERROR"
    except Exception as e:
        print(f"API Connection Error: {e}")
        return "API_ERROR"

def process_like(message, region, uid):
    chat_id = message.chat.id
    user_id = message.from_user.id

    # Check Limit
    if user_id not in VIP_USERS and like_request_tracker.get(user_id, False):
        bot.reply_to(message, "⚠️ You have exceeded your daily request limit! ⏳ Try again later.")
        return

    # Initial Processing Message
    processing_msg = bot.reply_to(message, "⏳ **Processing Your Request...** 🔄", parse_mode="Markdown")

    try:
        # Visual Progress Updates
        updates = [
            "🔄 Fetching data from server... 10%",
            "🔄 Validating UID & Region... 30%",
            "🔄 Sending like request... 60%",
            "🔄 Almost Done... 90%"
        ]
        
        for text in updates:
            time.sleep(0.8)
            bot.edit_message_text(text, chat_id, processing_msg.message_id)

        response = call_api(region, uid)

        if response == "API_ERROR":
            bot.edit_message_text("🚨 **API ERROR!** ⚒️\nWe are fixing it, please wait. ⏳", chat_id, processing_msg.message_id, parse_mode="Markdown")
            return

        # Check if success (API returns status 1 for success)
        if response.get("status") == 1 or response.get("status") == "Success":
            if user_id not in VIP_USERS:
                like_request_tracker[user_id] = True  

            caption = (f"✅ **Like Added Successfully!**\n\n"
                       f"👤 **Nickname:** `{response.get('player', 'N/A')}`\n"
                       f"🆔 **UID:** `{uid}`\n"
                       f"📈 **Before:** `{response.get('likes_before', '0')}`\n"
                       f"📈 **After:** `{response.get('likes_after', '0')}`\n"
                       f"➕ **Added:** `{response.get('likes_added', '0')}`\n\n"
                       "🗿 **JOIN CHANNEL:** @nayakcheatss")

            # Try to send with User's Profile Photo
            try:
                photos = bot.get_user_profile_photos(user_id)
                if photos.total_count > 0:
                    file_id = photos.photos[0][-1].file_id
                    bot.delete_message(chat_id, processing_msg.message_id)
                    bot.send_photo(chat_id, file_id, caption=caption, parse_mode="Markdown")
                else:
                    bot.edit_message_text(caption, chat_id, processing_msg.message_id, parse_mode="Markdown")
            except:
                bot.edit_message_text(caption, chat_id, processing_msg.message_id, parse_mode="Markdown")
        
        else:
            # Handle API rejection (Already liked/Limit reached)
            error_msg = response.get("message", "UID has already received Max Likes for Today.")
            bot.edit_message_text(f"💔 **Limit Reached** 💔\n\n`{error_msg}`\n🔄 Try a different UID.", 
                                  chat_id, processing_msg.message_id, parse_mode="Markdown")

    except Exception as e:
        print(f"Error in process_like: {e}")
        bot.send_message(chat_id, "❌ An unexpected error occurred. Please try again.")
@bot.message_handler(commands=['on'])
def bot_on(message):
    global BOT_ACTIVE
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ 𝐍ᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ")
        return

    BOT_ACTIVE = True
    bot.reply_to(message, "🟢 ʙᴏᴛ ɪs ɴᴏᴡ ᴏɴ ")
@bot.message_handler(commands=['off'])
def bot_off(message):
    global BOT_ACTIVE
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ")
        return

    BOT_ACTIVE = False
    bot.reply_to(message, "🔴 ʙᴏᴛ ɪs ɴᴏᴡ ᴏғғ")
@bot.message_handler(commands=['like'])
def handle_like(message):
    chat_id = message.chat.id
    if not BOT_ACTIVE:
        bot.reply_to(message, "🚫 ʙᴏᴛ ɪs ᴄᴜʀʀᴇɴᴛʟʏ ᴏғғ")
        return
    # Group Restriction
    if chat_id != ALLOWED_GROUP_ID:
        bot.reply_to(message, "🚫 This group is not authorized to use this bot!")
        return

    args = message.text.split()
    if len(args) != 3:
        bot.reply_to(message, "❌ **Incorrect Format!**\n\nUse: `/like {region} {uid}`\nExample: `/like ind 1559920553`", parse_mode="Markdown")
        return

    region, uid = args[1].lower(), args[2]

    # Validation
    if not uid.isdigit():
        bot.reply_to(message, "⚠️ **Invalid UID!** Please provide numbers only.")
        return

    # Run in thread to prevent bot lagging
    threading.Thread(target=process_like, args=(message, region, uid)).start()

print("Bot is running...")
keep_alive()
bot.polling(none_stop=True)
