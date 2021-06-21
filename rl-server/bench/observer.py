from kubernetes import client, config, watch
from algorithm import load_balanced_reward_calculate, reward
from metrics import Monitor
import multiprocessing as mp
from client import K8sClient
import time
from collections import deque
import numpy as np
from threading import Thread
from config import ModelConfig

config.load_kube_config()

v1 = client.CoreV1Api()

time_str = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())


def start_monitor():
    m = Monitor(path="bench/data/cluster-{}.csv".format(time_str))
    m.start()


k8sClient = K8sClient()

mp.Process(target=start_monitor).start()

LOG_PATH = "bench/data/log-{}.csv".format(time_str)
log_file = open(LOG_PATH, mode='w')

w = watch.Watch()
scores = deque(maxlen=2000)
start_time = time.time()
cnt = 0

pod_list = []


def log(cnt):
    time.sleep(ModelConfig.get_train_interval)
    pod_list.append(pod_name)
    node_name = event['object'].spec.node_name
    node_list = k8sClient.get_nodes()
    res_map = k8sClient.get_all_node_percentage()
    reward = load_balanced_reward_calculate(node_name, node_list, res_map)

    scores.append(reward)
    spend_time = int(time.time() - start_time)
    log_file.write(str(spend_time) + ",{},{:.2f}\n".format(cnt,
                                                           np.mean(scores)))
    log_file.flush()


for event in w.stream(v1.list_namespaced_pod, ("default")):
    # print(event['object'].spec.node_name)

    pod_name = event['object'].metadata.name
    print("Event: %s %s %s %s" %
          (event['type'], event['object'].kind, pod_name, event['object'].status.phase))
    if event['object'].status.phase == "Running" and not (pod_name in pod_list):
        cnt += 1
        Thread(target=log, args=(cnt,)).start()
