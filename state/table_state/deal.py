# coding: utf-8

import random
import copy

from base.state_base.player.deal import DealState as PlayerDealState
from base.state_base.table.table_base_state import TableStateBase
from base.state_base.table.step import StepState
from logic.table_action import prompt_deal
from protocol.commands import DEAL

from state.table_state.settle_for_round import get_card_value
from state.table_state.settle_for_round import get_card_color
from state.table_state.settle_for_round import get_card_logic_value

from settings import redis
from protocol.serialize import send
from base.logger import Logger
import time


def get_card_type(cb_card_data, conf,type =0):  # 获取类型
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

        if b_same_count == 4:
            return 14
        else:
            b_same_count = 0
            b_second_value = get_card_value(cb_temp_data[1])
            for k, v in enumerate(cb_temp_data):
                if b_second_value == get_card_value(v):
                    b_same_count = b_same_count + 1

            if b_same_count == 4:
                return 14

    # 五小牛牌型
    if conf.is_five_small():
        b_five_small = 0
        for k, v in enumerate(cb_temp_data):
            b_five_small = b_five_small + get_card_value(v)
        if b_five_small <= 10:
            return 13

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
                    b_same_count_2 = b_same_count_2 +1
                elif b_second_value_2 == get_card_value(v):
                    b_same_count_2 = b_same_count_2 +1
        if b_same_count == 3:
            if b_same_count_2 == 2:
                return 18  # 葫芦牛
        elif b_same_count_2 == 3:
            if b_same_count == 2:
                return 18  # 葫芦牛





    # 金牛牌型
    if conf.is_gold():
        b_king_count = 0
        for k, v in enumerate(cb_temp_data):
            if get_card_value(v) > 10:
                b_king_count = b_king_count + 1

        if b_king_count == 5:
            return 12


    # 银牛牌型
    if conf.is_silver():
        b_king_count = 0
        for k, v in enumerate(cb_temp_data):
            if get_card_value(v) >= 10:
                b_king_count = b_king_count + 1

        if b_king_count == 5:
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

        if b_color_count == 5:
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
    if conf.is_long():
        yitiao_info = [1, 2, 3, 4, 5]
        yitiaolong = -1
        yitiaolong = cmp(yitiao_info, b_temp)
        if yitiaolong == 0:
            return 15  # 一条龙
    if type == 2:
        b_temp3 = []
        b_sum = 0
        for k, v in enumerate(cb_temp_data):
            b_temp3.append(get_card_value(v))
        b_temp3.sort()
        jqka_info = [1, 10, 11, 12, 13]
        jqklong = -1
        jqklong = cmp(jqka_info, b_temp3)
        if jqklong == 0:
            return 99  # 10 j q k A

      # 同花牛
    if conf.is_identical():
        b_color_count = 0
        color_type = get_card_color(cb_temp_data[0])
        for k, v in enumerate(cb_temp_data):
            if get_card_color(v) == color_type:
                b_color_count = b_color_count + 1

        if b_color_count == 5:
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
        for q, w in enumerate(b_temp):
            if e == q:

                continue
            if (b_sum - b_temp[e] - b_temp[q]) % 10 == 0:
                if b_temp[e] + b_temp[q] > 10:
                    return b_temp[e] + b_temp[q] - 10
                else:
                    return b_temp[e] + b_temp[q]

    return 0

