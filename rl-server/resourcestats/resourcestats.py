import pandas as pd
import logging
import numpy as np
import time
# {
#   'timestamp': 1671782840,
#   'window': {
#       'duration': '5m', 'start': 1671782539, 'end': 1671782839
#   },
#   'source': 'Prometheus',
#   'data': {
#       'NodeMetricsMap': {
#           'k8s-node01': {
#               'metrics': [
#                   {'name': 'kube_node_status_capacity', 'type': 'cpu', 'operator': 'Capacity', 'rollup': 'Latest', 'value': 8, 'unit': 'core'},
#                   {'name': 'kube_node_status_capacity', 'type': 'ephemeral_storage', 'operator': 'Capacity', 'rollup': 'Latest', 'value': 18238930944, 'unit': 'byte'},
#                   {'name': 'kube_node_status_capacity', 'type': 'hugepages_2mi', 'operator': 'Capacity', 'rollup': 'Latest', 'value': 0, 'unit': 'byte'},
#                   {'name': 'kube_node_status_capacity', 'type': 'memory', 'operator': 'Capacity', 'rollup': 'Latest', 'value': 21050421248, 'unit': 'byte'},
#                   {'name': 'kube_node_status_capacity', 'type': 'pods', 'operator': 'Capacity', 'rollup': 'Latest', 'value': 110, 'unit': 'integer'},
#                   {'name': 'kube_node_status_capacity', 'type': 'network', 'operator': 'Capacity', 'rollup': 'Latest', 'value': 10420224, 'unit': 'bytes'},
#                   {'name': 'instance:node_cpu:ratio', 'type': 'cpu', 'operator': 'Avg', 'rollup': '5m', 'value': 1.9266228070175555, 'unit': 'ratio'},
#                   {'name': 'instance:node_cpu:ratio', 'type': 'cpu', 'operator': 'Std', 'rollup': '5m', 'value': 0.05898366220314428, 'unit': 'ratio'},
#                   {'name': 'instance:node_cpu:ratio', 'type': 'cpu', 'operator': 'Latest', 'rollup': '5m', 'value': 1.8407894736843469, 'unit': 'ratio'},
#                   {'name': 'instance:node_memory_utilisation:ratio', 'type': 'memory', 'operator': 'Avg', 'rollup': '5m', 'value': 7.604473637562428, 'unit': 'ratio'},
#                   {'name': 'instance:node_memory_utilisation:ratio', 'type': 'memory', 'operator': 'Std', 'rollup': '5m', 'value': 0.006859209627176233, 'unit': 'ratio'},
#                   {'name': 'instance:node_memory_utilisation:ratio', 'type': 'memory', 'operator': 'Latest', 'rollup': '5m', 'value': 7.612861999862631, 'unit': 'ratio'},
#                   {'name': 'node_disk_total_util_rate', 'type': '', 'operator': 'Unknown', 'rollup': '', 'value': 0.512280701754386, 'unit': ''},
#                   {'name': 'node_disk_read_util_rate', 'type': '', 'operator': 'Unknown', 'rollup': '', 'value': 0, 'unit': ''},
#                   {'name': 'node_disk_write_util_rate', 'type': '', 'operator': 'Unknown', 'rollup': '', 'value': 0.512280701754386, 'unit': ''},
#                   {'name': 'node_running_pod_count', 'type': '', 'operator': 'Latest', 'rollup': '', 'value': 6, 'unit': 'integer'},
#                   {'name': 'node_disk_saturation', 'type': '', 'operator': 'Unknown', 'rollup': '5m', 'value': 0.020272904483501008, 'unit': ''},
#                   {'name': 'node_disk_util_rate', 'type': '', 'operator': 'Unknown', 'rollup': '5m', 'value': 0.0007719298245614991, 'unit': ''},
#                   {'name': 'node_cpu_util_rate', 'type': '', 'operator': 'Unknown', 'rollup': '5m', 'value': 0.02163157894749912, 'unit': ''},
#                   {'name': 'node_network_receive_bytes_excluding_lo', 'type': '', 'operator': 'Unknown', 'rollup': '5m', 'value': 38639.803508771925, 'unit': 'bytes'},
#                   {'name': 'node_network_receive_drop_bytes_excluding_lo', 'type': '', 'operator': 'Unknown', 'rollup': '5m', 'value': 0, 'unit': 'bytes'},
#                   {'name': 'node_network_transmit_bytes_excluding_lo', 'type': '', 'operator': 'Unknown', 'rollup': '5m', 'value': 61713.6596491228, 'unit': 'bytes'},
#                   {'name': 'node_network_transmit_drop_bytes_excluding_lo', 'type': '', 'operator': 'Unknown', 'rollup': '5m', 'value': 0, 'unit': 'bytes'},
#                   {'name': 'node_network_total_bytes_percentage_excluding_lo', 'type': '', 'operator': 'Unknown', 'rollup': '5m', 'value': 0.9630643559859628, 'unit': ''},
#                   {'name': 'pod_class_of_node_count', 'type': 'a', 'operator': 'Latest', 'rollup': '', 'value': 4, 'unit': 'integer'}], 'tags': {}, 'metadata': {'dataCenter': ''}}
#   'statistics': {'
#       StatisticsMap': {
#                   'a': {
#                       'metrics': [
#                           {'name': 'statistic', 'type': 'cpu', 'operator': 'Std', 'rollup': '15d', 'value': 146.91006622930837, 'unit': 'm'},
#                           {'name': 'statistic', 'type': 'cpu', 'operator': 'Avg', 'rollup': '15d', 'value': 118.89215034603538, 'unit': 'm'},
#                           {'name': 'statistic', 'type': 'memory', 'operator': 'Std', 'rollup': '15d', 'value': 28.24263868999416, 'unit': 'MiB'},
#                           {'name': 'statistic', 'type': 'memory', 'operator': 'Avg', 'rollup': '15d', 'value': 189.83690960621743, 'unit': 'MiB'}], 'tags': {}, 'metadata': {'dataCenter': ''}},
#                   'all': {'metrics': [
#                           {'name': 'statistic', 'type': 'cpu', 'operator': 'Std', 'rollup': '15d', 'value': 146.91006622930837, 'unit': 'm'},
#                           {'name': 'statistic', 'type': 'cpu', 'operator': 'Avg', 'rollup': '15d', 'value': 118.89215034603538, 'unit': 'm'},
#                           {'name': 'statistic', 'type': 'memory', 'operator': 'Std', 'rollup': '15d', 'value': 28.24263868999416, 'unit': 'MiB'},
#                           {'name': 'statistic', 'type': 'memory', 'operator': 'Avg', 'rollup': '15d', 'value': 189.83690960621743, 'unit': 'MiB'}], 'tags': {}, 'metadata': {'dataCenter': ''}}}}}


