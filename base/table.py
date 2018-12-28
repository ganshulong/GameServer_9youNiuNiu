# coding: utf-8

import pickle
import time
import gzip,StringIO
import json

from protocol.serialize import send
from base.state_base.player.show_card import ShowCardState as PlayerShowCardState
from base.state_base.table.ready import ReadyState
from base.state_base.table.pledge import CashPledgeState
from base.state_base.table.starting import StartingState
from base.state_base.table.show_card import ShowCardState
from state.table_state.loot_dealer import LootDealerState
from settings import redis
from base.logger import Logger
from logic.player import Player
from base.session_mgr import SessionMgr
from base.state_base.machine import Machine
from state.status import table_state_code_map, player_state_code_map
from base.state_base.table.step import StepState
from protocol.commands import *
from base.state_base.player.show_card import show_card_type2
from state.table_state.settle_for_round import get_card_logic_value
from state.table_state.settle_for_round import get_card_value
from state.table_state.settle_for_round import get_card_color
import copy

class Table(object):
    def __init__(self, room_id, room_uuid, group_id, guild_id, match, owner, kwargs):
        super(Table, self).__init__()
        self.chairs = 6  # 默认人数
        self.room_id = room_id #桌子ID
        self.room_uuid = room_uuid
        self.owner = owner #房主ID
        self.group_id = group_id  # 群id
        self.guild_id = guild_id  # 公会ID
        self.guild_admins = [] #公会管理员Id
        self.match = match  # 比赛房
        self.owner_info = None
        self.kwargs = str(kwargs)
        self.player_dict = {}
        self.seat_dict = {}#桌子上的玩家对象
        self.lookon_player_dict = {}  # 旁观玩家列表
        self.machine = None
        self.state = None
        self.dismiss_state = False
        self.dismiss_sponsor = None
        self.dismiss_time = 0
        self.logger = Logger()# 战斗日志
        self.dealer_seat = -1 # 庄家位置
        self.active_seat = -1
        self.active_card = 0
        self.discard_seat = -1
        self.event = None
        self.cards_total = 136
        self.base_score = 0  # 庄家压分 诈金牛奖金池
        self.conf = None # 桌子配置
        self.sport_id = 0

        self.st = time.time()
        self.dt = self.st + 20 * 60; #20分钟后解散房间
        if match > 0:
            self.dt = self.st + 72 * 3600
        self.et = 0
        self.replay = [] # 桌子记录
        self.cards_on_desk = [] # 当前桌子牌堆
        self.cur_round = 1 # 当前回合数
        self.timers = {}
        self.timer_active = True
        self.show_card_end_time = 0

        # 洗牌使用
        self.niu_max = 0  # 大牌型出现次数
        Machine(self)

    def dumps(self):
        self.logger.info("table state: {0}".format(self.state))
        data = {}
        for key, value in self.__dict__.items():
            if key in ("logger", "conf", "request", "lookon_player_dict"):
                continue
            elif key == "player_dict":
                data[key] = value.keys()
            elif key == "seat_dict":
                data[key] = {k: v.uuid for k, v in value.items()}
            elif key == "machine":
                data[key] = [None, None]
                if value.cur_state:
                    data[key][1] = value.cur_state.name
                if value.last_state:
                    data[key][0] = value.last_state.name
            else:
                data[key] = value
        redis.set("table:{0}".format(self.room_id), pickle.dumps(data))

    def delete(self):
        self.player_dict = {}
        self.lookon_player_dict = {}
        self.seat_dict = {}
        redis.delete("table:{0}".format(self.room_id))

    def enter_room(self, player_id, info, session):
        newinfo = info.replace("\\'", "")
        newinfo = newinfo.replace('\\"', "")
        newinfo = newinfo.replace('\\n', "")
        newinfo = newinfo.replace('\\t', "")
        if not self.owner_info and player_id == self.owner:
            self.owner_info = newinfo
        msg_dict = dict()
        msg_dict["room_id"] = self.room_id
        msg_dict["owner"] = self.owner
        msg_dict["owner_info"] = self.owner_info
        msg_dict["room_state"] = table_state_code_map[self.state]
        msg_dict["round"] = self.cur_round
        msg_dict["rounds"] = self.conf.rounds
        msg_dict["is_admin"] = (player_id in self.guild_admins)

        # if len(self.player_dict.keys()) + len(self.lookon_player_dict.keys()) >= self.chairs + 10:
        # if len(self.player_dict.keys()) >= self.chairs:
        #     msg_dict["code"] = 2
        #     send(ENTER_ROOM, msg_dict, session)
        #     self.logger.warn("room {0} is full, player {1} enter failed".format(self.room_id, player_id))
        #     return

        player = Player(player_id, newinfo, session, self)
        from base.match_mgr import MatchMgr
        MatchMgr().player_enter(player)
        from base.state_base.player.init import InitState
        player.machine.trigger(InitState())
        player.is_wait = True
        self.lookon_player_dict[player_id] = player
        SessionMgr().register(player, session)

        msg_dict["code"] = 0
        msg_dict["kwargs"] = self.kwargs
        msg_dict["rest_cards"] = self.cards_total
        msg_dict["state"] = player_state_code_map[player.state]
        msg_dict["player"] = list()
        msg_dict["dealer"] = self.dealer_seat
        msg_dict["player_status"] = player_state_code_map["InitState"]
        for k, v in self.seat_dict.items():
            p = dict()
            p["seat"] = k
            p["player"] = v.uuid
            p["info"] = v.info
            p["state"] = player_state_code_map[v.state]
            p["is_online"] = v.is_online
            p["score"] = v.get_total_score()
            p["pledge"] = v.round.pledge
            p["loot_dealer"] = v.round.loot_dealer
            p["is_wait"] = v.is_wait
            p["niu_type"] = v.round.niu_type

            if v.session is not None:
                p["ip"] = v.session.address[0]
            msg_dict["player"].append(p)

            p["cards_in_hand"] = list()
            count = len(v.round.cards_in_hand)
            if v.state == "ShowCardState":
                p["cardsign_in_hand"] = list()
                cards_hand = copy.deepcopy(v.round.cards_in_hand)
                cardsign_in_hand = show_card_type2(v.round.cards_in_hand, v.round.niu_type)
                for w in cardsign_in_hand:
                    p["cardsign_in_hand"].append(w)
                for c in cards_hand:
                    p["cards_in_hand"].append(c)
            else:
                for _ in v.round.cards_in_hand:
                    p["cards_in_hand"].append(0)

        send(ENTER_ROOM, msg_dict, session)

        '''
        msg_dict = dict()
        msg_dict["player"] = player_id
        msg_dict["info"] = player.info
        msg_dict["seat"] = player.seat
        msg_dict["dealer"] = self.dealer_seat  # 庄家位置
        msg_dict["state"] = player_state_code_map[player.state]
        msg_dict["is_online"] = player.is_online
        msg_dict["score"] = player.room.score
        msg_dict["pledge"] = player.round.pledge
        msg_dict["loot_dealer"] = player.round.loot_dealer
        msg_dict["is_wait"] = player.is_wait
        msg_dict["ip"] = player.session.address[0]

        for i in self.player_dict.values():
            if i.uuid == player_id:
                continue
            send(ENTER_ROOM_OTHER, msg_dict, i.session)
       '''
        self.dumps()

        self.logger.info("player {0} enter room".format(player_id))

    # reason: 0:结算解散 1:房主直接解散 2:投票解散
    def dismiss_room(self, reason=2):
        self.logger.info("room {0}-{1} dismiss for reason {2}".format(self.room_id, self.room_uuid, reason))

        # 如果是投票解散房间则进入大结算，否则直接推送房主解散命令
        if reason == 2 and self.state != "InitState" and self.state != "SettleForRoomState":
            from state.table_state.settle_for_room import SettleForRoomState
            self.machine.trigger(SettleForRoomState())
            return
        else:
            self.dismiss_room_msg(reason)

        from base.table_mgr import TableMgr
        TableMgr().dismiss(self.room_id)

        for player in self.player_dict.values():
            try:
                player.session.close()
            except Exception:
                pass
            player.delete()
        for player in self.lookon_player_dict.values():
            try:
                player.session.close()
            except Exception:
                pass
            player.delete()

        from base.center.request import dismiss_room
        dismiss_room(self)

        self.delete()

    def send(self, cmd, msg_dict):
        for player in self.player_dict.values():
            player.send(cmd, msg_dict)

    def is_all_ready(self):
        ready_count = 0
        pause_count = 0
        if self.seat_dict[self.dealer_seat].state != "ReadyState":
            return
        for player in self.player_dict.values():
            if player.state == "ReadyState" or player.state == "WaitState":
                ready_count += 1
            if player.state == "PauseState":
                pause_count += 1

        if self.cur_round == 1:
            if ready_count < 2:  # self.chairs
                return
            from base.center.request import room_state
            room_state(self, 1)
        else:
            len_count = len(self.player_dict)
            if ready_count + pause_count != len_count:  # self.chairs
                return
            if ready_count < 2:
                return

        self.machine.trigger(ReadyState())

    def is_all_starting(self):
        if self.state != "ReadyState":
            return

        self.kill_timer("start_10")
        self.machine.trigger(StartingState())

        if self.cur_round >= 1:
            self.kill_timer("ready_15")
            self.kill_timer("trusteeship_ready_15")

    def is_all_pledge(self):
        if self.conf.game_type == 5:
            if self.change_state("StartingState", "CashPledgeState", False, True) == False:
                return
        elif self.conf.game_type == 4 or self.conf.game_type == 7:
            if self.change_state("LootDealerState", "CashPledgeState", True, True) == False:
                return
        elif self.conf.game_type == 6:
            if self.change_state("LootDealerState", "CashPledgeState", True, True) == False:
                return
        else:
            if self.change_state("StartingState", "CashPledgeState", True, True) == False:
                return

        self.kill_timer("pledge_15")
        self.kill_timer("trusteeship_pledge_15")
        self.machine.trigger(CashPledgeState())

    def is_all_loot_dealer(self):
        if self.conf.game_type == 6:
            if self.change_state("StartingState", "LootDealerState", False, True) == False:
                return
        else:
            if self.change_state("DealState", "LootDealerState", False, True) == False:
                return

        self.kill_timer("loot_dealer_15")
        self.kill_timer("trusteeship_loot_dealer_15")
        self.machine.trigger(LootDealerState())

    def is_all_show_card(self):
        if self.conf.game_type == 5:
            if self.change_state("DealState", "ShowCardState", False, True) == False:
                return
        elif self.conf.game_type == 4 or self.conf.game_type == 7:
            if self.change_state("Deal2State", "ShowCardState", True, True) == False:
                return
        else:
            if self.change_state("DealState", "ShowCardState", True, True) == False:
                return
        self.kill_timer("show_card_15")
        self.kill_timer("trusteeship_show_card_15")

        dealer = self.seat_dict[self.dealer_seat]
        if dealer.state != "ShowCardState":
            dealer.show_card()  # 庄家最后show card
        else:
            self.machine.trigger(ShowCardState())

    def is_all_start(self):
        if self.change_state("ReadyState","CashPledgeState",True,True) == False:
            return
        self.machine.trigger(CashPledgeState())

    def change_state(self,former_state,new_stete,dealer_bo,init_bo):  # 转换状态 ：旧状态，新状态，是否过滤庄家,是否过滤旁观者
        if self.state != former_state:
            return False
        for player in self.player_dict.values():
            if init_bo:
                if not player.is_playing():
                    continue
            if dealer_bo:
                if player.seat == self.dealer_seat:  # 庄家不用压
                    continue
            if player.state != new_stete:
                    return False
        return  True

    def is_all_players_do_action(self):
        self.dumps()
        self.clear_prompt()
        self.clear_actions()

    def clear_prompt(self):
        for player in self.player_dict.values():
            player.action.clear_prompts()

    def clear_actions(self):
        for player in self.player_dict.values():
            player.action.clear_actions()

    def set_name_timer(self, timer):
        count = self.get_name_timer_count(timer)
        self.set_timer(timer, count)
        if timer == "show_card_15":
            self.set_timer("trusteeship_show_card_15",(count-5))
        if timer == "pledge_15":
            self.set_timer("trusteeship_pledge_15",(count-4))
        if timer == "loot_dealer_15":
            self.set_timer("trusteeship_loot_dealer_15",(count-3))
        if timer == "ready_15":
            self.set_timer("trusteeship_ready_15",(count-4))

    def get_name_timer_count(self,timer):
        count = 8
        if timer == "ready_15":
            left_time = int(self.show_card_end_time - time.time()) + 1
            if left_time < 0:
                left_time = 0
            if self.conf.is_not_wait() == False:
                count = 10 + left_time
            elif self.chairs == 10:
                if self.conf.game_type == 4 or self.conf.game_type == 6 or self.conf.game_type == 7:
                    count = 5 + left_time
                else:
                    count = 8 + left_time
            else:
                count = 5 + left_time
            return count
        elif timer == "show_card_15":
            count = 8
            if self.conf.is_not_wait() == False:
                if self.conf.app_id != 101:
                    count = 15
                return 10
            elif self.chairs == 10:
                count = 8
            elif self.conf.is_rub_card() == False:
                count = 6
            else:
                count = 8
            return count
        elif timer == "pledge_15":
            if self.conf.app_id == 101:
                return 8
            elif self.conf.is_not_wait() == False:
                count = 10
            elif self.chairs == 10:
                count = 9
            elif self.conf.game_type == 4 or self.conf.game_type == 7:
                count = 9
            else:
                count = 5
            return count
        elif timer == "loot_dealer_15":
            count = 8
            if self.conf.app_id == 101:
                return 5
            elif self.conf.is_not_wait() == False:
                count = 10
            elif self.chairs == 10:
                count = 6
            else:
                count = 6
            return count
        return count

    def set_timer(self, timer, seconds):  # 设置定时器
        self.timers[timer] = seconds

    def kill_timer(self, timer):        # 取消定时器
        if self.timers.get(timer):
            del self.timers[timer]

    def get_timer_left_count(self, timer):    # 获取定时器剩余时间
        if self.timers.get(timer):
            return self.timers[timer]

    def get_timer_left(self):           # 获取定时器剩余时间
        for v in self.timers.values():
            return v
        return 0

    def get_timer_left_key(self):  # 获取定时器KEY

        for v in self.timers.keys():
            if "trusteeship_show_card_15" != v or "trusteeship_pledge_15" !=v or "trusteeship_loot_dealer_15"!=v or"trusteeship_ready_15"!=v:
                return v
            else:
                continue
        return 0

    def pause_timer(self):              # 暂停定时器
        self.timer_active = False

    def resume_timer(self):             # 恢复定时器
        self.timer_active = True

    def heartbeat(self):
        self.set_ai_time_type() #检测玩家是否开启离线托管
        if not self.timer_active:
            return
        for k in self.timers.keys():
            self.timers[k] -= 1
            if self.timers[k] <= 0:
                self.on_timer(k)
                del self.timers[k]
                break

    def on_timer(self, timer):
        if timer == "call_later_5":
            pass
        elif timer == "show_card_15":
            self.show_card()
        elif timer == "pledge_15":
            self.pledge_15()
        elif timer == "loot_dealer_15":
            self.loot_dealer_15()
        elif timer == "ready_15":
            self.ready_15()
        elif timer == "start_10":
            self.start_10()
        elif timer == "trusteeship_show_card_15":
            self.trusteeship("show_card_15")
        elif timer == "trusteeship_pledge_15":
            self.trusteeship("pledge_15")
        elif timer == "trusteeship_loot_dealer_15":
            self.trusteeship("loot_dealer_15")
        elif timer == "trusteeship_ready_15":
            self.trusteeship("ready_15")

    def test(self):
        self.set_timer("call_later_5", 5)

    def show_card(self):
        for i in self.player_dict.values():#得出所有人的牛
            player = i#取出桌子中K位置的玩家对象
            if not player.is_playing():
                continue
            if self.conf.game_type != 5:  # 非通比牛牛
                if player.seat == self.dealer_seat:
                    continue
            if player.state == "DealState" or player.state == "CashPledgeState" or player.state == "Deal2State":
                 player.show_card()

    def pledge_15(self):
        for i in self.player_dict.values():  # 得出所有人的牛
            player = i  # 取出桌子中K位置的玩家对象
            if player.state != "CashPledgeState":
                if player.seat == self.dealer_seat:
                    continue
                if player.round.pledge != 0:
                    continue
                if not player.is_playing():
                    continue
                count = 0
                if self.conf.game_type == 7:
                    count = 1
                else:
                    count = self.conf.score
                if self.conf.app_id == 101:
                    if self.conf.pledge_res:
                        if i.round.loot_dealer == self.conf.loot_dealer:
                            count = self.conf.get_score_Max(self.conf.score)
                player.pledge_score(count,0,i.round.loot_dealer)


    def loot_dealer_15(self,count = -1):
        for i in self.player_dict.values():  # 得出所有人的牛
            player = i  # 取出桌子中K位置的玩家对象
            if player.state != "LootDealerState":
                if not player.is_playing():
                    continue
                player.loot_dealer_type(count)

    def ready_15(self):
        for i in self.player_dict.values():  # 得出所有人的牛
            player = i  # 取出桌子中K位置的玩家对象
            if player.state == "InitState" or player.state == "SettleState":
                player.ready()

    def start_10(self):
        msg_dict = {"code": 0, "seat": 1}
        self.send_table_msg(START_DN, msg_dict, True, True)
        self.machine.trigger(StartingState())

    def is_push_score(self):
        for i in self.player_dict.values():
            if i.state == "ReadyState" or i.state == "WaitState":
                continue
            if self.conf.is_push_score():
                if self.conf.pledge_res:
                    if i.round.loot_dealer == self.conf.loot_dealer:
                        pass
                    else:
                        i.room.push_pledge = 0
            else:
                i.room.push_pledge = 0

    def add_chat_msg(self, user_id, msg_dict, seat):
        if msg_dict.get("type") == 5 and msg_dict.get("msg") == "gunshootFX_hit":
            if self.match > 0:
                from base.match_mgr import MatchMgr
                if not MatchMgr().dec_emo_amount(self.room_id, user_id):
                    return

        msg_dict["user_id"] = user_id
        msg_dict["seat"] = seat
        self.send_table_msg(SPEAKER, msg_dict, True, True)

    def look_card_msg(self,seat):
        msg_dict = dict()
        msg_dict["seat"] = seat
        self.send_table_msg(LOOK_CARD_DN,msg_dict,True,True)

    def loot_dealer_msg(self,seat,loot_dealer):
        msg_dict = dict()
        msg_dict["code"] = 0
        msg_dict["seat"] = seat
        msg_dict["loot_dealer"] = loot_dealer  # 倍率
        self.send_table_msg(LOOT_DEALER_DN,msg_dict,True,True)

    def pledge_msg(self,seat,pledge,code):
        msg_dict = dict()
        msg_dict["seat"] = seat
        msg_dict["pledge"] = pledge #押金
        msg_dict["code"] = code  # 错误1
        self.send_table_msg(PLEDGE_DN, msg_dict,True,True)

    def double_pledge_msg(self,seat,code):
        msg_dict = dict()
        msg_dict["seat"] = seat
        msg_dict["code"] = code  # 错误1
        self.send_table_msg(DOUBLE_PLEDGE, msg_dict, True, True)

    def ready_msg(self,seat):
        msg_dict = dict()
        msg_dict["seat"] = seat
        self.send_table_msg(READY, msg_dict,True,True)

    def wait_msg(self, seat):
        msg_dict = dict()
        msg_dict["seat"] = seat
        self.send_table_msg(WAIT_DN, msg_dict, True, True)

    def show_card_msg(self,seat,cards,niu_type,cardsign_in_hand):
        msg_dict = dict()
        msg_dict["seat"] = seat
        msg_dict["cards"] = cards
        msg_dict["niu_type"] = niu_type
        msg_dict["cardsign_in_hand"] = cardsign_in_hand #亮牌
        self.send_table_msg(SHOW_CARD_DN, msg_dict,True,True)

    def prompt_card_msg(self,flag):
        msg_dict = dict()
        msg_dict["time"] = self.get_name_timer_count("show_card_15")
        msg_dict["flag"] = flag
        self.send_table_msg(PROMPT_CARD_DN, msg_dict,True, True,False)

    def dealer_msg(self,seat,score):
        msg_dict = dict()
        msg_dict["seat"] = seat  # 新的庄家位置
        msg_dict["score"] = score  # 庒家分數
        msg_dict["room_state"] = table_state_code_map[self.state]
        self.send_table_msg(DEALER_SEAT, msg_dict,True,True)

    def prompt_start_msg(self,flag):
        msg_dict = dict()
        msg_dict["flag"] = flag  # 提示庄家可以开始游戏(flag=0可以,flag=1不可以)
        self.send_dealer_msg(PROMPT_START_DN,msg_dict)

    def prompt_loot_dealer_msg(self, flag): #玩家可以抢庄
        msg_dict = dict()
        msg_dict["time"] = self.get_name_timer_count("loot_dealer_15")
        msg_dict["flag"] = flag
        self.send_table_msg(PROMPT_LOOT_DEALER_DN, msg_dict,True,True,False)

    def exit_room_msg(self,uuid,seat):
        msg_dict = dict()
        msg_dict["player"] = uuid
        msg_dict["seat"] = seat
        self.send_table_msg(EXIT_ROOM, msg_dict, True, True)

    def dismiss_room_msg(self,reason):
        msg_dict = dict()
        msg_dict["code"] = reason
        self.send_table_msg(DISMISS_ROOM, msg_dict, True, True)

    def trusteeship_msg(self, seat,ai_type):
        msg_dict = dict()
        msg_dict["seat"] = seat
        msg_dict["ai_type"] = ai_type
        self.send_table_msg(TRUSTEESHIP, msg_dict, True, True)

    def enter_room_other_msg(self,player):
        msg_dict = dict()
        msg_dict["player"] = player.uuid
        msg_dict["info"] = player.info
        msg_dict["seat"] = player.seat
        msg_dict["dealer"] = self.dealer_seat  # 庄家位置
        msg_dict["state"] = player_state_code_map[player.state]
        msg_dict["is_online"] = player.is_online
        msg_dict["score"] = player.get_total_score()
        msg_dict["pledge"] = player.round.pledge
        msg_dict["loot_dealer"] = player.round.loot_dealer
        msg_dict["is_wait"] = player.is_wait
        msg_dict["ip"] = player.session.address[0]
        self.send_table_msg(ENTER_ROOM_OTHER, msg_dict, True, True)

    def prompt_pledge_msg(self,flag):
        msg_dict = dict()
        msg_dict["time"] = self.get_name_timer_count("pledge_15")

        for i in self.player_dict.values():
            if i.seat != self.dealer_seat:
                if not i.is_playing():
                    msg_dict["show_max_score"] = False
                    msg_dict["push_pledge"] = 0
                    msg_dict["flag"] = 1
                    i.send(PROMPT_PLEDGE_DN, msg_dict)
                    continue
                msg_dict["pledge_double"] = 0
                if self.conf.get_pledge_double():
                    if i.round.loot_dealer == self.conf.loot_dealer:
                        msg_dict["pledge_double"] = 1
                    else:
                        msg_dict["pledge_double"] = 0
                msg_dict["show_max_score"] = False
                msg_dict["flag"] = flag
                msg_dict["push_pledge"] = i.room.push_pledge  # 推注
                if self.conf.get_pledge_res() == 1:
                    if i.round.loot_dealer == self.conf.loot_dealer:
                        msg_dict["show_max_score"] = True
                    else:
                        msg_dict["push_pledge"] = 0  # 推注
                        i.room.push_pledge = 0
                i.send(PROMPT_PLEDGE_DN, msg_dict)
            else:
                msg_dict["show_max_score"] = False
                msg_dict["push_pledge"] = 0
                msg_dict["flag"] = 1
                i.send(PROMPT_PLEDGE_DN, msg_dict)
            self.prompt_pledge2_msg(flag)

    def pledge_prompt_msg(self): #推注提示
        msg_dict = dict()
        msg_dict["player"] = list()
        for i in self.player_dict.values():
            p = dict()
            p["seat"] = i.seat
            if i.seat != self.dealer_seat:
                if not i.is_playing():
                    p["push_pledge"] = 0
                    msg_dict["player"].append(p)
                    continue
                p["push_pledge"] = i.room.push_pledge  # 推注
                msg_dict["player"].append(p)
            else:
                p["push_pledge"] = 0
                msg_dict["player"].append(p)
        self.send_table_msg(PUSH_PLEDGE, msg_dict, True, True)

    def prompt_pledge2_msg(self,flag):
        msg_dict = dict()
        msg_dict["time"] = self.get_name_timer_count("pledge_15")
        msg_dict["show_max_score"] = False
        msg_dict["push_pledge"] = 0
        msg_dict["flag"] = 1
        self.send_table_msg(PROMPT_PLEDGE_DN, msg_dict,False,True,False)

    def send_dealer_msg(self,msg_name,msg_dict):  # 发送给庄家
        if self.conf.game_id == 3:
            #如果是牛爷，则需要房主或者公会会长开始游戏
            all_player = self.player_dict.values()
            all_player.extend(self.lookon_player_dict.values())

            for player in all_player:
                if self.guild_id > 0 :
                    #公会房间
                    if player.uuid in self.guild_admins:
                        player.send(msg_name, msg_dict)
                else:
                    #开房间
                    if player.uuid == self.owner:
                        player.send(msg_name, msg_dict)
                        return
        else:
            self.seat_dict[self.dealer_seat].send(msg_name, msg_dict)

    # 广播桌子消息
    # include_dealer: 是否同时发给庄家
    # include_lookon: 是否同时发给旁观者
    def send_table_msg(self, cmd, msg_dict, include_dealer=True,include_lookon=True,exclude_state=False):
        if cmd not in (READY,ENTER_ROOM_OTHER,ROUND_STATE,SPEAKER):
            self.replay.append( {"type":2,"cmd":cmd,"data":msg_dict,"time": int(time.time() * 1000 ) } )

        for i in self.player_dict.values():
            if not include_dealer and i.seat == self.dealer_seat:
                continue
            if exclude_state:
                if not i.is_playing():
                    continue
            i.send(cmd, msg_dict)
        if include_lookon:
            for i in self.lookon_player_dict.values():
                i.send(cmd, msg_dict)

    def add_replay(self,cmd,msg_dict):
        self.replay.append({"type": 2, "cmd": cmd, "data": msg_dict, "time": int(time.time() * 1000)})

    def get_replay_compress(self):
        buf = StringIO.StringIO()
        f = gzip.GzipFile(mode='wb', fileobj=buf)
        try:
            f.write(pickle.dumps( self.replay ))
        finally:
            f.close()
        return buf.getvalue()

    def is_negative(self):   # 可否负分
        if self.match > 0 and self.conf.ex_neg == 0:
            return False
        return True

    def ai_get_card_type(self,cb_card_data, conf):  # 获取类型
        cb_temp_data = []
        for k, v in enumerate(cb_card_data):
            cb_temp_data.append(v)

        # 炸弹牌型
        if conf.is_bomb():
            b_same_count = 0
            b_second_value = get_card_value(cb_temp_data[0])
            for k, v in enumerate(cb_temp_data):
                if b_second_value == get_card_value(v):
                    b_same_count = b_same_count + 1

            if b_same_count >= 3:
                return 14
            else:
                b_same_count = 0
                b_second_value = get_card_value(cb_temp_data[1])
                for k, v in enumerate(cb_temp_data):
                    if b_second_value == get_card_value(v):
                        b_same_count = b_same_count + 1

                if b_same_count >= 3:
                    return 14

        # 五小牛牌型
        #if conf.is_five_small():
        #    b_five_small = 0
        #    for k, v in enumerate(cb_temp_data):
        #        b_five_small = b_five_small + get_card_value(v)
        #    if b_five_small <= 10:
        #        return 13

        # 葫芦牛
        if conf.is_calabash():
            b_same_count = 0
            b_second_value = get_card_value(cb_temp_data[0])
            b_second_value_2 = 0
            b_same_count_2 = 0
            for k, v in enumerate(cb_temp_data):
                if b_second_value == get_card_value(v):
                    b_same_count = b_same_count + 1
                else:
                    if b_second_value_2 == 0:
                        b_second_value_2 = get_card_value(v)
                        b_same_count_2 = b_same_count_2 + 1
                    elif b_second_value_2 == get_card_value(v):
                        b_same_count_2 = b_same_count_2 + 1
            if b_same_count == 2:
                if b_same_count_2 == 2:
                    return 18  # 葫芦牛
            elif b_same_count == 3:
                if b_same_count_2 == 1:
                    return 18  # 葫芦牛
            elif b_same_count_2 == 2:
                if b_same_count == 2:
                    return 18  # 葫芦牛
            elif b_same_count_2 == 3:
                if b_same_count == 1:
                    return 18  # 葫芦牛

        # 金牛牌型 有疑问
        if conf.is_gold():
            b_king_count = 0
            for k, v in enumerate(cb_temp_data):
                if get_card_value(v) > 10:
                    b_king_count = b_king_count + 1

            if b_king_count == 4:
                return 12

        # 银牛牌型
        if conf.is_silver():
            b_king_count = 0
            b_10_count = 0
            for k, v in enumerate(cb_temp_data):
                if get_card_value(v) >= 10:
                    b_king_count = b_king_count + 1

            if b_king_count == 4:
                return 11

        # --牛一~牛牛牌型 或 一条龙
        b_temp = []
        b_sum = 0
        for k, v in enumerate(cb_temp_data):
            b_temp.append(get_card_logic_value(v))
            b_sum = b_sum + b_temp[k]

        # 一条龙之后判定牛几
        b_temp.sort()

        b_temp2 = []
        for k, v in enumerate(cb_temp_data):
            b_temp2.append(get_card_value(v))
        b_temp2.sort()

        # 同花顺牛
        if conf.is_straight_flush():
            b_color_count = 0
            color_type = get_card_color(cb_temp_data[0])
            for k, v in enumerate(cb_temp_data):
                if get_card_color(v) == color_type:
                    b_color_count = b_color_count + 1

            if b_color_count == 4:
                is_sequence = False
                for e, r in enumerate(b_temp2):
                    if e == 0:
                        continue
                    cb_count = get_card_value(b_temp2[e - 1]) + 1
                    cb_count2 = get_card_value(r)
                    if cb_count != cb_count2:
                        is_sequence = False
                        break
                    is_sequence = True
                if is_sequence == True:
                    return 19
        #if conf.is_long():
        #    yitiao_info = [1, 2, 3, 4, 5]
        #    yitiaolong = -1
        #    yitiaolong = cmp(yitiao_info, b_temp)
        #    if yitiaolong == 0:
        #        return 15  # 一条龙


                # 同花牛
        if conf.is_identical():
            b_color_count = 0
            color_type = get_card_color(cb_temp_data[0])
            for k, v in enumerate(cb_temp_data):
                if get_card_color(v) == color_type:
                    b_color_count = b_color_count + 1

            if b_color_count == 4:
                return 17
        # 顺子牛
        if conf.is_sequence():
            is_sequence = False
            for e, r in enumerate(b_temp2):
                if e == 0:
                    continue
                cb_count = get_card_value(b_temp2[e - 1]) + 1
                cb_count2 = get_card_value(r)
                if cb_count != cb_count2:
                    is_sequence = False
                    break
                is_sequence = True
            if is_sequence == True:
                return 16

        for e, r in enumerate(b_temp):
            if (b_sum - b_temp[e]) % 10 == 0:
                if b_temp[e] > 10:
                    return b_temp[e] - 10
                else:
                    return b_temp[e]

        return 0
    def trusteeship(self,timer):
        for i in self.player_dict.values():
            if not i.is_playing():
                continue
            if i.room.ai_type == 0:
                continue
            #timer =self.get_timer_left_key()
            self.set_ai(i,timer)
    def set_ai_time(self,seat):
        if self.conf.game_type == 7:
            pass
        elif self.conf.game_type == 4:
            pass
        else:
            return
        ai_time = time.time()
        ai_time = 20*1000
        self.seat_dict[seat].room.ai_time =ai_time
    def set_ai_time_type(self):
        ai_time = time.time()
        for i in self.player_dict.values():
            if not i.is_playing():
                continue
            if i.room.ai_type != 0:
                continue
            if i.room.ai_time == 0:
                continue
            if ai_time >= i.room.ai_time:
                i.trusteeship(1,0,0,0,0,0) #设置玩家默认托管


    def set_ai(self,player,timer):
        log = {}
        log["player"] = player.uuid
        log["seat"] = player.seat
        log["room_id"] = self.room_id
        log["timer_type"] = timer
        log["player_state"] = player.state
        log["table_state"] = self.state
        if player.table.conf.game_type == 7:
            pass
        elif player.table.conf.game_type == 4:
            pass
        else:
            return
        if player.room.ai_type != 0:
            if timer == "show_card_15":
                self.ai_show_card(player)
            if timer == "pledge_15":
                niu_type = 0
                if len(player.round.cards_in_hand)!= 0:
                    niu_type = self.ai_get_card_type(player.round.cards_in_hand,self.conf)
                    log["cards_rest"] = player.round.cards_in_hand
                    log["niu_type"] = niu_type
                pledge_type = 0
                count = 0
                if player.room.pledge_type == 1:
                    if niu_type >= 8:
                        count = player.room.pledge
                else:
                    count = player.room.pledge
                if player.room.push_pledge != 0 and player.room.push_pledge_type != 0:
                    # 推注
                    push_pledge_niu_type = 0
                    if player.room.push_pledge_type == 1:
                        push_pledge_niu_type = 8
                    if player.room.push_pledge_type == 2:
                        push_pledge_niu_type = 9
                    if player.room.push_pledge_type == 3:
                        push_pledge_niu_type = 10
                    if push_pledge_niu_type != 0:
                        if niu_type >= push_pledge_niu_type:
                            count = player.room.push_pledge
                            pledge_type = 1
                # 没分 填补最低
                if count == 0:
                    if self.conf.game_type == 7:
                        count = 1
                    else:
                        count = self.conf.score

                log["pledge_score"] = count
                log["pledge_type"] = pledge_type
                self.ai_pledge(player,count, pledge_type)
            if timer == "loot_dealer_15":
                niu_type = 0
                if len(player.round.cards_in_hand) != 0:
                    niu_type = self.ai_get_card_type(player.round.cards_in_hand,self.conf)
                    log["cards_rest"] = player.round.cards_in_hand
                    log["niu_type"] = niu_type

                loot_dealer_niu_type = 0
                count = -1
                if player.room.loot_dealer_type != 0:
                    # 抢庄
                    loot_dealer_niu_type = 0
                    if player.room.loot_dealer_type == 1:
                        loot_dealer_niu_type = 8
                    if player.room.loot_dealer_type == 2:
                        loot_dealer_niu_type = 9
                    if player.room.loot_dealer_type == 3:
                        loot_dealer_niu_type = 10
                    if loot_dealer_niu_type != 0:
                        if niu_type >= loot_dealer_niu_type:
                            count = player.room.loot_dealer
                    log["loot_dealer"] = count
                self.ai_loot_dealer_15(player,count)
            if timer == "ready_15":
                self.ai_ready_15(player)

            self.logger.info(log)

    def ai_pledge(self,player,count,pledge_type):
        if player.state != "CashPledgeState":
            if player.seat == self.dealer_seat:
                return
            if player.round.pledge != 0:
                return
            if not player.is_playing():
                return
            if self.conf.pledge_res:
                if player.round.loot_dealer == self.conf.loot_dealer:
                    count = self.conf.get_score_Max(self.conf.score)
            if self.conf.game_type == 4 or self.conf.game_type == 6 or self.conf.game_type == 7:
                if self.state == "LootDealerState":
                    player.pledge_score(count, pledge_type, player.round.loot_dealer)
                    return

    def ai_show_card(self,player):
        if not player.is_playing():
            return
        if self.conf.game_type != 5:  # 非通比牛牛
            if player.seat == self.dealer_seat:
                return
        if player.state == "DealState" or player.state == "CashPledgeState" or player.state == "Deal2State":
            player.show_card()

    def ai_loot_dealer_15(self,player,count=-1):
        if player.state != "LootDealerState":
            if not player.is_playing():
                return
            if self.state == "DealState":
                if self.conf.game_type == 4 or self.conf.game_type == 7:
                    player.loot_dealer_type(count)
                    return
            if self.state == "StartingState":
                if self.conf.game_type == 6:
                    player.loot_dealer_type(count)
                    return

    def ai_ready_15(self,player):
        if player.state == "InitState" or player.state == "SettleState":
            player.ready()