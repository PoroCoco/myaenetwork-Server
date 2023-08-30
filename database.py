import oracledb
import json

# Load database credentials
try:
    with open("config.json", "r") as config_file:
        config = json.load(config_file)
        DB_USERNAME = config.get("DB_USERNAME")
        DB_PASSWORD = config.get("DB_PASSWORD")
except FileNotFoundError:
    print("Error: Database credentials not found in config file.")
    exit(1)

def database_execute(commandSQL, parameters = (), fetch="one"):
    with oracledb.connect(user=DB_USERNAME, password=DB_PASSWORD, host="adb.eu-marseille-1.oraclecloud.com", dsn="(description= (retry_count=20)(retry_delay=3)(address=(protocol=tcps)(port=1521)(host=adb.eu-marseille-1.oraclecloud.com))(connect_data=(service_name=gff35b25ac52c7a_ggcbkdqvcse0dvpd_low.adb.oraclecloud.com))(security=(ssl_server_dn_match=yes)))") as connection:
        with connection.cursor() as cursor:
            try:
                cur = cursor.execute(commandSQL, parameters)
                if fetch == "one":
                    rows = cur.fetchone()
                elif fetch == "all":
                    rows = cur.fetchall()
                elif fetch == "none":
                    rows = None
                else:
                    print("database_execute only take 'one' and 'all' as paramater for the 'fetch' argument")
                connection.commit()
                if rows != None:
                    print(rows)
                    return rows
                return True
            except Exception as e :
                print("error when running: " + commandSQL + ". Exception : \n" + str(e))
                return False


def add_user(name, password, id):
    r = database_execute("""insert into USERS (USER_NAME, USER_PASSWORD, USER_ID) values (:username, :password, :id)""", [name, password, id], "none")
    if (r == False):
        print("Tried to add already existing user.")
        return False
    return True

def check_user(username, password):
    count = database_execute("SELECT count(*) from users WHERE user_name=:username AND user_password=:password", [username,password])[0]
    return count == 1

def get_user_id(username):
    id = database_execute("SELECT user_id FROM users WHERE user_name=:username",[username])[0]
    return id

# database_execute("CREATE TABLE users (user_name VARCHAR(64) NOT NULL UNIQUE, user_password VARCHAR(64) NOT NULL, user_id VARCHAR(64) PRIMARY KEY )", [])
# database_execute("DROP TABLE Users", [])
