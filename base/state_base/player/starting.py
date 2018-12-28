# coding: utf-8
#庄家开始游戏

from base.state_base.player.player_base_state import PlayerStateBase
from protocol.commands import *


class StartingState(PlayerStateBase):
    def enter(self, owner):
        super(StartingState, self).enter(owner)

        owner.table.dt = 0

        # 广播其他玩家
        msg_dict = dict()
        msg_dict["seat"] = owner.seat
        msg_dict["code"] = 0

        owner.table.send_table_msg(START_DN, msg_dict, True, True)

        owner.table.is_all_starting()

    def execute(self, owner, event, msg_dict=None):
        super(StartingState, self).execute(owner, event, msg_dict)

        if event == "loot_dealer":
            if owner.table.conf.game_type == 6:
                if owner.table.state == "StartingState":
                    owner.loot_dealer_type(msg_dict["loot_dealer"])
        else:
            owner.table.logger.warn("player {0} event {1} not register".format(owner.seat, event))
