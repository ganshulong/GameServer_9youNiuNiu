# coding: utf-8
from datetime import datetime
from copy import copy
import copy
from base.state_base.player.settle import SettleState
from base.state_base.player.ready import ReadyState
from base.state_base.player.wait import WaitState
from base.state_base.player.pause import PauseState
from base.state_base.table.table_base_state import TableStateBase
from base.state_base.table.restart import RestartState
from protocol.commands import *
import json

def get_card_value(cb_card_data):  # 获取数值
    return cb_card_data & 0x0f

def get_card_color(cb_card_data):  # 获取花色
    return (cb_card_data & 0xf0) >> 4

def get_card_logic_value(cb_card_data):  # 逻辑数值
    b_card_value = get_card_value(cb_card_data)
    if b_card_value > 10:
        return 10
    else:
        return b_card_value

def get_card_weight_value(cb_card_data):   # 权重数值
    return ((cb_card_data & 0x0f) << 4) + ((cb_card_data & 0xf0) >> 4)

def card_comp(vx, vy):  # 比较大小
    return get_card_weight_value(vy) - get_card_weight_value(vx)

# 计算牛类型权重
def get_niu_type_weight(niu_type):
    weights = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10,  # 无牛~牛牛
               12,    # 11 银
               14,    # 12 金牛
               16,    # 13 五小
               17,    # 14 炸弹
               18,    # 15 一条龙
               11,    # 16 顺子
               13,    # 17 同花
               15,    # 18 葫芦
               19,    # 19 同花顺牛
               0]
    return weights[niu_type]

# 计算牌型权重
def get_cards_weight(cards, niu_type):
    niu_type_weight = get_niu_type_weight(niu_type)
    return (niu_type_weight << 8) + get_card_weight_value(cards[0])

# 输赢结果
def compare_cards(cards1, niu_type1, cards2, niu_type2):
    if niu_type1 == niu_type2:
        if niu_type1 == 14 or niu_type1== 18:
            # 炸弹牛额外
            return get_card_value(cards1[2])>get_card_value(cards2[2])
    return get_cards_weight(cards1, niu_type1) > get_cards_weight(cards2, niu_type2)


# 输赢倍数
def get_multiple_by_type(niu_type,double_type):
    if double_type == 1:
        if niu_type == 0:
            return 1
        elif niu_type <= 7:
            return 1
        elif niu_type <= 9:
            return 2
        elif niu_type == 10:
            return 3
        elif niu_type == 11:
            return 5
        elif niu_type == 12:
            return 6
        elif niu_type == 13:
            return 7
        elif niu_type == 14:
            return 8
        elif niu_type == 15:
            return 9
        elif niu_type == 16:
            return 5
        elif niu_type == 17:
            return 6
        elif niu_type == 18:
            return 7
        elif niu_type == 19:
            return 10
    elif double_type == 2:
        if niu_type == 0:
            return 1
        elif niu_type <= 6:
            return 1
        elif niu_type <= 8:
            return 2
        elif niu_type == 9:
            return 3
        elif niu_type == 10:
            return 4
        elif niu_type == 11:
            return 5
        elif niu_type == 12:
            return 6
        elif niu_type == 13:
            return 7
        elif niu_type == 14:
            return 8
        elif niu_type == 15:
            return 9
        elif niu_type == 16:
            return 5
        elif niu_type == 17:
            return 6
        elif niu_type == 18:
            return 7
        elif niu_type == 19:
            return 10
    elif double_type == 4:
        if niu_type == 0:
            return 1
        elif niu_type <= 6:
            return 1
        elif niu_type <= 9:
            return 2
        elif niu_type == 10:
            return 3
        elif niu_type == 11:
            return 5
        elif niu_type == 12:
            return 6
        elif niu_type == 13:
            return 7
        elif niu_type == 14:
            return 8
        elif niu_type == 15:
            return 9
        elif niu_type == 16:
            return 5
        elif niu_type == 17:
            return 6
        elif niu_type == 18:
            return 7
        elif niu_type == 19:
            return 10


