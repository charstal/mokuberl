from os import sysconf
from client.type import Resource
from client import K8sClient, EtcdClient
import numpy as np
from config import POSITIVE_REWARD, NEGATIVE_REWARD
from config import SysConfig, ModelConfig
from threading import Lock, Timer

TERMINATE_STATE = 0
TERMINATE_ACTION = ["none"]

ETCD_PORT = SysConfig.get_etcd_port()
ETCD_URL = SysConfig.get_etcd_url()
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

        # actions 需要重新设计
        self.actions = TERMINATE_ACTION + list_product(
            self.node_list, NODE_CLASS)

        # node_lock.release()
        # return node_list

    def __init__(self):

        self.k8sclient = K8sClient()
        self.etcdclient = EtcdClient(url=ETCD_URL,
                                     port=ETCD_PORT,
                                     username=ETCD_USERNAME,
                                     password=ETCD_PASSWORD)

        self.update_node_list()

        # 暂时使用定时器，之后看需求可以改成 watch 模式
        self.node_timer = Timer(NODE_INTERVAL, self.update_node_list)
        self.node_timer.start()
        # node_list = self.get_node_list()
        # self.node_list = node_list[:min(len(node_list), DEFAULT_NODE_SIZE)]

        self.terminate_states = TERMINATE_STATE

    def pre_step(self, act):
        node_name = ""
        # 当前 node 对应的action数量， 包含终止状态
        if act < len(self.actions):
            action = self.actions[act]
            if action == TERMINATE_ACTION:
                return "no-selected"

            arr = action.split("_")
            node_name = arr[0]

        if len(node_name) == 0 or not self.node_states[self.node_list.index(node_name)]:
            node_name = self.trimaran_node_select()
        return node_name

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
        return len(NODE_CLASS) * NODE_SIZE * 2 + len(NODE_CLASS)

    def get_states(self, pod_resource):
        usage = self.k8sclient.get_all_node_usage()
        capacity = self.k8sclient.get_all_node_capacity()
        states = np.empty(shape=(0,))

        for node in self.node_list:
            print(usage[node])
            st = np.array([
                usage[node].get_cpu(),
                usage[node].get_memory(),
                capacity[node].get_cpu(),
                capacity[node].get_memory(),
            ])
            states = np.concatenate((states, st), axis=0)

        for _ in range(NODE_SIZE - len(self.node_list)):
            st = np.array([0, 0, 0, 0])
            states = np.concatenate((states, st), axis=0)

        states = np.concatenate((states, np.array([
            pod_resource.get_cpu(),
            pod_resource.get_memory(),
        ])), axis=0)

        return states

    def trimaran_node_select():
        pass


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
    print(se.get_states(Resource(1000, 1000)))
