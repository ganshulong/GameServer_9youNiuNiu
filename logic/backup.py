# coding: utf-8

import pickle

from base.state_base.player.deal import DealState
from base.state_base.player.discard import DiscardState
from base.state_base.player.pause import PauseState
from base.state_base.player.prompt_discard import PromptDiscardState
from base.state_base.player.deal2 import Deal2State

from base.state_base.player.init import InitState
from base.state_base.player.ready import ReadyState
from base.state_base.player.wait import WaitState
from base.state_base.player.settle import SettleState
from base.state_base.player.pledge import CashPledgeState
from base.state_base.player.starting import StartingState
from base.state_base.player.show_card import ShowCardState
from base.state_base.player.loot_dealer import LootDealerState
from base.state_base.table.end import EndState as TableEndState
from base.state_base.table.init import InitState as TableInitState
from base.state_base.table.ready import ReadyState as TableReadyState
from base.state_base.table.restart import RestartState as TableRestartState
from base.state_base.table.step import StepState as TableStepState
from base.state_base.table.wait import WaitState as TableWaitState
from base.state_base.table.pledge import CashPledgeState as TableCashPledgeState
from base.state_base.table.starting import StartingState as TableStartingState
from base.state_base.table.show_card import ShowCardState as TableShowCardState


from base.table import Table
from logic.player import Player
from logic.table_conf import TableConf
from settings import redis
from state.table_state.deal import DealState as TableDealState
from state.table_state.settle_for_room import SettleForRoomState as TableSettleForRoomState
from state.table_state.settle_for_round import SettleForRoundState as TableSettleForRoundState
from state.table_state.loot_dealer import  LootDealerState as TableLootDealerState
from state.table_state.deal2 import  Deal2State as TableDeal2State

from base.session_mgr import SessionMgr

player_state = {
    "DealState": DealState(),
    "DiscardState": DiscardState(),
    "InitState": InitState(),
    "CashPledgeState": CashPledgeState(),
    "PauseState": PauseState(),
    "PromptDiscardState": PromptDiscardState(),
    "ReadyState": ReadyState(),
    "SettleState": SettleState(),
    "WaitState": WaitState(),
    "StartingState": StartingState(),
    "ShowCardState": ShowCardState(),
    "LootDealerState": LootDealerState(),
    "Deal2State": Deal2State()
}

table_state = {
    "DealState": TableDealState(),
    "EndState": TableEndState(),
    "InitState": TableInitState(),
    "ReadyState": TableReadyState(),
    "CashPledgeState": TableCashPledgeState(),
    "RestartState": TableRestartState(),
    "SettleForRoomState": TableSettleForRoomState(),
    "SettleForRoundState": TableSettleForRoundState(),
    "StepState": TableStepState(),
    "WaitState": TableWaitState(),
    "StartingState": TableStartingState(),
    "ShowCardState": TableShowCardState(),
    "LootDealerState": TableLootDealerState(),
    "Deal2State": TableDeal2State()
}


def loads_player(uuid, table):
    raw = redis.get("player:{0}".format(uuid))
    # print "player", uuid, raw
    if not raw:
        return
    data = pickle.loads(raw)
    player = Player(uuid, None, None, table)
    for k, v in data.items():
        if k in ("table", "session", "machine", "round", "action", "room"):
            continue
        else:
            player.__dict__[k] = v
    state = data["machine"]
    # for k, v in player.action_dict.items():
    #     player.action_dict[int(k)] = v
    #     del player.action_dict[k]
    player.machine.last_state = player_state[state[0]] if state[0] else None
    player.machine.cur_state = player_state[state[1]] if state[1] else None
    player.round.__dict__.update(data["round"])
    player.action.__dict__.update(data["action"])
    player.room.__dict__.update(data["room"])

    return player


def loads_table(room_id):
    raw = redis.get("table:{0}".format(room_id))
    # print "table", room_id, raw
    if not raw:
        return
    data = pickle.loads(raw)

    table = Table(room_id, None, "", 0, 0, None, None)
    for k, v in data.items():
        if k in ("logger", "conf", "player_dict", "seat_dict", "machine", "lookon_player_dict"):
            continue
        else:
            table.__dict__[k] = v

    table.conf = TableConf(table.kwargs)
    table.chairs = table.conf.max_chairs

    for i in data["player_dict"]:
        player = loads_player(i, table)
        if player:
            table.player_dict[i] = player

    for i, j in data["seat_dict"].items():
        if j in table.player_dict:
            table.seat_dict[int(i)] = table.player_dict[j]

    state = data["machine"]
    table.machine.last_state = table_state[state[0]] if state[0] else None
    table.machine.cur_state = table_state[state[1]] if state[1] else None

    return table
