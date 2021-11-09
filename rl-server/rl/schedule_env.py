from time import sleep
from client import K8sClient, EtcdClient, Resource
import numpy as np
from config import SysConfig, ModelConfig, TrimaranConfig
from threading import Thread, Timer
from algorithm import Trimaran, load_balanced_reward_calculate

# TERMINATE_STATE = 0
TERMINATE_ACTION = "no-selected"

ETCD_PORT = SysConfig.get_etcd_port()
ETCD_URL = SysConfig.get_etcd_url()
ETCD_USERNAME = SysConfig.get_etcd_username()
ETCD_PASSWORD = SysConfig.get_etcd_password()
RESOURCE_THRESHOLD = SysConfig.get_resource_threshold()

NODE_UPDATE_INTERVAL = SysConfig.get_node_update_interval()
NODE_SIZE = SysConfig.get_node_size()
RESOURCE_CLASS = ModelConfig.get_resource_class()
POSITIVE_REWARD = ModelConfig.get_positive_reward()
NEGATIVE_REWARD = ModelConfig.get_negative_reward()

TRIMARAN_LOAD_SCORE_BOUNDARY = TrimaranConfig.get_load_score_boundary()


class ScheduleEnv():
    def update_node_list(self):
        """update_node_list
            需要一段时间运行更新，node_list 和 node_states

            最终返回一个NODE_SIZE大小的node_list 和 node_states
            其中node_list = ["node1", "node2"] 放置node名称
            node_states = [True, False] 标识 node 的开关机

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
        old_node_list = self.node_list
        self.node_list = node_list[:NODE_SIZE]
        self.node_states = node_states

        if old_node_list != self.node_list:
            self.nodes_changed = True
        # action = 56
        # 56 / node_size = node_ind
        # 56 % node_size = class index -> class
        # actions 需要重新设计
        # ["none", "node01|CPU, "node01|MEMORY" ....]
        # self.actions = [TERMINATE_ACTION] + list_product(
        #     self.node_list, NODE_CLASS)

        self.actions = [TERMINATE_ACTION] + self.node_list
        # node_lock.release()
        # return node_list

    def get_alive_node(self):
        return [node for i, node in enumerate(self.node_list) if self.node_states[i]]

    def __init__(self):

        self.k8sclient = K8sClient()
        self.etcdclient = EtcdClient(url=ETCD_URL,
                                     port=ETCD_PORT,
                                     username=ETCD_USERNAME,
                                     password=ETCD_PASSWORD)

        self.node_list = []
        self.nodes_changed = False
        self.update_node_list()

        # 暂时使用定时器，之后看需求可以改成 watch 模式
        # self.node_timer = Timer(NODE_UPDATE_INTERVAL, self.update_node_list)
        # self.node_timer.start()
        Thread(target=self.update_node_list_per_interval).start()
        # node_list = self.get_node_list()
        # self.node_list = node_list[:min(len(node_list), DEFAULT_NODE_SIZE)]

        self.normal_negative_reward = NEGATIVE_REWARD
        self.normal_positive_reward = POSITIVE_REWARD
        # self.terminate_states = TERMINATE_STATE

    def update_node_list_per_interval(self):
        while True:
            self.update_node_list()
            sleep(NODE_UPDATE_INTERVAL)

    def action2node(self, action_idx):
        node_name = self.actions[action_idx]
        # if action == TERMINATE_ACTION:
        #     return TERMINATE_ACTION, None

        # arr = action.split("|")
        # node_name, kind = arr[0], arr[1]

        return node_name

    def node_and_kind2action(self, node_name):
        # action = "|".join([node_name, action_kind])
        # print(action)
        return self.actions.index(node_name)

    # 找打一个合适aciton
    def pre_step(self, act, pod_resource):
        node_name = ""
        act_idx = act
        # 当前 node 对应的action数量， 包含终止状态
        if act_idx < len(self.actions):
            node_name = self.action2node(act_idx)

        if len(node_name) == 0 or (node_name in self.node_list and not self.node_states[self.node_list.index(node_name)]):
            act_idx = self.target_load_packing_node_select(pod_resource)
            node_name = self.action2node(act_idx)

        return node_name, act_idx

    def step(self, act):
        node_name = self.action2node(act)

        next_states = self.get_states()
        done = True
        reward = POSITIVE_REWARD

        nodes_list = self.get_alive_node()
        nodes_occupancy = self.k8sclient.get_all_node_percentage()
        # print(nodes_occupancy)
        # 判断所有正在运行的nodes资源各项资源是否达到阈值
        # 只有所有nodes有一项资源超过THRESHOLD就认为是done
        for node in nodes_list:
            sub_done = False
            for k in RESOURCE_CLASS:
                if nodes_occupancy[node][k] > RESOURCE_THRESHOLD:
                    sub_done = True
                    break
            if not sub_done:
                done = False
                break

        # 如果动作为TERMINATE_ACTION，如果未达到阈值，给予惩罚, 没有则给予奖励
        if node_name == TERMINATE_ACTION:
            if not done:
                reward = NEGATIVE_REWARD
        else:
            node_list = self.get_alive_node()
            res = self.k8sclient.get_all_node_percentage()
            reward = load_balanced_reward_calculate(node_name, node_list, res)

        return next_states, reward, done, {}

    def reset(self):
        self.update_node_list()
        # states = []

        # for _ in range(len(self.node_list)):
        #     states.append((1 << len(NODE_CLASS)) - 1)
        # return np.array(states)

    def get_node_size(self):
        return len(self.node_list)

    # 包含一个TERMINATE_ACTION , 以及不同node
    def get_action_size(self):
        # return len(NODE_CLASS) * NODE_SIZE + 1
        return len(self.node_list) + 1

    # flattern 之后 每一个node的资源信息和 待分配的pod的资源limit/request
    def get_state_size(self):
        return len(RESOURCE_CLASS) * NODE_SIZE + len(RESOURCE_CLASS)

    def get_states(self, pod_resource=Resource(0, 0)):
        # usage = self.k8sclient.get_all_node_usage()
        capacity = list(self.k8sclient.get_all_node_capacity().values())[0]
        usage_occupy = self.k8sclient.get_all_node_percentage()
        states = np.empty(shape=(0,))

        node_list = self.node_list

        for node in node_list:
            # print(usage[node])
            st = np.array([
                usage_occupy[node].get_cpu(),
                usage_occupy[node].get_memory(),
            ])
            states = np.concatenate((states, st), axis=0)

        # print(NODE_SIZE - len(node_list))

        for _ in range(NODE_SIZE - len(node_list)):
            st = np.array([0, 0])
            states = np.concatenate((states, st), axis=0)

        states = np.concatenate((states, np.array([
            pod_resource.get_cpu() / capacity.get_cpu() / 1000 * 100,
            pod_resource.get_memory() / capacity.get_memory() / 1000 * 100,
        ])), axis=0)

        # print(states)

        return states

    # 正常维持替代算法
    def target_load_packing_node_select(self, pod_usage):
        predict_usage = self.k8sclient.get_all_node_predict_usage_by_addind_pod(
            pod_usage)
        capacity = self.k8sclient.get_all_node_capacity()

        max_score = 0
        selected_node = TERMINATE_ACTION

        node_list = self.get_alive_node()

        for node_name in node_list:
            u = predict_usage[node_name] / capacity[node_name]
            score = 0
            overhead = False
            for kind in RESOURCE_CLASS:
                s = Trimaran.target_load_packing_calculate(u[kind])
                if s <= TRIMARAN_LOAD_SCORE_BOUNDARY:
                    overhead = True
                    break
                score += s
            if overhead:
                continue
            score /= len(RESOURCE_CLASS)
            if score > max_score:
                selected_node = node_name
                max_score = score

        return self.node_and_kind2action(selected_node)

    def get_normal_negative_reward(self):
        return self.normal_negative_reward

    def get_normal_positive_reward(self):
        return self.normal_positive_reward

    def check_overload(self, node_name):
        if node_name != TERMINATE_ACTION:
            avg_metrics = self.k8sclient.get_metrics_avg()[node_name]
            var_metrics = self.k8sclient.get_metrics_variation()[node_name]

            if not Trimaran.load_variation_risk_balancing(avg_metrics.get_cpu(), var_metrics.get_cpu()):
                return True, TERMINATE_ACTION
            if not Trimaran.load_variation_risk_balancing(avg_metrics.get_memory(), var_metrics.get_memory()):
                return True, TERMINATE_ACTION

        return False, node_name

        # def list_product(*lists):
        #     result = [[]]

        #     for pool in lists:
        #         tmp = []
        #         for x in result:
        #             for y in pool:
        #                 tmp.append(x + [y])
        #         result = tmp

        #     result_str = ["|".join(item) for item in result]

        #     return result_str


if __name__ == "__main__":
    # node = ["node01", "node02", "node03"]
    se = ScheduleEnv()
    # print(se.get_states(Resource(1000, 1000)))
    # print(se.target_load_packing_node_select(Resource(1000, 1000)))
    # print(se.pre_step(10, Resource(1000, 1000)))
    # print(se.step(1))
    # print(se.load_balanced_reward())
    # print(se.node_list)
    # print(se.get_alive_node())
    print(se.step(1))
