#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import select
# give OS level IO ability no matter WIN/MAC/LINUX
# select() 函数是部署底层操作系统的直接接口。
# 它监视着套接字，打开的文件和管道（任何调用 fileno() 方法后会返回有效文件描述符的东西）直到它们变得可读可写或有错误发生。
# select() 让我们同时监视多个连接变得简单，同时比在 Python 中使用套接字超时写轮询池要有效，
# 因为这些监视发生在操作系统网络层而不是在解释器层。
# 注意：将 select() 与 Python 的文件对象结合使用在 Unix 下是有效的，不过在 Windows 下无效？


HEADER_LENGTH = 10
IP = "127.0.0.1"
PORT = 1234


server_socket =  socket.socket(socket.AF_INET,socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
# the SO_REUSEADDR flag tells the kernel to reuse a local socket in TIME_WAIT state,
# without waiting for its natural timeout to expire.
# SOL-Socket Option Level, SO-Socket Option, 1 is true, allows us to reconnect

server_socket.bind((IP,PORT))
server_socket.listen()

sockets_list = [server_socket]

clients = {} #用户空字典，记录用户


def receive_message(client_socket):
    try:
        message_header = client_socket.recv(HEADER_LENGTH)

        if not len(message_header):
            return False

        message_length = int(message_header.decode("utf-8").strip())
        return {"header": message_header, "data": client_socket.recv(message_length)}

    except: #一般不会
        return False



while True:
    # select模块会自动过滤没有数据的套接字，有的话会将该套接字放入子集里面。
    # select、poll、epoll
    # 其中epoll克服了select和poll筛选效率低的问题，套接字数据有了就主动通知调用者进行处理，
    # 通过回调函数机制实现效率的大幅提升。但是只在linux平台下可以使用。这样selectors模块应运而生！
    # 它可以根据用户使用不同的平台来自动选择该使用select还是epoll

    read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list)
    # select.select(rlist, wlist, xlist[, timeout])
    # This is a straightforward interface to the Unix select() system call.
    # The first three arguments are iterables of ‘waitable objects’:
    # either integers representing file descriptors or objects with a parameterless method named fileno() returning such an integer:

    # rlist: wait until ready for reading
    # wlist: wait until ready for writing
    # xlist: wait for an “exceptional condition” (see the manual page for what your system considers such a condition)

    for notified_socket in read_sockets:
        #read_sockets是select监听的sockets_list里的可读套接字，并且它此时有数据可读！（用户申请加入群组或用户发来消息）
        #如果该可读套接字是主服务器，对它的处理是让他准备好接受新的连接
        if notified_socket == server_socket: #means some one just wamt to connect to this server: new user
            client_socket, client_address = server_socket.accept()

            user = receive_message(client_socket)#第一次发来的信息是用户信息
            if user is False:
                continue

            #将新的套接字加如监听列表
            sockets_list.append(client_socket)

            clients[client_socket] = user

            print(f"Accept new connection from {client_address[0]}:{client_address[1]} username:{user['data'].decode('utf-8')}")

        else:
            message = receive_message(notified_socket)

            if message is False: #用户退群
                print(f"Closed connection from {clients[notified_socket]['data'].decode('utf-8')}")
                sockets_list.remove(notified_socket)
                del clients[notified_socket]
                continue

            user = clients[notified_socket] #通过用户字典对应此时的用户
            print(f"receive message from {user['data'].decode('utf-8')} : {message['data'].decode('utf-8')}")

            for client_socket in clients:
                if client_socket != notified_socket: #发送给群组里面的其他用户
                    client_socket.send(user['header'] + user['data'] + message['header'] + message['data'])

    for notified_socket in exception_sockets:
        sockets_list.remove(notified_socket)
        del clients[notified_socket]