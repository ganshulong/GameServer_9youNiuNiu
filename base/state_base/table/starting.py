# coding: utf-8


from base.state_base.table.table_base_state import TableStateBase
from state.table_state.deal import DealState
from protocol.commands import *


class StartingState(TableStateBase):
    def enter(self, owner):
        super(StartingState, self).enter(owner)
        msg_dict = dict()

        #创建replay
        msg_dict_round = dict()
        msg_dict_round["round"] = owner.cur_round
        msg_dict_round["rounds"] = owner.conf.rounds
        owner.add_replay( ROUND_STATE,msg_dict_round)
        owner.send_table_msg(ROUND_STATE, msg_dict_round, True, True)
        owner.pledge_prompt_msg()

        if owner.conf.game_type == 4 or owner.conf.game_type == 7:
            owner.prompt_loot_dealer_msg(0)
            owner.set_name_timer("loot_dealer_15")
        elif owner.conf.game_type == 5:

            for i in owner.player_dict.values():
                if i.state == "InitState":
                    continue
                i.round.pledge = owner.conf.score  # 给所有人放上押金

            owner.prompt_card_msg(0)
        elif owner.conf.game_type == 6:
            owner.prompt_loot_dealer_msg(0)
            owner.set_name_timer("loot_dealer_15")
        else:
            owner.is_push_score()
            owner.prompt_pledge_msg(0)
            owner.set_name_timer("pledge_15")
        from base.center.request import room_state
        room_state(owner, 2)

    def after(self, owner):
        if owner.conf.game_type == 5:
            owner.machine.trigger(DealState())
        elif owner.conf.game_type == 4 or owner.conf.game_type == 7:
            owner.machine.trigger(DealState())
