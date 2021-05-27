from config import ModelConfig, SysConfig

RESOURCE_THRESHOLD = SysConfig.get_resource_threshold()
RESOURCE_CLASS = ModelConfig.get_resource_class()
MID_HIGH_LOADING_THRESHOLD = SysConfig.get_mid_high_loading_threshold()


def load_balanced_reward_calculate(node_list, resource_map):
    # 中高负载节点尽量均衡，可以更好的应对已存在 pod 突如其来的高负载，减少资源抢占
    # 而低负载节点在高负载的没达到阈值时尽量不要分配 pod，以便上面的 pod 自己跑完从而关闭节点
    alpha = 1
    beta = 1
    theta = 1
    gamma = 2
    kappa = 0.5

    print("************************** reward calculate **************************")
    score = alpha * get_util(node_list, resource_map) - beta * get_diff_node(node_list, resource_map) - theta * \
        get_diff_res(node_list, resource_map) - gamma * \
        get_overload_punishment(node_list, resource_map) + \
        kappa * get_free_point(node_list, resource_map)
    print("***************************** reward end *****************************")
    return score

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
    score /= len(ulist)
    print("diff node score: ", score)
    return score

# 超过阈值的扣分


def get_overload_punishment(node_list, resource_map):
    score = 0
    for node in node_list:
        s = 0
        for k in RESOURCE_CLASS:
            if resource_map[node][k] > RESOURCE_THRESHOLD:
                s += abs(resource_map[node]
                         [k] - RESOURCE_THRESHOLD)
        score += s
    print("overload punishment score: ", score)
    return score


# 给与低负载的node的空闲分，低负载越空分数越高，
def get_free_point(node_list, resource_map):
    score = 0
    ulist = []
    for node in node_list:
        s = 0
        for k in RESOURCE_CLASS:
            s += resource_map[node][k]
        s /= len(RESOURCE_CLASS)
        # 只限定中高负载
        if s < MID_HIGH_LOADING_THRESHOLD:
            ulist.append(s)
            score += MID_HIGH_LOADING_THRESHOLD - s
    score /= len(ulist)
    print("get free node point: ", score)
    return score
