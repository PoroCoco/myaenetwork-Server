from flask import Flask
from flask import request, render_template, redirect
from flask.globals import session
import time
import math

import tcp_serv
import poroNet
import database

app = Flask(__name__)
adminMessage = ""

def process_item(itemData):
    itemData = itemData.split(";")
    itemData.pop(-1)
    processed_item = []
    for item in itemData:
        item = item.split("~")
        processed_item.append(item[0]) # name
        processed_item.append(int(item[1])) # count
        processed_item.append(item[2] == "true") # isCraftable
    return processed_item

def process_crafts_status(crafts):
    if crafts == "" :
        return []
    crafts = crafts.split(";")
    crafts.pop(-1)
    crafts.reverse()
    processed_crafts = []

    for craft in crafts:
        craft = craft.split("~")
        processed_crafts.append(craft[0]) # name
        processed_crafts.append(int(craft[1])) # count
        processed_crafts.append(craft[2]) # Status

    return processed_crafts

def process_cpus(cpus):
    cpus = cpus.split(";")
    processed_cpus = []
    for cpu in cpus:
        processed_cpus += cpu.split("~")
    return processed_cpus

def process_energy(energy):
    energy = energy.split(";")
    energy[0] = float(energy[0])
    energy[1] = float(energy[1])
    energy[2] = float(energy[2])
    if energy[1] != 0 and energy[2] != 0:
        energy.append(math.floor((energy[2]/energy[1])*100))
    else :
        energy.append(0)
    return energy

@app.route("/network")
def network():
    networkMessage = ""
    try: #tries to see if the user id for the session exist, if it doesn't sends back the user to the login form
        type(session["user_id"])
    except:
        return render_template("loginForm.html", message = "needLogin")
    
    time_start = time.time()
    data = tcp_serv.get_update_user(session["user_id"], poroNet.flags["update"]["ALL"])
    itemData, energy, cpus, craftingStatusData = data.split("|")
    itemData = process_item(itemData)
    energy = process_energy(energy)
    cpus = process_cpus(cpus)
    craftingStatusData = process_crafts_status(craftingStatusData)
    time_end = time.time()

    print("Retrived OC data took : " + str(time_end-time_start))

    if energy[3] == 0:
        networkMessage = "Network is out of energy"

    return render_template("mainScreen.html",
                        aeItems = itemData, 
                        craftingStatusData = craftingStatusData,
                        energy = energy,
                        cpus = cpus,
                        networkMessage = networkMessage,
                        adminMessage = adminMessage)

@app.route("/loginCheck",methods = ['GET', 'POST'])
def loginCheck():
    username = request.form["username"]
    password = request.form["password"]
    if database.check_user(username, password):
        session["user_id"] = database.get_user_id(username)
        session["craftingRequestString"] = "EMPTY;EMPTY"
        # print("session id is : "+ session["user_id"]) 
        if session["user_id"] == str(0):
            return render_template("loginForm.html", message = "idFailed")
        return redirect("/network")
    else:
        return render_template("loginForm.html", message = "loginFailed")

#after form when a user request a new crafting request.  
@app.route("/craftingRequest")
def craftingRequest():
    numberRequested = request.args.get("number")
    itemRequested = request.args.get("itemName")
    tcp_serv.send_craft_request(session["user_id"], itemRequested, numberRequested)

    return redirect("/network")

@app.route("/")
def login():
    return render_template("loginForm.html")