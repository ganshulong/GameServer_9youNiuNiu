# coding: utf-8

import pickle
import struct
import time
import weakref

from tornado.ioloop import IOLoop
from tornado.iostream import StreamClosedError

from base.state_base.machine import Machine
from protocol.commands import *
from settings import redis, dismiss_delay
from base.state_base.player.ready import ReadyState
from base.state_base.player.wait import WaitState
from base.state_base.player.pledge import CashPledgeState
from base.state_base.player.starting import StartingState
from base.state_base.player.show_card import ShowCardState
from base.state_base.player.loot_dealer import LootDealerState
from base.state_base.player.look_card import LookCardState
from base.blackboard.action import ActionBlackboard
from base.blackboard.room import RoomBlackboard
from base.blackboard.round import RoundBlackboard
from base.logger import Logger
from base.match_mgr import MatchMgr


class PlayerBase(object):
    def __init__(self, uuid, info, session, table):
        self.uuid = uuid
        self.table = weakref.proxy(table)
        self.info = info
        self.seat = -1
        self.prev_seat = None
        self.next_seat = None
        self.session = session
        self.is_online = True
        self.state = None
        self.vote_state = None
        self.vote_timer = None
        self.is_owner = 0
        self.status = 0
        self.event = None
        self.is_wait = True  # T代表旁观者 F代表参与者
        self.match_score = 0  # 比赛积分
        self.machine = None
        Machine(self)

        self.round = RoundBlackboard(self)
        self.action = ActionBlackboard(self)
        self.room = RoomBlackboard(self)
        self.router = []
        self.cmd = None

    def dumps(self):
        data = {}
        for key, value in self.__dict__.items():
            if key == "table":
                data[key] = value.room_id
            elif key in ("session", "vote_timer"):
                continue
            elif key == "machine":
                data[key] = [None, None]
                if value.last_state:
                    data[key][0] = value.last_state.name
                if value.cur_state:
                    data[key][1] = value.cur_state.name
            elif key in ("round", "action", "room"):
                data[key] = value.dumps()
            else:
                data[key] = value
        redis.set("player:{0}".format(self.uuid), pickle.dumps(data))
        self.table.dumps()

    def delete(self):
        redis.delete("player:{0}".format(self.uuid))
        redis.delete("token:{0}".format(self.uuid))

    def clear_for_round(self):
        self.action.clear()
        self.round.clear()
        self.dumps()

    def clear_for_room(self):
        self.clear_for_round()
        self.room.clear()

    def get_total_score(self):
        return self.room.score + self.match_score

    def is_playing(self):
        if self.state in ("InitState", "WaitState", "PauseState"):
            return False
        return True

    def online_status(self, status):
        self.is_online = status

        if self.seat == -1:
            if status == False and self.table and self.uuid in self.table.lookon_player_dict:
                del self.table.lookon_player_dict[self.uuid]
            return

        msg_dict = dict()
        msg_dict["seat"] = self.seat
        msg_dict["flag"] = (1 if self.is_online else 0)
        if self.table:
            self.table.logger.info("player {0} toggle online status {1}".format(self.seat, status))
            for i in self.table.player_dict.values():
                if i.uuid == self.uuid:
                    continue
                i.send(ONLINE_STATUS, msg_dict)

    def reconnect(self):
        pass

    def reload_extra(self):
        # 发送操作提示
        self.reload_dismiss_state()

    def reload_dismiss_state(self):
        if not self.table.dismiss_state:
            return
        # 先弹出投票界面
        expire_seconds = int(dismiss_delay + self.table.dismiss_time - time.time())
        if expire_seconds <= 0:
            self.table.dismiss_room(2)
            return

        # 生成定时器
        if not self.vote_timer and self.uuid != self.table.dismiss_sponsor and not self.vote_state:
            msg_dict = dict()
            msg_dict["flag"] = True
            self.vote_timer = IOLoop().instance().add_timeout(
                self.table.dismiss_time + dismiss_delay, self.vote, msg_dict)

        if self.is_wait:  # 不参与投票
            return

        msg_dict = dict()
        msg_dict["room_id"] = self.table.room_id
        msg_dict["sponsor"] = self.table.dismiss_sponsor
        msg_dict["expire_seconds"] = expire_seconds
        self.send(SPONSOR_VOTE, msg_dict)

        # 遍历所有人的投票状态
        for player in self.table.player_dict.values():
            msg_dict = dict()
            msg_dict["player"] = player.uuid
            if player.vote_state is not None:
                msg_dict["flag"] = player.vote_state
                self.send(VOTE, msg_dict)

    def exit_room(self):
        if self.table.sport_id > 0:
            return
        if self.seat >= 0 and (self.table.state != 'ReadyState' and self.table.state != 'InitState'):
            return
        if self.state == "InitState" or self.table.state == 'InitState' or self.state == "WaitState"\
            or (self.table.state == 'ReadyState' and self.table.cur_round == 1)\
            or (self.state == "ReadyState"and (self.table.state == 'ReadyState'or self.table.state == 'InitState') and self.table.cur_round == 1):
            is_dealer = False
            if self.seat == self.table.dealer_seat:
                dealer_seat = -1
                len_count = len(self.table.seat_dict)
                if len_count <= 1:
                    dealer_seat = -1
                else:
                    for seat in self.table.seat_dict.keys():
                        if seat == self.seat:
                            continue
                        if seat > self.table.dealer_seat:
                            dealer_seat = seat
                            break
                    if dealer_seat == -1:
                        for seat in self.table.seat_dict.keys():
                            if seat == self.seat:
                                continue
                            dealer_seat = seat
                            break
                    if self.table.conf.game_type == 2:  # 斗公牛模式 庄家提前压分
                        dealer = self.table.seat_dict[dealer_seat]
                        dealer.room.score = dealer.room.score + self.table.conf.base_score

                self.table.dealer_seat = dealer_seat
                is_dealer = True
                self.room.score = 0

            from base.center.request import exit_room
            exit_room(self.table, self.uuid)

            self.table.exit_room_msg(self.uuid,self.seat)

            if is_dealer:
                self.table.dealer_msg(self.table.dealer_seat, self.table.conf.base_score)
                len_count = len(self.table.seat_dict)
                if len_count > 1:
                    self.table.is_all_ready()

            self.table.logger.info("player {0} exit room".format(self.uuid))

            self.delete()
            # SessionMgr().cancel(self.session)
            try:
                self.session.close()
            except Exception:
                pass

            if self.uuid in self.table.lookon_player_dict:
                del self.table.lookon_player_dict[self.uuid]
            if self.seat in self.table.seat_dict:
                del self.table.seat_dict[self.seat]
            if self.uuid in self.table.player_dict:
                del self.table.player_dict[self.uuid]

            self.table.dumps()
            self.table = None
        else:
            self.table.logger.info("player {0} exit room failed".format(self.uuid))

    def dismiss_room(self):
        # 解散房间不重复响应
        if self.table.dismiss_state:
            return
        # 限时比赛房间 不允许解散
        if self.table.sport_id >0:
            return
        if self.table.state == "InitState" or self.table.state == "ReadyState":
            # 房间未开局直接由房主解散
            if self.uuid == self.table.owner or (self.uuid in self.table.guild_admins):
                self.table.dismiss_room(1)
                return
            if self.table.match == 0:   # 非比赛房
                # 庄家解散房间
                seat = self.table.dealer_seat
                if seat == -1:
                    return
                dealer = self.table.seat_dict[seat]
                if self.uuid == dealer.uuid:
                    self.table.dismiss_room(1)
                return
        else:
            if self.uuid != self.table.owner and self.uuid not in self.table.player_dict:
                return
            #统计投票人数
            vote_count = 0
            for player in self.table.player_dict.values():
                if player.is_wait:    # 不参与投票
                    continue
                if player.uuid == self.uuid:
                    continue
                vote_count += 1
            if vote_count <= 0:
                if self.uuid == self.table.owner:
                    self.table.dismiss_room(1)
                else:
                    return

            # 房间已开局则直接发起投票
            self.table.dismiss_state = True
            self.table.dismiss_sponsor = self.uuid
            self.table.dismiss_time = time.time()
            self.vote_state = True
            self.table.timer_active = False
            self.dumps()
            msg_dict = dict()
            msg_dict["room_id"] = self.table.room_id
            msg_dict["sponsor"] = self.table.dismiss_sponsor
            msg_dict["seconds"] = dismiss_delay
            for lookon_player in self.table.lookon_player_dict.values():
                lookon_player.send(SPONSOR_VOTE, msg_dict)
            for player in self.table.player_dict.values():
                player.send(SPONSOR_VOTE, msg_dict)
                if player.uuid == self.uuid:
                    continue
                if player.is_wait:    # 不参与投票
                    continue
                msg_vote_dict = dict()
                msg_vote_dict["flag"] = True
                player.vote_timer = IOLoop().instance().add_timeout(
                    self.table.dismiss_time+dismiss_delay, player.vote, msg_vote_dict)
            self.table.logger.info("player {0} sponsor dismiss room {1}".format(self.uuid, self.table.room_id))

    def vote(self, msg_dict):
        IOLoop().instance().remove_timeout(self.vote_timer)
        self.vote_timer = None
        self.vote_state = msg_dict.get("flag")
        self.dumps()
        self.table.logger.info("player {0} vote {1}".format(self.uuid, self.vote_state))

        msg_back_dict = dict()
        msg_back_dict["player"] = self.uuid
        msg_back_dict["flag"] = msg_dict.get("flag")
        self.table.send_table_msg(VOTE, msg_back_dict, True, True, False)

        if msg_dict.get("flag"):
            for player in self.table.player_dict.values():
                if player.is_wait:  # 不参与投票
                    continue
                if not player.vote_state:
                    return

            self.table.dismiss_room(2)
        else:
            # 只要有一人拒绝则不能解散房间
            self.table.dismiss_state = False
            self.table.dismiss_sponsor = None
            self.table.dismiss_time = 0
            self.table.timer_active = True
            for player in self.table.player_dict.values():
                player.vote_state = None
                if player.vote_timer:
                    IOLoop.instance().remove_timeout(player.vote_timer)
                    player.vote_timer = None

    def ready(self):

        if self.table.state == "InitState" or self.table.state == "ReadyState" or self.table.state == "SettleState"or self.table.state == "RestartState":
            self.machine.trigger(ReadyState())
        else:
            self.machine.trigger(WaitState())

    def pledge_score(self, score,pledge_type,pledge_double):
        if pledge_type == 1:
            if score != self.room.push_pledge:
                return
        elif self.table.conf.check_score(score) == False:
            if self.table.conf.get_pledge_double():
                if self.table.conf.check_loot_dealer_score(self.round.loot_dealer,score) == False:
                    if self.table.conf.game_type == 7:
                        score = 1
                    else:
                        score = self.table.conf.score
            else:
                if self.table.conf.game_type == 7:
                    score = 1
                else:
                    score = self.table.conf.score
        self.round.pledge = max(1, score)
        self.machine.trigger(CashPledgeState())

    def start_type(self):
        msg_dict = dict()
        msg_dict["seat"] = self.seat
        if len(self.table.player_dict) <= 1:
            msg_dict["code"] = 2 #人数不够无法开始
            self.send(START_DN, msg_dict)
            return
        ready_count = 0
        for player in self.table.player_dict.values():
            if player.seat == self.table.dealer_seat:
                continue
            if player.state != "ReadyState" and player.state != "WaitState" and player.state != "PauseState":
                msg_dict["code"] = 1 #还有其他玩家未准备
                self.send(START_DN, msg_dict)
                return


            ready_count +=1
        #count = self.table.chairs
        #if count == 10:
        #    if self.table.conf.pay == 2:
        #        ready_count+=1  #庄家准备
        #        if ready_count < 6:
        #            msg_dict["code"] = 3  # AA 10人 要6人准备人数不够无法开始
        #            self.table.seat_dict[self.table.dealer_seat].send(START_DN, msg_dict)
        #            return
        if self.table.conf.game_id == 3:
            # 如果是牛爷，应该是庄开始游戏
            self.table.seat_dict[self.table.dealer_seat].machine.trigger(StartingState())
        else:
            self.machine.trigger(StartingState())

    def show_card(self):
        end_time = time.time() + 1
        if self.table.show_card_end_time + 1 < end_time:
            self.table.show_card_end_time = end_time
        else:
            self.table.show_card_end_time += 1
        self.machine.trigger(ShowCardState())

    def loot_dealer_type(self,score):
        if not MatchMgr().player_loot_dealer(self, score):
            return
        if score == 0 or  score > self.table.conf.loot_dealer:
            score = -1
        self.round.loot_dealer = max(-1, score)
        self.machine.trigger(LootDealerState())

    def look_card_type(self):
        self.machine.trigger(LookCardState())

    def send(self, cmd, msg_dict):
        if self.session is not None:
            try:
                msg_dict["cmd"] = cmd
                self.session.send_message(msg_dict)
            except (StreamClosedError, AttributeError) as e:
                print e

    # 踢出玩家，只有比赛房房卡不足时调用，慎用
    def kick_out(self):
        if self.table and self.uuid in self.table.player_dict:  # 坐下时不能踢出
            return
        self.table.logger.info("player {0} kicked out from {1}".format(self.uuid, self.table.room_id))
        try:
            if self.session:
                msg_dict = dict()
                msg_dict["cmd"] = EXIT_ROOM
                msg_dict["player"] = self.uuid
                msg_dict["seat"] = self.seat
                self.session.send_message(msg_dict)
        except Exception, e:
            pass
        self.delete()

        try:
            self.session.close()
        except Exception:
            pass
    def trusteeship(self,ai_type,pledge_type,pledge,push_pledge_type,loot_dealer_type,loot_dealer):
        if not self.is_playing():
            return
        if ai_type == self.room.ai_type:
            return
        if ai_type >0 and self.room.ai_type>0:
            return
        if ai_type == 2:
            self.room.ai_type = ai_type
            self.room.pledge_type = pledge_type
            score = pledge
            if self.table.conf.check_score(score) == False:
                if self.table.conf.get_pledge_double():
                    if self.table.conf.check_loot_dealer_score(self.round.loot_dealer, score) == False:
                        if self.table.conf.game_type == 7:
                            score = 1
                        else:
                            score = self.table.conf.score
                else:
                    if self.table.conf.game_type == 7:
                        score = 1
                    else:
                        score = self.table.conf.score

            self.room.pledge =score
            self.room.push_pledge_type = push_pledge_type
            self.room.loot_dealer_type = loot_dealer_type
            self.room.loot_dealer = loot_dealer
        else:
            self.room.ai_type = ai_type
            self.room.pledge_type = 0
            score = 0
            if self.table.conf.game_type == 7:
                score = 1
            else:
                score = self.table.conf.score

            self.room.pledge = score
            self.room.push_pledge_type = 0
            self.room.loot_dealer_type = 0
            self.room.loot_dealer = -1
        timer = self.table.get_timer_left_key()
        count = self.table.get_timer_left_count(timer)
        count_time = self.table.get_name_timer_count(timer)
        self.table.trusteeship_msg(self.seat,self.room.ai_type)
        if timer == "show_card_15":
            count_time -= (count_time - 5)
        if timer == "pledge_15":
            count_time -= (count_time - 4)
        if timer == "loot_dealer_15":
            count_time -= (count_time - 3)
        if timer == "ready_15":
            count_time -= (count_time - 4)
        if count > count_time:
            return
        self.table.set_ai(self,timer)

