# coding: utf-8

import time

from protocol.serialize import send
from base.state_base.table.table_base_state import TableStateBase
from protocol.commands import *
import json
from datetime import datetime
from base.table_mgr import TableMgr
from base.match_mgr import MatchMgr
from settings import redis


class SettleForRoomState(TableStateBase):
    def enter(self, owner):
        owner.et = time.time()
        msg_dict = dict()
        flag = 0 if owner.dismiss_state else 1
        msg_dict["flag"] = flag
        log = {"flag": flag, "uuid": owner.room_uuid, "owner": owner.owner, "rounds": owner.conf.rounds,
               "st": owner.st, "et": owner.et, "room_id": owner.room_id, "player_data": []}

        if owner.conf.game_type == 2:
            owner.seat_dict[owner.dealer_seat].room.score -= owner.conf.base_score;

        round_time = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        msg_dict["round_time"] = round_time
        msg_dict["player_data"] = list()
        for p in owner.player_dict.values():
            i = dict()
            i["player"] = p.uuid
            i["seat"] = p.seat
            i["score"] = p.room.score
            i["pt"] = p.get_total_score()
            i["win"] = p.room.win_cnt
            i["lose"] = p.room.lose_cnt
            i["null"] = p.room.null_cnt
            i["niu"] = p.room.niu_cnt
            is_owner = 1 if p.uuid == owner.owner else 0
            i["is_owner"] = is_owner
            i["sex"] = 1
            p.trusteeship(0,0,0,0,0,0) # 所有玩家关闭托管
            p.room.ai_time = 0
            try:
                info = json.loads(p.info)
                i["sex"] = info.get("sex")
            except Exception, e:
                print e
                info = dict()
            i["info"] = info
            i["nick"] = info.get("nick")
            msg_dict["player_data"].append(i)
            log["player_data"].append({
                "player": p.uuid,
                "info": info,
                "seat": p.seat,
                "score": p.room.score,
                "pt": p.get_total_score(),
                "win": p.room.win_cnt,
                "lose": p.room.lose_cnt,
                "null": p.room.null_cnt,
                "niu": p.room.niu_cnt,
                "is_owner": is_owner,
            })
            p.match_score += p.room.score

        owner.logger.info(log)
        owner.dumps()
        owner.send_table_msg(SETTLEMENT_FOR_ROOM_DN, msg_dict, True, True)
        from base.center.request import settle_for_room
        settle_for_room(owner, log)

        TableMgr().set_room_settle(owner.room_id, msg_dict)

        if owner.match > 0:     # 比赛房间
            from base.center.request import room_reset
            room_reset(owner)
        else:
            owner.dismiss_room(0)
