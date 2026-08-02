from os import environ as env
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler, \
    filters, CallbackContext

from quotes import Quotes

NAME, QUOTES, END = range(3)
class GetQuotes:
    async def start(update: Update, context: CallbackContext):
        zitat = Quotes.getQuotes(context.args, offset=0)
        if not zitat:
