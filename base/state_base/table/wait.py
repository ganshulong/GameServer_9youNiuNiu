# coding: utf-8

from base.state_base.table.table_base_state import TableStateBase
from logic.table_action import step, end


class WaitState(TableStateBase):

    def execute(self, owner, event):
        super(WaitState, self).execute(owner, event)
        if event == "step":
            step(owner)
        elif event == "end":
            end(owner)
