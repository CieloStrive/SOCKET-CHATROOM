# SOCKET-CHATROOM

- [SOCKET-CHATROOM](#socket-chatroom)
  - [build server](#build-server)
    - [1. start with the imports and some starting values](#1-start-with-the-imports-and-some-starting-values)
    - [2. Initially setup our socket](#2-initially-setup-our-socket)
    - [3. setting for socket option](#3-setting-for-socket-option)
    - [4. bind and listen](#4-bind-and-listen)
    - [5. create two monitoring lists](#5-create-two-monitoring-lists)
    - [6. define an function for receive message](#6-define-an-function-for-receive-message)
    - [7. function of server](#7-function-of-server)
  - [build client](#build-client)
    - [1.  import library and do some initialization](#1-import-library-and-do-some-initialization)
    - [2. for the first connection](#2-for-the-first-connection)
    - [3. now define function for send message](#3-now-define-function-for-send-message)
    - [4. define function for receive message](#4-define-function-for-receive-message)
  - [Appendix](#appendix)
    - [1. about setblocking() and socket modes](#1-about-setblocking-and-socket-modes)
    - [2. about header in message](#2-about-header-in-message)

## build server 

### 1. start with the imports and some starting values

```py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import select
# give OS level IO ability no matter WIN/MAC/LINUX
# select() 函数是部署底层操作系统的直接接口。
# 它监视着套接字，打开的文件和管道（任何调用 fileno() 方法后会返回有效文件描述符的东西）直到它们变得可读可写或有错误发生。
# select() 让我们同时监视多个连接变得简单，同时比在 Python 中使用套接字超时写轮询池要有效，
# 因为这些监视发生在操作系统网络层而不是在解释器层。

HEADER_LENGTH = 10
IP = "127.0.0.1"
PORT = 1234

```
### 2. Initially setup our socket

```py
server_socket =  socket.socket(socket.AF_INET,socket.SOCK_STREAM)
```

### 3. setting for socket option

set the following to overcome the "Address already in use" that we hit often while building our program. This modifies the socket to allow us to reuse the address. 

the SO_REUSEADDR flag tells the kernel to reuse a local socket in TIME_WAIT state,
without waiting for its natural timeout to expire.
SOL - Socket Option Level, SO - Socket Option, 1 is true, allows us to reconnect

```py
server_socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
# the SO_REUSEADDR flag tells the kernel to reuse a local socket in TIME_WAIT state,
# without waiting for its natural timeout to expire.
# SOL-Socket Option Level, SO-Socket Option, 1 is true, allows us to reconnect
```

### 4. bind and listen

```py
server_socket.bind((IP,PORT))
server_socket.listen()
```

### 5. create two monitoring lists

one for monitoring sockets, one for record clients in chatroom, the second is actually a dictionary for "socket: username".

```py

sockets_list = [server_socket]

clients = {} #用户空字典，记录用户

```

### 6. define an function for receive message

```py
def receive_message(client_socket):
    try:
        message_header = client_socket.recv(HEADER_LENGTH)

        if not len(message_header):
            return False

        message_length = int(message_header.decode("utf-8").strip())
        return {"header": message_header, "data": client_socket.recv(message_length)}

    except: #一般不会
        return False
```

### 7. function of server

receive and identify user for the first connection and record them, receive message from them and transfer the message to the rest user. The server needs to accept new connections from clients. So our clients need to connect to server and for the first connection and transmission we design client to ask user to input a username and pass to server. Beyond all this, the server will collect incoming messages and then distribute them to the rest of the connected clients.

```py
while True:
    # select模块会自动过滤没有数据的套接字，有的话会将该套接字放入子集里面。
    # select、poll、epoll
    # 其中epoll克服了select和poll筛选效率低的问题，套接字数据有了就主动通知调用者进行处理，
    # 通过回调函数机制实现效率的大幅提升。但是只在linux平台下可以使用。这样selectors模块应运而生！
    # 它可以根据用户使用不同的平台来自动选择该使用select还是epoll

    read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list)
    # select监听的sockets_list里的可读套接字
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
```

---

## build client

### 1.  import library and do some initialization 

```py
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
```

### 2. for the first connection

as we designed in server, we ask user to input username and pass to server.

```py

#create an username
my_username = input("Username: ")
client_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
client_socket.connect((IP,PORT))

client_socket.setblocking(False)
# set connection to non-blocking state, 
# so .recv() call won't block, just return some exception we will handle

#first connect to server sending your username
username = my_username.encode("utf-8")
username_header = f"{len(username):<{HEADER_LENGTH}}".encode("utf-8")
client_socket.send(username_header + username)
```

### 3. now define function for send message

an while loop make it monitor for input from user

```py
def send_message(client_socket):
    while True:  
        message = input(f"{my_username} > ")

        if message:
            message = message.encode("utf-8")
            message_header = f"{len(message) :< {HEADER_LENGTH}}".encode("utf-8")
            client_socket.send(message_header + message)
```

### 4. define function for receive message 

an while loop makes it monitoring socket for imcoming message. And then we have to make receive function consistent to server, disassemble message to user_header, username, message_header, message and correctly receive them.    Moreover, there will be exception like IO exception when there is no message incoming, we have to handle this situation and let function continue, and for other exception let system exit. 

```py
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

```

---

## Appendix

### 1. about setblocking() and socket modes

```py 
setblocking(False) 
```
使socket为非阻塞，即不用一直等待新的一条消息到来， 如果此时没有消息receive就直接报exception然后我们会处理使其continue。

关于socket mode：

A socket object can be in one of three modes: blocking, non-blocking, or timeout. Sockets are by default always created in blocking mode, but this can be changed by calling setdefaulttimeout().

In blocking mode, operations block until complete or the system returns an error (such as connection timed out).

In non-blocking mode, operations fail (with an error that is unfortunately system-dependent) if they cannot be completed immediately: functions from the select can be used to know when and whether a socket is available for reading or writing.

In timeout mode, operations fail if they cannot be completed within the timeout specified for the socket (they raise a timeout exception) or if the system returns an error.

Note At the operating system level, sockets in timeout mode are internally set in non-blocking mode. Also, the blocking and timeout modes are shared between file descriptors and socket objects that refer to the same network endpoint. This implementation detail can have visible consequences if e.g. you decide to use the fileno() of a socket.

### 2. about header in message

header is designed for let program know how long is the message 

for detailed explanation in the use of header, please check my another repo [socket-prigramming][1].

[1]: https://github.com/CieloStrive/SOCKET-PROGRAMMING "socket-prigramming"