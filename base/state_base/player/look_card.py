# coding: utf-8
# 所有玩家压倍数

from base.state_base.player.player_base_state import PlayerStateBase
from protocol.commands import *


class LookCardState(PlayerStateBase):
    def enter(self, owner):
        super(LookCardState, self).enter(owner)
        # 广播其他玩家
        owner.table.look_card_msg(owner.seat)
