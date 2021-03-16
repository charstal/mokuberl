from kubernetes import client, config
import math

CPU = "CPU"
MEMORY = "MEMORY"

class K8sClient:
    def __init__(self):
        # Configs can be set in Configuration class directly or using helper utility
        config.load_kube_config()
        self._instance = client.CoreV1Api()


    def get_all_node_capacity(self):
        """get node capacity
        """
        capacity_map = dict()
        ret = self._instance.list_node(watch=False)
        for i in ret.items:
            capacity_map[i.metadata.name] = {
                "cpu": cpu_convert(i.status.capacity['cpu']),
                "memory": memory_convert(i.status.capacity['memory']),
            }
        return capacity_map

def cpu_convert(src):
    if src.endswith("m"):
        return int(float(src[:len(src)-1]))
    try:
        return int(float(src) * 1000)
    except ValueError:
        return 0

def memory_convert(src):
    factor = 1000
    table = {'K': 1, 'M': 2, 'G': 3, 'T': 4, 'P': 5, 'E': 6}
    if src.endswith("i"):
        factor = 1024
        src = src[:len(src)-1]
    try:
        return int(src)
    except ValueError:
        digit = int(src[:len(src)-1])
        print(digit)
        return int(digit * math.pow(factor, table[src[len(src)-1]]))
        


if __name__ == "__main__": 
    k8sclient = K8sClient()
    print(k8sclient.get_all_node_capacity())
    # print(cpu_convert("12"))
    # print(memory_convert("123Mi"))

