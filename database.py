
import psycopg2
import psycopg2.extras
import io

#put the path to the GtDictionnaryString.py here
inputFile = "XXXXXXXXXX"

def connectDatabase():
    
    USERNAME="XXXX"
    DBNAME="XXXX"
    PASSWORD="XXXX"
    HOST="XXXX"
    PORT="XXXX"
    try:
        conn = psycopg2.connect(dbname=DBNAME,user=USERNAME,password=PASSWORD,host=HOST,port=PORT,connect_timeout=60)
    except Exception as e :
        exit("Connexion impossible a la base de donnees: " + str(e))
    
    conn.autocommit = True

    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    return(cur,conn)

def disconnectDatabase(cur,conn):
    
    cur.close()
    conn.close()

def execute_command_multiple_parameters(commandSQL,parametres = ()):
    cur,conn = connectDatabase()
    try:
        cur.execute(commandSQL,parametres) 
    except Exception as e :
        disconnectDatabase(cur,conn)
        print("error when running: " + commandSQL + " : " + str(e))
        return
    
    try :
        command_result = cur.fetchall()
        disconnectDatabase(cur,conn)
        return command_result
    except:
        disconnectDatabase(cur,conn)
        return "fetch Impossible"

def execute_command(commandSQL,parametres = []):
    cur,conn = connectDatabase()

    try:
        cur.execute(commandSQL,[parametres]) 
    except Exception as e :
        disconnectDatabase(cur,conn)
        print("error when running: " + commandSQL + " : " + str(e))
        return -1
    
    try :
        command_result = cur.fetchall()
        disconnectDatabase(cur,conn)
        return command_result
    except:
        disconnectDatabase(cur,conn)
        return "fetch Impossible"

def gtDatabase():
    with io.open(inputFile, 'r', errors="ignore", encoding="utf-8") as data:
        lines = []
        for line in data:
            lines.append(line)

    for i in range(1,len(lines)-2):
        name, translation = lines[i].split("=", 1)
        name = name[6::]
        execute_command_multiple_parameters("INSERT INTO GtTranslate VALUES (%s,%s)", (name,translation))
