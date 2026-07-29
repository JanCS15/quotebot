import concurrent
import random

from telegram import Update, constants
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, Defaults, ConversationHandler, MessageHandler
from dotenv import load_dotenv
from os import environ as env
import logging
from quotes import Quotes
from addquote import Addquote

load_dotenv(dotenv_path="access.env")

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
    zitat = Quotes.getDailyMessage()

    await update.message.reply_text(zitat)

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "*Willkommen zum ZitateBot der LAN Party* \n\nCommands: \n\n /randomzitat vorname nachname \n /zitate vorname nachname \n /addzitat \n /topzitate \n\nRandom:\n /lovis \n /credits\n\n _version 2\\.0\\.0_", parse_mode=parse_mode)

async def credits(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Programmiert by Jan \n\nTechnische Hilfe: Fabian und Henning \n\nIdee Zitat des Tages: Claudio", parse_mode=parse_mode)

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.warning(f'Error {update} caused error {context.error}')

##############################################################################################################






def main():
    app = ApplicationBuilder().token(token).build()

    #app.job_queue.run_daily(dailyMessage, time=datetime.time(hour=18, minute=0, second=0), days=(0, 1, 2, 3, 5, 6))

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("randomzitat", randomzitat))
    app.add_handler(CommandHandler("lovis", lovis))
    app.add_handler(CommandHandler("zitate", zitate))
    app.add_handler(CommandHandler("daily", dailyMessage))
    app.add_handler(CommandHandler("help", help))
    app.add_handler(CommandHandler("credits", credits))
    app.add_handler(Addquote.addQuoteHandler)

    app.add_error_handler(error)

    app.run_polling()

if __name__ == "__main__":
    main()