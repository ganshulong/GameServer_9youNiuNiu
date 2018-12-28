# coding: utf-8
#亮牌

from base.state_base.player.player_base_state import PlayerStateBase
from protocol.commands import *
from state.table_state.settle_for_round import get_card_logic_value
from state.table_state.settle_for_round import get_card_value
from state.table_state.settle_for_round import get_card_color
import copy

def card_comp(vx, vy):  # 获取类型
    x = get_card_value(vx)
    y = get_card_value(vy)
    if x < y:
        return -1
    elif x > y:
        return 1
    else:
        color1 = get_card_color(vx)
        color2 = get_card_color(vy)
        if color1 < color2:
            return -1
        else:
            return 1
def show_card_type(cb_card_data, niu_type):  # 获取类型
    cb_temp_data = []
    for k, v in enumerate(cb_card_data):
        cb_temp_data.append(v)

    cb_temp_data.sort(card_comp)
    if niu_type == 0:
        return cb_temp_data
    # 炸弹牌型
    if niu_type == 14:
        b_same_count = 0
        card_seat = -1
        b_second_value = get_card_value(cb_temp_data[2])
        for k, v in enumerate(cb_temp_data):
            if b_second_value != get_card_value(v):
                card_seat = k
                b_same_count = b_same_count + 1
        if card_seat != 4:
            cb_data = []
            for k, v in enumerate(cb_temp_data):
                if k == card_seat:
                    continue
                cb_data.append(v)
            cb_data.append(cb_temp_data[card_seat])
            #count = cb_temp_data[card_seat]
            #cb_temp_data[card_seat] = cb_temp_data[4]
            #cb_temp_data[4] = count
            return cb_data
        else:
            return cb_temp_data

    if niu_type == 18:
        b_same_count = 0
        card_seat = -1
        b_second_value = get_card_value(cb_temp_data[2])
        cb_data = []
        for k, v in enumerate(cb_temp_data):
            if b_second_value == get_card_value(v):
                cb_data.append(v)
        for k, v in enumerate(cb_temp_data):
            if b_second_value != get_card_value(v):
                cb_data.append(v)
        return cb_data

    # 五小牛牌型
    if niu_type == 13:
        return cb_temp_data
    if niu_type == 12:
        return cb_temp_data
    if niu_type == 11:
        return cb_temp_data
    if niu_type == 15:
        return cb_temp_data
    if niu_type == 16:
        return cb_temp_data
    if niu_type == 17:
        return cb_temp_data

    # --牛一~牛牛牌型 或 一条龙
    b_temp = []
    b_sum = 0
    for k, v in enumerate(cb_temp_data):
        b_temp.append(get_card_logic_value(v))
        b_sum = b_sum + b_temp[k]

    card_seat_a = 0
    card_seat_b = 0
    for e, r in enumerate(b_temp):
        for q, w in enumerate(b_temp):
            if e == q:
                continue
            if (b_sum - b_temp[e] - b_temp[q]) % 10 == 0:
                    cb_data = []
                    for uk, uv in enumerate(cb_temp_data):
                        if uk == e:
                            continue
                        if uk == q:
                            continue
                        cb_data.append(uv)
                    cb_data.append(cb_temp_data[e])
                    cb_data.append(cb_temp_data[q])
                    return cb_data
    #print niu_type+cb_card_data
    return cb_temp_data

def show_card_type2(cb_card_data, niu_type):  # 获取类型
    cb_temp_data = []

    cardsign_in_hand = [0,0,0,0,0]
    for k, v in enumerate(cb_card_data):
        cb_temp_data.append(v)

    cb_temp_data.sort(card_comp)
    if niu_type == 0:
        return cardsign_in_hand
    # 炸弹牌型
    if niu_type == 14:
        b_same_count = 0
        card_seat = -1
        b_second_value = get_card_value(cb_temp_data[2])
        for k, v in enumerate(cb_temp_data):
            if b_second_value != get_card_value(v):
                card_seat = k
                b_same_count = b_same_count + 1
        if card_seat != 4:
            cb_data = []
            for k, v in enumerate(cb_temp_data):
                if k == card_seat:
                    continue
                cb_data.append(v)
            #count = cb_temp_data[card_seat]
            #cb_temp_data[card_seat] = cb_temp_data[4]
            #cb_temp_data[4] = count
            for k, v in enumerate(cb_data):
                for q, w in enumerate(cb_card_data):
                    if v == w:
                        cardsign_in_hand[q] = 1
            return cardsign_in_hand
        else:
            return cardsign_in_hand

    if niu_type == 18:
        b_same_count = 0
        card_seat = -1
        b_second_value = get_card_value(cb_temp_data[2])
        cb_data = []
        for k, v in enumerate(cb_temp_data):
            if b_second_value != get_card_value(v):
                cb_data.append(v)
        for k, v in enumerate(cb_data):
            for q, w in enumerate(cb_card_data):
                if v == w:
                    cardsign_in_hand[q] = 1
        return cardsign_in_hand

    # 五小牛牌型
    data = [1, 1, 1, 1, 1]
    if niu_type == 13:
        return data
    if niu_type == 12:
        return data
    if niu_type == 11:
        return data
    if niu_type == 15:
        return data
    if niu_type == 16:
        return data
    if niu_type == 17:
        return data
    if niu_type == 19:
        return data

    # --牛一~牛牛牌型 或 一条龙
    b_temp = []
    b_sum = 0
    for k, v in enumerate(cb_temp_data):
        b_temp.append(get_card_logic_value(v))
        b_sum = b_sum + b_temp[k]

    card_seat_a = 0
    card_seat_b = 0
    for e, r in enumerate(b_temp):
        for q, w in enumerate(b_temp):
            if e == q:
                continue
            if (b_sum - b_temp[e] - b_temp[q]) % 10 == 0:
                    cb_data = []

                    cb_data.append(cb_temp_data[e])
                    cb_data.append(cb_temp_data[q])
                    for k, v in enumerate(cb_data):
                        for q, w in enumerate(cb_card_data):
                            if v == w:
                                cardsign_in_hand[q] = 1
                    return cardsign_in_hand
    return cardsign_in_hand

class ShowCardState(PlayerStateBase):
    def enter(self, owner):
        super(ShowCardState, self).enter(owner)
        # 广播其他玩家
        cards_hand = copy.deepcopy(owner.round.cards_in_hand)
        #cards_hand = show_card_type(owner.round.cards_in_hand,owner.round.niu_type)
        cardsign_in_hand = show_card_type2(owner.round.cards_in_hand,owner.round.niu_type)
        #owner.round.cards_in_hand = copy.deepcopy(cards_hand)
        owner.table.show_card_msg(owner.seat,cards_hand,owner.round.niu_type,cardsign_in_hand)

        owner.table.is_all_show_card()