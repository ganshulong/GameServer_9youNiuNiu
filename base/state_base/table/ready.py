# coding: utf-8


from base.state_base.table.table_base_state import TableStateBase
from state.table_state.deal import DealState
from protocol.commands import *
import time

class ReadyState(TableStateBase):
    def enter(self, owner):
        super(ReadyState, self).enter(owner)
        for k, v in owner.seat_dict.items():
            next_seat = k + 1
            if next_seat == owner.chairs:
                next_seat = 0
            v.next_seat = next_seat
            prev_seat = k - 1
            if prev_seat == -1:
                prev_seat = 2
            v.prev_seat = prev_seat
        owner.logger.info("table ready")
        owner.dumps()

        if owner.conf.get_banker() != 1:  # 非默认 房主坐庄模式 都得重新换庄
            owner.dealer_msg(owner.dealer_seat,0)
        else:
            msg_dict = dict()
            msg_dict["seat"] = owner.dealer_seat  # 新的庄家位置
            msg_dict["score"] = 0  #抢庄倍数
            from state.status import table_state_code_map
            msg_dict["room_state"] = table_state_code_map[owner.state]
            owner.add_replay(DEALER_SEAT,msg_dict)


        # 广播其他玩家
        if owner.cur_round == 1:
            # 第一局手动
            owner.prompt_start_msg(0)


    def after(self, owner):
        if owner.conf.game_id == 3:
            #牛爷自动开始
            if owner.cur_round == 1 and owner.conf.auto_player_num > 0 :
                #判断是否人数足够
                ready_count = 0;
                for player in owner.player_dict.values():
                    if player.state == "ReadyState" or player.state == "WaitState":
                        ready_count += 1
                if ready_count >= owner.conf.auto_player_num:
                    owner.seat_dict[owner.dealer_seat].start_type()
            elif owner.cur_round != 1:
                owner.seat_dict[owner.dealer_seat].start_type()
        else:
            if owner.cur_round != 1:
                owner.seat_dict[owner.dealer_seat].start_type()
