import concurrent
import random
from operator import add

from telegram import Update, constants
from telegram.ext import ApplicationBuilder, filters, CommandHandler, ContextTypes, Defaults, ConversationHandler, \
    MessageHandler, CallbackQueryHandler
from dotenv import load_dotenv
from os import environ as env
import logging
from quotes import Quotes
from addquote import AddQuote
from datetime import time

load_dotenv(dotenv_path=".env")

logging.basicConfig (format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)

token = env.get('TG_TOKEN')


parse_mode = constants.ParseMode.MARKDOWN_V2
FNAME, LNAME, ZITAT, YEAR, CONTEXTREQUEST, CONTEXTPROMPT, USERCONFIRM, ADMINCONFIRM = range(8)

#########################################################################################


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'Hello {update.effective_user.username}')

async def randomzitat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_input = context.args
    zitat = Quotes.getRandomQuote(user_input)
    
    await update.message.reply_text(zitat)

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

async def dailyMessage(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    quote = Quotes.getDailyMessage()
    await context.bot.send_message(chat_id=env.get('ADMIN_CHAT_ID'), text=quote)

async def fridaysMessage(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    quote = Quotes.getFridaysMessage()
    await context.bot.send_message(chat_id=env.get('ADMIN_CHAT_ID'), text=quote)

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "*Willkommen zum ZitateBot der LAN Party* \n\nCommands: \n\n /randomzitat vorname nachname \n /zitate vorname nachname \n /addzitat \n /topzitate \n\nRandom:\n /lovis \n /credits\n\n _version 2\\.0\\.0_", parse_mode=parse_mode)

async def credits(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Programmiert by Jan \n\nTechnische Hilfe: Fabian und Henning \n\nIdee Zitat des Tages: Claudio", parse_mode=parse_mode)

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.warning(f'Error {update} caused error {context.error}')

##############################################################################################################






def main():
    app = ApplicationBuilder().concurrent_updates(False).token(token).build()
    j = app.job_queue
    j.run_daily(dailyMessage, time=time(hour=18, minute=0, second=0), days=(0, 1, 2, 3, 5, 6))
    j.run_daily(fridaysMessage, time=time(hour=18, minute=0, second=0), days=(4,))

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("randomzitat", randomzitat))
    app.add_handler(CommandHandler("lovis", lovis))
    app.add_handler(CommandHandler("zitate", zitate))
    app.add_handler(CommandHandler("daily", dailyMessage))
    app.add_handler(CommandHandler("help", help))
    app.add_handler(CommandHandler("credits", credits))
    app.add_handler(
        ConversationHandler(
            entry_points=[CommandHandler("addzitat", AddQuote.start)],
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
    app.add_handler(CallbackQueryHandler(AddQuote.adminconfirm, pattern="^admin_"))
    app.add_error_handler(error)

    app.run_polling()

if __name__ == "__main__":
    main()