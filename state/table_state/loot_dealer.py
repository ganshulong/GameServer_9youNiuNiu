# coding: utf-8

import random
from copy import copy

from base.state_base.player.deal import DealState as PlayerDealState
from base.state_base.table.table_base_state import TableStateBase
from base.state_base.table.step import StepState
from logic.table_action import prompt_deal
from protocol.commands import *

from state.table_state.settle_for_round import get_card_value
from state.table_state.settle_for_round import get_card_color
from state.table_state.settle_for_round import get_card_logic_value

from settings import redis
from protocol.serialize import send
from base.logger import Logger

class LootDealerState(TableStateBase):
    def __init__(self):
        super(LootDealerState, self).__init__()

    def enter(self, owner):
        super(LootDealerState, self).enter(owner)
        owner.active_seat = -1
        log = {}
        double_2 =[]
        double_1 =[]
        double_0 =[]
        double_3 =[]
        double_4 = []
        double_5 = []
        for i in owner.player_dict.values():
            player = i
            if not player.is_playing():
                continue

            if player.round.loot_dealer == -1:
                double_0.append(player.seat)
            elif player.round.loot_dealer == 1:
                double_1.append(player.seat)
            elif player.round.loot_dealer == 2:
                double_2.append(player.seat)
            elif player.round.loot_dealer == 3:
                double_3.append(player.seat)
            elif player.round.loot_dealer == 4:
                double_4.append(player.seat)
            elif player.round.loot_dealer == 5:
                double_5.append(player.seat)
        cards_seat = -1

        len_0_count = len(double_0)
        len_5_count = len(double_5)
        len_3_count = len(double_3)
        len_4_count = len(double_4)
        len_2_count = len(double_2)
        len_1_count = len(double_1)
        if len_5_count != 0:
            cards_seat = self.get_cards_seat(double_5)
        elif len_4_count != 0:
            cards_seat = self.get_cards_seat(double_4)
        elif len_3_count != 0:
            cards_seat = self.get_cards_seat(double_3)
        elif len_2_count != 0:
            cards_seat = self.get_cards_seat(double_2)
        elif len_1_count != 0:
            cards_seat = self.get_cards_seat(double_1)
        elif len_0_count != 0:
            cards_seat = self.get_cards_seat(double_0)

        if cards_seat == -1:
            return

        owner.dealer_seat = cards_seat
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
        owner.dealer_msg(owner.dealer_seat,0)

        owner.is_push_score()
        owner.prompt_pledge_msg(0)
        owner.set_name_timer("pledge_15")

    def get_cards_seat(self,double_x):
        cards_seat = -1
        len_6_count = len(double_x)
        if 	len_6_count != 0:
            if len_6_count == 1:
                cards_seat = double_x[0]
            else:
                dealer = random.randint(0, len_6_count - 1)
                cards_seat = double_x[dealer]
        return  cards_seat

    def next_state(self, owner):
        pass
        # owner.machine.trigger(StepState())

        # ggg = tornado.ioloop.IOLoop.instance().call_later(15, SuanNiu())


    def execute(self, owner, event):
        super(LootDealerState, self).execute(owner, event)
        if event == "prompt_deal":
            prompt_deal(owner)

