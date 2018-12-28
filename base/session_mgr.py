# coding: utf-8

import weakref

import time

from settings import heartbeat
from base.singleton import Singleton


class SessionMgr(object):
    __metaclass__ = Singleton

    def __init__(self):
        self.player_dict = {}
        self.session_set = set()
        self.online_set = set()

    def register(self, player, session):
        self.player_dict[session.uuid] = weakref.proxy(player)
        player.session = session
        self.online_set.add(session.uuid)

    def add(self, session):
        self.session_set.add(session)

    def cancel(self, session):
        if session:
            if session.uuid in self.player_dict.keys():
                del self.player_dict[session.uuid]
            if session.uuid  in self.online_set:
                self.online_set.remove(session.uuid)

    def delete(self, session):
        self.session_set.remove(session)

    def player(self, session):
        return self.player_dict.get(session.uuid)

    def heartbeat(self):
        now = time.time()
        # print("session total", len(self.session_set), "player total", len(self.player_dict))
        expire_session_set = set()
        for session in self.session_set:
            try:
                if now - session.last_time > heartbeat:
                    session.close()
                    # print("session recycle", session.uuid)
                    expire_session_set.add(session)
            except Exception:
                pass
        map(self.delete, expire_session_set)

