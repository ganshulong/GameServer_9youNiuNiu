# coding: utf-8
from copy import copy

from base.player import PlayerBase
from protocol.commands import *
from state.status import table_state_code_map, player_state_code_map
import copy
from base.state_base.player.show_card import show_card_type2
from base.state_base.player.ready import ReadyState
from base.state_base.player.wait import WaitState
import json

class Player(PlayerBase):

    def reconnect(self):
        msg_dict = dict()
        msg_dict["room_id"] = self.table.room_id
        msg_dict["kwargs"] = self.table.kwargs
        msg_dict["owner"] = self.table.owner
        msg_dict["owner_info"] = self.table.owner_info
        msg_dict["room_state"] = table_state_code_map[self.table.state]
        msg_dict["round"] = self.table.cur_round
        msg_dict["rounds"] = self.table.conf.rounds
        msg_dict["steal"] = self.table.conf.steal
        msg_dict["dealer"] = self.table.dealer_seat # 庄家位置
        #msg_dict["qh_base_score"] = self.table.get_qh_base_score()
        msg_dict["player_status"] = player_state_code_map[self.state]
        msg_dict["is_admin"] = (self.uuid in self.table.guild_admins)
        show_max_score = False
        if self.table.conf.pledge_res:
            if self.round.loot_dealer == self.table.conf.loot_dealer:
                show_max_score = False
        pledge_double = 0
        if self.table.conf.get_pledge_double():
            if self.round.loot_dealer == self.table.conf.loot_dealer:
                pledge_double = 1
        msg_dict["pledge_double"] = pledge_double
        msg_dict["push_pledge"] = self.room.push_pledge
        msg_dict["time"] = self.table.get_timer_left()

        active_seat = self.table.active_seat
        # 对于前端只有活动玩家处于出牌状态才发送指示灯
        if active_seat >= 0 and self.table.seat_dict[active_seat].state in ("DiscardState"):
            msg_dict["active_seat"] = self.table.active_seat
        else:
            msg_dict["active_seat"] = -1

        if self.state == "DiscardState":
            msg_dict["rest_cards"] += 1
        msg_dict["code"] = 1

        log = {
            "description": "reconnect",
            "room_id": self.table.room_id,
            "kwargs": self.table.kwargs,
            "owner": self.table.owner,
            "owner_info": self.table.owner_info,
            "cur_round": self.table.cur_round,
            "room_state": table_state_code_map[self.table.state],
            "dealer": self.table.dealer_seat,
            "active_seat": self.table.active_seat,
            "discard_seat": self.table.discard_seat,
            "rest_cards": len(self.table.cards_on_desk),
            "code": 1,
            "players": [],
        }

        cards_in_hand = copy.deepcopy(self.round.cards_in_hand)
        msg_dict["player"] = list()
        for i in self.table.player_dict.values():
            body = dict()
            body["seat"] = i.seat
            body["player"] = i.uuid
            body["info"] = i.info
            body["state"] = player_state_code_map[i.state]
            body["is_online"] = i.is_online
            body["score"] = i.get_total_score()
            body["pledge"] = i.round.pledge
            body["loot_dealer"] = i.round.loot_dealer
            body["is_wait"] = i.is_wait
            body["niu_type"] = i.round.niu_type
            body["double_pledge"] = i.round.double_pledge
            body["ai_type"] = i.room.ai_type
            body["push_pledge"]=i.room.push_pledge

            if i.session is not None:
                body["ip"] = i.session.address[0]

            body["cards_in_hand"] = list()
            if i.uuid == self.uuid:
                count = len(cards_in_hand)
                if i.state == "ShowCardState":
                    cards_hand = copy.deepcopy(self.round.cards_in_hand)
                    #cards_hand = show_card_type(self.round.cards_in_hand, self.round.niu_type)
                    #cards_in_hand = copy.deepcopy(cards_hand)
                    body["cardsign_in_hand"] = list()
                    cardsign_in_hand = show_card_type2(self.round.cards_in_hand, self.round.niu_type)
                    for w in cardsign_in_hand:
                        body["cardsign_in_hand"].append(w)
                for c in cards_in_hand:
                    body["cards_in_hand"].append(c)
                if count != 0:
                    while count < 5:
                        count += 1
                        body["cards_in_hand"].append(0)
            else:
                count = len(i.round.cards_in_hand)
                if i.state != "WaitState":
                    if i.state == "ShowCardState":
                        cards_hand = copy.deepcopy(i.round.cards_in_hand)
                        #cards_hand = show_card_type(i.round.cards_in_hand, i.round.niu_type)

                        body["cardsign_in_hand"] = list()
                        cardsign_in_hand = show_card_type2(i.round.cards_in_hand, i.round.niu_type)
                        for w in cardsign_in_hand:
                            body["cardsign_in_hand"].append(w)
                        for c in cards_hand:
                            body["cards_in_hand"].append(c)
                    else:
                        for _ in i.round.cards_in_hand:
                            body["cards_in_hand"].append(0)
                        if count != 0:
                            while count < 5:
                                count += 1
                                body["cards_in_hand"].append(0)


            msg_dict["player"].append(body)

            log["players"].append({
                "seat": i.seat,
                "player": i.uuid,
                "info": i.info,
                "state": player_state_code_map[i.state],
                "is_online": i.is_online,
                "total": i.get_total_score(),
                "cards_in_hand": i.round.cards_in_hand,
                "loot_dealer": i.round.loot_dealer,
            })
        self.send(RECONNECT_DN, msg_dict)
        self.room.ai_time = 0 #关闭托管倒计时
        self.table.logger.info(log)

    def ready(self):

        if self.is_wait == True and self.seat == -1:
            if self.uuid not in self.table.lookon_player_dict.keys():
                log = {}
                log["player"] = self.uuid
                log["seat"] = self.seat
                log["room_id"] = self.room_id
                log["is_wait"] =  self.is_wait
                self.table.logger.info(log)
                return
            if len(self.table.player_dict.keys()) >= self.table.chairs:
                msg_dict = dict()
                self.send(READY_LATE, msg_dict)
                return
            if self.seat < 0:  # 分配座位
                seat = -1
                for seat in range(self.table.chairs):
                    if seat in self.table.seat_dict.keys():
                        continue
                    break
                table = self.table
                table.player_dict[self.uuid] = self
                table.seat_dict[seat] = self
                table.lookon_player_dict.pop(self.uuid)
                if table.dealer_seat == -1:
                    table.dealer_seat = seat  # 第一个位置的为庄家
                    if table.cur_round == 1:
                        if table.conf.game_type == 2:  # 斗公牛模式 庄家提前压分
                            dealer = table.seat_dict[table.dealer_seat]
                            dealer.room.score = dealer.room.score + table.conf.base_score
                if self.table.state == "InitState" or self.table.state == "ReadyState" or self.table.state == "SettleState"or self.table.state == "RestartState":
                    self.is_wait = False
                self.seat = seat
                if self.session:
                    self.table.enter_room_other_msg(self)

                from base.center.request import enter_room
                enter_room(self.table, self.uuid, self.info)
                self.table.logger.info("player {0} sit down".format(self.uuid))

        super(Player, self).ready()

    def get_simple_info(self):
        try:
            info = json.loads(self.info)
            simple_info = {"nick": info.get("nick", ""), "sex": info.get("sex", "")}
        except Exception, e:
            print e
            simple_info = {"nick": "", "sex": 1}
        return json.dumps(simple_info,ensure_ascii=False)
