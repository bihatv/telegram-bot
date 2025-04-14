from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ConversationHandler, ContextTypes
)
import logging
import datetime
import asyncio
import aiocron
import requests
from flask import Flask
from threading import Thread

# --- Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Config ---
TOKEN = "8097927539:AAE4iAQS-O6pS27x0e3FQuVQY7gZE2qYXbI"
GROUP_ID = -1002587301398
GROUP_JOIN_LINK = "https://t.me/hupcodenhacai1"
ADMIN_IDS = [7014048216]

# --- States ---
WITHDRAW = range(1)

# --- Data ---
USER_DATA = {}
TOTAL_WITHDRAWN = 0

# --- Flask keep-alive ---
app_flask = Flask('')

@app_flask.route('/')
def home():
    return "Bot đang chạy!"

def run():
    app_flask.run(host='0.0.0.0', port=8080)

Thread(target=run).start()

# --- Auto Ping ---
async def auto_ping():
    while True:
        try:
            requests.get("https://telegram-bot-017s.onrender.com")
        except:
            pass
        await asyncio.sleep(280)

# --- Check group membership ---
async def is_member(user_id: int, context: ContextTypes.DEFAULT_TYPE):
    try:
        member = await context.bot.get_chat_member(GROUP_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

# --- Start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id

    if not await is_member(user_id, context):
        join_buttons = [[InlineKeyboardButton("🔗 Tham gia nhóm", url=GROUP_JOIN_LINK)]]
        await update.message.reply_text("🚫 Bạn cần tham gia nhóm để sử dụng bot!", reply_markup=InlineKeyboardMarkup(join_buttons))
        return

    if USER_DATA.get(user_id, {}).get("banned", False):
        await update.message.reply_text("🚫 Bạn đã bị chặn khỏi hệ thống.")
        return

    if user_id not in USER_DATA:
        ref = update.message.text.split(' ')[1] if len(update.message.text.split(' ')) > 1 else None
        USER_DATA[user_id] = {
            'balance': 0,
            'ref': ref,
            'ref_count': 0,
            'last_checkin': None,
            'banned': False,
        }
        if ref and ref.isdigit() and int(ref) != user_id and int(ref) in USER_DATA:
            if not USER_DATA[int(ref)].get("banned", False):
                USER_DATA[int(ref)]['balance'] += 3500
                USER_DATA[int(ref)]['ref_count'] += 1

    await show_menu(update, context)

# --- Show Menu ---
async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("💰 Số dư", callback_data="balance"),
            InlineKeyboardButton("👥 Mời bạn", callback_data="ref")
        ],
        [
            InlineKeyboardButton("💸 Rút tiền", callback_data="withdraw"),
            InlineKeyboardButton("✅ Điểm danh", callback_data="checkin")
        ]
    ]
    await update.message.reply_text("Chào mừng bạn đến với bot!", reply_markup=InlineKeyboardMarkup(keyboard))

# --- Main ---
if __name__ == '__main__':
    import asyncio

    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    # Bạn có thể thêm các handler khác tại đây

    # Chạy auto_ping song song
    asyncio.get_event_loop().create_task(auto_ping())

    # Chạy bot
    application.run_polling()

