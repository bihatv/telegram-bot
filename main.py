from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes
)
import logging
import datetime
import asyncio
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
    except Exception as e:
        print(f"Lỗi kiểm tra nhóm: {e}")
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

# --- Button Callback Handler ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "balance":
        balance = USER_DATA.get(user_id, {}).get("balance", 0)
        await query.edit_message_text(f"💰 Số dư hiện tại của bạn: {balance}đ")
    elif query.data == "ref":
        ref_link = f"https://t.me/{context.bot.username}?start={user_id}"
        ref_count = USER_DATA.get(user_id, {}).get("ref_count", 0)
        await query.edit_message_text(f"👥 Mời bạn qua link: {ref_link}\nĐã mời: {ref_count} người")
    elif query.data == "withdraw":
        await query.edit_message_text("💸 Nhập số tiền bạn muốn rút (ví dụ: 20000):")
        return WITHDRAW
    elif query.data == "checkin":
        now = datetime.datetime.now().date()
        last_checkin = USER_DATA[user_id].get("last_checkin")
        if last_checkin == now:
            await query.edit_message_text("❌ Bạn đã điểm danh hôm nay rồi.")
        else:
            USER_DATA[user_id]["last_checkin"] = now
            USER_DATA[user_id]["balance"] += 1000
            await query.edit_message_text("✅ Điểm danh thành công! Bạn nhận được 1.000đ.")

# --- Main ---
if __name__ == '__main__':
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))

    asyncio.get_event_loop().create_task(auto_ping())

    application.run_polling()




