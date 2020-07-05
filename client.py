#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import socket
import select
import errno
import sys
import threading

HEADER_LENGTH = 10

IP = "127.0.0.1"
PORT = 1234

#create an username
my_username = input("Username: ")
client_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
client_socket.connect((IP,PORT))

client_socket.setblocking(False)
#set connection to non-blocking state, so .recv() call won't block, just return some exception we will handle

#first connect to server sending your username
username = my_username.encode("utf-8")
username_header = f"{len(username):<{HEADER_LENGTH}}".encode("utf-8")
client_socket.send(username_header + username)


def send_message(client_socket):
    while True:  # 发现一个缺陷，更新消息会被input阻塞，按回车更新,用多线程试试
        message = input(f"{my_username} > ")

        if message:
            message = message.encode("utf-8")
            message_header = f"{len(message) :< {HEADER_LENGTH}}".encode("utf-8")
            client_socket.send(message_header + message)

def receive_message(client_socket):
    while True:
        # receive message
        try:
            while True:
                username_header = client_socket.recv(HEADER_LENGTH)

                # if we receive no data from server(receive header but no message), close connection
                if not len(username_header):
                    print("connection closed by the server")
                    sys.exit()
                username_length = int(username_header.decode("utf-8").strip())
                username = client_socket.recv(username_length).decode("utf-8")

                message_header = client_socket.recv(HEADER_LENGTH)
                message_length = int(message_header.decode("utf-8").strip())
                message = client_socket.recv(message_length).decode("utf-8")


                print(f"\n{username} > {message}")

        except IOError as e:
            # This is normal on non-blocking connections -- when there are no incoming data, error will be raised
            # some OS will indicate that using AGAIN, and some using WOULDBLOCK
            # we gonna check both, if one of tht two hit, just continue
            # if hit none of this two, something happened
            if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
                print('Reading error', str(e))
                sys.exit()
            continue  # if it is E AGAIN or E WOULD BLOCK, we don't care, continue

        except Exception as e:
            # ANy other exception happened, exit
            print('General error', str(e))
            sys.exit()


receive = threading.Thread(target=receive_message, args=(client_socket,), name='receive_msg')
receive.start()
send = threading.Thread(target=send_message, args=(client_socket,), name='send_msg')
send.start()

