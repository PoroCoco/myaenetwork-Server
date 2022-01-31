from flask import Flask
from flask import request, render_template, redirect
from flask.globals import session
import time
import database
import math
import base64
import json

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['DEBUG'] = True
app.config['use_reloader'] = True
app.config['SECRET_KEY'] = b'XXXX'

remakeDBTranslation = False #takes a very long time
luaProgramVersion = "1.0"
firstCharTranslate = ["g","b","m","f"]
remakeDB = False #true to erase and reset the database 
translateGTName = True #Translate all the gregtech Item name into readable name (long computing time -> needs to be optimized)
replaceSpacebyUnderscore = False
sortDesc = True #sort the item list by desc order

adminMessage = "" #message to displayed on the website 
message_computer_no_response = "Computer didn't send the data. Please retry. The computer enters a 'sleep' mode if you didn't make any requests for a while. If you still get this message then the computer is most likely offline and needs a reboot."

secondBeforeTimeout = 6 #how many seconds to wait for a computer response
sleepTimeWaitingUpdateNetwork = 0.5 #how many seconds between each query to see if it has been updated (network route)
emptyCraftingRequestString = '{"itemNumber":"EMPTY", "itemName":"EMPTY"}'

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

#return the traducted string from gregtech if the string given is translatable. Uses the txt file made from the GTNamePruner.py
def traductionGTName(string):
    if string[0] in firstCharTranslate:
        translation = database.execute_command("SELECT translated FROM gttranslate WHERE name=%s",string)
        #print(string)
        #print(len(translation))
        # if len(translation) == 0:
        #     print("unable to translate " + string)
        if len(translation) > 0 : 
            translation = translation[0][0]
            return translation
        else:
            return string
    else:
        return string

#take the string containing the info of the crafting data and return a list out of them
def craftingStatusDataToList(string):
    array = string.split("}")
    for i in range(0,len(array)-1):
        subArray = array[i].split(";")
        subArray[1] = int(subArray[1])
        array[i] = subArray
    array.pop()
    array.reverse()
    return array

def processItem(itemDataDict):
    for item in itemDataDict :
        if translateGTName:
            translatedItem = traductionGTName(item)
            itemDataDict[translatedItem] = itemDataDict.pop(item)
    return itemDataDict

def processCraftingStatusData(craftingStatus):
    if type(craftingStatus) == bytes:
        craftingStatus = craftingStatus.decode()
    if type(craftingStatus) != list:
        craftingStatus = craftingStatusDataToList(craftingStatus)
    return craftingStatus


def processEnergy(energy):
    energy["avgPowerUsage"] = float(energy["avgPowerUsage"])
    energy["maxStoredPower"] = float(energy["maxStoredPower"])
    energy["storedPower"] = float(energy["storedPower"])
    return energy

#return a list from the cpus data string. returned list  : [[cpuname,processing power,coprocessor,status],...]
def processCpus(cpus):
    liste = cpus.split(';')
    b=[]
    for i in liste:
        b+=i.split("~")
    return b



if remakeDB:
    database.execute_command("DROP TABLE aedata")
    database.execute_command("DROP TABLE accounts")
    database.execute_command("""CREATE TABLE aedata
                    (ID INT PRIMARY KEY,
                    ITEMS TEXT,
                    CRAFTINGSTATUS TEXT,
                    UPDATEREQUESTED BOOL,
                    CRAFTINGREQUESTSTRING TEXT,
                    ENERGY TEXT,
                    CPUS TEXT)
                    """)
    database.execute_command("""CREATE TABLE accounts
                    (USERNAME VARCHAR(30) NOT NULL UNIQUE,
                     PASSWORD VARCHAR(30) NOT NULL,
                     ID INT PRIMARY KEY
                     )
                    """)

if remakeDBTranslation:
    database.execute_command("DROP TABLE gttranslate")
    database.execute_command("""CREATE TABLE gttranslate
                    (NAME TEXT PRIMARY KEY,
                    TRANSLATED TEXT)
                    """)
    database.gtDatabase()

@app.route("/")
def login():
    return render_template("loginForm.html")

@app.route("/loginCheck",methods = ['GET', 'POST'])
def loginCheck():
    username = request.form["username"]
    password = request.form["password"]
    if database.execute_command_multiple_parameters("SELECT count(*) from accounts WHERE username=%s AND password=%s;",(username,password))[0][0] == 1 :
        session["user_id"] = database.execute_command("SELECT id FROM accounts WHERE username=%s",username)[0][0]
        session["craftingRequestString"] = "EMPTY;EMPTY"
        # print("session id is : "+ str(session["user_id"]))
        if session["user_id"] == -1 :
            return render_template("loginForm.html", message = "idFailed")
        return redirect("/network")
    else:
        return render_template("loginForm.html", message = "loginFailed")

