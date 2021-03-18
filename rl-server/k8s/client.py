from kubernetes import client, config
import math

CPU = "CPU"
MEMORY = "MEMORY"

config.load_kube_config()


class K8sClient:
    def __init__(self):
        # Configs can be set in Configuration class directly or using helper utility
        self._core_client = client.CoreV1Api()
        self._custom_api_client = client.CustomObjectsApi()

    def get_all_node_capacity(self):
        """get node capacity
        """
        capacity_map = dict()
        ret = self._core_client.list_node(watch=False)
        for i in ret.items:
            capacity_map[i.metadata.name] = {
                "cpu": cpu_convert(i.status.allocatable['cpu']),
                "memory": memory_convert(i.status.allocatable['memory']),
            }
        return capacity_map

    def get_all_node_usage(self):
        """get node usage
        """
        usage_map = dict()
        ret = self._custom_api_client.list_cluster_custom_object(
            'metrics.k8s.io', 'v1beta1', 'nodes')
        for i in ret['items']:
            usage_map[i['metadata']['name']] = {
                "cpu": cpu_convert(i['usage']['cpu']),
                "memory": memory_convert(i['usage']['memory']),
            }
        return usage_map


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
        return int(digit * math.pow(factor, table[src[len(src)-1]]))


if __name__ == "__main__":
    k8sclient = K8sClient()
    # print(k8sclient.get_all_node_capacity())
    print(k8sclient.get_all_node_usage())
    # print(cpu_convert("12"))
    # print(memory_convert("123Mi"))