class StatisticsStats():
    def __init__(self, raw_data: dict):
        '''
        cpu unit is mills, 
        memory unit is memory
        example: 
        'cpu': {
            'Std': 146.91006622930837   # mills
            'Avg': 118.89215034603538   # mills
            }, 
        'memory': {
            'Std': 28.24263868999416,   # MB
            'Avg': 189.83690960621743   # MB
            }
        '''
        statistics_map = dict()

        raw_metrics = raw_data["metrics"]
        for m in raw_metrics:
            t = m["type"]
            op = m["operator"]
            # rollup = m["rollup"]
            value = m["value"]
            if t not in statistics_map:
                statistics_map[t] = dict()
            statistics_map[t][op] = value

        self.statistics_map = statistics_map

    def get(self):
        return self.statistics_map

    def __getitem__(self, key):
        return self.statistics_map[key]


class LabelStatisticsMap():
    def __init__(self, raw_data):
        '''
        exmaple:

        'all': {
            'cpu': {
                'Std': 146.91006622930837   # mills
                'Avg': 118.89215034603538   # mills
                }, 
            'memory': {
                'Std': 28.24263868999416,   # MB
                'Avg': 189.83690960621743   # MB
                }
        },
        'a': ......

        '''
        m = dict()
        for key in raw_data:
            m[key] = StatisticsStats(raw_data[key])

        self.label_map = m

    def get(self):
        return self.label_map

    def __getitem__(self, key):
        if key not in self.label_map:
            logging.warn("label", key, "not exists using all instead")
            return self.label_map["all"]
        return self.label_map[key]


