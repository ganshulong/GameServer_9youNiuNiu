# coding: utf-8

import weakref


class Blackboard(object):
    def __init__(self, owner):
        self.owner = weakref.proxy(owner)
        # self.type = {}

    # def attr_type(self):
    #     for k, v in self.__dict__.items():
    #         if k == "type":
    #             continue
    #         if v is None:
    #             self.type[k] = None
    #             continue
    #         if isinstance(v, (dict, str, list, tuple, int)):
    #             self.type[k] = type(v)()

    def clear(self):
        # for k, v in self.type.items():
        #     if k == "type":
        #         continue
        #     if v is None:
        #         self.__dict__[k] = None
        #         continue
        #     self.__dict__[k] = type(v)()
        self.reset()

    def dumps(self):
        data = {}
        for k, v in self.__dict__.items():
            if v is None:
                data[k] = v
                continue
            if isinstance(v, (dict, str, list, tuple, int)):
                data[k] = v
        return data

    def reset(self):
        pass

