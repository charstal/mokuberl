import numpy as np


class Resource:
    def __init__(self, cpu, memory):
        self._cpu = cpu
        self._memory = memory

    def get_cpu(self):
        return self._cpu

    def get_memory(self):
        return self._memory

    def __truediv__(self, rhs):
        cpu_per = self._cpu * 100 / rhs._cpu
        memory_per = self._memory * 100 / rhs._memory

        return ResourceAnalysis(cpu_per, memory_per)

    def __add__(self, rhs):
        return Resource(self._cpu + rhs._cpu, self._memory + rhs._memory)

    def __str__(self):
        return "cpu: {}, memory: {}".format(self._cpu, self._memory)

    def __getitem__(self, index):
        res_dict = {
            "CPU": self._cpu,
            "MEMORY": self._memory
        }

        return res_dict[index]


class ResourceAnalysis:
    def __init__(self, cpu_percentage, memory_percentage):
        self.cpu = cpu_percentage
        self.memory = memory_percentage

    def __str__(self):
        return "{},{}".format(self.cpu, self.memory)

    def transfer_to_vec(self):
        para_list = [self.cpu, self.memory]
        return np.array(para_list)

    def __getitem__(self, index):
        res_dict = {
            "CPU": self.cpu,
            "MEMORY": self.memory
        }

        return res_dict[index]


if __name__ == "__main__":
    a = Resource(1000, 1000)
    print(a['CPU'])
