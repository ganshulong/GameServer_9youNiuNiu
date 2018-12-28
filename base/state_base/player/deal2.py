# coding: utf-8

from base.state_base.player.wait import WaitState

from base.state_base.player.player_base_state import PlayerStateBase


class Deal2State(PlayerStateBase):
    def __init__(self):
        super(Deal2State, self).__init__()

    def enter(self, owner):
        super(Deal2State, self).enter(owner)

    def next_state(self, owner):
        #owner.machine.trigger(WaitState())
        pass

    def execute(self, owner, event, msg_dict=None):
        super(Deal2State, self).execute(owner, event, msg_dict)
        if event == "show_card":
            if owner.table.conf.game_type == 4 or owner.table.conf.game_type == 7:
                if owner.table.state == "Deal2State":
                    owner.show_card()
        else:
            owner.table.logger.warn("player {0} event {1} not register".format(owner.seat, event))





