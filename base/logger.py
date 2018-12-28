# coding: utf-8

import os
import sys
import json
import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime
from base.singleton import Singleton
from tornado.options import options

try:
    syslog = __import__("syslog")
except ImportError:
    syslog = None

from settings import log_dir


__all__ = ["Logger", "LogRotate"]


# noinspection PyBroadException
def frame():
    try:
        raise Exception
    except:
        return sys.exc_info()[2].tb_frame.f_back


if hasattr(sys, '_getframe'):
    # noinspection PyProtectedMember
    frame = lambda: sys._getframe(3)

CRITICAL = 60
FATAL = 50
ERROR = 40
WARNING = 30
WARN = WARNING
INFO = 20
DEBUG = 10
NOTSET = 0

level_names = {
    CRITICAL: 'CRITICAL',
    ERROR: 'ERROR',
    WARNING: 'WARNING',
    INFO: 'INFO',
    DEBUG: 'DEBUG',
    NOTSET: 'NOTSET',
    FATAL: 'FATAL',
    'CRITICAL': CRITICAL,
    'ERROR': ERROR,
    'WARN': WARNING,
    'WARNING': WARNING,
    'INFO': INFO,
    'DEBUG': DEBUG,
    'NOTSET': NOTSET,
    'FATAL': FATAL,
}
_srcfile = os.path.normcase(frame.__code__.co_filename).capitalize()


class Logger(object):
    __metaclass__ = Singleton

    def __init__(self):
        self.pid = os.getpid()
        self.level = None
        self.line = None
        self.msg = None

        self.logger = logging.getLogger("game")
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = 0
        file_handler = TimedRotatingFileHandler(os.path.join(log_dir, options.logfile), when='d')
        file_handler.setLevel(logging.DEBUG)
        file_handler.formatter = logging.Formatter('%(levelname)s %(message)s')
        self.logger.addHandler(file_handler)

        self.level_router = {
            DEBUG: self.logger.debug,
            "DEBUG": self.logger.debug,
            INFO: self.logger.info,
            "INFO": self.logger.info,
            WARN: self.logger.warn,
            "WARN": self.logger.warn,
            WARNING: self.logger.warning,
            "WARNING": self.logger.warning,
            FATAL: self.logger.fatal,
            "FATAL": self.logger.fatal,
            CRITICAL: self.logger.critical,
            "CRITICAL": self.logger.critical,
        }

    def file_descriptor(self):
        """
        Find the stack frame of the caller so that we can note the source
        file name, line number and function name.
        """
        f = frame()
        # On some versions of IronPython, currentframe() returns None if
        # IronPython isn't run with -X:Frames.
        if f is not None:
            f = f.f_back

        rv = "(unknown file)", 0, "(unknown function)"
        while hasattr(f, "f_code"):
            co = f.f_code
            filename = os.path.normcase(co.co_filename).capitalize()
            if filename == _srcfile:
                f = f.f_back
                continue
            rv = (co.co_filename, f.f_lineno, co.co_name)
            break
        self.line = "{0}:{2}[{1}]".format(*rv)

    def debug(self, msg):
        self.level = DEBUG
        self.msg = msg
        self.record()

    def info(self, msg):
        self.level = INFO
        self.msg = msg
        self.record()

    def warn(self, msg):
        self.level = WARN
        self.msg = msg
        self.record()

    def fatal(self, msg):
        self.level = FATAL
        self.msg = msg
        self.record()

    def critical(self, msg):
        self.level = CRITICAL
        self.msg = msg
        self.record()

    def net(self, msg):
        self.level_router[INFO](msg)

    def record(self):
        self.file_descriptor()
        record_format = json.dumps({
            "line": self.line,
            "msg": self.msg,
            "pid": self.pid,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
        })
        if self.level > level_names["INFO"]:
            print record_format
        self.level_router[self.level](record_format)
        self.reset()

    def reset(self):
        self.level = None
        self.line = None
        self.msg = None

    @staticmethod
    def local(record):
        with open(os.path.join(log_dir, "game.log"), 'a+') as fp:
            fp.write(record + '\n')

    @staticmethod
    def local(logfile, record):
        with open(os.path.join(log_dir, logfile), 'a+') as fp:
            fp.write(record + '\n')

    @staticmethod
    def rsyslog(record):
        if not syslog:
            return
        syslog.openlog(logoption=syslog.LOG_PID, facility=syslog.LOG_MAIL)
        syslog.syslog(record)

