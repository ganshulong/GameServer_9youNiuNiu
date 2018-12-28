# coding: utf-8

from base.state_base.player.player_base_state import PlayerStateBase
from logic.player_action import *


class WaitState(PlayerStateBase):
    def enter(self, owner):
        super(WaitState, self).enter(owner)
        # 广播其他玩家
        owner.table.wait_msg(owner.seat)
        owner.table.is_all_ready()

    def execute(self, owner, event, msg_dict=None):
        super(WaitState, self).execute(owner, event, msg_dict)

        owner.table.logger.warn("player {0} event {1} not register".format(owner.seat, event))