@app.route("/network")
def network():
    waitingForUpdate = True
    counter = 0
    networkMessage = ""
    try: #tries to see if the user id for the session exist, if it doesn't sends back the user to the login form
        type(session["user_id"])
    except:
        return render_template("loginForm.html", message = "needLogin")

    if database.execute_command("SELECT * FROM aedata WHERE id = %s",session["user_id"]) == []:
        return "no data to id"

    #set the requestUpdate to true for the session id
    database.execute_command("UPDATE aedata SET updaterequested = true WHERE id = %s",session["user_id"])
    #waits until the requestUpdate goes back to false (meaning that it got updated)
    while waitingForUpdate:
        time.sleep(sleepTimeWaitingUpdateNetwork)
        if counter*sleepTimeWaitingUpdateNetwork >= secondBeforeTimeout:
            return message_computer_no_response

        if database.execute_command("SELECT updaterequested FROM aedata WHERE id = %s",session["user_id"])[0][0] == False:
            waitingForUpdate = False
        counter = counter + 1
    #query all the infos for the session id then processes it(string to list) to render the template
    itemData = database.execute_command("SELECT items FROM aedata WHERE id = %s",session["user_id"])[0][0]
    craftingStatusData = database.execute_command("SELECT craftingstatus FROM aedata WHERE id = %s",session["user_id"])[0][0]
    energy = database.execute_command("SELECT energy FROM aedata WHERE id = %s",session["user_id"])[0][0]
    cpus = database.execute_command("SELECT cpus FROM aedata WHERE id = %s",session["user_id"])[0][0]
    itemData = json.loads(itemData)
    energy = json.loads(energy)
    cpus = json.loads(cpus)
    energy = processEnergy(energy)
    craftingStatusData = json.loads(craftingStatusData)
    itemData = processItem(itemData)
    if energy["storedPower"] == 0:
        networkMessage = "Network is out of energy"
    return render_template("mainScreen.html",
                        aeItems = itemData, 
                        craftingStatusData = processCraftingStatusData(craftingStatusData),
                        energy = energy,
                        cpus = cpus,
                        networkMessage = networkMessage,
                        adminMessage = adminMessage)

#only for computers to know if they need to send new infos. Computer send a request with it's ID then server return if an update is needed and also if a crafting request has been requested
@app.route("/toPing", methods = ['POST'])
def toPing():
    pingData = request.get_data()
    pingData = base64.b64decode(pingData)
    pingData = pingData.decode('utf-8', 'ignore')
    pingData = json.loads(pingData)
    res = {}
    computer_id = pingData["computer_id"]
    computer_version = pingData["progVersion"]
    if computer_version != luaProgramVersion :
        return "Outdated"
    res["updateRequest"] = database.execute_command("SELECT updaterequested FROM aedata WHERE id = %s",computer_id)[0][0]
    res["craftingRequest"] = database.execute_command("SELECT craftingrequeststring FROM aedata WHERE id = %s",computer_id)[0][0]
    if res["craftingRequest"] != emptyCraftingRequestString:
        database.execute_command_multiple_parameters("UPDATE aedata SET craftingrequeststring= %s WHERE ID = %s",(emptyCraftingRequestString, computer_id))
    return json.dumps(res)

#for computers to send the data about the stored item, the energy levels and Cpus state in the network
@app.route("/inputItemData", methods = ['POST'])
def inputItemData():
    itemData = request.get_data()
    itemData = base64.b64decode(itemData)
    itemData = itemData.decode('utf-8', 'ignore')
    itemData = json.loads(itemData)
    computer_id = itemData["computer_id"]
    if computer_id == -1:
        print("!!!! : computer_id = -1 ")
    items = json.dumps(itemData["items"])
    energy = json.dumps(itemData["energy"])
    cpus = json.dumps(itemData["cpus"])
    database.execute_command_multiple_parameters("UPDATE aedata SET items=%s WHERE ID = %s",(items,computer_id))
    database.execute_command_multiple_parameters("UPDATE aedata SET energy=%s WHERE ID = %s",(energy,computer_id))
    database.execute_command_multiple_parameters("UPDATE aedata SET cpus=%s WHERE ID = %s",(cpus,computer_id))
    database.execute_command("UPDATE aedata SET updaterequested = False WHERE id = %s",computer_id)
    return "OK"

#for computers to send the info of the account created by the user. return Failed if the name or id is already registered in the database 
#create a new row in both aedata and accounts tables with the same ID
@app.route("/accountCreation", methods = ['POST'])
def accountCreation():
    accountData = request.get_data()
    accountData = base64.b64decode(accountData)
    accountData = accountData.decode('utf-8', 'ignore')
    accountData = accountData.split(";")
    database.execute_command_multiple_parameters("INSERT INTO accounts VALUES (%s,%s,%s)", (accountData[1],accountData[2],int(accountData[0])))
    database.execute_command_multiple_parameters("INSERT INTO aedata VALUES (%s,%s,%s,%s,%s)", (int(accountData[0]),"","",False,'{\"itemNumber\":\"EMPTY\", \"itemName\":\"EMPTY\"}'))
    res = database.execute_command_multiple_parameters("SELECT COUNT(*) FROM accounts WHERE username=%s AND password =%s AND id =%s",(accountData[1],accountData[2],int(accountData[0])))
    if res == None or res[0][0] != 1 :
        return "Failed"
    else:
        return "Account accepted"

#after form when a user request a new crafting request.  
@app.route("/craftingRequest")
def craftingRequest():
    craftingString = {}
    craftingString["itemNumber"] = request.args.get("number")
    craftingString["itemName"] = request.args.get("itemName")
    craftingStringJson = json.dumps(craftingString)
    print(craftingStringJson)
    database.execute_command_multiple_parameters("UPDATE aedata SET craftingrequeststring=%s WHERE ID = %s",(craftingStringJson,session["user_id"]))
    #print(requestString)
    return redirect("/network")

#for computer to send data about the status of the requested item craft
@app.route("/inputCraftingStatus", methods =['POST'])
def inputCraftingStatus():
    craftingStatusData = request.get_data()
    craftingStatusData = base64.b64decode(craftingStatusData)
    craftingStatusData = craftingStatusData.decode('utf-8', 'ignore')
    craftingStatusData = json.loads(craftingStatusData)
    computer_id = craftingStatusData["computer_id"]
    craftingStatusData = json.dumps(craftingStatusData["crafts"])
    database.execute_command_multiple_parameters("UPDATE aedata SET craftingstatus=%s WHERE ID = %s",(craftingStatusData,computer_id))
    return "OK"


if __name__ == "__main__":
    app.run()
