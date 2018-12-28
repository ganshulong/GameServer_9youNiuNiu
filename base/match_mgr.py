# coding: utf-8

from tornado.ioloop import IOLoop
from base.singleton import Singleton
from settings import redis
from base.table_mgr import TableMgr
from protocol.commands import *
from base.center.client import CenterClient
from base.logger import Logger
import time


class MatchMgr(object):
    __metaclass__ = Singleton

    def __init__(self):
        self.emo_amount_dict = {}

    def player_enter(self, player):
        if player.table.guild_id == 0 or player.table.match == 0:
            if player.table.sport_id == 0:
                player.match_score = 0
        else:
            msg_dict = {"cmd": GC_MATCH_ACT, "act": "enter", "room_id": player.table.room_id,
                        "user_id": player.uuid, "guild_id": player.table.guild_id}
            CenterClient().send_message(msg_dict)

    def sync_score(self, guild_id, user_id, score):     # 管理员修改分数走这里
        room_dict = TableMgr().room_dict
        for table in room_dict.values():
            if table.guild_id == guild_id and table.match > 0:
                if score > 0:
                    if user_id in table.player_dict:
                        player = table.player_dict[user_id]
                        player.match_score = score
                        msg_dict = {"player": user_id, "score": player.get_total_score()}
                        table.send_table_msg(SYNC_SCORE, msg_dict)
                        break
                if user_id in table.lookon_player_dict:
                    player = table.lookon_player_dict[user_id]
                    player.match_score = score
                    #msg_dict = {"player": user_id, "score": player.get_total_score()}
                    #player.send(SYNC_SCORE, msg_dict)
                    break

    def player_ready(self, player):
        msg_dict = {"cmd": GC_MATCH_ACT, "act": "ready", "room_id": player.table.room_id,
                    "user_id": player.uuid, "guild_id": player.table.guild_id}
        CenterClient().send_message(msg_dict)

    def player_loot_dealer(self, player, score):
        if score > 0 and not player.table.is_negative():
            min_score = player.table.conf.get_loot_score()
            if player.get_total_score() < min_score:
                player.send(LOOT_DEALER_DN, {"code": 1, "min_score": min_score})
                return False
        return True

    def on_room_reseted(self, room_id, room_uuid, kick_user_id, guild_admins):
        table = TableMgr().room_dict.get(room_id)
        if table:
            if room_uuid == 0:
                table.dismiss_room(1)
                return

            table.room_uuid = room_uuid
            table.st = time.time()
            table.dt = table.st + 72 * 3600
            table.et = 0
            table.cur_round = 1  # 当前回合数
            table.timers = {}
            table.timer_active = True
            table.show_card_end_time = 0
            table.dealer_seat = -1
            table.base_score = 0
            table.replay = []
            table.dismiss_state = False
            table.dismiss_sponsor = None
            table.dismiss_time = 0
            table.niu_max = 0
            table.guild_admins = guild_admins

            kick_player = []
            for pid, player in table.player_dict.items():
                player.seat = -1
                player.is_wait = True
                player.vote_state = None
                if player.vote_timer:
                    IOLoop.instance().remove_timeout(player.vote_timer)
                    player.vote_timer = None
                player.clear_for_room()
                from base.state_base.player.init import InitState
                player.machine.trigger(InitState(), False)

                if pid in kick_user_id:
                    kick_player.append(player)
                else:
                    table.lookon_player_dict[pid] = player

            from base.state_base.table.init import InitState as TableInitState
            table.machine.trigger(TableInitState())
            table.logger.info("room %d[%d] reseted" % (room_id, room_uuid))

            table.player_dict = {}
            table.seat_dict = {}

            # 房卡不足的玩家踢出
            for player in kick_player:
                player.kick_out()

    def del_room(self, room_id):
        if room_id in self.emo_amount_dict:
            del self.emo_amount_dict[room_id]

    def add_emo_amount(self, room_id, amount, players):
        table = TableMgr().room_dict.get(room_id)
        if table:
            if room_id not in self.emo_amount_dict:
                self.emo_amount_dict[room_id] = {}
            room = self.emo_amount_dict[room_id]
            for player_id in players:
                if player_id in room:
                    room[player_id] += amount
                else:
                    room[player_id] = amount

    def dec_emo_amount(self, room_id, player_id):
        room = self.emo_amount_dict.get(room_id)
        if room and room.get(player_id, 0) > 0:
            room[player_id] -= 1
            return True
        return False

    def on_match_act(self, act, room_id, user_id, score):
        table = TableMgr().room_dict.get(room_id)
        if table and table.match > 0:
            player = table.player_dict.get(user_id)
            if not player:
                player = table.lookon_player_dict.get(user_id)
            if player:
                # 同步分数
                player.match_score = score
                msg_dict = {"player": user_id, "score": player.get_total_score()}
                table.send_table_msg(SYNC_SCORE, msg_dict)

                # 处理动作
                if act == "ready":
                    if player.state == "InitState" or player.state == "SettleState" or player.state == "PauseState":
                        if player.get_total_score() < player.table.conf.get_sit_score():
                            player.send(SCORE_LEAK, {})
                        else:
                            player.ready()
                elif act == "enter":
                    pass
            else:
                Logger().warn("match room {0} ready user {1} not exist".format(room_id, user_id))
