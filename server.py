# coding: utf-8
import time
import random
import socket
from uuid import uuid4
import traceback
from tornado.ioloop import IOLoop, PeriodicCallback
from tornado.tcpserver import TCPServer
from tornado.iostream import StreamClosedError
import struct
import msgpack
from tornado.options import define, options


def get_crc(data):
    s = 65535
    size = len(data)
    for i in range(size):
        d = ord(data[i])
        s ^= d
        if s & 1 == 0:
            s /= 2
        else:
            s = int(s / 2) ^ 0x70B1
    return s


class Connection(object):
    uuid = None
    last_time = 0

    def __init__(self, stream, address):
        from base.session_mgr import SessionMgr
        self.uuid = str(uuid4())
        SessionMgr().add(self)

        self._stream = stream
        self.address = address
        self.last_time = time.time()
        self._stream.set_close_callback(self.on_close)
        self._stream.read_bytes(8, self.on_head)
        self.head_data = None
        print "connection opened.", address, "count:", len(SessionMgr().session_set)

    def on_head(self, data):
        self.last_time = time.time()
        self.head_data = data
        size = ord(data[0])*256 + ord(data[1])
        if size <= 0 or size > 4096:
            print "bad package, size:", size, " ", self.address
            self.close()
            from base.logger import Logger
            Logger().local("fake_ip.log", self.address[0] + ":" + str(self.address[1]) + ":size")
            return
        self._stream.read_bytes(size, self.on_body)

    def checkcrc(self, cmd, body_data):
        size = ord(self.head_data[0])*256 + ord(self.head_data[1])
        crc_data = ""
        if size < 122:
            crc_data = self.head_data[4:8] + chr(int(cmd/256)) + chr(cmd%256) + body_data[0:size]
        else:
            crc_data = self.head_data[4:8] + chr(int(cmd/256)) + chr(cmd%256) + body_data[0:122]
        if get_crc(crc_data) != ord(self.head_data[2])*256 + ord(self.head_data[3]):
            return False

        return True

    def on_body(self, data):
        try:
            msg_dict = msgpack.unpackb(data)
        except Exception, e:
            print e, self.address
            self.close()
            from base.logger import Logger
            Logger().local("fake_ip.log", self.address[0] + ":" + str(self.address[1]) + ":unpack")
            return

        if isinstance(msg_dict, dict):
            cmd = msg_dict.get("cmd")
            if not self.checkcrc(cmd, data):
                print "check crc fail", self.address
                self.close()
                from base.logger import Logger
                Logger().local("fake_ip.log", self.address[0] + ":" + str(self.address[1]) + ":crc")
                return
            if cmd is not None:
                from protocol.deserialize import receive
                receive(cmd, msg_dict, self)
        else:
            print "bad msg dict.", self.address
            self.close()
            return

        try:
            self._stream.read_bytes(8, self.on_head)
        except StreamClosedError:
            pass

    def send_message(self, msg_dict):
        msg = msgpack.packb(msg_dict)
        size = len(msg)
        checksum = random.randint(0, 65535)
        t = time.time()
        data = struct.pack("BBHI", int(size / 256), size % 256, checksum, t) + msg
        self._stream.write(data)

    def send_data(self, data):
        self._stream.write(data)

    def on_close(self):
        from base.session_mgr import SessionMgr
        address = self.address
        try:
            player = SessionMgr().player(self)
            if player and player.session == self:
                player.online_status(False)
                player.session = None
                if player.room.ai_time == 0:
                    player.table.set_ai_time(player.seat) #玩家断线设置托管时间
        except ReferenceError:
            pass
        SessionMgr().cancel(self)
        print "connection closed.", address, "count:", len(SessionMgr().session_set)

    def close(self):
        if self._stream is not None:
            self._stream.close()

class GameServer(TCPServer):
    def handle_stream(self, stream, address):
        Connection(stream, address)

		
def reload_data():
    # 重新加载所有的房间数据
    from settings import redis
    from logic.backup import loads_table
    from base.table_mgr import TableMgr

    name = "table:mgr:{0}".format(options.server_port)
    room_list = redis.smembers(name)
    for room in room_list:
        room_id = int(room)
        try:
            table = loads_table(room_id)
            if table:
                TableMgr().room_dict[room_id] = table
            print room_id, "load success"
        except Exception as e:
            print room_id, "load failed"
            print e
            traceback.print_exc()

def heartbeat():
    from base.table_mgr import TableMgr
    TableMgr().heartbeat()

    from base.session_mgr import SessionMgr
    SessionMgr().heartbeat()


def main():
    define("host", "", type=str)
    define("server_port", 10010, type=int)
    define("redis_host", "127.0.0.1", type=str)
    define("redis_port", 6379, type=int)
    define("redis_password", None, type=str)
    define("redis_db", 5, type=int)
    define("center_host", "127.0.0.1", type=str)
    define("center_port", 8000, type=int)
    define("logfile", "game.log", type=str)
    options.parse_command_line()
    if options.host == "":
        options.host = socket.gethostbyname(socket.gethostname())

    reload_data()

    server = GameServer()
    server.listen(options.server_port)

    from base.center.client import CenterClient
    client = CenterClient()
    client.connect(options.center_host, options.center_port)

    # 定时汇报服务器信息
    from base.center.request import report_server_info
    PeriodicCallback(report_server_info, 1000 * 60).start()

    PeriodicCallback(heartbeat, 1000).start()
    IOLoop.instance().start()


if __name__ == '__main__':
    main()
