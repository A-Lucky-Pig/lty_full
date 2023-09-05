from socket import *
import struct
import requests
import time

class SocketsTo():
    def __init__(self, IP, PORT, proxy) -> None:
        self.IP = IP
        self.PORT = PORT
        self.ADDR = (IP, PORT)
        self.BUFSIZ = 1024
        self.c = None
        self.s = None
        self.recvdata = ''
        self.socks = []
        self.c_addr = None
        self.proxy = proxy
        self.connect_flag = True

    def hand_shaking(self):
        try:
            proxy = {
            'http': self.proxy
            }
            response = requests.get('http://www.baidu.com', proxies=proxy)
            if response:
                print("Hand_Shaking_OK!")
            else:
                raise BaseException("No_Respose")
        except Exception as res:
            print(res)

    def connect_with(self):
        self.c = socket(AF_INET, SOCK_STREAM)
        self.c.connect(self.ADDR)
        self.connect_flag = True
        while True:
            self.receving()
            if self.recvdata.__contains__('start'):
                print("Connected!")
                break
        
    def wake_up(self):
        while True:
            self.receving()
            if self.recvdata.__contains__('wake'):
                print("Waked!")
                break

    def server_in(self):
        self.s = socket(AF_INET, SOCK_STREAM)
        self.s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.s.bind(self.ADDR)
        self.s.listen(10)  # 最大连接数
        self.c, self.c_addr = self.s.accept()

    def sending(self, text):
        length = len(text)
        #将int类型的长度转成字节
        len_data = struct.pack("i",length)
        # 先发送长度，在发真实数据有可能长度数据和真实数据黏在一起，而接收方不知道长度数据的字节数 导致黏包
        # 解决的方案就是 长度信息占的字节数固定死  整数 转成一个固定长度字节
        # 先发送长度给客户端 
        self.c.send(len_data)
        # 再发送数据给客户端
        self.c.send(text.encode('utf-8'))
        # print("已发送" + text)
    
    def receving(self):
        length = self.c.recv(4)
        # 转换为整型
        len_data = struct.unpack("i",bytes(length))[0] 
        # print("数据长度为%s" % len_data)
        # 存储已接收数据
        all_data = b"" 
        # 已接收长度
        rcv_size = 0
        # 循环接收直到接收到的长度等于总长度

        while  rcv_size < len_data:
            data = self.c.recv(1024)
            rcv_size += len(data)
            all_data += data

        self.recvdata = all_data.decode('utf-8')

        if self.recvdata.__contains__('exit'):
            self.client_close()
            # self.server_close()
            self.connect_flag = False

        print("已收到"+self.recvdata)
    
    def client_close(self):
        if self.c:
            try:
                self.sending('exit')
            except Exception as res:
                print(res)
            print("client_exit!")
            self.c.close()

    def server_close(self):
        if self.s:
            try:
                self.sending('exit')
            except Exception as res:
                print(res)
            print("server_exit!")
            self.s.close()
        


    