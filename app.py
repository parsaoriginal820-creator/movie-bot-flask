import os
from flask import Flask, request
import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from utils.scraper import search_psarips, get_links_from_page

app = Flask(__name__)

TOKEN = os.environ.get("BOT_TOKEN")
bot = telegram.Bot(token=TOKEN)
application = Application.builder().token(TOKEN).build()

DOMAIN = "https://movie-bot-flask.vercel.app"  # بعد از deploy، این رو با دامنه خودت عوض کن

# هندلرها (همون کد قبلی)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎬 سلام! اسم فیلم یا سریال بفرست تا لینک مستقیم بدم\nمثال: Oppenheimer")

async def search_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    await update.message.reply_chat_action("typing")
    results = search_psarips(query)
    
    if not results:
        await update.message.reply_text("چیزی پیدا نشد 😔\nدوباره امتحان کن")
        return

    keyboard = [[InlineKeyboardButton(res["title"][:50], callback_data=f"movie_{res['link']}")] for res in results]
    await update.message.reply_text("نتایج جستجو:", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("movie_"):
        url = query.data.replace("movie_", "")
        await query.edit_message_text("در حال استخراج لینک‌ها... ⏳")
        
        links = get_links_from_page(url)
        
        if not links:
            await query.edit_message_text("لینک پیدا نشد 😢")
            return
            
        text = "لینک‌های دانلود:\n\n"
        keyboard = []
        for i, link in enumerate(links, 1):
            text += f"{i}. {link}\n\n"
            keyboard.append([InlineKeyboardButton(f"لینک {i}", url=link)])
        
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), disable_web_page_preview=True)

# اضافه کردن هندلرها
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_movie))
application.add_handler(CallbackQueryHandler(button_callback))

# ورسل endpoint
@app.route('/webhook', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    application.process_update(update)
    return 'ok'

# ست کردن وب‌هوک (فقط یک‌بار اجرا کن)
@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    webhook_url = f"{DOMAIN}/webhook"
    bot.setWebhook(webhook_url)
    return f"Webhook set to {webhook_url}"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
