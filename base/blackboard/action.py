# coding: utf-8
from base.blackboard.blackboard_base import Blackboard
from protocol.commands import *


class ActionBlackboard(Blackboard):
    def __init__(self, owner):
        super(ActionBlackboard, self).__init__(owner)

        self.prompts = {}
        # 提示ID
        self.prompt_id = 0
        # 动作
        self.id = 0
        self.weight = 0
        self.rule = None
        self.op_card = None
        # self.attr_type()

    def reset(self):
        self.prompts = {}
        # 提示ID
        self.prompt_id = 0
        # 动作
        self.id = 0
        self.weight = 0
        self.rule = None
        self.op_card = None

    def add(self, prompt, rule, op_card):
        self.prompt_id += 1
        self.prompts[self.prompt_id] = {"rule": rule, "op_card": op_card, "prompt": prompt}

    def max_weight(self):
        weight = 0
        for i in self.prompts.values():
            if i["prompt"] > weight:
                weight = i["prompt"]
        return weight

    def execute(self, action_id):
        self.id = action_id
        action = self.prompts[action_id]
        self.rule = action["rule"]
        self.weight = action["prompt"]
        self.op_card = action["op_card"]
        #self.owner.table.replay["procedure"].append([{"action": action, "seat": self.owner.seat}])

    def send(self, force=False):
        # 向客户端发送提示
        if not force:
            if not self.prompts:
                return

        msg_dict = dict()
        msg_dict["prompt"] = list()
        for k, v in self.prompts.items():
            prompt = dict()
            prompt["action_id"] = k
            prompt["prompt"] = v["prompt"]
            prompt["op_card"] = v["op_card"]

        # self.owner.send(PROMPT_DN, msg_dict)
        self.owner.table.logger.info(self.prompts)

    def clear_prompts(self):
        self.prompt_id = 0
        self.prompts = {}

    def clear_actions(self):
        self.id = 0
        self.weight = 0
        self.rule = None
        self.op_card = None
