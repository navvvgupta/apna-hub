import socket
import sys
import threading
import os
import tqdm

global main_server_conn
BUFFER_SIZE = 1024
SEPARATOR = '<SEPARATOR>'
nickname = input("Choose your nickname: ")

def connect_to_main_server():
    global main_server_conn
    try:
        main_server_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        main_server_conn.connect(('192.168.137.1', 9999))
        print("Connected to the main server!")
    except socket.error as msg:
        print("Socket creation error: " + str(msg))

#connect with the main server
connect_to_main_server()

def send_file(file_transfer_conn,file_name):
    filesize = os.path.getsize(file_name)
    file_transfer_conn.send(f"{file_name}{SEPARATOR}{filesize}".encode())
    # start sending the file
    progress = tqdm.tqdm(range(filesize), f"Sending {file_name}", unit="B", unit_scale=True, unit_divisor=1024)
    with open(file_name, "rb") as f:
        while True:
            # read the bytes from the file
            bytes_read = f.read(BUFFER_SIZE)
            if not bytes_read:
                progress.close()
                break
            # we use sendall to assure transmission in busy networks
            file_transfer_conn.sendall(bytes_read)
            # update the progress bar
            progress.update(len(bytes_read))

# File transfer server(runs on every client)
def file_transfer_server():
    while True:
        try:
            print("File transfer server is running...")
            host = ""
            port = 10500
            file_transfer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            file_transfer_socket.bind((host, port))
            file_transfer_socket.listen()
            file_transfer_conn, address = file_transfer_socket.accept()
            file_name = file_transfer_conn.recv(1024).decode('utf-8')
            send_file(file_transfer_conn,file_name)
            file_transfer_conn.close()
        except socket.error as msg:
            print("Socket creation error: " + str(msg))

# Listening to Server and Sending Nickname
def listen_messages():
    global main_server_conn
    while True:
        try:
            message = main_server_conn.recv(1024).decode('utf-8')
            if message == 'NICK':
                main_server_conn.send(nickname.encode('utf-8'))
            elif message:
                print(message)
        except:
            # Close Connection When Error
            print("An error occurred!")
            main_server_conn.close()
            break

#Receive the file sent from the client
def receive_file(client_conn):
    try:
        #receive the file infos(FileName+FileSize)
        file_info_data = client_conn.recv(BUFFER_SIZE).decode()
        filename, filesize = file_info_data.split(SEPARATOR)
        # remove absolute path if there is
        filename = os.path.basename(filename)
        # convert to integer
        filesize = int(filesize)
        # start receiving the file from the socket
        progress = tqdm.tqdm(range(filesize), f"Receiving {filename}", unit="B", unit_scale=True, unit_divisor=1024)
        with open(filename, "wb") as f:
            while True:
                # read 1024 bytes from the socket (receive)
                bytes_read = client_conn.recv(BUFFER_SIZE)
                if not bytes_read:    
                    progress.close()
                    f.close()
                    break
                # write to the file the bytes we just received
                f.write(bytes_read)
                progress.update(len(bytes_read))
            client_conn.close()
    except socket.error as msg:
        print("Erorr aaya hai",str(msg))

#Establish client to client connection
def client_to_client_conn(ip,file_name):
    client_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_conn.connect((ip, 10500))
    client_conn.send(file_name.encode('utf-8'))
    receive_file(client_conn)

# Broadcasting messages through the main server
def send_message():
    global ip
    global main_server_conn
    while True:
        user_input = input('')
        message = '{}: {}'.format(nickname, user_input)
        if "connect(" in user_input:
            start_index = user_input.find('(')
            end_index = user_input.find(')')
            ip = user_input[start_index + 1 : end_index]
            print(f'Enter the file name you want from {ip}: ')
            file_name=input('')
            client_to_client_conn(ip,file_name)
        elif message:
            main_server_conn.send(message.encode('utf-8'))

broadcast_message_thread = threading.Thread(target=send_message)
broadcast_message_thread.start()

listen_message_thread = threading.Thread(target=listen_messages)
listen_message_thread.start()

file_transfer_server_thread = threading.Thread(target=file_transfer_server)
file_transfer_server_thread.start()

