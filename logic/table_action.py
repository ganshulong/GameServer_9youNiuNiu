# coding: utf-8
from base.state_base.table.end import EndState
from base.state_base.table.step import StepState


def step(table):
    table.machine.trigger(StepState())


def prompt_deal(table):
    for player in table.player_dict.values():
        if player.state != "WaitState":
            return
    table.machine.trigger(StepState())


def end(table):
    if not table.all_prompt_list:
        table.machine.trigger(EndState())
