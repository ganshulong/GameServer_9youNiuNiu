# coding: utf-8

from base.state_base.player.player_base_state import PlayerStateBase
from base.match_mgr import MatchMgr
from protocol.commands import *

class PauseState(PlayerStateBase):

    def enter(self, owner):
        super(PauseState, self).enter(owner)
        # 广播其他玩家
        msg_dict = dict()
        msg_dict["seat"] = owner.seat
        owner.table.send_table_msg(PAUSE, msg_dict, True, True)

    def execute(self, owner, event, msg_dict=None):
        super(PauseState, self).execute(owner, event, msg_dict)
        if event == "ready":
            if owner.table.match > 0:
                MatchMgr().player_ready(owner)
            else:
                owner.ready()
        else:
            owner.table.logger.warn("player {0} event {1} not register".format(owner.seat, event))
