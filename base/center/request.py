# coding: utf-8
# 代表 服务器对总控制台的请求，例如：发送总分数

import os
import json
from tornado.options import options
from base.center.client import CenterClient
from base.table import Table
from protocol.commands import *

from protocol.commands import *
from base.session_mgr import SessionMgr

def enter_room(table, player, info):
    msg_dict = dict()
    msg_dict["cmd"] = GC_ENTER_ROOM
    msg_dict["room_id"] = table.room_id
    msg_dict["player"] = player
    msg_dict["info"] = info
    msg_dict["app_id"] = table.conf.app_id

    CenterClient().send_message(msg_dict)

def exit_room(table, player):
    msg_dict = dict()
    msg_dict["cmd"] = GC_EXIT_ROOM
    msg_dict["player"] = player
    msg_dict["room_id"] = table.room_id
    msg_dict["app_id"] = table.conf.app_id

    CenterClient().send_message(msg_dict)

def dismiss_room(table):
    msg_dict = dict()
    msg_dict["cmd"] = GC_DISMISS_ROOM
    msg_dict["room_id"] = table.room_id
    msg_dict["cur_round"] = table.cur_round
    msg_dict["app_id"] = table.conf.app_id
    msg_dict["owner"] = table.owner

    CenterClient().send_message(msg_dict)

def settle_for_round(table, data,replay):
    msg_dict = dict()
    msg_dict["cmd"] = GC_SETTLE_ROUND
    msg_dict["app_id"] = table.conf.app_id
    msg_dict["data"] = json.dumps(data)
    msg_dict["replay"] = replay
    CenterClient().send_message(msg_dict)

def settle_for_room(table, data):
    msg_dict = dict()
    msg_dict["cmd"] = GC_SETTLE_ROOM
    msg_dict["app_id"] = table.conf.app_id
    msg_dict["data"] = json.dumps(data)

    CenterClient().send_message(msg_dict)

#1 表示ready 2表示start
def room_state(table,state):
    msg_dict = dict()
    msg_dict["cmd"] = GC_ROOM_STATE
    msg_dict["room_id"] = table.room_id
    msg_dict["state"] = state

    CenterClient().send_message(msg_dict)

# 向center server汇报
def report_server_info():

    msg_dict = dict()
    msg_dict["cmd"] = LC_SERVER_REPORT
    msg_dict["online_count"] = len(SessionMgr().online_set)
    CenterClient().send_message(msg_dict)


# 房间重置
def room_reset(table):
    msg_dict = dict()
    msg_dict["cmd"] = GC_ROOM_RESET
    msg_dict["room_id"] = table.room_id

    CenterClient().send_message(msg_dict)

