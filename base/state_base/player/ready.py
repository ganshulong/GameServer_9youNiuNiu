# coding: utf-8
#准备

from base.state_base.player.player_base_state import PlayerStateBase
from protocol.commands import *


class ReadyState(PlayerStateBase):
    def enter(self, owner):
        super(ReadyState, self).enter(owner)
        # 广播其他玩家
        if owner.machine.last_state.name != "WaitState":
            owner.table.ready_msg(owner.seat)
        owner.table.is_all_ready()

    def execute(self, owner, event, msg_dict=None):
        super(ReadyState, self).execute(owner, event, msg_dict)
        if event == "start":
            if owner.table.conf.game_id == 3:
                # 如果是牛爷
                if owner.uuid != owner.table.owner and owner.uuid not in owner.table.guild_admins:
                    return
                if owner.table.cur_round != 1:
                    return

            owner.start_type()
            return
        if owner.table.state == "StartingState":
            if event == "pledge":
                if owner.table.conf.game_type == 1 or owner.table.conf.game_type == 2 or owner.table.conf.game_type == 7:
                    owner.pledge_score(msg_dict.get("pledge"), msg_dict.get("pledge_type"),
                                       msg_dict.get("pledge_double", 0))
            elif event == "loot_dealer":
                if owner.table.conf.game_type == 6:
                    owner.loot_dealer_type(msg_dict["loot_dealer"])
            return

        owner.table.logger.warn("player {0} event {1} not register".format(owner.seat, event))

