import socket
import threading
from time import sleep, time
import poroNet 
import database

current_version = "0.1"

# Ping database every 24hour

all_sockets = {}

def recvall(socket, len):
    sleep(0.2)
    data = b""
    MTU = 1024
    while len > 0:
        data += socket.recv(MTU)
        len -= MTU
    return data.decode("utf-8")

def get_user_socket(user_id):
    return all_sockets[user_id]

def get_update_user(user_id, flag):
    client_socket = get_user_socket(user_id)
    client_socket.send(poroNet.create_header(poroNet.packet_types["update"], 0, flag))
    packet_header = client_socket.recv(6)
    packet_type, packet_len, packet_flag = poroNet.unpack_header(packet_header)
    if (packet_type != poroNet.packet_types["update"]):
        print("Received back wrong packet after asking client for update")
        return None

    update_data = recvall(client_socket, packet_len) 
    # print(update_data)
    return update_data
    
def send_craft_request(user_id, item_name, item_count):
    client_socket = get_user_socket(user_id)
    payload = str(item_name) + "~" + str(item_count)
    payload = payload.encode("utf-8")
    packet = poroNet.create_header(poroNet.packet_types["craft"], len(payload), 0)
    packet += payload
    # print("sending",packet)
    client_socket.sendall(packet)


def register_socket(socket, packet_len):
    # Update global socket dict with the user_id to this socket
    data = socket.recv(packet_len)
    data = data.decode("utf-8")
    user_id, user_version = data.split(";")
    if (user_version != current_version):
        socket.sendall(b'1')
        socket.close()
        return
    else:
        socket.sendall(b'0')

    if (user_id in all_sockets):
        all_sockets[user_id].close()
    all_sockets[user_id] = socket

def register_account(socket, packet_len):
    payload = socket.recv(packet_len)
    payload = payload.decode("utf-8")
    name, id, password = payload.split(";")
    
    database.add_user(str(name), str(password), str(id))

    socket.send(poroNet.create_header(poroNet.packet_types["account"], 0, poroNet.flags["account"]["SUCCESS"]))


def handle_socket(socket):
    try:
        packet_header = socket.recv(6)
        packet_type, packet_len, packet_flag = poroNet.unpack_header(packet_header)
        if (packet_type == poroNet.packet_types["identification"]):
            register_socket(socket, packet_len)
            return
        elif (packet_type == poroNet.packet_types["account"]):
            register_account(socket, packet_len)
            socket.close()
            return
        elif (packet_type == poroNet.packet_types["craft"]):
            return 
        else:
            print("CLient packet is using an incorrect type for a first packet. Packet type = ", packet_type)            
            socket.close()

    except Exception as e:
        print(f"Error: {str(e)}")
        socket.close()

def tcp_server_launcher(host, port):
    # Create a socket object
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # Bind the socket to the address and port
    server_socket.bind((host, port))

    # Listen for incoming connections (max 16 clients in the queue)
    server_socket.listen(16)
    print(f"Server is listening on {host}:{port}")

    while True:
        # Accept a connection from a client
        client_socket, client_address = server_socket.accept()
        print(f"Accepted connection from {client_address}")

        # Start a new thread to handle the client
        client_handler = threading.Thread(target=handle_socket, args=(client_socket,))
        client_handler.start()

