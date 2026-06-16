import random
import sqlite3
from datetime import time

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters,
)

# =========================
#تنظیمات
# =========================
TOKEN = ""
ADMINS = [	]  # آیدی عددی

# =========================
#دیتابیس
# =========================
conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    name TEXT,
    score INTEGER DEFAULT 0,
    study INTEGER DEFAULT 0
)
""")
conn.commit()

def get_user(uid, name):
    cursor.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (user_id, name, score, study) VALUES (?, ?, 0, 0)", (uid, name))
        conn.commit()

def add_score(uid, val):
    cursor.execute("UPDATE users SET score = score + ? WHERE user_id=?", (val, uid))
    conn.commit()

def add_study(uid, val):
    cursor.execute("UPDATE users SET study = study + ? WHERE user_id=?", (val, uid))
    conn.commit()

def get_user_data(uid):
    cursor.execute("SELECT score, study FROM users WHERE user_id=?", (uid,))
    return cursor.fetchone()

def leaderboard():
    cursor.execute("SELECT name, score FROM users ORDER BY score DESC LIMIT 10")
    return cursor.fetchall()

# =========================
#جملات
# =========================
replies = {
    "سلام": ["سلام عزیزم ", "سلام درسخون 😁📚", "سلام قهرمان آینده "],
    "بابات": ["بیناموس گروه درسیه", "گمشو بیرون از گروه"],
    "باباته": ["بیناموس گروه درسیه", "گمشو بیرون از گروه"],
    "شب بخیر": ["شبت بخیر درسخون جون 🌙", "بخواب که فردا میزنن "],
    "بای": ["به سلامت ", "فعلاً خدافظ قهرمان 😎"],
    "خدافظ": ["به سلامت ", "فعلاً خدافظ قهرمان 😎"],
    "خداحافظ": ["به سلامت ", "فعلاً خدافظ قهرمان 😎"],
}

motivations = [
    "📚 بخون که فردا حسرت نخوری",
    "🔥 پشتکار = رتبه خوب",
    "🚀 امروز سختی = فردا موفقیت",
    "😴 بیدار شو رقیب خواب نیست"
]

# =========================
#ثبت کاربر
# =========================
def ensure(update: Update):
    user = update.message.from_user
    get_user(user.id, user.first_name)

# =========================
#پیام‌ها
# =========================
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user = update.message.from_user

    ensure(update)

    # پاسخ حساس
    if text in replies:
        await update.message.reply_text(random.choice(replies[text]))
        return

    # پروفایل
    if text == "پروفایل":
        target = user
        if update.message.reply_to_message:
            target = update.message.reply_to_message.from_user

        score, study = get_user_data(target.id)
        level = (score // 100) + 1

        await update.message.reply_text(
            f"👤 {target.first_name}\n"
            f"⭐ امتیاز: {score}\n"
            f"📚 مطالعه: {study} دقیقه\n"
            f"🏆 لول: {level}"
        )
        return

    # جدول
    if text == "جدول":
        rows = leaderboard()
        msg = "🏆 رتبه بندی:\n\n"
        for i, r in enumerate(rows, 1):
            msg += f"{i}. {r[0]} — {r[1]} امتیاز\n"
        await update.message.reply_text(msg)
        return

    # ثبت مطالعه فقظ ادمین
    if text.startswith("مطالعه"):
        if user.id not in ADMINS:
            await update.message.reply_text("مگه ادمینی تو")
            return

        if not update.message.reply_to_message:
            await update.message.reply_text("ریپلای کن دیوونه")
            return

        try:
            minutes = int(text.split()[1])
        except:
            await update.message.reply_text("یه عدد درست بنویس")
            return

        target = update.message.reply_to_message.from_user
        get_user(target.id, target.first_name)

        add_study(target.id, minutes)
        add_score(target.id, minutes // 10)

        await update.message.reply_text("🔥 ثبت شد، دمت گرم!")
        return

# =========================
#ورود به گروه
# =========================
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام بچه های درسخون 😎📚\n"
        "من بات گروه هستم، آماده جنگ کنکور باشید 🔥😂"
    )

# =========================
#انگیزشی
# =========================
async def motivation_job(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    await context.bot.send_message(chat_id, random.choice(motivations))

# =========================
#گزارش شب
# =========================
async def night_report(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    rows = leaderboard()

    msg = "🌙 گزارش شبانه:\n\n"
    for i, r in enumerate(rows[:5], 1):
        msg += f"{i}. {r[0]} — {r[1]} امتیاز\n"

    await context.bot.send_message(chat_id, msg)

# =========================
#اجرا
# =========================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))

# هر 1 ساعت انگیزشی
app.job_queue.run_repeating(motivation_job, interval=3600, first=10)

# گزارش شب 22:00
app.job_queue.run_daily(night_report, time=time(22, 0))

print("Bot is running...")
app.run_polling()
