from flask import Flask
from flask import request, render_template, redirect
from flask.globals import session
import time
import database
import math
import base64

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['DEBUG'] = True
app.config['use_reloader'] = True
app.config['SECRET_KEY'] = b'XXXX'

remakeDBTranslation = False #takes a very long time
luaProgramVersion = "0.13"
firstCharTranslate = ["g","b","m","f"]
remakeDB = False #true to erase and reset the database 
translateGTName = True #Translate all the gregtech Item name into readable name (long computing time -> needs to be optimized)
replaceSpacebyUnderscore = False
sortDesc = True #sort the item list by desc order

adminMessage = "" #message to displayed on the website 
message_computer_no_response = "Computer didn't send the data. Please retry. The computer enters a 'sleep' mode if you didn't make any requests for a while. If you still get this message then the computer is most likely offline and needs a reboot."

secondBeforeTimeout = 6 #how many seconds to wait for a computer response
sleepTimeWaitingUpdateNetwork = 0.5 #how many seconds between each query to see if it has been updated (network route)


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

#sort the array by descending order while keeping the array correct ie: ["item name", itemCount, "IsCraftable","item name2", itemCount2, "IsCraftable2"]
def tri_insertion(tab): 
  for y in range(1,len(tab),3):
    max = -1
    index = 0
    for i in range(y,len(tab),3):
        if type(tab[i]) != int :
            if 0>max:
                max = 0
                index = i
        elif tab[i] > max:
            max = tab[i]
            index = i
    tmpCount= tab[y]
    tmpName = tab[y-1]
    tmpIsCraftable = tab[y+1]
    tab[y] = tab[index]
    tab[y-1] = tab[index-1]
    tab[y+1] = tab[index+1]
    tab[index] = tmpCount
    tab[index-1] = tmpName
    tab[index+1] = tmpIsCraftable


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

#take the string containing the info of the items inside the AE network and return a list out of them
def StrItemToList(string):
    liste = string.split(';')
    b=[]
    for i in liste:
        b+=i.split("~")
    return b

def processItemData(itemData):
    itemData = StrItemToList(itemData)
    if translateGTName:
        for i in range(0,len(itemData)-1,3):
            itemData[i] = traductionGTName(itemData[i])
    for i in range(len(itemData)):
        if i%3 == 0 and replaceSpacebyUnderscore:
            itemData[i] = itemData[i].replace(" ","_")
        if is_number(itemData[i]):
            itemData[i] = itemData[i].replace(".0","")
            itemData[i] = int(itemData[i])
    itemData.pop()
    if sortDesc : tri_insertion(itemData)
    return itemData
    
def getComputerId(itemData):
    computer_id = ""
    if len(itemData) != 0:
        for i in range(1,9):
            if itemData[-i] != ";":
                computer_id = computer_id + itemData[-i]
            else :
                return computer_id[::-1]
    return -1

def clearIdFromData(itemData):
    if len(itemData) != 0:
        for i in range(1,9):
            if itemData[-1] !=";":
                itemData = itemData[:-1]
            else:
                itemData = itemData[:-1]
                return itemData
    return 

def processCraftingStatusData(craftingStatus):
    if type(craftingStatus) == bytes:
        craftingStatus = craftingStatus.decode()
    if type(craftingStatus) != list:
        craftingStatus = craftingStatusDataToList(craftingStatus)
    return craftingStatus

def separateItemDataMiscInfo(itemData):
    array = itemData.split("|")
    return array[0], array[1], array[2]

def processEnergy(energy):
    array = energy.split(";")
    array[0] = math.floor(float(array[0]))
    array[1] = math.floor(float(array[1]))
    array[2] = math.floor(float(array[2]))
    if array[1] != 0 and array[2] != 0:
        array.append(math.floor((array[2]/array[1])*100))
    else :
        array.append(0)
    return array

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
    startItemData = time.time()
    itemData = processItemData(itemData)
    endItemData = time.time()
    print("item data took : " + str(endItemData-startItemData))
    energy = processEnergy(energy)
    if energy[3] == 0:
        networkMessage = "Network is out of energy"
    return render_template("mainScreen.html",
                        aeItems = itemData, 
                        craftingStatusData = processCraftingStatusData(craftingStatusData),
                        energy = energy,
                        cpus = processCpus(cpus),
                        networkMessage = networkMessage,
                        adminMessage = adminMessage)

#only for computers to know if they need to send new infos. Computer send a request with it's ID then server return if an update is needed and also if a crafting request has been requested
@app.route("/toPing", methods = ['POST'])
def toPing():
    pingData = request.get_data()
    pingData = pingData.decode('utf-8', 'ignore')
    computer_id = getComputerId(pingData)
    computer_version = clearIdFromData(pingData)
    if computer_version != luaProgramVersion :
        return "Outdated"
    res = database.execute_command("SELECT updaterequested FROM aedata WHERE id = %s",computer_id)[0][0]
    craftingrequestString = database.execute_command("SELECT craftingrequeststring FROM aedata WHERE id = %s",computer_id)[0][0]
    if craftingrequestString != 'EMPTY;EMPTY':
        database.execute_command("UPDATE aedata SET craftingrequeststring='EMPTY;EMPTY' WHERE ID = %s",computer_id)
    stringReturned = str(res) + ";" + craftingrequestString
    return stringReturned

#for computers to send the data about the stored item, the energy levels and Cpus state in the network
@app.route("/inputItemData", methods = ['POST'])
def inputItemData():
    itemData = request.get_data()
    itemData = base64.b64decode(itemData)
    itemData = itemData.decode('utf-8', 'ignore')
    computer_id = getComputerId(itemData)
    if computer_id == -1:
        print("!!!! : computer_id = -1 ")
    itemData = clearIdFromData(itemData)
    itemData, energy, cpus = separateItemDataMiscInfo(itemData)
    database.execute_command_multiple_parameters("UPDATE aedata SET items=%s WHERE ID = %s",(itemData,computer_id))
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
    database.execute_command_multiple_parameters("INSERT INTO aedata VALUES (%s,%s,%s,%s,%s)", (int(accountData[0]),"","",False,'EMPTY;EMPTY'))
    res = database.execute_command_multiple_parameters("SELECT COUNT(*) FROM accounts WHERE username=%s AND password =%s AND id =%s",(accountData[1],accountData[2],int(accountData[0])))
    if res == None or res[0][0] != 1 :
        return "Failed"
    else:
        return "Account accepted"

#after form when a user request a new crafting request.  
@app.route("/craftingRequest")
def craftingRequest():
    numberRequested = request.args.get("number")
    itemRequested = request.args.get("itemName")
    requestString = itemRequested + ";" + str(numberRequested) + ";"
    database.execute_command_multiple_parameters("UPDATE aedata SET craftingrequeststring=%s WHERE ID = %s",(requestString,session["user_id"]))
    #print(requestString)
    return redirect("/network")

#for computer to send data about the status of the requested item craft
@app.route("/inputCraftingStatus", methods =['POST'])
def inputCraftingStatus():
    craftingStatusData = request.get_data()
    craftingStatusData = base64.b64decode(craftingStatusData)
    craftingStatusData= craftingStatusData.decode('utf-8', 'ignore')
    computer_id = getComputerId(craftingStatusData)
    craftingStatusData = clearIdFromData(craftingStatusData)
    database.execute_command_multiple_parameters("UPDATE aedata SET craftingstatus=%s WHERE ID = %s",(craftingStatusData,computer_id))
    return "OK"


if __name__ == "__main__":
    app.run()
