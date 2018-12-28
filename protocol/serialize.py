# coding: utf-8
from tornado.iostream import StreamClosedError


def send(cmd, msg_dict, session):
    try:
        if session:
            msg_dict["cmd"] = cmd
            session.send_message(msg_dict)
    except (StreamClosedError, AttributeError) as e:
        print e
