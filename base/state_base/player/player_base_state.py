# coding: utf-8

# from transitions import Machine
#
#
# class StatePlayer(object):
#     states = ['await', 'deal', 'discard', 'chow', 'pong', 'kong', 'win']
#
#     def __init__(self):
#         self.machine = Machine(model=self, states=StatePlayer.states, initial='await')
#         self.machine.add_transition(trigger='await', source='', dest='', conditions='')

from base.state_base.state_base import StateBase


class PlayerStateBase(StateBase):
    def __init__(self):
        super(PlayerStateBase, self).__init__()
        self.register = {}

    def enter(self, owner):
        owner.table.logger.info("player [{0}] {1} enter {2}".format(owner.seat, owner.uuid, self.name))

    def execute(self, owner, event, msg_dict=None):
        owner.table.logger.info("player [{0}] {1} execute event {2}".format(owner.seat, owner.uuid, event))
        owner.event = event
