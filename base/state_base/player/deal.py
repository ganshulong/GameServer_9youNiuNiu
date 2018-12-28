# coding: utf-8

from base.state_base.player.wait import WaitState

from base.state_base.player.player_base_state import PlayerStateBase


class DealState(PlayerStateBase):
    def __init__(self):
        super(DealState, self).__init__()

    def enter(self, owner):
        super(DealState, self).enter(owner)

    #def next_state(self, owner):
    #    owner.machine.trigger(WaitState())

    def execute(self, owner, event, msg_dict=None):
        super(DealState, self).execute(owner, event, msg_dict)

        if owner.table.state == "DealState":
            if event == "loot_dealer":
                if owner.table.conf.game_type == 4 or owner.table.conf.game_type == 7:
                    owner.loot_dealer_type(msg_dict["loot_dealer"])
            elif event == "show_card":
                if owner.table.conf.game_type == 6 or owner.table.conf.game_type == 1 or owner.table.conf.game_type == 2 or owner.table.conf.game_type == 5:
                        owner.show_card()
            else:
                owner.table.logger.warn("player {0} event {1} not register".format(owner.seat, event))