class CapacityStats():
    def __init__(self, raw_data):
        '''
        example
        "k8s-master": {
            "cpu":8000,
            "ephemeral_storage":17394,
            "hugepages_2mi":0,
            "memory":20075.24609375,
            "pods":110,
            "network":9.9375,
        }
        '''
        capacity_map = dict()

        mege_factor = 1.0 / 1024 / 1024     # byte -> MB
        core_factor = 1000                  # 1 core = 1000 mills

        for node in raw_data:
            cap = dict()
            for metric in raw_data[node]["metrics"]:
                if metric["name"] == "kube_node_status_capacity":
                    tt = metric["type"]
                    unit = metric["unit"]
                    value = metric["value"]
                    if unit == "byte":
                        value = value * mege_factor
                    if unit == "core":
                        value = value * core_factor

                    cap[tt] = value
            capacity_map[node] = cap

        self.capacity_map = capacity_map

    def __getitem__(self, key):
        return self.capacity_map[key]

    def get(self):
        return self.capacity_map


class InstanceStats():
    def __init__(self, raw_data, capacity):
        '''
        "k8s-master":{
            "instance:node_cpu:ratio:Avg":175.4035087719337,                                // abs mill
            "instance:node_cpu:ratio:Std":2.3036898153068566,                               // abs mill
            "instance:node_memory_utilisation:ratio:Avg":2455.3980468749996,                // abs MB
            "instance:node_memory_utilisation:ratio:Std":5.8811977599010925,                // abs MB
            "node_disk_saturation":0.0049255360623803,                                      // percentage / 100
            "node_network_total_bytes_percentage_excluding_lo":0.007425617048391295         // percentage / 100
        },
        ...
        '''
        instance_map = dict()

        ratio_resource_list = ["instance:node_cpu:ratio",
                               "instance:node_memory_utilisation:ratio"]
        operator_list = ["Avg", "Std"]

        scale_resource_list = [
            "node_network_total_bytes_percentage_excluding_lo", "node_disk_saturation"]

        pod_class_resource_list = [
            "node_running_pod_count",
            "pod_class_of_node_count"
        ]

        for node in raw_data:
            cap = dict()
            for metric in raw_data[node]["metrics"]:
                name = metric["name"]
                op = metric["operator"]
                if name in ratio_resource_list and op in operator_list:
                    new_name = name + ":" + op
                    value = self.ratio_to_absulote(node, metric, capacity)
                    cap[new_name] = value
                elif name in scale_resource_list:
                    value = metric["value"] / 100
                    cap[name] = value
                elif name in pod_class_resource_list:
                    pass

            instance_map[node] = cap

        self.instance_map = instance_map

    def ratio_to_absulote(self, node, metric, capacity):
        resource_type = metric["type"]
        value = metric["value"] / 100

        return capacity[node][resource_type] * value

    def get_map(self):
        return self.instance_map


