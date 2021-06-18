from config import ModelConfig, SysConfig
from client import ResourceAnalysis
RESOURCE_THRESHOLD = SysConfig.get_resource_threshold()
RESOURCE_CLASS = ModelConfig.get_resource_class()
MID_HIGH_LOADING_THRESHOLD = SysConfig.get_mid_high_loading_threshold()


def load_balanced_reward_calculate(seleted_node, node_list, resource_map):
    # 中高负载节点尽量均衡，可以更好的应对已存在 pod 突如其来的高负载，减少资源抢占
    # 而低负载节点在高负载的没达到阈值时尽量不要分配 pod，以便上面的 pod 自己跑完从而关闭节点
    alpha = 1
    beta = 1
    theta = 1
    gamma = 3
    kappa = 0.5

    print("************************** reward calculate **************************")
    score = alpha * get_util(node_list, resource_map) - \
        beta * get_diff_node(node_list, resource_map) - \
        theta * get_diff_res(node_list, resource_map) -  \
        gamma * get_overload_punishment(seleted_node, resource_map) + \
        kappa * get_free_point(node_list, resource_map)
    print("***************************** reward end *****************************")

    return normallize(score)


def normallize(score):
    # MAX = 100 + MID_HIGH_LOADING_THRESHOLD # 150
    # MIN = 100 - 100 -
    return score / 100
# 获得系统的平均利用率


def get_util(node_list, resource_map):
    score = 0
    for node in node_list:
        s = 0
        for k in RESOURCE_CLASS:
            s += resource_map[node][k]
        s /= len(RESOURCE_CLASS)
        score += s
    score /= len(node_list)
    print("util score: ", score)
    return score


# 获得上node不同资源之间的差值
def get_diff_res(node_list, resource_map):
    score = 0
    for node in node_list:
        for i in range(len(RESOURCE_CLASS)):
            for j in range(i, len(RESOURCE_CLASS)):
                score += abs(resource_map[node][RESOURCE_CLASS[i]] -
                             resource_map[node][RESOURCE_CLASS[j]])
    score /= len(node_list)

    print("diff res score: ", score)
    return score


# 获得不同node资源平均值的差值
def get_diff_node(node_list, resource_map):
    score = 0

    ulist = []
    for node in node_list:
        s = 0
        for k in RESOURCE_CLASS:
            s += resource_map[node][k]
        s /= len(RESOURCE_CLASS)
        # 只限定中高负载
        if s > MID_HIGH_LOADING_THRESHOLD:
            ulist.append(s)

    for i in range(len(ulist)):
        for j in range(i, len(ulist)):
            score += abs(ulist[i] - ulist[j])
    if len(ulist) != 0:
        score /= len(ulist)
    print("diff node score: ", score)
    return score


# 超过阈值的扣分
def get_overload_punishment(seleted_node, resource_map):
    score = 0
    for k in RESOURCE_CLASS:
        if resource_map[seleted_node][k] >= RESOURCE_THRESHOLD:
            score += abs(resource_map[seleted_node]
                         [k] - RESOURCE_THRESHOLD)
            score = (score + 8) ** 1.1
    print("overload punishment score: ", score)
    return score


# 给与低负载的node的空闲分，低负载越空分数越高，
def get_free_point(node_list, resource_map):
    score = 0
    for node in node_list:
        s = 0
        for k in RESOURCE_CLASS:
            s += resource_map[node][k]
        s /= len(RESOURCE_CLASS)
        # 只限定低负载
        if s < MID_HIGH_LOADING_THRESHOLD:
            score += MID_HIGH_LOADING_THRESHOLD - s
    if len(node_list) != 0:
        score /= len(node_list)
    print("get free node point: ", score)
    return score


if __name__ == "__main__":
    node_list = ["k8s-master", "k8s-node01", "k8s-node02"]
    seleted_node = node_list[2]

    # for per in range(0, 101):
    resource_map = {
        "k8s-master": ResourceAnalysis(72, 50),
        "k8s-node01": ResourceAnalysis(101, 85),
        "k8s-node02": ResourceAnalysis(20, 24),
    }

    reward = load_balanced_reward_calculate(
        seleted_node, node_list, resource_map)
    print(":res-map-reward:", reward)
