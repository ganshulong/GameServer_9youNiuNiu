# coding: utf-8

from base.singleton import Singleton


class StateBase(object):
    __metaclass__ = Singleton

    def __init__(self):
        self.name = self.__class__.__name__

    def enter(self, owner):
        pass

    def exit(self, owner):
        pass

    def prepare(self, owner):
        pass

    def after(self, owner):
        pass

    def before(self, owner):
        pass

    def next_state(self, owner):
        pass
