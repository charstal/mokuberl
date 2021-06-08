from threading import Timer

from pandas.core.frame import DataFrame
from client import K8sClient
import pandas as pd
import time

time_str = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
CLUSTER_RESOURCE_PATH = "metrics/data/cluster-{}.csv".format(time_str)
# cluster_resource_file = open(CLUSTER_RESOURCE_PATH, mode='w')

# Second
INTERVAL = 10
TIMES_PER_SAVE = 20


class Monitor:
    def __init__(self):
        self.k8sclient = K8sClient()
        self.cnt = 0
        self.data = {}
        self.time = []

    def start(self):
        while True:
            time.sleep(INTERVAL)
            self.run()

    def run(self):
        self.cnt += 1
        nodes_per = self.k8sclient.get_all_node_percentage()

        for item in nodes_per.keys():
            if self.data.get(item) == None:
                self.data[item] = [nodes_per[item]]
            else:
                self.data[item].append(nodes_per[item])
        self.time.append(self.cnt * INTERVAL)
        # print(self.cnt)
        if self.cnt % TIMES_PER_SAVE == 0:
            df = DataFrame(self.data, index=self.time)
            df.to_csv(CLUSTER_RESOURCE_PATH)


if __name__ == "__main__":
    m = Monitor()
    m.start()
