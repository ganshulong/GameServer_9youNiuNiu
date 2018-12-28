# coding: utf-8
import json

"""
斗牛 桌子配置参数命名
"""


class TableConf(object):
    def __init__(self, kwargs):
        self.kwargs = kwargs
        self.settings = json.loads(kwargs)
        self.rounds = self.settings.get("rounds", 10)  # 游戏轮数
        self.game_type = self.settings.get("game_type", 1)  # 游戏类型 1:经典斗牛 2:斗公牛 3:炸金牛 4:明牌抢庄 5:通比牛牛 6：自由抢庄 7:琼海抢庄
        self.banker = self.settings.get("banker", 1)  # 坐庄方式 1:房主坐庄2:轮流坐庄 3:牛牛坐庄 4:牌大做庄
        self.app_id = self.settings.get("app_id",100)  # 应用ID(100快诺 101阿牛哥 102战牛)
        self.options = self.settings.get("options", "111110111000000")  # 个性选择
        self.chips = self.settings.get("chips", 3)  # 消耗房卡
        self.score = self.settings.get("score", 2)  # 游戏分数 1分 2分 4分
        self.base_score = self.settings.get("base_score", 400)  # 庄分
        self.pay = self.settings.get("pay", 1)  # 付费方式 1:房主付费 2:AA付费
        self.cards_count = self.settings.get("cards_count",1) # 手牌数量 3张 4张
        self.double_type = self.settings.get("double_type", 1)  # 牛翻倍类型 类型1，类型2
        self.push_pledge = self.settings.get("push_pledge", 0)  # 押注开关 0关闭，5倍
        self.steal = self.settings.get("steal",0) # 暗抢庄 0代表关闭 1代表开启
        self.pledge_res = self.settings.get("pledge_res",0) # 押注限制 0关闭，1开启
        self.loot_dealer = self.settings.get("loot_dealer",1) # 抢庄倍率 1倍 2倍 4倍 6倍
        self.max_chairs = self.settings.get("max_chairs",6)  # 房间人数
        self.auto_player_num = self.settings.get("auto_player_num", 0)  # 自动开始玩家人数 0手动开桌
        self.pledge_double = self.settings.get("pledge_double",0)  #0不翻倍  1翻倍
        self.qh_base_score = self.settings.get("qh_base_score",1)  #琼海抢庄 房间底分
        self.game_id = self.settings.get('game_id',1)
        # 比赛相关参数
        self.ex_neg = self.settings.get("ex_neg", 0)    # 积分能否为负
        self.ex_sits = self.settings.get("ex_sits", 2000)  # 坐下分数
        self.ex_loots = self.settings.get("ex_loots", 1000)  # 抢庄分数

        if self.game_id != 3 and self.game_type !=7:
            if self.game_type != 4 and self.game_type != 6:
                self.pledge_res = 0  # 押注限制 0关闭，1开启
                self.loot_dealer = 1 # 抢庄倍率 1倍 2倍 4倍 6倍
                self.steal = 0 # 暗抢庄 0代表关闭 1代表开启
        if self.game_type == 6:
            self.loot_dealer = 1.
        if self.game_type == 7:
            self.push_pledge = 0
            self.pledge_res = 0  # 押注限制 0关闭，1开启
            self.steal = 0 # 暗抢庄 0代表关闭 1代表开启

    def get_qh_base_score(self):
        if self.game_type != 7:
            return 1
        return self.qh_base_score

    def get_pledge_res(self):
        return self.pledge_res

    def get_banker(self):
        if self.game_type != 1:
            return 1
        return self.banker

    #推注
    def get_push_pledge(self):
        if self.game_type == 5:
            return 0
        return self.push_pledge

    def get_double_type(self):
        return self.double_type

    def get_max_chairs(self):
        return  self.max_chairs

    def get_pay(self):
        return  self.pay

    def get_pledge_double(self):
        if self.app_id == 101:
            return False
        if self.game_type != 4 and self.game_type !=6:
            return False
        return self.pledge_double == 1

    def check_score(self, score):
        # 牛爷
        if self.game_id == 3:
            if self.score == 1:
                return score in (1, 2)
            if self.score == 2:
                return score in (2, 4)
            if self.score == 3:
                return score in (3, 6)
            if self.score == 4:
                return score in (4, 8)
            return score in (5, 10)
        if self.game_type == 7:
            if self.score == 5:
                if score not in (1, 2,  4, 5):
                    return False
            elif self.score == 8:
                if score not in (1,  3,  5,  8):
                    return False
        elif self.app_id == 100:
            if self.score == 1:
                if score not in (1, 2):
                    return False
            elif self.score == 2:
                if score not in (2, 4):
                    return False
            elif self.score == 3:
                if score not in (3, 6):
                    return False
            if self.score == 4:
                if score not in (4, 8):
                    return False
            elif self.score == 5:
                if score not in (5, 10):
                    return False
        elif self.app_id == 101:
            if self.score == 1:
                if score not in (1, 2, 3):
                    return False
            elif self.score == 3:
                if score not in (3, 4, 5):
                    return False
            if self.score == 6:
                if score not in (6,8,10):
                    return False
        else:
            if self.score == 1:
                if score not in (1, 2):
                    return False
            elif self.score == 2:
                if score not in (2, 4):
                    return False
            elif self.score == 3:
                if score not in (3, 6):
                    return False
            if self.score == 4:
                if score not in (4, 8):
                    return False
            elif self.score == 5:
                if score not in (5, 10):
                    return False
        return True

    def check_loot_dealer_score(self, loot_dealer,score): # 抢庄翻倍
        if loot_dealer == 0:
            return False
        if loot_dealer != self.loot_dealer:
            # return self.score
            return False

        #牛爷
        if self.game_id == 3:
            if score not  in (2,4,6,8,10,12,16,20):
                return False
            else:
                return True

        if self.game_type == 7:
            if self.score == 5:
                if score not in (1,2,3,4,5):
                    return False
            elif self.score ==8:
                if score not in (1, 2, 3, 4, 5, 6, 7, 8):
                    return False
        if self.app_id == 100:
            if self.score == 1:
                if score not in (2, 4):
                    return False
            elif self.score == 2:
                if score not in (4, 8):
                    return False
            elif self.score == 3:
                if score not in (6, 12):
                    return False
            if self.score == 4:
                if score not in (8, 16):
                    return False
            if self.score == 5:
                if score not in (10, 20):
                    return False
        elif self.app_id == 101:
            if self.score == 1:
                if score not in (1, 2, 3):
                    return False
            elif self.score == 3:
                if score not in (3, 4, 5):
                    return False
            if self.score == 6:
                if score not in (6, 8, 10):
                    return False
        else:
            if self.score == 1:
                if score not in (2, 4):
                    return False
            elif self.score == 2:
                if score not in (4, 8):
                    return False
            elif self.score == 3:
                if score not in (6, 12):
                    return False
            if self.score == 4:
                if score not in (8, 16):
                    return False
            if self.score == 5:
                if score not in (10, 20):
                    return False
        return True

    def get_score_Max(self,mix_score):
        max_score = 0
        if self.app_id == 100:
            if mix_score == 1:
                max_score = 2
            elif mix_score == 2:
                max_score = 4
            elif mix_score == 3:
                max_score = 6
            elif mix_score == 4:
                max_score = 8
            elif mix_score == 5:
                max_score = 10
            else:
                max_score = 3
        elif self.app_id == 101:
            if mix_score == 1:
                max_score = 3
            elif mix_score == 3:
                max_score = 5
            elif mix_score == 6:
                max_score = 10
            else:
                max_score = 3
        else:
            if mix_score == 1:
                max_score = 2
            elif mix_score == 2:
                max_score = 4
            elif mix_score == 3:
                max_score = 6
            elif mix_score == 4:
                max_score = 8
            elif mix_score == 5:
                max_score = 10
            else:
                max_score = 3
        return max_score

    def is_long(self):  # 一条龙
        return self.options[0] == '1'

    def is_five_small(self):    # 五小牛
        return self.options[1] == '1'

    def is_bomb(self):      # 炸弹牛
        return self.options[2] == '1'

    def is_gold(self):      # 金牛
        return self.options[3] == '1'

    def is_silver(self):    # 银牛
        return self.options[4] == '1'

    def is_no_jqk(self):  # 无花牌
        if self.max_chairs == 10:
            return False
        return self.options[5] == '1'

    def is_cant_join_started(self):  # 开局后禁止加入
        return False
        return self.options[6] == '1'

    def is_not_wait(self):      # 不等待离开玩家（操作时间开关） 1代表开启
        return self.options[7] == '1'

    def is_rub_card(self):  # 搓牌开关 0代表开启
        return self.options[8] == '0'

    def is_sequence(self):  # 顺子牛
        return self.options[9] == '1'

    def is_identical(self):  # 同花牛
        return self.options[10] == '1'

    def is_calabash(self):  # 葫芦牛
        return self.options[11] == '1'

    def is_straight_flush(self):  # 同花顺牛
        return self.options[12] == '1'

    def is_push_score(self):
        if self.push_pledge != 0:
            return  True
        return False

    def get_sit_score(self):    # 坐下分数
        return self.ex_sits

    def get_loot_score(self):   # 抢庄分数
        return self.ex_loots