def get_push_pledge(score,multiple_type,push_pledge,app_id,niu_type):
    if push_pledge == 0:
        return 0
    if app_id == 101:
        count = 1
        if multiple_type >= 2:
            count = 2
        return score * count * push_pledge
    else:
        if niu_type <= 3:
            score_count = 3
        elif niu_type <= 6:
            score_count = 4
        elif niu_type <= 9:
            score_count = 8
        else:
            score_count = 10

        if score == 1:
            score_double = 1
        elif score == 2:
            score_double = 2
        elif score == 3:
            score_double = 3
        elif score == 4:
            score_double = 4
        elif score == 5:
            score_double = 5
        return score_count * score_double


class SettleForRoundState(TableStateBase):
    def __init__(self):
        super(SettleForRoundState, self).__init__()
        self.max_seat = 0
        self.max_niu_type = 0

    def enter(self, owner):
        super(SettleForRoundState, self).enter(owner)

        # 计算输赢
        self.calculate(owner)

        # 统计数据，广播玩家，上报中心
        self.stat_and_notify(owner)

    def after(self, owner):
        # 将所有玩家至于结算状态
        if not owner.is_negative():      # 不能负分
            score_count = 0  # 比赛积分满足继续游戏的玩家数
            for player in owner.player_dict.values():
                if player.get_total_score() <= 0:
                    player.is_wait = True
                    player.machine.trigger(PauseState())
                else:
                    score_count += 1
                    player.is_wait = False
                    if player.state == "WaitState":
                        player.machine.trigger(ReadyState())
                    else:
                        player.machine.trigger(SettleState())
                player.clear_for_round()

            if score_count < 2:
                owner.logger.info("match room {0} dismiss for less score user".format(owner.room_id))
                from state.table_state.settle_for_room import SettleForRoomState
                owner.machine.trigger(SettleForRoomState())
                return
        else:
            for player in owner.player_dict.values():
                player.clear_for_round()
                player.is_wait = False
                if player.state == "WaitState":
                    player.machine.trigger(ReadyState())
                else:
                    player.machine.trigger(SettleState())

        if owner.cur_round > owner.conf.rounds:
            from state.table_state.settle_for_room import SettleForRoomState
            owner.machine.trigger(SettleForRoomState())
            return

        # 换庄
        self.change_dealer(owner)

        #msg_dict = dict()
        #msg_dict["round"] = owner.cur_round
        #msg_dict["rounds"] = owner.conf.rounds
        #owner.send_table_msg(ROUND_STATE, msg_dict,True,True)

        if owner.conf.game_type == 2:   # 斗公牛
            dealer = owner.seat_dict[owner.dealer_seat]
            if dealer.room.score <= 0:
                from state.table_state.settle_for_room import SettleForRoomState
                owner.machine.trigger(SettleForRoomState())
                return

        owner.replay = []
        if owner.cur_round <= owner.conf.rounds:
            owner.set_name_timer("ready_15")

        owner.machine.trigger(RestartState())

    def exit(self, owner):
        # 清空玩家的当局数据
        super(SettleForRoundState, self).exit(owner)

    # 计算输赢
    def calculate(self, owner):
        require_positive = not owner.is_negative()        # 分数只能为正
        dealer = owner.seat_dict[owner.dealer_seat]
        dealer_cards = copy.deepcopy(dealer.round.cards_in_hand)
        dealer_cards.sort(card_comp)
        dealer_niu_type = dealer.round.niu_type

        self.max_seat = owner.dealer_seat  # 牛最大选手位置（默认等于庄家）
        max_cards = copy.deepcopy(dealer_cards)  # 牛最大手牌
        self.max_niu_type = dealer_niu_type
        win_player_list = []
        for seat in owner.seat_dict.keys():
            player = owner.seat_dict[seat]
            if not player.is_playing():
                continue
            cards = copy.deepcopy(player.round.cards_in_hand)
            cards.sort(card_comp)  # 排序手牌
            niu_type = player.round.niu_type
            if seat == owner.dealer_seat:  # 庄家
                continue
            result = compare_cards(cards, niu_type, dealer_cards, dealer_niu_type)
            if dealer.round.loot_dealer == 0:
                dealer.round.loot_dealer = 1
            if result:  # 赢了
                multiple_type = get_multiple_by_type(niu_type, owner.conf.get_double_type())
                win_score = owner.conf.get_qh_base_score() * player.round.pledge * multiple_type * abs(dealer.round.loot_dealer)
                if require_positive and player.get_total_score() < win_score:   # 比赛场闲家得分不高于自身积分
                    win_score = player.get_total_score()
                win_player_list.append([seat, get_cards_weight(cards, niu_type), win_score])
                player.round.score = win_score
                dealer.round.score -= win_score
                # 计算下一局推注
                if player.room.push_pledge == 0:
                    if owner.conf.game_id == 3:
                        # 如果是牛爷
                        player.room.push_pledge = player.round.score + player.round.pledge
                        player.room.push_pledge = min(player.room.push_pledge,
                                                      owner.conf.score * owner.conf.get_push_pledge())
                    else:
                        player.room.push_pledge = get_push_pledge(owner.conf.score, multiple_type,
                                                                  owner.conf.get_push_pledge(), owner.conf.app_id,
                                                                  niu_type)
                else:
                    if player.round.pledge == player.room.push_pledge:
                        player.room.push_pledge = 0
                    else:
                        if owner.conf.game_id == 3:
                            # 如果是牛爷
                            player.room.push_pledge = player.round.score + player.round.pledge
                            player.room.push_pledge = min(player.room.push_pledge,
                                                          owner.conf.score * owner.conf.get_push_pledge())
                        else:
                            player.room.push_pledge = get_push_pledge(owner.conf.score, multiple_type,
                                                                      owner.conf.get_push_pledge(), owner.conf.app_id,
                                                                      niu_type)
                dealer.room.push_pledge = 0
            else:
                multiple_type = get_multiple_by_type(dealer_niu_type, owner.conf.get_double_type())
                win_score = owner.conf.get_qh_base_score() * player.round.pledge * multiple_type * abs(dealer.round.loot_dealer)
                if require_positive:
                    if player.get_total_score() < win_score:    # 比赛场庄家得分不能高于闲家积分
                        win_score = player.get_total_score()
                    if dealer.get_total_score() < win_score:    # 比赛场庄家得分不能高于自身积分
                        win_score = dealer.get_total_score()
                player.round.score = -win_score
                dealer.round.score += win_score
                player.room.push_pledge = 0
                dealer.room.push_pledge = 0

            # 得出最大牛选手
            if compare_cards(cards, niu_type, max_cards, self.max_niu_type):
                self.max_seat = player.seat
                max_cards = copy.deepcopy(cards)  # 牛最大手牌
                self.max_niu_type = niu_type

        if owner.conf.game_type == 5:   # 通比牛牛
            dealer = owner.seat_dict[self.max_seat]
            dealer.round.score = 0
            for seat in owner.seat_dict.keys():
                player = owner.seat_dict[seat]
                if not player.is_playing() or player.seat == self.max_seat:
                    continue
                win_score = player.round.pledge * get_multiple_by_type(self.max_niu_type, owner.conf.get_double_type())
                if require_positive:
                    if player.get_total_score() < win_score:    # 比赛场庄家得分不能高于闲家积分
                        win_score = player.get_total_score()
                    if dealer.get_total_score() < win_score:    # 比赛场庄家得分不能高于自身积分
                        win_score = dealer.get_total_score()
                player.round.score = -win_score
                dealer.round.score += win_score
        elif owner.conf.game_type == 2 or require_positive:  # 斗公牛 或者 比赛场
            if require_positive:
                base_score = dealer.round.score + dealer.get_total_score()
            else:
                base_score = dealer.round.score + dealer.room.score
            if base_score < 0:
                win_player_list = sorted(win_player_list, key=lambda x: x[1], reverse=True)
                base_score -= dealer.round.score
                dealer.round.score = -base_score
                for k, v in enumerate(win_player_list):
                    player = owner.seat_dict[v[0]]
                    if not player.is_playing():
                        continue
                    if base_score >= v[2]:
                        base_score -= v[2]
                        player.round.score = v[2]
                    else:
                        player.round.score = base_score
                        base_score = 0

    # 统计数据，广播玩家，上报中心
    def stat_and_notify(self, owner):
        log = {"uuid": owner.room_uuid, "current_round": owner.cur_round,
               "room_id": owner.room_id,
               "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
               "player_data": []}

        msg_dict = dict()
        msg_dict["owner_info"] = owner.owner_info
        msg_dict["time"] = owner.get_name_timer_count("ready_15")
        msg_dict["max_seat"] = self.max_seat
        msg_dict["player_data"] = list()
        for seat in owner.seat_dict.keys():
            player = owner.seat_dict[seat]
            if not player.is_playing():
                continue
            # 有牛，无牛
            if player.round.niu_type < 1:
                player.room.null_cnt += 1
            else:
                player.room.niu_cnt += 1
            # 输赢次数
            if player.round.score > 0:
                player.room.win_cnt += 1
            else:
                player.room.lose_cnt += 1
            # 总分数
            player.room.score += player.round.score

            data = dict()
            data["seat"] = seat
            data["score"] = player.round.score
            data["total_score"] = player.room.score
            msg_dict["player_data"].append(data)

            log["player_data"].append({
                "player": player.uuid,
                "info": player.get_simple_info(),
                "seat": player.seat,
                "cards_in_hand": player.round.cards_in_hand,
                "score": player.round.score,
                "pt": player.get_total_score(),
                "pledge": player.round.pledge,
                "niu": player.round.niu_type,
                "z": 1 if seat == owner.dealer_seat else 0,
                "q": player.round.loot_dealer
            })
        # 发送结果
        owner.send_table_msg(SETTLEMENT_FOR_ROUND_DN, msg_dict, True, True)

        # 数据上报
        from base.center.request import settle_for_round
        settle_for_round(owner, log,owner.get_replay_compress())
        owner.cur_round += 1

    # 换庄
    def change_dealer(self, owner):
        if owner.dealer_seat in owner.seat_dict:
            dealer = owner.seat_dict[owner.dealer_seat]
            if dealer.state == "PauseState":    # 如果庄家被踢出
                for seat, player in owner.seat_dict.items():
                    if player.state != "PauseState":
                        owner.dealer_seat = seat
                        break

        if owner.conf.get_banker() == 2: # 轮流坐庄
            dealer_seat = -1
            for seat, player in owner.seat_dict.items():
                if seat == owner.dealer_seat:
                    continue
                if player.state == "PauseState":
                    continue
                if seat > owner.dealer_seat:
                    dealer_seat = seat
                    break
            if dealer_seat == -1:
                for seat, player in owner.seat_dict.items():
                    if seat != owner.dealer_seat and player.state != "PauseState":
                        dealer_seat = seat
                        break

            owner.dealer_seat = dealer_seat
        elif owner.conf.get_banker() == 3: # 牛牛坐庄
            if self.max_niu_type > 9 and self.max_seat in owner.seat_dict:
                max_player = owner.seat_dict[self.max_seat]
                if max_player.state != "PauseState":
                    owner.dealer_seat = self.max_seat
        elif owner.conf.get_banker() == 4:  # 牌大坐庄
            if self.max_seat in owner.seat_dict:
                max_player = owner.seat_dict[self.max_seat]
                if max_player.state != "PauseState":
                    owner.dealer_seat = self.max_seat
