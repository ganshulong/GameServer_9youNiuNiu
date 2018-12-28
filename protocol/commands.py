# coding: utf-8

""" 系统命令 服务器之间交互 0x0001 ~ 0x00FF """
CG_CREATE_ROOM = 0x0001             # 创建房间
CG_DISMISS_ROOM = 0x0002            # 解散房间
GC_DISMISS_ROOM = 0x0003            # 解散房间
CG_SYNC_ROOM = 0x0004               # 同步房间
GC_ENTER_ROOM = 0x0005              # 进入房间
GC_EXIT_ROOM = 0x0006               # 退出房间
GC_SETTLE_ROUND = 0x0007            # 每轮结算
GC_SETTLE_ROOM = 0x0008             # 每局结算
GC_ROOM_STATE = 0x0009              # 房间状态
GC_SERVER_INFO = 0x0011             # 游戏服务器信息
LC_JOIN_ROOM = 0x0012               # 加入房间
LC_CREATE_ROOM = 0x0013             # 创建房间
LC_SERVER_INFO = 0x0014             # 登录服务器信息
LC_ROOM_LIST = 0x0015               # 房间列表
CL_ROOM_CARD = 0x0016               # 房卡信息
LC_USER_STATE = 0x0017              # 玩家当前房间
LC_SERVER_REPORT = 0X0018           # 服务器定时汇报
CL_KICK_PLAYER = 0x0019             # 踢掉在线玩家(ban user)
RC_RECHARGE_URLS = 0x001A           # 充值回调列表
GC_SEAT_DOWN = 0x001B               # 玩家座下
CL_PROXY_CODE = 0x001C              # 邀请码信息
CL_GAME_COUNT = 0x001D              # 战斗次数广播
CL_DAILY_COUNT = 0x001E             # 获得抽奖次数
CG_USER_TOKEN = 0x001F              # 玩家认证token
CG_MATCH_SCORE = 0x0020             # 比赛分数
GC_ROOM_RESET = 0x0021              # 房间重置
CG_EMO_AMOUNT = 0x0022              # 表情次数
GC_MATCH_ACT = 0x0023               # 比赛动作
CG_CREATE_SPORT_ROOM = 0x0024       # 创建赛场房间
CG_DISMISS_SPORT = 0x0025           # 解散赛场
CL_SPORT_FEE = 0x0026               # 赛场收费

""" 通用命令 0x0100 ~ 0x0FFF """
CREATE_ROOM = 0x100                   # 创建房间
JOIN_ROOM = 0x101                     # 加入房间
ENTER_ROOM = 0x0102                   # 进入房间
ENTER_ROOM_OTHER = 0x0103             # 其他玩家进入房间
EXIT_ROOM = 0x0104                    # 玩家退出房间
DISMISS_ROOM = 0x0105                 # 房主解散房间
SPONSOR_VOTE = 0x0106                 # 发起投票解散
VOTE = 0x0107                         # 玩家选择投票
ONLINE_STATUS = 0x0108                # 在线状态广播
SPEAKER = 0x0109                      # 超级广播命令
READY = 0x010A                        # 准备
DEAL = 0x010B                         # 起手发牌
DRAW = 0x010C                         # 摸牌
DISCARD = 0x010D                      # 出牌
SYNCHRONISE_CARDS = 0x010E            # 服务端主动同步手牌
HEARTBEAT = 0x010F            		  # 服务端主动检测心跳
ROUND_STATE = 0x0110
BINDING_PROXY_CODE = 0x0111           # 绑定邀请码
PAY_ORDER = 0x0112                    # 请求支付订单
RECHARGE_INFO = 0x0113                # 充值记录
PAY_RESULT = 0x0114                   # 充值结果
SYNC_SCORE = 0x0115                    # 同步积分
SCORE_LEAK = 0x0116                   # 积分不足
PAUSE = 0x0117                        # 暂停
PAY_GOODS = 0x0118                    # 商品列表

ENTER_GAME = 0x200                    # 进入游戏
LOGIN = 0x201                         # 玩家登录
ROOM_CARD = 0x202                     # 玩家房卡
ROOM_LIST = 0x203                     # 房间列表
RECORD = 0x204                        # 房间战绩
RECORD_INFO = 0x205                   # 战绩详情
ROOM_REPLAY = 0x206                   # 游戏回放
NOTICE = 0x207                        # 游戏公告
LOGIN_USERID = 0x208                  # ID登录
ENTER_HALL = 0x209					  # 进入大厅
ROOM_HISTORY = 0x210                  # 我创建的已完成的房间


""" 斗牛 0x1000 ~ 0x102F """
RECONNECT_DN = 0x1000  			  # 玩家断线重连
SETTLEMENT_FOR_ROUND_DN = 0x1001	  # 结算#一回合（小）
ACTION_DN = 0x1002				      # 玩家动作
PROMPT_PLEDGE_DN = 0x1003			# 提示闲家可以压分了
SETTLEMENT_FOR_ROOM_DN = 0x1004     # 结算#一整局（大）
PLEDGE_DN = 0x1005                     # 押金
START_DN = 0x1006                   # 开始游戏
PROMPT_START_DN = 0x1007            # 提示庄家可以开始游戏(flag=0可以,flag=1不可以)
SHOW_CARD_DN = 0x1008               # 亮牌
PROMPT_CARD_DN = 0x1009             # 提示玩家可以亮牌
DEALER_SEAT = 0x100A				# 庄家位置
PROMPT_LOOT_DEALER_DN = 0x100B       # 提示玩家可以压倍率
LOOT_DEALER_DN = 0x100C              # 抢庄 倍率
DEAL2_DN = 0x0100D                   # 发牌2
LOOK_CARD_DN = 0x100E                # 看牌
WAIT_DN = 0x100F                     # 等待（准备）
READY_LATE = 0x1010                  # 准备晚了，座位被占了
DOUBLE_PLEDGE = 0x1011               # 加倍下分
TRUSTEESHIP = 0x101F                 # 托管
PUSH_PLEDGE = 0x1020                 # 推注提示

""" 跑胡子 """


""" 湖南麻将 """
