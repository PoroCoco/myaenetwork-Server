import threading
import json
import tcp_serv
from web_serv import app

if __name__ == "__main__":
    try:
        with open("config.json", "r") as config_file:
            config = json.load(config_file)
            FLASK_KEY = config.get("FLASK_KEY")
            TCP_SERVER_IP = config.get("TCP_SERVER_IP")
            TCP_SERVER_PORT = config.get("TCP_SERVER_PORT")
    except FileNotFoundError:
        print("Error: Flask secret key not found in config file.")
        exit(1)

    tcp_server = threading.Thread(target=tcp_serv.tcp_server_launcher, name="Tcp Server", args=(TCP_SERVER_IP, TCP_SERVER_PORT))
    tcp_server.start()

    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.config['DEBUG'] = False # Cannot have background thread with the debug on
    app.config['use_reloader'] = True
    
    app.config['SECRET_KEY'] = FLASK_KEY.encode("utf-8")
    app.run()