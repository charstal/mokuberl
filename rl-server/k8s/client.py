from multiprocessing import Value
from kubernetes import client, config
import math
import warnings
from config import NODE_CLASS_CPU, NODE_CLASS_MEMORY


config.load_kube_config()


class Resource:
    def __init__(self, cpu, memory):
        self._cpu = cpu
        self._memory = memory

    def get_all(self):
        return {
            NODE_CLASS_CPU: self._cpu,
            NODE_CLASS_MEMORY: self._memory
        }
    
    def get_cpu(self):
        return self._cpu

    def get_memory(self):
        return self._memory

    def __str__(self):
        return "cpu: {}, memory: {}".format(self._cpu, self._memory)


class K8sClient:
    def __init__(self):
        # Configs can be set in Configuration class directly or using helper utility
        self._core_client = client.CoreV1Api()
        self._custom_api_client = client.CustomObjectsApi()

    def get_all_node_capacity(self, taints=False):
        """get node capacity
        """
        capacity_map = dict()
        ret = self._core_client.list_node(watch=False)
        
        for i in ret.items:
            capacity_map[i.metadata.name] = Resource(
                cpu_convert(i.status.allocatable['cpu']), 
                memory_convert(i.status.allocatable['memory'])
            )
            # {
            #     "cpu": cpu_convert(i.status.allocatable['cpu']),
            #     "memory": memory_convert(i.status.allocatable['memory']),
            # }

        return capacity_map

    def get_all_node_usage(self):
        """get node usage
        """
        usage_map = dict()
        ret = self._custom_api_client.list_cluster_custom_object(
            'metrics.k8s.io', 'v1beta1', 'nodes')
        for i in ret['items']:
            usage_map[i['metadata']['name']] = Resource(
                cpu_convert(i['usage']['cpu']),
                memory_convert(i['usage']['memory'])
            )
            # {
            #     "cpu": cpu_convert(i['usage']['cpu']),
            #     "memory": memory_convert(i['usage']['memory']),
            # }
        return usage_map

    def get_all_node_percentage(self):
        capacity = self.get_all_node_capacity()
        usage = self.get_all_node_usage()
        
        nodes_occupy = dict()
        for k, v in capacity.items():
            nodes_occupy[k] = {
                NODE_CLASS_CPU: usage[k].get_cpu() * 100 / v.get_cpu(),
                NODE_CLASS_MEMORY: usage[k].get_memory() * 100 / v.get_memory()
            }

        return nodes_occupy

    def get_node_percentage(self, node_name):
        capacity = self.get_all_node_capacity()[node_name]
        usage = self.get_all_node_usage()[node_name]

        return {
            NODE_CLASS_CPU: usage.get_cpu() * 100 / capacity.get_cpu(),
            NODE_CLASS_MEMORY: usage.get_memory() * 100 / capacity.get_memory()
            }

    def get_pod(self, pod_name, namespace):
        """get pod info
        """
        ret = self._core_client.read_namespaced_pod(pod_name, namespace)
        return ret

    def get_nodes(self, taints=False):
        """get all nodes without taints
        """
        node_list = []
        ret = self._core_client.list_node(watch=False)
        
        for i in ret.items:
            if not taints and i.spec.taints is not None:
                continue
            node_list.append(i.metadata.name)

        if len(node_list) == 0:
            warnings.warn("no node available or connect server")
        return node_list

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
    # test_capacity = k8sclient.get_all_node_capacity()
    # for key, value in test_capacity.items():
    #     print(key, value)
    # test_usage = k8sclient.get_all_node_usage()
    # for key, value in test_usage.items():
    #     print(key, value)
    # print(k8sclient.get_node_percentage("minikube"))
    all_nodes_p = k8sclient.get_all_node_percentage()
    for key, value in all_nodes_p.items():
        print(key)
        print(value)
    # print(k8sclient.get_pod("metrics-server-56c4f8c9d6-gxqgt", "kube-system"))
