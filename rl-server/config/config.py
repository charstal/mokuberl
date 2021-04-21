import os
import configparser
from threading import ThreadError

ENV = os.getenv('ENV', 'DEV')

config = configparser.ConfigParser()

config_url = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          'config.ini')

config.read(config_url, encoding='utf-8')


class SysConfig:
    def get_grpc_port():
        return int(config.get(ENV, "GRPC_PORT"))

    def get_etcd_port():
        return int(config.get(ENV, "ETCD_PORT"))

    def get_etcd_username():
        return config.get(ENV, "ETCD_USERNAME")

    def get_etcd_password():
        return config.get(ENV, "ETCD_PASSWORD")

    def get_etcd_url():
        return config.get(ENV, "ETCD_URL")

    def get_node_size():
        return int(config.get(ENV, "NODE_SIZE"))

    def get_node_interval():
        return int(config.get(ENV, "NODE_INTERVAL"))


class ModelConfig:
    def get_model_path():
        return config.get(ENV, "MODEL_PATH")

    def get_train_interval():
        return int(config.get("MODEL", "TRAIN_INTERVAL"))

    def get_eps_start():
        return float(config.get("MODEL", "EPS_START"))

    def get_eps_end():
        return float(config.get("MODEL", "EPS_END"))

    def get_eps_decay():
        return float(config.get("MODEL", "EPS_DECAY"))

    def get_mode_save_train_times():
        return int(config.get("MODEL", "MODEL_SAVE_TRAIN_TIMES"))

    def get_buffer_size():
        return int(float(config.get("MODEL", "BUFFER_SIZE")))

    def get_batch_size():
        return int(config.get("MODEL", "BATCH_SIZE"))

    def get_gamma():
        return float(config.get("MODEL", "GAMMA"))

    def get_tau():
        return float(config.get("MODEL", "TAU"))

    def get_lr():
        return float(config.get("MODEL", "LR"))

    def get_update_every():
        return int(config.get("MODEL", "UPDATE_EVERY"))

    def get_node_class():
        return config.get("MODEL", "NODE_CLASS").split(",")


class TrimaranConfig:

    def get_node_resource_class():
        return config.get("MODEL", "NODE_CLASS").split(",")

    def get_target_load_packing_config():
        target_load_pack_config = dict()
        k = config.get("MODEL", "NODE_CLASS").split(",")
        v = config.get("TRIMARAN", "TARGET_LOAD_PACKING_PERCENTAGE").split(",")
        print(k)
        for i in range(len(k)):
            target_load_pack_config[k[i]] = float(v[i])
        return target_load_pack_config

    def get_resource_threshold():

        k = config.get("MODEL", "NODE_CLASS").split(",")
        threshold_config = dict()
        for item in k:
            threshold_config[item] = float(
                config.get("TRIMARAN", item + "_THRESHOLD"))

        return threshold_config


# node resource class
# C: cpu
# M: memory
NODE_CLASS = ["C", "M"]

NODE_CLASS_CPU = "C"
NODE_CLASS_MEMORY = "M"

# node state
# 1, can be scheduled
# 0, cannot be scheduled
NODE_STATE = [0, 1]

# node amount
DEFAULT_NODE_SIZE = 10

CLASS_THRESHOLD = {
    NODE_CLASS_CPU: 70,
    NODE_CLASS_MEMORY: 70
}
NODE_CPU_THRESHOLD = 70
NODE_MEMORY_THRESHOLD = 70

# model train interval
# TRAIN_INTERVAL_SECONDS = 5


POSITIVE_REWARD = 1.0
NEGATIVE_REWARD = -1.0

# MODEL_PATH = 'checkpoint.pth'


# ETCD_USERNAME = "root"
# ETCD_PASSWORD = "JpcQt2zGZL"
# ETCD_PORT = 2379


if __name__ == "__main__":
    print(SysConfig.get_grpc_port())
    print(SysConfig.get_etcd_username())
    print(SysConfig.get_etcd_password())
    print(SysConfig.get_etcd_port())
    print(ModelConfig.get_train_interval())
    print(ModelConfig.get_batch_size())
    print(ModelConfig.get_buffer_size())
    print(ModelConfig.get_eps_decay())
    print(ModelConfig.get_gamma())
    print(ModelConfig.get_lr())
    print(ModelConfig.get_node_class())
    print(TrimaranConfig.get_target_load_packing_config())
    print(TrimaranConfig.get_resource_threshold())
