# coding: utf-8
import socket
import tornado
import msgpack
import time
import struct
import random
from tornado.options import options
from base.logger import Logger
from base.singleton import Singleton
from protocol.commands import *

class CenterClient(object):
    __metaclass__ = Singleton

    def __init__(self):
        self._host = None
        self._port = None
        self._stream = None
        self._is_connected = False
        self._msg_list = list()

    def connect(self, host, port):
        self._host = host
        self._port = port
        sock_fd = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        self._stream = tornado.iostream.IOStream(sock_fd)
        self._stream.set_close_callback(self.on_close)
        self._stream.connect((host, port), self.on_connected)

    def reconnect(self):
        self.connect(self._host, self._port)

    def on_connected(self):
        self._is_connected = True
        msg_dict = {"cmd": GC_SERVER_INFO, "host": options.host, "port": options.server_port, "game_id": [1,3,4]}
        self.send_message(msg_dict)
        self._stream.read_bytes(8, self.on_head)

    def heartbeat(self):
        msg_dict = {"cmd": HEARTBEAT}
        self.send_message(msg_dict)

    def on_head(self, data):
        size = ord(data[0]) * 256 + ord(data[1])
        self._stream.read_bytes(size, self.on_body)

    def on_body(self, data):
        msg_dict = msgpack.unpackb(data)
        from base.center.handler import handler
        cmd = msg_dict.get("cmd")
        if cmd is not None:
            handler(cmd, msg_dict, self)
        self._stream.read_bytes(8, self.on_head)

    def send_message(self, msg_dict):
        msg = msgpack.packb(msg_dict)
        size = len(msg)
        checksum = random.randint(0, 65535)
        t = time.time()
        data = struct.pack("BBHI", int(size / 256), size % 256, checksum, t) + msg

        if self._is_connected:
            for one_data in self._msg_list:
                self._stream.write(one_data)
            self._msg_list = list()
            self._stream.write(data)
        else:
            self._msg_list.append(data)

    def on_close(self):
        self._is_connected = False
        tornado.ioloop.IOLoop.instance().call_later(5, self.reconnect)
        Logger().warn("center connect closed, reconnect 5s later")