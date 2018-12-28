# coding: utf-8

import weakref


class Machine(object):
    def __init__(self, owner):
        self.owner = weakref.proxy(owner)
        self.last_state = None
        self.cur_state = None
        self.owner.machine = self

    def trigger(self, new_state, dump=True):
        if self.cur_state:
            self.cur_state.exit(self.owner)
            self.last_state = self.cur_state
        self.cur_state = new_state
        self.owner.state = new_state.name
        self.cur_state.before(self.owner)
        self.cur_state.enter(self.owner)
        self.cur_state.after(self.owner)
        if dump:
            try:
                self.owner.dumps()
            except ReferenceError:
                pass

    def to_last_state(self):
        self.trigger(self.last_state)

    def execute(self, callback, msg_dict):
        self.cur_state.execute(self.owner, callback, msg_dict)

    def next_state(self):
        self.cur_state.next_state(self.owner)
