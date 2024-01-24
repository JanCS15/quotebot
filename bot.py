from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv
import os, psycopg2, logging
print("test")
load_dotenv(dotenv_path="access.env")

logging.basicConfig (format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

token = os.environ.get('TG_TOKEN')
dbcon = psycopg2.connect(host=os.environ.get('PG_HOST'), user=os.environ.get('PG_USER'), dbname=os.environ.get('PG_DBNAME'), password=os.environ.get('PG_PASSWORD'))
dbcur = dbcon.cursor()

dbQuery = dbcur.execute
dbFetchOne = dbcur.fetchone
dbFetchAll = dbcur.fetchall
dbCommit = dbcon.commit

##########################################################################################


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'Hello {update.effective_user.username}')

async def randomzitat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_input = context.args
    zitat = Quotes.getRandomZitat(user_input)
    
    await update.message.reply_text(zitat)

async def zitate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_input = context.args
    zitat = Quotes.getZitate(user_input)

    await update.message.reply_text(zitat)




class Quotes:

    def getRandomZitat(*args):         
        if len(*args) == 0:       
            dbQuery("SELECT zitate.zitat, zitate.kontext, persons.fname, persons.lname FROM zitate INNER JOIN persons on zitate.person_id = persons.person_id WHERE active = true ORDER by random() LIMIT 1")
            query = dbFetchOne()         

            zitat = query[0]
            kontext = query[1]
            fname = query[2].capitalize()
            lname = query[3][0].capitalize()

            if kontext is not None and kontext!= "":
                zitat = kontext + "\n\n" + fname + " " + lname[0].capitalize() + ": " + zitat
                print(zitat)
            else:
                zitat = fname + " " + lname + ": " + zitat

        ## Other Args Length
        #
        #
        #
        ##
                        
        else: 
            zitat = "Dieses Feature ist nicht wieder implementiert worden"
                
        return zitat
    
    def getZitate(*args):
        if len(*args) == 0 or len(*args) > 2:
            return("Bitte gebe einen Vornamen oder einen Vor- und Nachnamen an")

        if len(*args) == 1:
            inputname = args[0][0].lower()
            dbQuery("SELECT true FROM persons WHERE fname = %s OR lname = %s", (inputname, inputname))                                #Check if fname or lname exists in persons
            checkname = dbFetchOne()                                                                                            
            doubles = Quotes.checkDoubles(inputname)

            if checkname != None and checkname[0] == True:                                                                                  #If name Exists ->
                if doubles == False:
                    dbQuery("SELECT zitate.year, zitate.kontext, persons.fname, persons.lname, zitate.zitat FROM zitate INNER JOIN persons ON zitate.person_id = persons.person_id WHERE active = true AND fname = %s OR lname = %s", (inputname, inputname))
                    zitatelst = dbFetchAll()
                    print(zitatelst)
                if doubles == True:
                    return("Diese Person gibt es doppelt")
            if not checkname:
                return("Diese Person existiert nicht")
        if len(*args) == 2:
            fname = args[0][0].lower()
            lname = args[0][1].lower()
            dbQuery("SELECT true FROM persons WHERE fname = %s AND lname = %s", (fname, lname))                                #Check if fname or lname exists in persons
            checkname = dbFetchOne() 

            if checkname != None and checkname[0] == True:
                dbQuery("SELECT zitate.year, zitate.kontext, persons.fname, persons.lname, zitate.zitat FROM zitate INNER JOIN persons ON zitate.person_id = persons.person_id WHERE active = true AND fname = %s AND lname = %s", (fname, lname))    
                zitatelst = dbFetchAll()
                print(zitatelst)
        
            if not checkname:
                return("Diese Person existiert nicht")
            
        if not zitatelst:
            return("Diese Person hat keine Zitate")
        else:
            zitate = ""
            fname = zitatelst[0][2]
            lname = zitatelst[0][3]
            for row in zitatelst:
                if row[1] is not None and row[1] != "":
                    zitate = zitate + str(row[0]) + ": " + row[1] + "\n" + row[4] + "\n\n"
                else:
                    zitate = zitate + str(row[0]) + ": " + row[4] + "\n\n"

            return("Zitate " + fname + " " + lname + ": \n\n" + zitate)

    def checkDoubles(inputname):
        dbQuery("SELECT fname FROM persons WHERE fname = %s",[inputname])                         #Check if fname isn't Double   
        doubleFname = dbFetchAll()

        dbQuery("SELECT lname FROM persons WHERE lname = %s",[inputname])                         #Check if lname isn't Double
        doubleLname = dbFetchAll()

        if len(doubleFname) <= 1 and len(doubleLname) <= 1:
            return(False)
        else: 
            return(True)

app = ApplicationBuilder().token(token).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("randomzitat", randomzitat))
app.add_handler(CommandHandler("zitate", zitate))

app.run_polling()

