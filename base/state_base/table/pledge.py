# coding: utf-8


from base.state_base.table.table_base_state import TableStateBase
from state.table_state.deal import DealState
from state.table_state.deal2 import Deal2State
from protocol.commands import *

class CashPledgeState(TableStateBase):
    def enter(self, owner):
        super(CashPledgeState, self).enter(owner)

        if owner.conf.game_type != 3:
            owner.prompt_card_msg(0)

    def after(self, owner):

        if owner.conf.game_type == 4 or owner.conf.game_type == 7:
            owner.machine.trigger(Deal2State())
        else:
            owner.machine.trigger(DealState())