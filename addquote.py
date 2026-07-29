from os import environ as env
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler, filters
import psycopg2
from quotes import Quotes, getAllowedChatIds


load_dotenv(dotenv_path="access.env")
dbcon = psycopg2.connect(host=env.get('PG_HOST'), user=env.get('PG_USER'), dbname=env.get('PG_DBNAME'), password=env.get('PG_PASSWORD'))
dbcur = dbcon.cursor()

dbQuery = dbcur.execute
dbFetchOne = dbcur.fetchone
dbFetchAll = dbcur.fetchall
dbCommit = dbcon.commit

FNAME, LNAME, QUOTE, YEAR, CONTEXTREQUEST, CONTEXTPROMPT, USERCONFIRM, ADMINCONFIRM = range(8)


class Addquote:

    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        update.message.reply_text("Hi, bitte gebe den Vornamen der Person ein.\n\n" "Zum stoppen des Vorgangs bitte /cancel eingeben")
        return FNAME
    
    async def fname(update: Update, context: ContextTypes.DEFAULT_TYPE):
        input = update.message.text.lower()
        dbQuery("SELECT fname, lname FROM persons WHERE fname = %s", [input])
        existingNames = dbFetchAll()

        if input == "/cancel":
            update.message.reply_text("Bis zum nächsten Mal")
            return ConversationHandler.END
            
        elif not existingNames:
            update.message.reply_text("Es gibt keine Person mit diesem Vornamen, bitte gebe erneut einen Namen ein oder beende mit /cancel!")
            return FNAME

        elif len(existingNames) == 1:
            context.user_data[0] = existingNames[0][0]
            context.user_data[1] = existingNames[0][1]

            update.message.reply_text("Bitte gebe das Zitat für " + existingNames[0][0].capitalize() + " " + existingNames[0][1].capitalize() + " ein")
            return QUOTE

        elif len(existingNames) > 1:
            context.user_data[0] = existingNames[0][0]

            keyboard = []
            for row in existingNames:
                keyboard.append([InlineKeyboardButton(row[1], callback_data=row[1])])

            markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text("Welchen " + input.capitalize() + " meintest du? ", reply_markup=markup)
            return LNAME

    async def lname(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        lname = update.callback_query.data

        query.answer("Du hast " + context.user_data[0] + " " + lname.capitalize() + " gewählt. Bitte gebe das Zitat ein")
        context.user_data[1] = lname

        return QUOTE

    async def quote(update: Update, context: ContextTypes.DEFAULT_TYPE):
        return ConversationHandler.END

    async def cancel(update: Update):
        update.message.reply_text("Bis dann!")
        return ConversationHandler.END

    addQuoteHandler = ConversationHandler(
        entry_points=[CommandHandler("addzitat", start, filters.Chat(getAllowedChatIds()))],
        states={
            FNAME: [MessageHandler(filters.TEXT, fname)],
            LNAME: [MessageHandler(filters.TEXT, lname)],
            QUOTE: [MessageHandler(filters.TEXT, quote)] 
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )


    