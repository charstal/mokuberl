from client import K8sClient, EtcdClient
import numpy as np
from config import POSITIVE_REWARD, NEGATIVE_REWARD
from config import SysConfig, ModelConfig
from threading import Lock, Timer

TERMINATE_STATE = 0
TERMINATE_ACTION = ["none"]

ETCD_PORT = SysConfig.get_etcd_port()
ETCD_USERNAME = SysConfig.get_etcd_username()
ETCD_PASSWORD = SysConfig.get_etcd_password()

NODE_INTERVAL = SysConfig.get_node_interval()
NODE_SIZE = SysConfig.get_node_size()
NODE_CLASS = ModelConfig.get_node_class()
# node_lock = Lock()


class ScheduleEnv():
    def update_node_list(self):
        """update_node_list
            需要一段时间运行更新，node_list 和 node_states

            最终返回一个NODE_SIZE大小的node_list 和 node_states
            其中node_list = ["node1", "node2"] 放置node名称
            node_states = [True, False] 标识 node 的开关机

            TODO:
                node_list 应该还有进一步优化空间
        """
        # 已开机的node
        k8s_nodes = self.k8sclient.get_nodes()
        # 历史node排序
        etcd_nodes = self.etcdclient.get_nodes()

        node_states = [False] * NODE_SIZE
        node_list = etcd_nodes
        for node in k8s_nodes:
            if node not in etcd_nodes:
                node_list.append(node)
            # 仅得到前 NODE_SIZE 的开关机情况
            node_ind = node_list.index(node)
            if node_ind < NODE_SIZE:
                node_states[node_ind] = True

        # 保存新的nodes顺序数据
        self.etcdclient.put_nodes(node_list)

        # 应该不需要加锁
        # node_lock.acquire()
        self.node_list = node_list[:NODE_SIZE]
        self.node_states = node_states
        # node_lock.release()
        # return node_list

    def __init__(self):

        self.k8sclient = K8sClient()
        self.etcdclient = EtcdClient(port=ETCD_PORT,
                                     username=ETCD_USERNAME,
                                     password=ETCD_PASSWORD)

        self.update_node_list()

        # 暂时使用定时器，之后看需求可以改成 watch 模式
        self.node_timer = Timer(NODE_INTERVAL, self.update_node_list)
        self.node_timer.start()
        # node_list = self.get_node_list()

        # self.node_list = node_list[:min(len(node_list), DEFAULT_NODE_SIZE)]

        self.actions = TERMINATE_ACTION + list_product(
            self.node_list, NODE_CLASS)

        self.terminate_states = TERMINATE_STATE

    def pre_step(self, act):
        action = self.actions[act]
        if action == TERMINATE_ACTION:
            return ""

        arr = action.split("_")
        node_name = arr[0]

        return node_name

    # def update_state(self, states):
    #     current_states = states
    #     current_node_states = self.k8s_client.get_all_node_percentage()

    #     for node_name, resource in current_node_states.items():
    #         is_full = False
    #         for kind in NODE_CLASS:
    #             if resource[kind] > CLASS_THRESHOLD[kind]:
    #                 is_full = True
    #                 current_states = self.set_state(
    #                     node_name=node_name, states=states, kind=kind, is_full=is_full)
    #     return current_states

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

    # def set_state(self, node_name, states, kind, is_full):
    #     curr_state = states[self.node_list.index(node_name)]
    #     if is_full:
    #         curr_state = curr_state & ~(1 << (NODE_CLASS.index(kind)))
    #     else:
    #         curr_state = curr_state | (1 << (NODE_CLASS.index(kind)))
    #     states[self.node_list.index(node_name)] = curr_state
    #     return states

    # def get_state(self, node_name, states, kind):
    #     curr_state = states[self.node_list.index(node_name)]
    #     return (curr_state >> (NODE_CLASS.index(kind))) & 1

    # # callback or timing?
    # def update_node_list(self):
    #     node_list = self._k8s_client.get_nodes()
    #     self.node_list = node_list[:min(len(node_list), DEFAULT_NODE_SIZE)]

    #     return node_list

    def reset(self):
        self.update_node_list()
        # states = []

        # for _ in range(len(self.node_list)):
        #     states.append((1 << len(NODE_CLASS)) - 1)
        # return np.array(states)

    def get_node_size(self):
        return len(self.node_list)

    # 包含一个TERMINATE_ACTION , 每个node以及每个node支持的资源类型的乘机
    def get_action_size(self):
        return len(NODE_CLASS) * NODE_SIZE + 1

    # flattern 之后 每一个node的资源信息和 待分配的pod的资源limit/request
    def get_state_size(self):
        return len(NODE_CLASS) * NODE_SIZE + len(NODE_CLASS)

    def get_states(self, pod_resource_limit):


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
