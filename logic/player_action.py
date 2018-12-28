# coding: utf-8
from copy import copy

from protocol.serialize import send
from base.state_base.player.pause import PauseState
from protocol.commands import *


def discard(player, card, auto=False):
    if card not in player.round.cards_in_hand:
        # 出不存在的牌的时候同步手牌
        msg_dict = dict()
        msg_dict["card"] = list()
        for i in player.round.cards_in_hand:
            msg_dict["card"].append(i)
        send(SYNCHRONISE_CARDS, msg_dict, player.session)
        player.table.logger.warn("player {0} discard {1} not exist in hand".format(player.seat, card))
        return
    #player.table.replay["procedure"].append({"discard": [player.seat, card]})

    # 将出牌玩家至于当前玩家
    player.table.discard_seat = player.seat
    player.round.cards_in_hand.remove(card)
    player.table.logger.info("player {0} discard {1}".format(player.seat, card))
    player.table.active_card = card

    player.machine.next_state()


def action(player, action_id):
    if action_id:
        # 判断是否在提示列表中
        if action_id in player.action.prompts.keys():
            player.table.logger.info("player {0} do {1} action {2}".format(
                player.seat, action_id, player.action.prompts[action_id]))
            player.action.execute(action_id)

            player.table.is_all_players_do_action()
        else:
            player.table.logger.warn("player {0} do {1} not illegal".format(player.seat, action_id))
            return
    else:
        player.table.logger.info("player {0} pass".format(player.seat))
        player.action.clear_prompts()
        player.machine.next_state()
        if player.state == "DiscardState" and player.machine.last_state.name == "PromptDrawState":
            player.table.clear_prompt()
            player.table.clear_actions()
        else:
            player.table.is_all_players_do_action()
