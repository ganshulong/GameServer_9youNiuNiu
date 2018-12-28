# coding: utf-8

import os
from ConfigParser import ConfigParser
import redis as r
from tornado.options import options


root = os.path.dirname(__file__)
log_dir = os.path.join(root, "log")
if not os.path.exists(log_dir):
    os.mkdir(log_dir)

redis = r.Redis(host=options.redis_host, port=options.redis_port, password=options.redis_password, db=options.redis_db)

dismiss_delay = 60
heartbeat = 60

