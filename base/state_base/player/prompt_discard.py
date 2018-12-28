# coding: utf-8

from base.state_base.player.player_base_state import PlayerStateBase


class PromptDiscardState(PlayerStateBase):

    def enter(self, owner):
        super(PromptDiscardState, self).enter(owner)

    def next_state(self, owner):
        owner.machine.to_last_state()

    def execute(self, owner, event, msg_dict=None):
        super(PromptDiscardState, self).execute(owner, event, msg_dict)
        from logic.player_action import action
        if event == "action":
            action(owner, msg_dict.get("action_id"))
        else:
            owner.table.logger.warn("player {0} event {1} not register".format(owner.seat, event))
