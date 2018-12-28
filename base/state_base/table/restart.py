# coding: utf-8


from base.state_base.table.table_base_state import TableStateBase


class RestartState(TableStateBase):

    def execute(self, owner, event):
        super(RestartState, self).execute(owner, event)
        if event == "ready":
            owner.is_all_ready()
