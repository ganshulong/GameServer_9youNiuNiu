# coding: utf-8
#出牌
from base.state_base.player.wait import WaitState

from base.state_base.player.player_base_state import PlayerStateBase
from logic.player_action import discard


class DiscardState(PlayerStateBase):
    def enter(self, owner):
        super(DiscardState, self).enter(owner)
        owner.table.clear_prompt()
        owner.table.clear_actions()

    def execute(self, owner, event, msg_dict=None):
        super(DiscardState, self).execute(owner, event, msg_dict)
        if event == "discard":
            discard(owner, msg_dict.get("card"))
        else:
            owner.table.logger.warn("player {0} event {1} not register".format(owner.seat, event))

    def exit(self, owner):
        super(DiscardState, self).exit(owner)

    def next_state(self, owner):
        pass
        # 切换为等待状态
        #owner.machine.trigger(WaitState())
        #owner.table.machine.cur_state.execute(owner.table, "step")
