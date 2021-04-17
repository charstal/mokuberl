from config import NODE_CLASS, NODE_STATE, DEFAULT_NODE_SIZE, CLASS_THRESHOLD
from client import K8sClient, EtcdClient
import numpy as np
from config import POSITIVE_REWARD, NEGATIVE_REWARD
from config import SysConfig


TERMINATE_STATE = 0
TERMINATE_ACTION = ["none"]

ETCD_PORT = SysConfig.get_etcd_port()
ETCD_USERNAME = SysConfig.get_etcd_username()
ETCD_PASSWORD = SysConfig.get_etcd_password()


class ScheduleEnv():

    def get_node_list(self):

        k8s_nodes = self.k8sclient.get_nodes()
        etcd_nodes = self.etcdclient.get_nodes()

        node_list = etcd_nodes
        for node in k8s_nodes:
            if node not in etcd_nodes:
                node_list.append(node)

        self.etcdclient.put_nodes(node_list)

        return node_list

    def __init__(self):

        self.k8sclient = K8sClient()
        self.etcdclient = EtcdClient(port=ETCD_PORT, username=ETCD_USERNAME,
                                     password=ETCD_PASSWORD)

        node_list = self.get_node_list()

        self.node_list = node_list[:min(len(node_list), DEFAULT_NODE_SIZE)]

        self.actions = list_product(
            self.node_list, NODE_CLASS) + TERMINATE_ACTION

        self.terminate_states = TERMINATE_STATE

    def pre_step(self, act):
        action = self.actions[act]
        if action == TERMINATE_ACTION:
            return ""

        arr = action.split("_")
        node_name = arr[0]

        return node_name

    def update_state(self, states):
        current_states = states
        current_node_states = self.k8s_client.get_all_node_percentage()

        for node_name, resource in current_node_states.items():
            is_full = False
            for kind in NODE_CLASS:
                if resource[kind] > CLASS_THRESHOLD[kind]:
                    is_full = True
                    current_states = self.set_state(
                        node_name=node_name, states=states, kind=kind, is_full=is_full)
        return current_states

    def step(self, act, states):
        action = self.actions[act]

        next_states = self.update_state(states)

        done = True
        reward = POSITIVE_REWARD
        for state in next_states:
            if state != 0:
                done = False
                break

        if action == TERMINATE_ACTION[0] and done:
            return next_states, reward, done, {}

        arr = action.split("_")
        node_name, kind = arr[0], arr[1]

        if self.get_state(node_name, next_states, kind) == 0:
            reward = NEGATIVE_REWARD

        return next_states, reward, done, {}

    def set_state(self, node_name, states, kind, is_full):
        curr_state = states[self.node_list.index(node_name)]
        if is_full:
            curr_state = curr_state & ~(1 << (NODE_CLASS.index(kind)))
        else:
            curr_state = curr_state | (1 << (NODE_CLASS.index(kind)))
        states[self.node_list.index(node_name)] = curr_state
        return states

    def get_state(self, node_name, states, kind):
        curr_state = states[self.node_list.index(node_name)]
        return (curr_state >> (NODE_CLASS.index(kind))) & 1

    # callback or timing?
    def update_node_list(self):
        node_list = self._k8s_client.get_nodes()
        self.node_list = node_list[:min(len(node_list), DEFAULT_NODE_SIZE)]

        return node_list

    def reset(self):
        states = []

        for _ in range(len(self.node_list)):
            states.append((1 << len(NODE_CLASS)) - 1)
        return np.array(states)

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

    result_str = ["_".join(item) for item in result]

    return result_str


if __name__ == "__main__":
    # node = ["node01", "node02", "node03"]
    se = ScheduleEnv()
    print(se.reset())
