# coding: utf-8

PLAYER_STATUS_INIT = 0
PLAYER_STATUS_READY = 1
PLAYER_STATUS_PLAYING = 2
PLAYER_STATUS_SETTLE = 3

player_state_code_map = {
    "InitState": 0,             # 初始化
    "ReadyState": 1,            # 准备
    "StartingState":2,          # 开始游戏
    "CashPledgeState":3,       #  压分
    "LootDealerState":4,       #  抢庄
    "DealState": 5,             #  发牌
    "Deal2State":6,             # 发牌2
    "ShowCardState":7,         #  亮牌
    "DiscardState": 8,
    "PauseState": 9,
    "WaitState": 10,
    "PromptDiscardState": 11,
    "SettleState": 12,
}

table_state_code_map = {
    "InitState": 0,               # 初始化
    "ReadyState": 1,              # 准备
    "StartingState": 2,           # 开始游戏
    "CashPledgeState": 3,        # 压分
    "LootDealerState": 4,        # 抢庄
    "DealState": 5,               # 发牌
    "Deal2State": 6,             # 发牌2
    "ShowCardState": 7,          # 亮牌
    "StepState": 8,              # 下一步
    "WaitState": 9,              # 等待
    "EndState": 10,              # 结束
    "RestartState": 11,         # 重新开始
    "SettleForRoundState": 12,  # 小结算
    "SettleForRoomState": 13,  # 大结算
}
