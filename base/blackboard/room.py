# coding: utf-8

from base.blackboard.blackboard_base import Blackboard


class RoomBlackboard(Blackboard):
    def __init__(self, owner):
        super(RoomBlackboard, self).__init__(owner)

        self.score = 0  # 总分数
        self.win_cnt = 0  # 胜利次数
        self.lose_cnt = 0  # 失败次数
        self.null_cnt = 0  # 无牛次数
        self.niu_cnt =0  # 有牛次数
        self.push_pledge = 0 # 推注

        #托管
        self.ai_type = 0 #托管类型(0:无效 1:系统托管 2：手动托管)
        self.pledge_type = 0  # 押注类型 （例：0默认 1代表牛八以上押注）
        self.pledge=0  #押注 （例：5分 10分）
        self.push_pledge_type = 0 #推注(0:不推 1：牛8推 2牛九推 3牛牛推)
        self.loot_dealer_type = 0 #抢庄方式（0：不抢 1牛八抢庄 2牛九抢庄 3牛牛以上抢庄）
        self.loot_dealer = -1 #抢庄倍数（-1：不抢  1倍 2倍 3倍等）
        self.ai_time = 0 #离线托管时间

        #洗牌使用
        self.niu_max_count = 0 #大牌型出现次数

    def reset(self):
        self.score = 0
        self.win_cnt = 0
        self.lose_cnt = 0
        self.null_cnt = 0
        self.niu_cnt =0
        self.push_pledge = 0 # 推注

        self.ai_type = 0
        self.pledge = 0
        self.pledge_type = 0
        self.loot_dealer = -1
        self.loot_dealer_type = 0
        self.pledge_type = 0
        self.ai_time = 0

        self.niu_max_count = 0
