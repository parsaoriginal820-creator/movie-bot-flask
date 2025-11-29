import os
from flask import Flask, request
import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, CallbackQueryHandler, filters

app = Flask(__name__)
TOKEN = os.environ["BOT_TOKEN"]
bot = telegram.Bot(TOKEN)

# حالا utils رو بعد از deploy ایمپورت می‌کنیم
from utils.scraper import search_psarips, get_links_from_page

dispatcher = Dispatcher(bot, None, workers=0)

# هندلرها
def start(update, context):
    update.message.reply_text("🎬 سلام!\nاسم فیلم یا سریال بفرست تا لینک مستقیم بدم")

def search(update, context):
    query = update.message.text
    context.bot.send_chat_action(chat_id=update.message.chat_id, action="typing")
    results = search_psarips(query)
    if not results:
        update.message.reply_text("متأسفانه چیزی پیدا نشد 😔")
        return
    keyboard = [[InlineKeyboardButton(r["title"][:60], callback_data=f"sel_{i}")] for i, r in enumerate(results[:8])]
    update.message.reply_text("نتایج:", reply_markup=InlineKeyboardMarkup(keyboard))

def button(update, context):
    query = update.callback_query
    query.answer()
    idx = int(query.data.split("_")[1])
    results = search_psarips(query.message.text.split("\n")[0])  # ساده
    if idx >= len(results):
        query.edit_message_text("خطا!")
        return
    page_url = results[idx]["link"]
    query.edit_message_text("در حال گرفتن لینک‌ها...")
    links = get_links_from_page(page_url)
    if not links:
        query.edit_message_text("لینک پیدا نشد 😢")
        return
    text = "لینک‌های دانلود:\n\n"
    keyboard = [[InlineKeyboardButton(f"لینک {i+1}", url=l)] for i, l in enumerate(links)]
    query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), disable_web_page_preview=True)

dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search))
dispatcher.add_handler(CallbackQueryHandler(button))

@app.route('/webhook', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return 'ok', 200

@app.route('/set_webhook')
def set():
    bot.set_webhook(url="https://movie-bot-flask.vercel.app/webhook")
    return "Webhook set!"

if __name__ == '__main__':
    app.run()
