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
            requests.get("https://Tui--ha-thanhthanh5.repl.co")
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
        ],
        [
            InlineKeyboardButton("🏆 BXH Ref", callback_data="top"),
            InlineKeyboardButton("📊 Thống kê", callback_data="stats")
        ]
    ]
    await update.message.reply_text("👇 Chọn chức năng:", reply_markup=InlineKeyboardMarkup(keyboard))

# --- Buttons ---
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if not await is_member(user_id, context):
        join_buttons = [[InlineKeyboardButton("🔗 Tham gia nhóm", url=GROUP_JOIN_LINK)]]
        await query.edit_message_text("🚫 Bạn cần tham gia nhóm để sử dụng bot!", reply_markup=InlineKeyboardMarkup(join_buttons))
        return

    if USER_DATA.get(user_id, {}).get("banned", False):
        await query.edit_message_text("🚫 Bạn đã bị chặn khỏi hệ thống.")
        return

    data = query.data
    user = USER_DATA[user_id]

    if data == "balance":
        await query.edit_message_text(f"💰 Số dư: {user['balance']}đ\n👥 Lượt mời: {user['ref_count']}")
    elif data == "ref":
        link = f"https://t.me/{context.bot.username}?start={user_id}"
        await query.edit_message_text(f"📨 Link mời của bạn:\n{link}\n\n💵 Mỗi lượt mời nhận 3.500đ")
    elif data == "withdraw":
        await query.edit_message_text("💸 Nhập số tiền muốn rút (tối thiểu 20.000đ):")
        return WITHDRAW
    elif data == "checkin":
        today = datetime.date.today()
        if user['last_checkin'] == today:
            await query.edit_message_text("✅ Bạn đã điểm danh hôm nay rồi.")
        else:
            user['last_checkin'] = today
            user['balance'] += 1000
            await query.edit_message_text("🎉 Điểm danh thành công! Nhận 1.000đ.")
    elif data == "top":
        top = sorted(USER_DATA.items(), key=lambda x: x[1]['ref_count'], reverse=True)
        msg = "\n".join([f"{i+1}. ID {u[0]} - {u[1]['ref_count']} lượt mời" for i, u in enumerate(top[:5])])
        await query.edit_message_text("🏆 Top ref:\n" + msg)
    elif data == "stats":
        total_users = len(USER_DATA)
        total_balance = sum(u['balance'] for u in USER_DATA.values())
        await query.edit_message_text(
            f"📊 Thống kê:\n👥 Tổng user: {total_users}\n💸 Đã rút: {TOTAL_WITHDRAWN}đ\n💰 Còn lại: {total_balance}đ")

    return ConversationHandler.END

# --- Handle Withdraw ---
async def handle_withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global TOTAL_WITHDRAWN
    user_id = update.message.from_user.id
    user = USER_DATA.get(user_id)

    try:
        amount = int(update.message.text)
        if amount >= 20000 and user['balance'] >= amount:
            user['balance'] -= amount
            TOTAL_WITHDRAWN += amount
            await update.message.reply_text(f"✅ Yêu cầu rút {amount}đ đã được ghi nhận!")
        else:
            await update.message.reply_text("🚫 Số tiền không hợp lệ hoặc không đủ số dư.")
    except:
        await update.message.reply_text("⚠️ Vui lòng nhập số tiền hợp lệ.")

    return ConversationHandler.END

# --- Gửi top ref mỗi tuần ---
async def send_weekly_top(bot):
    if not USER_DATA:
        return

    top = sorted(USER_DATA.items(), key=lambda x: x[1]['ref_count'], reverse=True)
    if not top:
        return

    msg = "📊 BẢNG XẾP HẠNG REF TUẦN:\n\n"
    for i, (uid, data) in enumerate(top[:5]):
        msg += f"{i+1}. ID {uid} - {data['ref_count']} lượt mời\n"

    if len(top) >= 1:
        USER_DATA[top[0][0]]['balance'] += 10000
        msg += f"\n🥇 Top 1 được thưởng 10.000đ"
    if len(top) >= 2:
        USER_DATA[top[1][0]]['balance'] += 5000
        msg += f"\n🥈 Top 2 được thưởng 5.000đ"

    await bot.send_message(chat_id=GROUP_ID, text=msg)
    for u in USER_DATA.values():
        u['ref_count'] = 0

# --- Main ---
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(buttons, pattern="withdraw")],
        states={WITHDRAW: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_withdraw)]},
        fallbacks=[]
    )
    app.add_handler(conv)

    # Tự ping bản thân giữ Replit sống
    asyncio.get_event_loop().create_task(auto_ping())

    # Gửi top ref mỗi thứ 2 lúc 8h sáng
    @aiocron.crontab("0 8 * * MON")
    async def weekly_task():
        await send_weekly_top(app.bot)

    app.run_polling()

if __name__ == "__main__":
    main()
