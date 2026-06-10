import logging
import os
import requests
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

# ─── تنظیمات ───────────────────────────────────────────────
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
APPS_SCRIPT_URL = os.environ.get(
    "APPS_SCRIPT_URL",
    "https://script.google.com/macros/s/AKfycbxIqetkE4yMH0C6w7E5vFG9N7RbJ9cEmKgdxsxr85rQex1-qVQDm58kmfl3JpfVmZyQIg/exec",
)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1hDrvkAJTrtwlWNSONcRcb73vBXGUfclt/edit?usp=sharing"

# ─── لاگ ───────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ─── مراحل مکالمه ──────────────────────────────────────────
WAITING_PREDICTION = 1

# ─── کیبورد اصلی ───────────────────────────────────────────
def main_keyboard():
    return ReplyKeyboardMarkup(
        [[KeyboardButton("🎯 پیشبینی بازی"), KeyboardButton("📊 نتایج")]],
        resize_keyboard=True,
    )

# ─── /start ────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name or "دوست عزیز"
    text = (
        f"سلااام {name} 👋\n\n"
        "برای پیشبینی بازی مورد نظرت تا یک روز قبل از اون بازی وقت داری که پیشبینیت رو ارسال کنی 🕐\n\n"
        "نتایج بازی‌ها، جدول هر گروه و رنکینگ پیشبینی‌کننده‌ها رو هم می‌تونی تو گوگل شیت ببینی 📈\n\n"
        "از دکمه‌های پایین استفاده کن 👇"
    )
    await update.message.reply_text(text, reply_markup=main_keyboard())
    return ConversationHandler.END

# ─── دکمه پیشبینی بازی ─────────────────────────────────────
async def prediction_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    guide = (
        "📋 راهنمای پیشبینی\n\n"
        "پیشبینی خودت رو به این شکل بنویس:\n\n"
        "مثال: ایران ۲ - ۱ آمریکا\n\n"
        "می‌تونی چند بازی رو با هم بنویسی، هر بازی یه خط جداگانه.\n\n"
        "بعد از ارسال، پیشبینیت ثبت میشه ✅"
    )
    await update.message.reply_text(guide)
    return WAITING_PREDICTION

# ─── دریافت پیشبینی ────────────────────────────────────────
async def receive_prediction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    prediction_text = update.message.text

    # ارسال به گوگل شیت
    try:
        payload = {
            "username": user.username or user.first_name or "ناشناس",
            "user_id": str(user.id),
            "prediction": prediction_text,
        }
        requests.post(APPS_SCRIPT_URL, json=payload, timeout=10)
    except Exception as e:
        logger.error(f"خطا در ارسال به گوگل شیت: {e}")

    confirm = (
        "✅ پیشبینیت دریافت شد!\n\n"
        "پیشبینی شما به دلیل کمبود دانش برنامه‌نویسی ما به صورت دستی به گوگل شیت اضافه میشه 😅\n"
        "پس منتظر آپدیت جداول پیشبینی و نتیجه بازیا باشید 🙏\n\n"
        "با تشکر ❤️"
    )
    await update.message.reply_text(confirm, reply_markup=main_keyboard())
    return ConversationHandler.END

# ─── دکمه نتایج ────────────────────────────────────────────
async def results_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📊 نتایج و جداول\n\n"
        "نتایج بازی‌ها، جدول گروه‌ها و رنکینگ پیشبینی‌کننده‌ها رو اینجا ببین:\n\n"
        f"👉 {SHEET_URL}"
    )
    await update.message.reply_text(text, reply_markup=main_keyboard())
    return ConversationHandler.END

# ─── کنسل ──────────────────────────────────────────────────
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("انصراف داده شد.", reply_markup=main_keyboard())
    return ConversationHandler.END

# ─── main ──────────────────────────────────────────────────
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🎯 پیشبینی بازی$"), prediction_button)],
        states={
            WAITING_PREDICTION: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND & ~filters.Regex("^(📊 نتایج|🎯 پیشبینی بازی)$"),
                    receive_prediction,
                )
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            MessageHandler(filters.Regex("^📊 نتایج$"), results_button),
        ],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv)
    app.add_handler(MessageHandler(filters.Regex("^📊 نتایج$"), results_button))

    logger.info("ربات شروع به کار کرد ✅")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
