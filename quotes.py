from dotenv import load_dotenv
from os import environ as env
from random import randint
import psycopg2

load_dotenv(dotenv_path="access.env")

dbcon = psycopg2.connect(host=env.get('PG_HOST'), user=env.get('PG_USER'), dbname=env.get('PG_DBNAME'), password=env.get('PG_PASSWORD'))
dbcur = dbcon.cursor()

dbQuery = dbcur.execute
dbFetchOne = dbcur.fetchone
dbFetchAll = dbcur.fetchall
dbCommit = dbcon.commit


def getAllowedChatIds():
    dbQuery("SELECT chat_id FROM persons WHERE chat_id IS NOT NUll")
    ids = dbFetchAll()
    arr = []

    for row in ids:
        arr.append(int(row[0]))

    return arr


class Quotes:
    def getRandomQuote(*args):
        if len(*args) == 0:
            dbQuery("SELECT zitate.zitat, zitate.kontext, persons.fname, persons.lname, zitate.year FROM zitate INNER JOIN persons on zitate.person_id = persons.person_id WHERE active = true ORDER by random() LIMIT 1")
            query = dbFetchOne()

            zitat = query[0]
            kontext = query[1]
            fname = query[2].capitalize()
            lname = query[3][0].capitalize()
            year = str(query[4])

            if kontext is not None and kontext != "":
                zitat = year + ": " + kontext + "\n\n" + fname + " " + lname[0].capitalize() + ": " + zitat
                print(zitat)
            else:
                zitat = fname + " " + lname + ": " + zitat

        else:
            zitat = "Dieses Feature ist nicht implementiert worden"

        return zitat

    def getQuotes(*args, offset):
        if len(*args) == 0 or len(*args) > 2:
            return "Bitte gebe einen Vornamen oder einen Vor- und Nachnamen an"

        if len(*args) == 1:
            inputname = args[0][0].lower()
            dbQuery("SELECT true FROM persons WHERE fname = %s OR lname = %s",
                    (inputname, inputname))  # Check if fname or lname exists in persons
            checkname = dbFetchOne()
            doubles = Quotes.checkDoubles(inputname)

            if checkname is not None and checkname[0] == True:  # If name Exists ->
                if doubles == False:
                    dbQuery(
                        "SELECT zitate.year, zitate.kontext, persons.fname, persons.lname, zitate.zitat FROM zitate INNER JOIN persons ON zitate.person_id = persons.person_id WHERE active = true AND fname = %s OR lname = %s",
                        (inputname, inputname))
                    zitatelst = dbFetchAll()
                if doubles == True:
                    return ("Diese Person gibt es doppelt")
            if not checkname:
                return ("Diese Person existiert nicht")
        if len(*args) == 2:
            fname = args[0][0].lower()
            lname = args[0][1].lower()
            dbQuery("SELECT true FROM persons WHERE fname = %s AND lname = %s",
                    (fname, lname))  # Check if fname or lname exists in persons
            checkname = dbFetchOne()

            if checkname != None and checkname[0] == True:
                dbQuery(
                    "SELECT zitate.year, zitate.kontext, persons.fname, persons.lname, zitate.zitat FROM zitate INNER JOIN persons ON zitate.person_id = persons.person_id WHERE active = true AND fname = %s AND lname = %s",
                    (fname, lname))
                zitatelst = dbFetchAll()
                print(zitatelst)

            if not checkname:
                return ("Diese Person existiert nicht")

        if not zitatelst:
            return ("Diese Person hat keine Zitate")
        else:
            zitate = ""
            fname = zitatelst[0][2]
            lname = zitatelst[0][3]
            for row in zitatelst:
                if row[1] is not None and row[1] != "":
                    zitate = zitate + str(row[0]) + ": " + row[1] + "\n" + row[4] + "\n\n"
                else:
                    zitate = zitate + str(row[0]) + ": " + row[4] + "\n\n"

            return ("Zitate " + fname + " " + lname + ": \n\n" + zitate)

    def checkDoubles(inputname):
        dbQuery("SELECT fname FROM persons WHERE fname = %s", [inputname])  # Check if fname isn't Double
        doubleFname = dbFetchAll()

        dbQuery("SELECT lname FROM persons WHERE lname = %s", [inputname])  # Check if lname isn't Double
        doubleLname = dbFetchAll()

        if len(doubleFname) <= 1 and len(doubleLname) <= 1:
            return (False)
        else:
            return (True)

    def getDailyMessage(self):
        dbQuery(
            "SELECT zitate.year, zitate.kontext, persons.fname, persons.lname, zitate.zitat FROM zitate INNER JOIN persons ON zitate.person_id = persons.person_id WHERE daily = True AND active = True ORDER BY date DESC LIMIT 10")
        recentZitate = dbFetchAll()

        if len(recentZitate) > 0:
            r = randint(0, len(recentZitate) - 1)
            year = str(recentZitate[r][0])
            kontext = recentZitate[r][1]
            fname = recentZitate[r][2].capitalize()
            lname = recentZitate[r][3].capitalize()
            zitat = recentZitate[r][4]
            if kontext is not None and kontext != "":
                return "Zitat des Tages:  \n\n" + year + ": " + kontext + "\n\n" + fname + " " + lname + ": " + zitat
            else:
                return "Zitat des Tages:  \n\n" + year + " \n" + fname + " " + lname + ": " + zitat
        else:
            return "test"