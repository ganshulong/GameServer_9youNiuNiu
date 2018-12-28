# coding: utf-8
#押金

from base.state_base.player.player_base_state import PlayerStateBase
from protocol.commands import *


class CashPledgeState(PlayerStateBase):
    def enter(self, owner):
        super(CashPledgeState, self).enter(owner)
        # 广播其他玩家
        owner.table.pledge_msg(owner.seat,owner.round.pledge,0)
        owner.table.is_all_pledge()

    def execute(self, owner, event, msg_dict=None):
        super(CashPledgeState, self).execute(owner, event, msg_dict)
        if event == "show_card":
            if owner.table.conf.game_type == 4 or owner.table.conf.game_type == 7:
                if owner.table.state == "Deal2State":
                    owner.show_card()
        else:
            owner.table.logger.warn("player {0} event {1} not register".format(owner.seat, event))
