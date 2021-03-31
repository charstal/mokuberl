from config import NODE_CLASS, NODE_STATE, DEFAULT_NODE_SIZE, CLASS_THRESHOLD
import random
from k8s import K8sClient

TERMINATE_STATE = 0
TERMINATE_ACTION = ["none"]

class ScheduleEnv():
    def __init__(self):

        self.k8s_client = K8sClient()
        node_list = self.k8s_client.get_nodes()

        # node_list = ["node01", "node02", "node03"]

        self.node_list = node_list[:min(len(node_list), DEFAULT_NODE_SIZE)]
        # 状态
        # self.states = states_init(self.node_list)
        # 动作
        self.actions = list_product(self.node_list, NODE_CLASS) + TERMINATE_ACTION

        self.terminate_states = TERMINATE_STATE


    def pre_step(self, act):
        action = self.actions[act]
        if action == TERMINATE_ACTION:
            return ""

        arr = action.split("_")
        node_name = arr[0]

        return node_name

    def step(self, act, states):
        action = self.actions[act]

        arr = action.split("_")
        node_name, kind = arr[0], arr[1]

        is_full = False
        reward = 1.0
        current_node_states = self.k8s_client.get_node_percentage(node_name)
        if current_node_states[NODE_CLASS.index(kind)] >= CLASS_THRESHOLD[NODE_CLASS.index(kind)]:
            is_full = True
            reward = -1.0
        next_states = self.set_state(node_name=node_name, states=states, kind=kind, is_full=is_full)

        done = True
        for state in states:
            if state != 0:
                done = False
                break

        return next_states, reward, done, {}
        
    def set_state(self, node_name, states, kind, is_full):
        curr_state = states[node_name]
        if is_full:
            curr_state = curr_state & ~(1 << (NODE_CLASS.index(kind)))
        else:
            curr_state = curr_state | (1 << (NODE_CLASS.index(kind)))
        states[node_name] = curr_state
        return states

    # callback or timing?
    def update_node_list(self):
        node_list = self._k8s_client.get_nodes()
        self.node_list = node_list[:min(len(node_list), DEFAULT_NODE_SIZE)]

        return node_list

    def reset(self):
        states = []

        for _ in range(len(self.node_list)):
            states.append((1 << len(NODE_CLASS)) - 1)
        return states

    def get_node_size(self):
        return len(self.node_list)

    def get_action_size(self):
        return len(self.actions)

    def get_state_size(self):
        return len(self.node_list)

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
    # node = ["node01", "node02", "node03"]
    se = ScheduleEnv()
    print(se.reset())