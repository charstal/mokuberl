from client import K8sClient, EtcdClient, Resource
import numpy as np
from config import SysConfig, ModelConfig, TrimaranConfig
from threading import Lock, Timer
from algorithm import Trimaran

# TERMINATE_STATE = 0
TERMINATE_ACTION = "no-selected"

ETCD_PORT = SysConfig.get_etcd_port()
ETCD_URL = SysConfig.get_etcd_url()
ETCD_USERNAME = SysConfig.get_etcd_username()
ETCD_PASSWORD = SysConfig.get_etcd_password()

NODE_INTERVAL = SysConfig.get_node_interval()
NODE_SIZE = SysConfig.get_node_size()
RESOURCE_CLASS = ModelConfig.get_resource_class()
POSITIVE_REWARD = ModelConfig.get_positive_reward()
NEGATIVE_REWARD = ModelConfig.get_negative_reward()

RESOURCE_THRESHOLD = TrimaranConfig.get_resource_threshold()
# TARGET_LOAD_PACKING = TrimaranConfig.get_target_load_packing_config()


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

        self.normal_negative_reward = NEGATIVE_REWARD
        self.normal_positive_reward = POSITIVE_REWARD
        # self.terminate_states = TERMINATE_STATE

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

        if len(node_name) == 0 or node_name in self.node_list and not self.node_states[self.node_list.index(node_name)]:
            act_idx = self.target_load_packing_node_select(pod_resource)
            node_name = self.action2node(act_idx)

        return node_name, act_idx

    def step(self, act):
        node_name = self.action2node(act)

        next_states = self.get_states()
        done = True
        reward = POSITIVE_REWARD

        nodes_occupancy_value = self.k8sclient.get_all_node_percentage().values()

        # 判断所有的nodes是否达到阈值
        for v in nodes_occupancy_value:
            for k in RESOURCE_CLASS:
                if v[k] < RESOURCE_THRESHOLD:
                    done = False
            if not done:
                break

        # 如果动作为TERMINATE_ACTION，如果未达到阈值，给予惩罚, 没有则给予奖励
        if node_name == TERMINATE_ACTION:
            if not done:
                reward = NEGATIVE_REWARD
        else:
            reward = self.load_balanced_reward()

        return next_states, reward, done, {}

    def load_balanced_reward(self):
        # 中高负载节点尽量均衡，可以更好的应对已存在 pod 突如其来的高负载，减少资源抢占
        # 而低负载节点在高负载的没达到阈值时尽量不要分配 pod，以便上面的 pod 自己跑完从而关闭节点
        alpha = 0.02
        beta = 0.01
        theta = 0.01
        gamar = 0.01

        return alpha * self.get_util() - beta * self.get_diff_node() - theta * self.get_diff_res() - gamar * self.get_overload_punishment()

    def get_util(self):
        score = 0
        nodes_percentage = self.k8sclient.get_all_node_percentage()
        for node in nodes_percentage.keys():
            s = 0
            for k in RESOURCE_CLASS:
                s += nodes_percentage[node][k]
            s /= len(RESOURCE_CLASS)
            score += s

        print("util score: ", score)
        return score

    def get_diff_node(self):
        score = 0
        nodes_percentage = self.k8sclient.get_all_node_percentage()
        for node in nodes_percentage.keys():
            for i in range(len(RESOURCE_CLASS)):
                for j in range(i, len(RESOURCE_CLASS)):
                    score += abs(nodes_percentage[node][RESOURCE_CLASS[i]] -
                                 nodes_percentage[node][RESOURCE_CLASS[j]])

        print("diff node score: ", score)
        return score

    def get_diff_res(self):
        score = 0
        nodes_percentage = self.k8sclient.get_all_node_percentage()
        mid_and_high_load = 50
        ulist = []
        for node in nodes_percentage.keys():
            s = 0
            for k in RESOURCE_CLASS:
                s += nodes_percentage[node][k]
            s /= len(RESOURCE_CLASS)
            # 只限定中高负载
            if s > mid_and_high_load:
                ulist.append(s)

        for i in range(len(ulist)):
            for j in range(i, len(ulist)):
                score += abs(ulist[i] - ulist[j])
        print("diff res score: ", score)
        return score

    def get_overload_punishment(self):
        score = 0
        nodes_percentage = self.k8sclient.get_all_node_percentage()
        for node in nodes_percentage.keys():
            s = 0
            for k in RESOURCE_CLASS:
                if nodes_percentage[node][k] > RESOURCE_THRESHOLD:
                    s += abs(nodes_percentage[node]
                             [k] - RESOURCE_THRESHOLD)
            score += s
        print("overload punishment score: ", score)
        return score

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
        return len(RESOURCE_CLASS) * NODE_SIZE * 2 + len(RESOURCE_CLASS)

    def get_states(self, pod_resource=Resource(0, 0)):
        usage = self.k8sclient.get_all_node_usage()
        capacity = self.k8sclient.get_all_node_capacity()
        states = np.empty(shape=(0,))

        for node in self.node_list:
            # print(usage[node])
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

    # 正常维持替代算法
    def target_load_packing_node_select(self, pod_usage):
        predict_usage = self.k8sclient.get_all_node_predict_usage_by_addind_pod(
            pod_usage)
        capacity = self.k8sclient.get_all_node_capacity()

        max_score = 0
        selected_node = ""

        for node_name in predict_usage.keys():
            u = predict_usage[node_name] / capacity[node_name]
            score = 0
            max_s = 0

            for kind in RESOURCE_CLASS:
                s = Trimaran.target_load_packing_calculate(
                    u[kind], kind)
                if max_s < s:
                    max_s = s
                score += s
                print(node_name, ":kind:", kind, ":", s, ":", score)
            if score > max_score:
                selected_node = node_name
                max_score = score

        return self.node_and_kind2action(selected_node)

    def get_normal_negative_reward(self):
        return self.normal_negative_reward

    def get_normal_positive_reward(self):
        return self.normal_positive_reward


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
    print(se.load_balanced_reward())
