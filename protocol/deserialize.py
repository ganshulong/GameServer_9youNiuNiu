# coding: utf-8

import struct

from base.table_mgr import TableMgr
from base.session_mgr import SessionMgr
from protocol.commands import *
from base.logger import Logger
import json
import traceback


def receive(cmd, msg_dict, session):
    try:
        # if cmd != HEARTBEAT:
        #     Logger().net("msg " + hex(cmd) + " " + json.dumps(msg_dict))
        serial_router[cmd](msg_dict, session)
    except AttributeError as e:
        player = SessionMgr().player(session)
        print "cmd", hex(cmd), "session", session.uuid, "player", player
        print e
        traceback.print_exc()


def heartbeat(msg_dict, session):
    try:
        session.heartbeats = 0
        session.send_message(msg_dict)
    except Exception, e:
        print e


def enter_room(msg_dict, session):
    TableMgr().enter(msg_dict.get("room_id"), msg_dict.get("player"), msg_dict.get("info"),msg_dict.get("token"), session)


def exit_room(msg_dict, session):
    player = SessionMgr().player(session)
    player.exit_room()


def dismiss_room(msg_dict, session):
    player = SessionMgr().player(session)
    player.dismiss_room()


def vote(msg_dict, session):
    player = SessionMgr().player(session)
    player.vote(msg_dict)


def ready(msg_dict, session):
    player = SessionMgr().player(session)
    player.machine.cur_state.execute(player, "ready", msg_dict)

def discard(msg_dict, session):
    player = SessionMgr().player(session)
    player.machine.cur_state.execute(player, "discard", msg_dict)


def action(msg_dict, session):
    player = SessionMgr().player(session)
    player.machine.cur_state.execute(player, "action", msg_dict)

def start(msg_dict, session):
    player = SessionMgr().player(session)
    player.machine.cur_state.execute(player, "start", msg_dict)

def pledge(msg_dict, session):
    player = SessionMgr().player(session)
    player.machine.cur_state.execute(player, "pledge", msg_dict)

def double_pledge(msg_dict,session):
    player = SessionMgr().player(session)
    player.machine.cur_state.execute(player, "double_pledge", msg_dict)

def loot_dealer(msg_dict, session):
    player = SessionMgr().player(session)
    player.machine.cur_state.execute(player, "loot_dealer", msg_dict)

def show_card(msg_dict, session):
    player = SessionMgr().player(session)
    player.machine.cur_state.execute(player, "show_card", msg_dict)

def look_card(msg_dict, session):
    player = SessionMgr().player(session)
    player.machine.cur_state.execute(player, "look_card", msg_dict)

def speaker(msg_dict,session):
    player = SessionMgr().player(session)
    player.table.add_chat_msg( player.uuid, msg_dict, player.seat)

def trusteeship(msg_dict, session):
    player = SessionMgr().player(session)
    player.trusteeship(msg_dict.get("ai_type"), msg_dict.get("pledge_type"), msg_dict.get("pledge"),msg_dict.get("push_pledge_type"),msg_dict.get("loot_dealer_type"),msg_dict.get("loot_dealer"))



serial_router = {
    HEARTBEAT: heartbeat,
    ENTER_ROOM: enter_room,
    EXIT_ROOM: exit_room,
    DISMISS_ROOM: dismiss_room,
    VOTE: vote,
    READY: ready,#准备
    START_DN: start,#开始
    PLEDGE_DN: pledge,#压分
    LOOT_DEALER_DN: loot_dealer, # 抢庄 倍率
    SHOW_CARD_DN:show_card,#亮牌
    LOOK_CARD_DN:look_card,#看牌
    DISCARD: discard,
    ACTION_DN: action,
    SPEAKER: speaker,
    TRUSTEESHIP:trusteeship,#托管
    DOUBLE_PLEDGE:double_pledge

}
