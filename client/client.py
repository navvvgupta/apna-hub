import socket
import threading
import json
import select
import inquirer
import sys
import signal
import os
import dotenv
import helper.chatRoom as chat
from helper.get_lan_ip import get_lan_ip
from helper.sendFile import send_file
from utils.constants import STOP_THREAD

global main_server_conn
BUFFER_SIZE = 1024
SEPARATOR = "<SEPARATOR>"
dotenv.load_dotenv()
# client ip address
CLIENT_IP = get_lan_ip()
print(CLIENT_IP)
metaData = {
    "username": os.getenv("USER_NAME"),
    "password": os.getenv("PASS_WORD"),
    "ip_address": os.getenv("MY_IP"),
}
serverIP = os.getenv("SERVER_IP")
global metadata_json
metadata_json = json.dumps(metaData)


def connect_to_main_server(metadata_json):
    global main_server_conn
    try:
        main_server_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        main_server_conn.connect((serverIP, 9999))
        main_server_conn.send(metadata_json.encode("utf-8"))
        auth = main_server_conn.recv(BUFFER_SIZE).decode()
        auth_object = json.loads(auth)
        if auth_object["header"]["isAuth"]:
            print(auth_object["body"]["data"])
            return True
        elif not auth_object["header"]["isAuth"]:
            print(auth_object["body"]["data"])
            main_server_conn.close()
            return False
    except socket.error as msg:
        print("Socket creation error: " + str(msg))


# File transfer server(runs on every client)
def file_transfer_server():
    global file_transfer_socket
    file_transfer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sockets_list = [file_transfer_socket]
    try:
        print("File transfer server is running...")
        host = ""
        port = 10500
        file_transfer_socket.bind((host, port))
        file_transfer_socket.listen()
        while True:
            read_sockets, _, _ = select.select(sockets_list, [], [])
            for notified_socket in read_sockets:
                if notified_socket == file_transfer_socket:
                    file_transfer_conn, address = file_transfer_socket.accept()
                    send_file_thread = threading.Thread(
                        target=send_file, args=(file_transfer_conn,)
                    )
                    send_file_thread.start()

    except socket.error as msg:
        print("Socket creation error: " + str(msg))


username = metaData["username"]


def main():
    global metadata_json
    global main_server_conn
    questions = [
        inquirer.List(
            "action",
            message="Select an option:",
            choices=["Register", "Login"],
        ),
    ]

    answers = inquirer.prompt(questions)
    selected = answers["action"]
    # username = input('Enter your username: ')
    # password = input('Enter your password: ')
    # ip = input('Enter your IP: ')
    metadata_dict = json.loads(metadata_json)
    if selected == "Register":
        metadata_dict["isLoginAuth"] = "False"
    if selected == "Login":
        metadata_dict["isLoginAuth"] = "True"
    msg = json.dumps(metadata_dict)
    print(msg)
    flag = connect_to_main_server(msg)
    if flag:
        broadcast_message_thread = threading.Thread(
            target=chat.send_message, args=(main_server_conn, username)
        )
        broadcast_message_thread.start()

        listen_message_thread = threading.Thread(
            target=chat.listen_messages, args=(main_server_conn,)
        )
        listen_message_thread.start()

        file_transfer_server_thread = threading.Thread(target=file_transfer_server)
        file_transfer_server_thread.start()

        broadcast_message_thread.join()
        listen_message_thread.join()
        file_transfer_server_thread.join()


def handle_exit(sig, frame):
    global main_server_conn
    global file_transfer_socket
    STOP_THREAD = True
    print("Exiting gracefully...")
    if file_transfer_socket:
        file_transfer_socket.close()
    if main_server_conn:
        main_server_conn.close()
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, handle_exit)
    main()
