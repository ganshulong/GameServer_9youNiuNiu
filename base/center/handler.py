# coding: utf-8
#总控制台对游戏服务器的请求 例如：总控制台对房间的分配

import traceback
from StringIO import StringIO
from base.table_mgr import TableMgr
import msgpack
from protocol.commands import *
from base.logger import Logger
from tornado.options import options
from base.match_mgr import MatchMgr
from settings import redis
from logic.player import Player
from uuid import uuid4
import json

def handler(cmd, msg_dict, session):
    if cmd == CG_CREATE_ROOM:
        create_room(msg_dict, session)
    elif cmd == CG_DISMISS_ROOM:
        dismiss_room(msg_dict, session)
    elif cmd == CG_SYNC_ROOM:
        sync_room(msg_dict, session)
    elif cmd == CG_USER_TOKEN:
        user_token(msg_dict, session)
    elif cmd == CG_MATCH_SCORE:
        match_score(msg_dict, session)
    elif cmd == GC_ROOM_RESET:
        room_reseted(msg_dict, session)
    elif cmd == CG_EMO_AMOUNT:
        emo_amount(msg_dict, session)
    elif cmd == GC_MATCH_ACT:
        match_act(msg_dict, session)
    elif cmd == CG_CREATE_SPORT_ROOM:
        create_sport_room(msg_dict, session)
    elif cmd == CG_DISMISS_SPORT:
        dismiss_sport(msg_dict, session)
    else:
        Logger().warn("center client error cmd:%d"%cmd)


def create_room(msg_dict, session):
    TableMgr().create(msg_dict.get("room_id"), msg_dict.get("room_uuid"),msg_dict.get("group_id"), 
                      msg_dict.get("guild_id", 0), msg_dict.get("match", 0), msg_dict.get("owner"),
                      msg_dict.get("kwargs"), msg_dict.get("guild_admins", []))
    #发送给Center Server 创建成功的消息
    msg_back = dict()
    msg_back["cmd"] = CG_CREATE_ROOM
    msg_back["room_id"] = msg_dict.get("room_id")
    msg_back["state"] = 1
    msg_back["host"] = options.host
    msg_back["port"] = options.server_port
    msg_back["logon"] = msg_dict.get("logon")
    session.send_message(msg_back)  # 发送到游戏服务器


def force_dismiss_room(room_id, session):
    table = TableMgr().room_dict.get(room_id)
    cur_round = 1
    if table:
        table.logger.info("room dismissed by force")
        table.dismiss_state = True
        cur_round = table.cur_round
        try:
            table.dismiss_room(1)
        except Exception:
            fp = StringIO()
            traceback.print_exc(file=fp)
            table.logger.critical(fp.getvalue())
            table.delete()
            TableMgr().dismiss(room_id)
    msg_back = dict()
    msg_back["cmd"] = GC_DISMISS_ROOM
    msg_back["code"] = 0
    msg_back["room_id"] = room_id
    msg_back["cur_round"] = cur_round
    session.send_message(msg_back)

def dismiss_room(msg_dict, session):
    force_dismiss_room(msg_dict.get("room_id"), session)


def sync_room(msg_dict, session):
    from tornado.options import options

    room_dict = TableMgr().room_dict
    for table in room_dict.values():
        msg_back = dict()
        msg_back["cmd"] = CG_SYNC_ROOM
        msg_back["app_id"] = table.conf.app_id
        msg_back["room_id"] = table.room_id
        msg_back["room_uuid"] = table.room_uuid
        msg_back["group_id"] = table.group_id
        msg_back["guild_id"] = table.guild_id
        msg_back["match"] = table.match
        msg_back["state"] = 0 if table.state == "InitState" else 1
        msg_back["round"] = table.cur_round
        msg_back["rounds"] = table.conf.rounds
        msg_back["kwargs"] = table.kwargs
        msg_back["owner"] = table.owner
        msg_back["sport_id"] = table.sport_id
        msg_back["host"] = options.host
        msg_back["port"] = options.server_port
        msg_back["players"] = dict()
        for player_id, player in table.player_dict.items():
            msg_back["players"][player_id] = player.info
        session.send_message(msg_back)


def user_token(msg_dict, session):
    redis.set("token:{0}".format(msg_dict.get("user_id")), msg_dict.get("token"))   # 存缓存里，服务重启不会丢失


def match_score(msg_dict, session):
    MatchMgr().sync_score(msg_dict.get("guild_id"), msg_dict.get("user_id"), msg_dict.get("score"))


def room_reseted(msg_dict, session):
    MatchMgr().on_room_reseted(msg_dict.get("room_id"), msg_dict.get("room_uuid"), msg_dict.get("kick_user", []), msg_dict.get("guild_admins", []))


def emo_amount(msg_dict, session):
    MatchMgr().add_emo_amount(msg_dict.get("room_id"), msg_dict.get("amount"), msg_dict.get("players"))


def match_act(msg_dict, session):
    MatchMgr().on_match_act(msg_dict.get("act"), msg_dict.get("room_id"), msg_dict.get("user_id"), msg_dict.get("score"))


def create_sport_room(msg_dict, session):
    table = TableMgr().create(msg_dict.get("room_id"), msg_dict.get("room_uuid"),
                              "", 0, 0, 0, msg_dict.get("kwargs"), [])
    table.sport_id = msg_dict.get("sport_id")
    players = msg_dict.get("players", [])
    player_tokens = {}
    for p in players:
        player_id = p.get("id")
        info_dict = {"nick": p.get("nick", ""), "icon": p.get("icon", ""), "sex": 1, "game_count": 0, "reg_time": ""}
        info = json.dumps(info_dict, ensure_ascii=False)
        player = Player(player_id, info, None, table)
        from base.state_base.player.init import InitState
        player.machine.trigger(InitState())
        table.lookon_player_dict[player_id] = player
        player.match_score = p.get("score", 0)
        player.is_wait = True
        player.ready()

        token = str(uuid4())
        redis.set("token:{0}".format(player_id), token)
        player_tokens[player_id] = token

    table.dumps()
    table.set_timer("start_10", 10)

    # 发送给Center Server 创建成功的消息
    msg_back = dict()
    msg_back["cmd"] = CG_CREATE_SPORT_ROOM
    msg_back["room_id"] = msg_dict.get("room_id")
    msg_back["state"] = 1
    msg_back["host"] = options.host
    msg_back["port"] = options.server_port
    msg_back["sport_id"] = msg_dict.get("sport_id")
    msg_back["player_tokens"] = player_tokens
    session.send_message(msg_back)  # 发送到游戏服务器

def dismiss_sport(msg_dict, session):
    sport_id = msg_dict.get("sport_id")
    room_dict = TableMgr().room_dict
    to_dismiss_rooms = []
    for table in room_dict.values():
        if sport_id > 0 and table.sport_id == sport_id:
            to_dismiss_rooms.append(table.room_id)

    for room_id in to_dismiss_rooms:
        force_dismiss_room(room_id, session)