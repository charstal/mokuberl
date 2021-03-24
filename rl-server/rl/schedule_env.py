import gym
from gym import spaces
from gym.utils import seeding

from k8s import K8sClient

node_class = ["cpu", "memory"]


class ScheduleEnv(gym.Env):
    def __init__(self):
        self.k8s_client = K8sClient()

        self.states = [1,2,3,4,5,6,7,8]             # 状态
        self.actions = ['n','e','s','w']            # 动作

        self.rewards = dict()		# 回报函数的数据结构为字典
        self.rewards['1_s'] = -1.0	
        self.rewards['3_s'] = 1.0
        self.rewards['5_s'] = -1.0

        self.t = dict()				# 状态转移的数据结构为字典
        self.t['1_s'] = 6
        self.t['1_e'] = 2
        self.t['2_w'] = 1
        self.t['2_e'] = 3
        self.t['3_w'] = 2
        self.t['3_e'] = 4
        self.t['3_s'] = 7
        self.t['4_w'] = 3
        self.t['4_e'] = 5
        self.t['5_w'] = 4
        self.t['5_s'] = 8

        self.terminate_states = [6,7,8]

    def reset(self):
        pass

    