class ResourceStats():
    def __init__(self, raw_data):

        self.load_from_raw_dict(raw_data=raw_data)

    def load_from_raw_dict(self, raw_data: dict):
        self.statistics = LabelStatisticsMap(
            raw_data["statistics"]["StatisticsMap"])

        self.duration = raw_data["window"]["duration"]
        self.time = raw_data["window"]["end"]

        self.capactiy = CapacityStats(raw_data["data"]["NodeMetricsMap"])
        self.instance = InstanceStats(
            raw_data["data"]["NodeMetricsMap"], self.capactiy)

    # def numpy(self):
    #     instance_map = self.instance.get_map()
    #     data = pd.DataFrame(instance_map)
    #     print(data)

    def add_pod_numpy1(self, pod_label: str):
        '''
        [2.16675439e-02 1.84927802e-02 1.31486762e-01 1.75052702e-03
        4.07563353e-03 4.85356876e-03 1.96026316e-02 1.89666464e-02
        8.53688260e-02 1.53273646e-03 9.62962963e-05 9.67085854e-03
        2.69114035e-02 1.89544219e-02 1.08460036e-01 1.69216746e-03
        1.38050682e-03 9.58257610e-03]
        (1 * 18)
        '''

        if len(pod_label) == 0:
            logging.error("please add pod numpy")
            return

        instance_map = self.instance.get_map()
        node_list = instance_map.keys()
        data = pd.DataFrame(instance_map).T
        pod_statistics = self.statistics[pod_label]

        data["instance:node_cpu:ratio:Avg"] = np.where(
            pod_statistics["cpu"]["Avg"] > data["instance:node_cpu:ratio:Avg"], pod_statistics["cpu"]["Avg"], data["instance:node_cpu:ratio:Avg"])
        data["instance:node_cpu:ratio:Std"] += pod_statistics["cpu"]["Std"]
        data["instance:node_memory_utilisation:ratio:Avg"] += pod_statistics["memory"]["Avg"]
        data["instance:node_memory_utilisation:ratio:Std"] += np.where(
            pod_statistics["memory"]["Std"] > data["instance:node_memory_utilisation:ratio:Std"], pod_statistics["memory"]["Std"], data["instance:node_memory_utilisation:ratio:Std"])

        for node in node_list:
            node_capacity = self.capactiy[node]
            data.loc[node, "instance:node_cpu:ratio:Avg"] /= node_capacity["cpu"]
            data.loc[node, "instance:node_cpu:ratio:Std"] /= node_capacity["cpu"]
            data.loc[node, "instance:node_memory_utilisation:ratio:Avg"] /= node_capacity["memory"]
            data.loc[node, "instance:node_memory_utilisation:ratio:Std"] /= node_capacity["memory"]

        # print(data)
        return data.to_numpy().flatten()

    # def
    def add_pod_numpy2(self, pod_label: str):
        '''
        (18,)
        (18,)
        (4,)
        [8.00000000e+03 1.73940000e+04 0.00000000e+00 2.00752461e+04
        1.10000000e+02 9.93750000e+00 8.00000000e+03 1.73940000e+04
        0.00000000e+00 2.00752461e+04 1.10000000e+02 9.93750000e+00
        8.00000000e+03 1.73940000e+04 0.00000000e+00 2.00752461e+04
        1.10000000e+02 9.93750000e+00 2.15603509e+02 4.51332421e+00
        1.98595391e+03 8.29521225e+00 1.31695906e-03 9.48405884e-03
        1.72887719e+02 6.18589625e-01 2.45281445e+03 5.83113854e+00
        3.73255361e-03 4.89303587e-03 1.58940351e+02 5.09508964e+00
        1.51925547e+03 6.98916009e+00 2.01559454e-04 9.70319613e-03
        1.46910066e+02 1.18892150e+02 2.82426387e+01 1.89836910e+02
        3.80613983e+01]
        (1 * 41)
        '''
        capacity_map = self.capactiy.get()
        capacity_array = pd.DataFrame(capacity_map).T.to_numpy().flatten()

        # print(capacity_array.shape)

        instance_map = self.instance.get_map()
        instance_array = pd.DataFrame(instance_map).T.to_numpy().flatten()

        # print(instance_array.shape)

        pod_statistics = self.statistics[pod_label].get()
        statistics_array = pd.DataFrame(pod_statistics).T.to_numpy().flatten()

        # print(statistics_array.shape)

        diff_time = time.time() - self.time

        return np.concatenate((capacity_array, instance_array, statistics_array, diff_time), axis=None)
