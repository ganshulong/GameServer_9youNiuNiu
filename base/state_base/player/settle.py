# coding: utf-8
# 结算
from base.state_base.player.player_base_state import PlayerStateBase
from base.match_mgr import MatchMgr

class SettleState(PlayerStateBase):

    def execute(self, owner, event, msg_dict=None):
        super(SettleState, self).execute(owner, event, msg_dict)
        if event == "ready":
            owner.ready()
        else:
            owner.table.logger.warn("player {0} event {1} not register".format(owner.seat, event))
