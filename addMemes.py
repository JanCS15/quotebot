from pathlib import Path

import psycopg2, os
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import BadRequest
from telegram.ext import ConversationHandler, ContextTypes, CallbackContext
import logging
from datetime import date

load_dotenv(dotenv_path=".env")

logging.basicConfig (format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

dbcon = psycopg2.connect(
    host=os.environ.get('PG_HOST'),
    user=os.environ.get('PG_USER'),
    dbname=os.environ.get('PG_DBNAME'),
    password=os.environ.get('PG_PASSWORD')
)
dbcur = dbcon.cursor()

# Simplifications:
dbQuery = dbcur.execute
dbFetchOne = dbcur.fetchone
dbFetchAll = dbcur.fetchall
dbCommit = dbcon.commit

MEME = range(1)

class AddMeme:
    @staticmethod
    async def start(update: Update, context: CallbackContext):
        await update.message.reply_text("Bitte sende dein Meme für den Meme Mittwoch hier rein (GIF oder Bild)")
        return MEME

    async def meme(update: Update, context: CallbackContext):
        try:
            if update.message.photo:
                photo = await update.message.photo[-1].get_file()
                path = f"./media/memes/meme_{photo.file_id}.jpg"
                await photo.download_to_drive(path)
                AddMeme.addMemeToDb(path=path, chat_id=update.effective_chat.id)
                await update.message.reply_text("Meme gespeichert, Vielen Dank")
            if update.message.animation:
                animation = await update.message.animation[-1].get_file()
                path = f"./media/memes/meme_{animation.file_id}.gif"
                await animation.download_to_drive(path)
                AddMeme.addMemeToDb(path=path, chat_id=update.effective_chat.id)
                await update.message.reply_text("Meme gespeichert, Vielen Dank")
            elif update.message.document:
                document = await update.message.document.get_file()
                file_name, file_type = os.path.splitext(update.message.document.file_name)
                file_type = file_type.lower()
                if file_type in {".jpg", ".jpeg", ".png", ".gif"}:
                    path = f"./media/{file_name}_{document.file_id}{file_type}"
                    await document.download_to_drive(path)
                    AddMeme.addMemeToDb(path=path, chat_id=update.effective_chat.id)
                    await update.message.reply_text("Datei gespeichert, Vielen Dank")
                else:
                    await update.message.reply_text("Dateityp nicht unterstützt")
                    return MEME

            await context.bot.send_message(
                chat_id=os.environ.get('ADMIN_CHAT_ID'),
                text=f"Neues Meme hochgeladen von {update.effective_chat.username}"
            )
            logger.info(f"File {path} added from {update.effective_chat.username}")
            return ConversationHandler.END

        except BadRequest as e:
            logger.info(f"Fehler: {e}")
            if "File is too big" in str(e):
                await update.message.reply_text("Fehler: Die Datei überschreitet 20 MB")

            else:
                await update.message.reply_text("Es gab ein Problem beim Herunterladen der Datei")
            return MEME

    @staticmethod
    def addMemeToDb(path, chat_id):
        dbQuery(
            "INSERT INTO memes (file_path, adddate, daily, active, addid) "
            "VALUES (%s, %s, %s, %s, %s)",
            (path, date.today(), True, True, chat_id)
        )
        dbCommit()
        logger.info(f"{path} - added to database")

    @staticmethod
    def getRandomMemeWednesday():
        dbQuery("SELECT file_path FROM memes WHERE active=True AND daily = True ORDER BY RANDOM() LIMIT 1")
        meme = dbFetchOne()
        if meme is None:
            dbQuery("UPDATE memes SET daily = True WHERE active = True")
        dbQuery("SELECT file_path FROM memes WHERE active=True AND daily = True ORDER BY RANDOM() LIMIT 1")
        meme = dbFetchOne()
        dbQuery("UPDATE memes SET daily = false WHERE file_path = %s", meme)
        dbCommit()

        return meme[0]