class DealState(TableStateBase):
    def __init__(self):
        super(DealState, self).__init__()

    def enter(self, owner):
        super(DealState, self).enter(owner)
        owner.active_seat = -1
        log = {}
        cards_rest = []
        a = 0
        while(a < 1):
            cards_rest = self.init_cards_stack(owner.conf.is_no_jqk()) # 初始化桌子牌堆 打乱
            cesi_cards_rest = copy.deepcopy(cards_rest)
            if self.cesi_deal(owner.conf.cards_count, cesi_cards_rest, owner) == 1:
                break
        '''
        owner.replay = {
            "room_id": owner.room_id,  # 记录重播房间信息？
            "round": owner.cur_round,
            "conf": owner.conf.settings,
            "dealer": owner.dealer_seat,  # 庄家位置
            "user": {},
            "deal": {},
            "procedure": [],
            "score": [],
            "pledge": [],
        }'''
        if owner.conf.game_type == 4 or owner.conf.game_type == 7:
            self.deal(owner.conf.cards_count, cards_rest, owner.conf.cards_count, owner, log)  # 发牌
        else:
            self.deal(5,cards_rest,5,owner,log) # 发牌
            owner.set_name_timer("show_card_15")
        owner.cards_on_desk = cards_rest
        log["cards_rest"] = cards_rest

    def next_state(self, owner):
        pass
        # owner.machine.trigger(StepState())

        # ggg = tornado.ioloop.IOLoop.instance().call_later(15, SuanNiu())
    def init_cards_stack(self,no_jqk):  # 初始化桌子上的牌堆 并且打乱
        if no_jqk:
            cards_rest = [0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A,
                          0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18, 0x19, 0x1A,
                          0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28, 0x29, 0x2A,
                          0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x3A]
        else:
            cards_rest = [0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D,
                          0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18, 0x19, 0x1A, 0x1B, 0x1C, 0x1D,
                          0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28, 0x29, 0x2A, 0x2B, 0x2C, 0x2D,
                          0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x3A, 0x3B, 0x3C, 0x3D]

        random.shuffle(cards_rest)  # 打乱当前牌组

        return cards_rest

    def deal(self, rounds_max, cards_rest, need_send_cards, table, log):  # 发牌（手上实际牌数，牌组，下发数量）

        seat = 0
        for i in table.player_dict.values():
            player = i
            rounds = 0
            if not player.is_playing():
                tile = [0] * need_send_cards
                self.deal_send_2c(player, table, 0, tile, 0, False)
                continue
            while rounds < rounds_max:
                player.round.cards_in_hand.append(cards_rest.pop())
                rounds += 1
            #table.replay["user"][str(player.seat)] = (player.uuid, player.info)
            #table.replay["deal"][str(player.seat)] = copy(player.round.cards_in_hand)
            log[str(player.seat)] = player.round.cards_in_hand

            tile = []
            tile_other = []
            cards_count = len(player.round.cards_in_hand)
            #if player.seat == table.dealer_seat:
            #    self.cesi(player,table.cur_round,rounds_max)
            #else:
            #    self.cesi2(player,table.cur_round,rounds_max)

            if cards_count == 5:
                res_type = get_card_type(player.round.cards_in_hand, table.conf)
                player.round.niu_type = res_type
            self_cards_count = 0

            while self_cards_count < need_send_cards:
                tile.append(player.round.cards_in_hand[self_cards_count])
                tile_other.append(0)
                self_cards_count += 1
            while self_cards_count < 5:
                tile.append(0)
                tile_other.append(0)
                self_cards_count += 1

            if table.conf.game_type == 4 or table.conf.game_type == 7:
                self.deal_send_2c(player,table,tile,tile_other,0)
            else:
                self.deal_send_2c(player, table, tile, tile_other, res_type)
            player.machine.trigger(PlayerDealState())

            table.logger.info(log)
        for i in table.lookon_player_dict.values():
            lookon_player = i
            lookon_tile_other = []
            lookon_self_cards_count = 0
            while lookon_self_cards_count < need_send_cards:
                lookon_tile_other.append(0)
                lookon_self_cards_count += 1
            self.deal_send_2c(lookon_player, table, 0, lookon_tile_other, 0, False)

    def cesi_deal(self, rounds_max, cards_rest,table):  # 发牌（手上实际牌数，牌组，下发数量）

        seat = 0
        niu_max_count = 0
        niu_max_player = table.seat_dict[table.dealer_seat]
        for i in table.player_dict.values():
            player = i
            rounds = 0
            if not player.is_playing():
                continue
            while rounds < rounds_max:
                player.round.cesi_cards_in_hand.append(cards_rest.pop())
                rounds += 1

            cards_count = len(player.round.cesi_cards_in_hand)
            if cards_count == 5:
                res_type = get_card_type(player.round.cesi_cards_in_hand, table.conf,2)
                player.round.cesi_niu_type = res_type
                if res_type >10:
                    if res_type == 99:
                        return 0
                    if table.niu_max >= 4:
                        return 0
                    if niu_max_count > 1:
                        return 0
                    niu_max_count+=1
                    niu_max_player = player
                    if player.room.niu_max_count >= 1:
                        return 0
        if cards_count != 5:
            for i in table.player_dict.values():
                player = i
                if player.state == "InitState":
                    continue
                self_cards_count = table.conf.cards_count
                if player.state == "WaitState" or player.state == "PauseState":
                   pass
                else:
                    record = True
                    while self_cards_count < 5:
                        i.round.cesi_cards_in_hand.append(cards_rest.pop())
                        self_cards_count += 1
                    res_type = get_card_type(player.round.cesi_cards_in_hand, table.conf,2)
                    player.round.cesi_niu_type = res_type
                    if res_type >10:
                        if res_type == 99:
                            return 0
                        if table.niu_max >= 4:
                            return 0
                        if niu_max_count > 1:
                            return 0
                        niu_max_count+=1
                        niu_max_player = player
                        if player.room.niu_max_count >= 1:
                            return 0
        table.niu_max +=1
        niu_max_player.room.niu_max_count+=1
        return 1



    def cesi(self,d_player,table_cur_round,rounds_max):
        return
        cards_rest = []
        if rounds_max == 4:
            if table_cur_round == 1:
                cards_rest = [0x21, 0x3a, 0x0b, 0x0c]
            elif table_cur_round == 2:
                cards_rest = [0x01, 0x11, 0x02, 0x12]
            elif table_cur_round == 3:
                cards_rest = [0x04, 0x3c, 0x2a, 0x1c]
            elif table_cur_round == 4:
                cards_rest = [0x0a, 0x0b, 0x0c, 0x3d]
            elif table_cur_round == 5:
                cards_rest = [0x0a, 0x0b, 0x0c, 0x3d]
            elif table_cur_round == 6:
                cards_rest = [0x01, 0x11, 0x21, 0x31]
            #elif table_cur_round == 7:
            #    cards_rest = [0x01, 0x02, 0x03, 0x04]
            else:
                return
        else:
            if table_cur_round == 1:
                cards_rest = [0x01, 0x02, 0x03, 0x04, 0x05]
                # cards_rest = [0x02, 0x03, 0x04, 0x05, 0x06]
            elif table_cur_round == 2:
                cards_rest = [0x01, 0x0a, 0x0b ,  0x0c, 0x0d]
            elif table_cur_round == 3:
                cards_rest = [0x01, 0x03, 0x05 ,  0x06 ,0x08]
            elif table_cur_round == 4:
                cards_rest = [0x11, 0x22, 0x33,  0x04, 0x05]
            elif table_cur_round == 5:
                cards_rest = [0x01, 0x11, 0x21,  0x05, 0x15]
            elif table_cur_round == 6:
                cards_rest = [0x11, 0x02, 0x03 , 0x24, 0x35]
            elif table_cur_round == 7:
                cards_rest = [0x01, 0x02, 0x03, 0x04, 0x05]
            else:
                return

        d_player.round.cards_in_hand = cards_rest

    def cesi2(self, d_player, table_cur_round,rounds_max):
        return
        cards_rest = []
        if rounds_max ==4:
            if table_cur_round == 1:
                cards_rest = [0x01, 0x02, 0x03, 0x04]
            elif table_cur_round == 2:
                cards_rest = [0x11, 0x02, 0x03, 0x04]
            elif table_cur_round == 3:
                cards_rest = [0x07, 0x02, 0x03, 0x04]
            elif table_cur_round == 4:
                cards_rest = [0x0a, 0x0b, 0x1a, 0x2d]
            elif table_cur_round == 5:
                cards_rest = [0x01, 0x11, 0x03, 0x23]
            elif table_cur_round == 6:
                cards_rest = [0x01, 0x11, 0x21, 0x31]
            elif table_cur_round == 7:
                cards_rest = [0x01, 0x11, 0x21, 0x04]
            else:
                return
        else:
            if table_cur_round == 1:
                cards_rest = [0x01, 0x02, 0x03, 0x04, 0x05]
                # cards_rest = [0x02, 0x03, 0x04, 0x05, 0x06]
            elif table_cur_round == 2:
                cards_rest = [0x01, 0x0a, 0x0b ,  0x0c, 0x0d]
            elif table_cur_round == 3:
                cards_rest = [0x01, 0x03, 0x05 ,  0x06 ,0x08]
            elif table_cur_round == 4:
                cards_rest = [0x11, 0x22, 0x33,  0x04, 0x05]
            elif table_cur_round == 5:
                cards_rest = [0x01, 0x11, 0x21,  0x05, 0x15]
            elif table_cur_round == 6:
                cards_rest = [0x11, 0x02, 0x03 , 0x24, 0x35]
            elif table_cur_round == 7:
                cards_rest = [0x01, 0x02, 0x03, 0x04, 0x05]
            else:
                return

        d_player.round.cards_in_hand = cards_rest

    def deal_send_2c(self, player, table, tile_data, tile_other, res_type, record=True):
        msg_dict = dict()
        msg_dict["self_cards"] = tile_data
        msg_dict["other_cards"] = tile_other
        msg_dict["res_type"] = res_type
        msg_dict["wait_time"] = 15

        player.send(DEAL, msg_dict)

        if record:
            replay = dict()
            replay["type"] = 3
            replay["cmd"] = DEAL
            replay["data"] = msg_dict
            replay["data"]["player"] = player.uuid
            replay["time"] = int(time.time() * 1000 )
            table.replay.append(replay)


    def execute(self, owner, event):
        super(DealState, self).execute(owner, event)
        if event == "prompt_deal":
            prompt_deal(owner)

