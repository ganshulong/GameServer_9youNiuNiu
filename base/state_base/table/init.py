# coding: utf-8


from base.state_base.table.table_base_state import TableStateBase
from base.state_base.table.ready import ReadyState


class InitState(TableStateBase):
    def next_state(self, owner):
        owner.machine.trigger(ReadyState())

    def execute(self, owner, event):
        super(InitState, self).execute(owner, event)
        if event == "ready":
            owner.is_all_ready()
