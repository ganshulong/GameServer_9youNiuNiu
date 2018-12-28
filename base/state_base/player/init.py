# coding: utf-8

from base.state_base.player.player_base_state import PlayerStateBase
from base.match_mgr import MatchMgr

class InitState(PlayerStateBase):

    def execute(self, owner, event, msg_dict=None):
        super(InitState, self).execute(owner, event, msg_dict)
        if event == "ready":
            if owner.table.match > 0:
                MatchMgr().player_ready(owner)
            else:
                owner.ready()
        elif event == "start":
            if owner.table.conf.game_id == 3:
                #如果是牛爷
                if owner.uuid == owner.table.owner or (owner.uuid in owner.table.guild_admins):
                    if owner.table.cur_round == 1:
                        owner.start_type()
        else:
            owner.table.logger.warn("player {0} event {1} not register".format(owner.seat, event))
