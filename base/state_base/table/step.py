# coding: utf-8


from base.state_base.player.discard import DiscardState
from base.state_base.table.table_base_state import TableStateBase


class StepState(TableStateBase):
    def __init__(self):
        super(StepState, self).__init__()

    def enter(self, owner):
        super(StepState, self).enter(owner)

    def next_state(self, owner):
        if owner.active_seat >= 0:
            active_player = owner.seat_dict[owner.active_seat]
            owner.active_seat = active_player.next_seat
        else:
            owner.active_seat = owner.dealer_seat
        active_player = owner.seat_dict[owner.active_seat]
        from base.state_base.table.wait import WaitState
        owner.machine.trigger(WaitState())
        active_player.machine.trigger(DiscardState())
