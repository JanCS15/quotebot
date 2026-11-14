import concurrent
import random
from operator import add

from telegram import Update, constants
from telegram.ext import ApplicationBuilder, filters, CommandHandler, ContextTypes, Defaults, ConversationHandler, \
    MessageHandler, CallbackQueryHandler
from dotenv import load_dotenv
from os import environ as env
from zoneinfo import ZoneInfo
import logging
from pathlib import Path
from quotes import Quotes, getAllowedChatIds
from addquote import AddQuote
from addMemes import AddMeme
from datetime import time

load_dotenv(dotenv_path=".env")

logging.basicConfig (format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)

token = env.get('TG_TOKEN')


parse_mode = constants.ParseMode.MARKDOWN_V2
FNAME, LNAME, ZITAT, YEAR, CONTEXTREQUEST, CONTEXTPROMPT, USERCONFIRM, ADMINCONFIRM = range(8)
MEME = range(1)
#########################################################################################


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'Hello {update.effective_user.username}')

async def randomzitat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_input = context.args
    zitat = Quotes.getRandomQuote(user_input)
    
    await update.message.reply_text(zitat)

async def randomMemeWednesday(context: ContextTypes.DEFAULT_TYPE) -> None:
    meme = AddMeme.getRandomMemeWednesday()
    meme = Path(meme)
    print("test")
    if meme.suffix == ".jpg" or meme.suffix == ".png":
        await context.bot.send_photo(chat_id=env.get('GROUP_CHAT'),photo=meme, caption="Es ist Mittwoch meine Freunde")
    elif meme.suffix == ".gif":
        await context.bot.send_animation(chat_id=env.get('GROUP_CHAT'),animation=meme, caption="Es ist Mittwoch meine Freunde")

async def zitate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_input = context.args
    zitat = Quotes.getQuotes(user_input)

    await update.message.reply_text(zitat)

async def lovis(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    x = random.randint(3, 20)
    countO = ""
    for i in range(x):
        countO += "o"
    await update.message.reply_text(text="L" + countO + "vis!")

async def dailyMessage(context: ContextTypes.DEFAULT_TYPE) -> None:
    quote = Quotes.getDailyMessage()
    await context.bot.send_message(chat_id=env.get('GROUP_CHAT'), text=quote)

async def fridaysMessage(context: ContextTypes.DEFAULT_TYPE) -> None:
    quote = Quotes.getFridaysMessage()
    await context.bot.send_message(chat_id=env.get('GROUP_CHAT'), text=quote)

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "*Willkommen zum ZitateBot der LAN Party* \n\nCommands: \n\n /randomzitat vorname nachname \n /zitate vorname nachname \n /addmeme \n /addzitat \n\nRandom:\n /lovis \n /credits\n\n _version 2\\.0\\.0_", parse_mode=parse_mode)

async def credits(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Programmiert by Jan \n\nTechnische Hilfe: Fabian und Henning \n\nIdee Zitat des Tages: Claudio", parse_mode=parse_mode)

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.warning(f'Error {update} caused error {context.error}')

##############################################################################################################

def main():
    app = ApplicationBuilder().concurrent_updates(False).token(token).build()
    tz = ZoneInfo("Europe/Berlin")
    chat_filter = filters.Chat(chat_id=getAllowedChatIds())

    j = app.job_queue
    j.run_daily(callback=dailyMessage, time=time(hour=18, minute=0, second=0, tzinfo=tz), days=(0, 1, 2, 3, 5, 6), chat_id=env.get("GROUP_CHAT"))
    j.run_daily(callback=fridaysMessage, time=time(hour=18, minute=0, second=0, tzinfo=tz), days=(4,), chat_id=env.get("GROUP_CHAT"))
    j.run_daily(callback=randomMemeWednesday, time=time(hour=17, minute=35, second=0, tzinfo=tz), days=(0, 1, 2, 3, 4, 5, 6), chat_id=env.get("GROUP_CHAT"))

    app.add_handler(CommandHandler("start", start, filters=chat_filter))
    app.add_handler(CommandHandler("randomzitat", randomzitat, filters=chat_filter))
    app.add_handler(CommandHandler("lovis", lovis, filters=chat_filter))
    app.add_handler(CommandHandler("zitate", zitate, filters=chat_filter))
    app.add_handler(CommandHandler("help", help, filters=chat_filter))
    app.add_handler(CommandHandler("credits", credits, filters=chat_filter))
    app.add_handler(
        ConversationHandler(
            entry_points=[CommandHandler("addzitat", AddQuote.start, filters=chat_filter)],
            states={
                FNAME: [
                    MessageHandler(filters.TEXT, AddQuote.fname),
                    MessageHandler(filters.VIDEO | filters.PHOTO | filters.AUDIO | filters.Document.ALL, AddQuote.addMedia)
                ],
                LNAME: [CallbackQueryHandler(AddQuote.lname)],
                ZITAT: [MessageHandler(filters.TEXT, AddQuote.zitat)],
                YEAR: [MessageHandler(filters.TEXT, AddQuote.year)],
                CONTEXTREQUEST: [CallbackQueryHandler(AddQuote.contextRequest)],
                CONTEXTPROMPT: [MessageHandler(filters.TEXT, AddQuote.contextPrompt)],
                USERCONFIRM: [CallbackQueryHandler(AddQuote.userconfirm)]
            },
            fallbacks = [CommandHandler("cancel", AddQuote.cancel)],
        )
    )
    app.add_handler(
        ConversationHandler(
            entry_points=[CommandHandler("addmeme", AddMeme.start, filters=chat_filter)],
            states={
                MEME: [MessageHandler(filters.PHOTO | filters.ANIMATION | filters.Document.ALL, AddMeme.meme)],
            },
            fallbacks = [CommandHandler("cancel", AddQuote.cancel)],
        )
    )
    app.add_handler(CallbackQueryHandler(AddQuote.adminconfirm, pattern="^admin_"))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), log_message))
    app.add_error_handler(error)

    app.run_polling()


async def log_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # User-Informationen und Nachrichtentext extrahieren
    user = update.message.from_user
    text = update.message.text

    # 2. Die Nachricht im Log anzeigen
    logger.info(f"Nachricht von {user.id} (ID: {user.id}): {text}")

if __name__ == "__main__":
    main()