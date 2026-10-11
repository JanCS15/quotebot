import psycopg2, os
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import BadRequest
from telegram.ext import ConversationHandler, ContextTypes, CallbackContext
import logging
from datetime import date

load_dotenv(dotenv_path=".env")

logging.basicConfig (format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

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

FNAME, LNAME, ZITAT, YEAR, CONTEXTREQUEST, CONTEXTPROMPT, USERCONFIRM, ADMINCONFIRM = range(8)


class AddQuote:

    @staticmethod
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "Hi, bitte gebe den Vornamen der Person ein oder lade ein Bild, eine Sprachnachricht oder ein Video hoch.\n\nZum stoppen des Vorgangs bitte /cancel eingeben")
        return FNAME

    @staticmethod
    async def fname(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_input = update.message.text.lower()
        dbQuery("SELECT fname, lname FROM persons WHERE fname = %s", [user_input])
        nameExists = dbFetchAll()

        if user_input == "/cancel":
            await update.message.reply_text("Bis zum nächsten Mal")
            return ConversationHandler.END

        elif not nameExists:
            await update.message.reply_text(
                "Es gibt keine Person mit diesem Vornamen, bitte gebe erneut einen Namen ein oder beende mit /cancel!")
            return FNAME

        elif len(nameExists) == 1:
            context.user_data[0] = nameExists[0][0]
            context.user_data[1] = nameExists[0][1]

            await update.message.reply_text(
                "Bitte gebe das Zitat für " + nameExists[0][0].capitalize() + " " + nameExists[0][
                    1].capitalize() + " ein")
            return ZITAT

        elif len(nameExists) > 1:
            context.user_data[0] = nameExists[0][0]

            keyboard = []
            for row in nameExists:
                keyboard.append([InlineKeyboardButton(row[1], callback_data=row[1])])

            markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("Welchen " + user_input.capitalize() + " meintest du? ",
                                            reply_markup=markup)
            return LNAME

    @staticmethod
    async def lname(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        lname = update.callback_query.data

        dbQuery("SELECT fname FROM persons WHERE lname = %s", [lname])
        name = dbFetchOne()

        await query.answer()
        await query.edit_message_text(
            text="Du hast " + name[0].capitalize() + " " + lname.capitalize() + " gewählt. Bitte gebe das Zitat ein")

        context.user_data[1] = lname

        return ZITAT

    @staticmethod
    async def zitat(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_input = update.message.text
        context.user_data[2] = user_input

        if user_input == "/cancel":
            await update.message.reply_text("Bis zum nächsten Mal")
            return ConversationHandler.END
        else:
            await update.message.reply_text("Bitte gebe das Entstehungsjahr des Zitats ein:")
            return YEAR

    @staticmethod
    async def year(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_input = update.message.text
        if user_input == "/cancel":
            await update.message.reply_text("Bis zum nächsten Mal")
            return ConversationHandler.END

        try:
            yearInt = int(user_input)

            if 2016 <= yearInt <= int(date.today().year):
                context.user_data[3] = user_input
                keyboard = [
                    [InlineKeyboardButton("Ja", callback_data="y"), InlineKeyboardButton("Nein", callback_data="n")]]
                markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text("Willst du einen Kontext hinzufügen?", reply_markup=markup)

                return CONTEXTREQUEST
            else:
                await update.message.reply_text(
                    "Bitte gebe ein Jahr als Zahl im Format xxxx und zwischen 2016 und dem jetzigen Jahr an")
                return YEAR
        except ValueError:
            await update.message.reply_text(
                "Bitte gebe ein Jahr als Zahl im Format xxxx und zwischen 2016 und dem jetzigen Jahr an")
            return YEAR

    @staticmethod
    async def contextRequest(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        state = update.callback_query.data
        await query.answer()

        if state == "y":
            await query.edit_message_text("Bitte gebe einen Kontext ein (Freitext)")
            return CONTEXTPROMPT
        if state == "n":
            context.user_data[4] = ""
            keyboard = [
                [InlineKeyboardButton("Ja", callback_data="y"), InlineKeyboardButton("Nein", callback_data="n")]]
            markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                "Bitte kontrolliere und bestätige: \n\n" + context.user_data[0] + " " + context.user_data[1] + ": " +
                context.user_data[2] + "\n\nJahr: " + context.user_data[3] + " Kontext:" + context.user_data[4],
                reply_markup=markup)
            return USERCONFIRM

    @staticmethod
    async def contextPrompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
        zcontext = update.message.text
        context.user_data[4] = zcontext

        if zcontext == "/cancel":
            await update.message.reply_text("Bis zum nächsten Mal!")
            return ConversationHandler.END
        else:
            keyboard = [
                [InlineKeyboardButton("Ja", callback_data="y"), InlineKeyboardButton("Nein", callback_data="n")]]
            markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                "Bitte kontrolliere und bestätige: \n\n" + context.user_data[0] + " " + context.user_data[1] + ": " +
                context.user_data[2] + "\n\nJahr: " + context.user_data[3] + " Kontext:" + context.user_data[4],
                reply_markup=markup)
            return USERCONFIRM

    @staticmethod
    async def userconfirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        state = update.callback_query.data

        fname = context.user_data[0]
        lname = context.user_data[1]
        quote = context.user_data[2]
        year = context.user_data[3]
        zcontext = context.user_data[4]
        chatid = update.callback_query.message.chat.id

        await query.answer()

        if state == "y":
            quote_id = AddQuote.addToDb(fname, lname, quote, chatid, year, zcontext)
            await query.edit_message_text(text="Vielen Dank für das Hinzufügen des Zitates")
            admin_keyboard = [
                [
                    InlineKeyboardButton("Akzeptieren", callback_data=f"admin_act_{quote_id}"),
                    InlineKeyboardButton("Ablehnen", callback_data=f"admin_rej_{quote_id}")
                ]
            ]
            admin_markup = InlineKeyboardMarkup(admin_keyboard)

            await context.bot.send_message(
                chat_id=os.environ.get('ADMIN_CHAT_ID'),
                text=f"Neues Zitat eingereicht von {update.callback_query.message.chat.username}:\n\nKontext: {zcontext}\n\n{fname.capitalize()} {lname.capitalize()}: {quote}",
                reply_markup=admin_markup,
            )

            return ConversationHandler.END
        if state == "n":
            await query.edit_message_text(text="Bitte starte von neu... Gebe einen Namen ein")
            return FNAME

    @staticmethod
    async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Bis zum nächsten Mal!")
        return ConversationHandler.END

    @staticmethod
    def addToDb(fname, lname, zitat, chatid, year, zcontext):
        dbQuery("SELECT person_id FROM persons WHERE fname = %s AND lname = %s", (fname, lname))
        person_id = dbFetchOne()

        # RETURNING id hinzugefügt (passe 'id' an, falls deine Spalte z.B. zitat_id heißt)
        dbQuery(
            "INSERT INTO zitate (zitat, person_id, active, addid, kontext, year, adddate) VALUES (%s, %s, False, %s, %s, %s, %s) RETURNING id",
            (zitat, person_id, chatid, zcontext, year, date.today()))
        new_id = dbFetchOne()[0] # ID für Admin zum confirmen
        dbCommit()

        return new_id

    @staticmethod
    async def adminconfirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        data = query.data
        await query.answer()

        # data sieht z.B. so aus: "admin_act_15"
        parts = data.split("_")
        action = parts[1]  # "act" oder "rej"
        zitat_id = parts[2]  # Die ID des Zitats

        if action == "act":
            # In der DB auf True setzen
            dbQuery("UPDATE zitate SET active = True AND daily = True WHERE id = %s", (zitat_id,))
            dbCommit()

            # Admin-Nachricht aktualisieren (Buttons entfernen)
            await query.edit_message_text(text=f"{query.message.text}\n\n*Wurde aktiviert.*", parse_mode="Markdown")

            # Optional: Den User benachrichtigen, dass es freigegeben wurde
            # (Dazu müsstest du dir die chat_id des Users beim Eintragen merken oder aus der DB holen)

        elif action == "rej":
            # Eintrag aus der DB löschen (oder als abgelehnt markieren)
            dbQuery("DELETE FROM zitate WHERE id = %s", (zitat_id,))
            dbCommit()

            # Admin-Nachricht aktualisieren
            await query.edit_message_text(text=f"{query.message.text}\n\n*Wurde abgelehnt & gelöscht.*", parse_mode="Markdown")

    @staticmethod
    async def addMedia(update: Update, context: ContextTypes.DEFAULT_TYPE):
        print("test")
        try:
            if update.message.photo:
                photo = await update.message.photo[-1].get_file()
                path = f"./media/photo_{photo.file_id}.jpg"
                await photo.download_to_drive(path)
                await update.message.reply_text("Bild gespeichert, Vielen Dank")
                AddQuote.addMediaToDB(media_type="file", path=path)
            if update.message.video:
                video = await update.message.video[-1].get_file()
                path = f"./media/video_{video.file_id}.mp4"
                await video.download_to_drive(path)
                await update.message.reply_text("Video gespeichert, Vielen Dank")
                AddQuote.addMediaToDB(media_type="file", path=path)
            if update.message.audio:
                audio = await update.message.audio[-1].get_file()
                path = f"./media/audio_{audio.file_id}.mp3"
                await audio.download_to_drive(path)
                await update.message.reply_text("Audio gespeichert, Vielen Dank")
                AddQuote.addMediaToDB(media_type="file", path=path)
            if update.message.document:
                document = await update.message.document.get_file()
                file_name, file_type = os.path.splitext(update.message.document.file_name)
                file_type = file_type.lower()
                if file_type in {".mp4", ".jpg", ".jpeg", ".png",  ".gif"}:
                    path = f"./media/{file_name}_{document.file_id}{file_type}"
                    await document.download_to_drive(path)
                    await update.message.reply_text("Datei gespeichert, Vielen Dank")
                    AddQuote.addMediaToDB(media_type="file", path=path)
                else:
                    await update.message.reply_text("Dateityp nicht unterstützt")
                    return FNAME

            await context.bot.send_message(
                chat_id=os.environ.get('ADMIN_CHAT_ID'),
                text=f"Neue Datei hochgeladen von {update.callback_query.message.chat.username}"
            )
            logging.info(f"Datei hinzugefügt von {update.callback_query.message.chat.username}")
            return ConversationHandler.END

        except BadRequest as e:
            logging.info(f"Fehler: {e}")
            if "File is too big" in str(e):
                await update.message.reply_text("Fehler: Die Datei überschreitet 20 MB")

            else:
                await update.message.reply_text("Es gab ein Problem beim Herunterladen der Datei")
            return FNAME


    @staticmethod
    def addMediaToDB(media_type, path):
        dbQuery(
            "INSERT INTO zitate (daily, active, adddate, file_path, type) "
            "VALUES (%s, %s, %s, %s, %s)",
            (False, False, date.today(), path, media_type)
        )
        dbCommit()