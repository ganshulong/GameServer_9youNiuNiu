# coding: utf-8


from base.state_base.table.table_base_state import TableStateBase
from state.table_state.settle_for_round import SettleForRoundState


class EndState(TableStateBase):
    def enter(self, owner):
        super(EndState, self).enter(owner)

    #  def next_state(self, owner):
        #  owner.machine.trigger(SettleForRoundState())
