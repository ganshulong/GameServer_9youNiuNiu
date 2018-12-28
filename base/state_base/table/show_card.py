# coding: utf-8


from base.state_base.table.table_base_state import TableStateBase
from state.table_state.deal import DealState
from state.table_state.settle_for_round import SettleForRoundState
from protocol.commands import *

class ShowCardState(TableStateBase):
    def enter(self, owner):
        super(ShowCardState, self).enter(owner)


    def after(self, owner):
        owner.machine.trigger(SettleForRoundState())