# coding: utf-8

import random
from copy import copy

from base.state_base.player.deal2 import Deal2State as PlayerDeal2State
from base.state_base.table.table_base_state import TableStateBase
from base.state_base.table.step import StepState
from logic.table_action import prompt_deal
from protocol.commands import *
from state.table_state.deal import get_card_type

from state.table_state.settle_for_round import get_card_value
from state.table_state.settle_for_round import get_card_color
from state.table_state.settle_for_round import get_card_logic_value

from settings import redis
from protocol.serialize import send
from base.logger import Logger
import time

class Deal2State(TableStateBase):
    def __init__(self):
        super(Deal2State, self).__init__()

    def enter(self, owner):
        super(Deal2State, self).enter(owner)
        owner.active_seat = -1
        log = {}
        tile_blank = [0] * 5
        for i in owner.player_dict.values():
            player = i
            if player.state == "InitState":
                continue

            self_cards_count =owner.conf.cards_count
            msg_dict = dict()
            record = False
            if player.state == "WaitState" or player.state == "PauseState":
                msg_dict["self_cards"] = tile_blank
            else:
                record = True
                while self_cards_count < 5:
                    i.round.cards_in_hand.append(owner.cards_on_desk.pop())
                    self_cards_count += 1

                #if player.seat == owner.dealer_seat:
                #    self.cesi(player, owner.cur_round)
                #else:
                #    self.cesi2(player, owner.cur_round)
                res_type = get_card_type(player.round.cards_in_hand,owner.conf)
                player.round.niu_type = res_type
                msg_dict["self_cards"] = player.round.cards_in_hand  # 剩余手牌
                log[str(player.seat)] = player.round.cards_in_hand
                player.machine.trigger(PlayerDeal2State())


            msg_dict["other_cards"] = tile_blank
            msg_dict["res_type"] = player.round.niu_type
            player.send(DEAL2_DN, msg_dict)

            if record:
                replay = dict()
                replay["type"] = 3
                replay["cmd"] = DEAL2_DN
                replay["data"] = msg_dict
                replay["data"]["player"] = player.uuid
                replay["time"] = int(time.time() * 1000 )
                owner.replay.append(replay)
        owner.logger.info(log)

        for i in owner.lookon_player_dict.values():
            lookon_player = i
            msg_dict = dict()
            msg_dict["self_cards"] = tile_blank  # 剩余手牌
            msg_dict["other_cards"] = tile_blank
            msg_dict["res_type"] = 0
            lookon_player.send(DEAL2_DN, msg_dict)
        owner.set_name_timer("show_card_15")

    def cesi(self, d_player, table_cur_round):
        return
        cards_rest = []
        if table_cur_round == 1:
            cards_rest = [0x2b, 0x38, 0x0c, 0x02, 0x0a]
            # cards_rest = [0x02, 0x03, 0x04, 0x05, 0x06]
        elif table_cur_round == 2:
            cards_rest = [0x01, 0x11, 0x02, 0x12, 0x05]
        elif table_cur_round == 3:
            cards_rest = [0x04, 0x3c, 0x2a, 0x1c, 0x05]
        elif table_cur_round == 4:
            cards_rest = [0x0a, 0x0b, 0x0c, 0x3d, 0x1a]
        elif table_cur_round == 5:
            cards_rest = [0x0a, 0x0b, 0x0c, 0x3d, 0x1a]
        elif table_cur_round == 6:
            cards_rest = [0x01, 0x11, 0x21, 0x31, 0x05]
        #elif table_cur_round == 7:
        #    cards_rest = [0x01, 0x02, 0x03, 0x04, 0x05]
        else:
            return

        d_player.round.cards_in_hand = cards_rest

    def cesi2(self, d_player, table_cur_round):
        return
        cards_rest = []
        if table_cur_round == 1:
            cards_rest = [0x01, 0x02, 0x03, 0x04, 0x05]
        elif table_cur_round == 2:
            cards_rest = [0x11, 0x02, 0x03, 0x04, 0x05]
        elif table_cur_round == 3:
            cards_rest = [0x07, 0x02, 0x03, 0x04, 0x05]
        elif table_cur_round == 4:
            cards_rest = [0x0a, 0x0b, 0x1a, 0x2d, 0x05]
        elif table_cur_round == 5:
            cards_rest = [0x01, 0x11, 0x03, 0x23, 0x05]
        elif table_cur_round == 6:
            cards_rest = [0x01, 0x11, 0x21, 0x31, 0x05]
        elif table_cur_round == 7:
            cards_rest = [0x01, 0x11, 0x21, 0x04, 0x14]
        else:
            return

        d_player.round.cards_in_hand = cards_rest
    def next_state(self, owner):
        pass
        # owner.machine.trigger(StepState())

        # ggg = tornado.ioloop.IOLoop.instance().call_later(15, SuanNiu())


    def execute(self, owner, event):
        super(Deal2State, self).execute(owner, event)
        if event == "prompt_deal":
            prompt_deal(owner)