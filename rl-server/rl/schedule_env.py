from config import NODE_CLASS, NODE_STATE, DEFAULT_NODE


class ScheduleEnv():
    def __init__(self, node_list):

        # 状态
        self.states = list_product(node_list, NODE_CLASS, NODE_STATE) + ["no_available"]
        # 动作
        self.actions = list_product(node_list, NODE_CLASS)

        # 回报函数的数据结构为字典
        self.rewards = dict()
        # for 
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

def list_product(*lists):
    result = [[]]

    for pool in lists:
        tmp = []
        for x in result:
            for y in pool:
                tmp.append(x + [y])
        result = tmp   

    result_str = ["_".join(item) for item in result ]

    return result_str

if __name__ == "__main__":
    node = ["node01", "node02", "node03"]
    se = ScheduleEnv(node)
    print(se.states)