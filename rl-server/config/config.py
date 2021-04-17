import os
import configparser

ENV = os.getenv('ENV', 'DEV')

config = configparser.ConfigParser()

config_url = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          'sys.ini')

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
        return float(config.get("MODEL", "EPS_DEVAY"))

    def get_mode_save_train_times():
        return int(config.get("MODEL", "MODEL_SAVE_TRAIN_TIMES"))


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
TRAIN_INTERVAL_SECONDS = 5


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
