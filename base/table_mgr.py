# coding: utf-8


from tornado.options import options

from protocol.serialize import send
from logic.table_conf import TableConf
from protocol.commands import *
from settings import redis
from base.session_mgr import SessionMgr
from base.singleton import Singleton
from base.logger import Logger
import time


class TableMgr(object):
    __metaclass__ = Singleton

    def __init__(self):
        self.room_dict = {}
        self.name = "table:mgr:{0}".format(options.server_port)
        self.room_settle_cache = {}

    def create(self, room_id, room_uuid, group_id, guild_id, match, owner, kwargs, guild_admins):
        from base.table import Table
        table = Table(room_id, room_uuid, group_id, guild_id, match, owner, kwargs)
        table.guild_admins = guild_admins
        table.conf = TableConf(table.kwargs)
        table.chairs = table.conf.max_chairs
        from base.state_base.table.init import InitState as TableInitState
        table.machine.trigger(TableInitState())
        self.room_dict[room_id] = table
        redis.sadd(self.name, room_id)
        return table

    def dismiss(self, room_id):
        try:
            del self.room_dict[room_id]
        except KeyError:
            print "room id ", room_id, "not in table mgr"
        redis.srem(self.name, room_id)

        from base.match_mgr import MatchMgr
        MatchMgr().del_room(room_id)

    def enter(self, room_id, player_id, info, user_token, session):
        print "enter room %d" % room_id
        table = self.room_dict.get(room_id)
        if not table:
            if room_id in self.room_settle_cache:
                send(SETTLEMENT_FOR_ROOM_DN, self.room_settle_cache[room_id], session)
                msg_dict = dict()
                msg_dict["code"] = 0
                send(DISMISS_ROOM, msg_dict, session)
            else:
                # 给前端返回房间不存在的错误
                msg_dict = dict()
                msg_dict["code"] = 1
                send(ENTER_ROOM, msg_dict, session)
                print("room {0} not exist, player {1} enter failed".format(room_id, player_id))
            return

        #检测token是否合法
        token = redis.get("token:{0}".format(player_id))

        if token == None or token != user_token:
            msg_dict = dict()
            msg_dict["code"] = 3 #token验证不通过，非法用户
            send(ENTER_ROOM, msg_dict, session)
            table.logger.info("token error: server;{0} client:{1}".format(token, user_token))
            return

        if table.room_id != room_id:
            self.room_dict[table.room_id] = table
            del self.room_dict[room_id]
            msg_dict = dict()
            msg_dict["code"] = 1
            send(ENTER_ROOM, msg_dict, session)
            table.logger.fatal("room id map error: msg {0} actually {1}".format(room_id, table.room_id))
            return
        from base.match_mgr import MatchMgr
        player = table.player_dict.get(player_id)
        if player:
            # 服务重启后player没有session
            if player.session:
                if session != player.session:
                    player.table.logger.info("player {0} cancel old session {1}".format(player_id, player.session.uuid))
                    # SessionMgr().cancel(player.session)
                    player.session.close()
            SessionMgr().register(player, session)
            player.table.logger.info("player {0} register new session {1}".format(player_id, player.session.uuid))
            if player.seat == -1:
                seat = -1
                for seat in range(table.chairs):
                    if seat in table.seat_dict.keys():
                        continue
                    break
                player.seat = seat
            MatchMgr().player_enter(player)
            player.reconnect()
            player.reload_extra()
            player.online_status(True)
        else:
            player = table.lookon_player_dict.get(player_id)
            if player and player.session and session != player.session:
                player.table.logger.info("player {0} cancel old session {1}".format(player_id, player.session.uuid))
                player.session.close()
            table.enter_room(player_id, info, session)

        Logger().local("ip.log", session.address[0] + ":" + str(session.address[1]))

    def heartbeat(self):
        overtime_rooms = []
        cur_time = time.time()
        for table in self.room_dict.values():
            table.heartbeat()

            if table.dt > 0 and cur_time >= table.dt:
                overtime_rooms.append(table)

        for table in overtime_rooms:
            table.dismiss_room(1)

        for k, v in self.room_settle_cache.items():
            if cur_time > v.get("t") + 600:
                del self.room_settle_cache[k]
                break

    def set_room_settle(self, room_id, data):
        data["t"] = time.time()
        self.room_settle_cache[room_id] = data
