# coding: utf-8
# 所有玩家压倍数

from base.state_base.player.player_base_state import PlayerStateBase
from protocol.commands import *


class LootDealerState(PlayerStateBase):
    def enter(self, owner):
        super(LootDealerState, self).enter(owner)
        # 广播其他玩家
        owner.table.loot_dealer_msg(owner.seat,owner.round.loot_dealer)
        owner.table.is_all_loot_dealer()

    def execute(self, owner, event, msg_dict=None):
        super(LootDealerState, self).execute(owner, event, msg_dict)

        if event == "pledge":
            if owner.table.conf.game_type == 4 or owner.table.conf.game_type == 6 or owner.table.conf.game_type == 7:
                if owner.table.state == "LootDealerState":
                    owner.pledge_score(msg_dict.get("pledge"),msg_dict.get("pledge_type"),msg_dict.get("pledge_double",0))
        elif event == "double_pledge":
            if owner.table.conf.game_type == 4 or owner.table.conf.game_type == 6:
                if owner.table.state == "LootDealerState":
                    owner.round.double_pledge = True
                    owner.table.double_pledge_msg( owner.seat,0)
        else:
            owner.table.logger.warn("player {0} event {1} not register".format(owner.seat, event))
