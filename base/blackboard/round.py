# coding: utf-8

from base.blackboard.blackboard_base import Blackboard


class RoundBlackboard(Blackboard):
    def __init__(self, owner):
        super(RoundBlackboard, self).__init__(owner)

        self.score = 0  # 分数
        self.cards_in_hand = []  # 手牌
        self.niu_type = 0  # 当前牛几
        self.online = True # 炸金牛 玩家是否出局 T=在游 F=出局
        self.loot_dealer = 0  # 抢庄倍率
        self.pledge = 0  # 押金
        self.double_pledge = False

        # 测试牌型使用

        self.cesi_cards_in_hand = []  # 手牌
        self.cesi_niu_type = 0  # 当前牛几

    def reset(self):
        self.score = 0
        self.cards_in_hand = []
        self.niu_type = 0
        self.loot_dealer = 0
        self.pledge = 0
        self.double_pledge = False
