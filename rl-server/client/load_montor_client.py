import requests
import logging
import time
import threading
from urllib import parse

from resourcestats import ResourceStats

HEARTBEAT_INTERVAL_SECONDES = 10
HEARTBEAT_TIMEOUT_SECONDES = 60
METRICS_UPDATE_INTERVAL_SECONDES = 30

DEFAULT_LOAD_MONITOR_ADDRESS = "http://10.214.241.226:32020"


STATE_SIZE = 41
ACTION_SIZE = 3+1


class LoadMonitorClient():
    def __init__(self, load_monitor_address: str = DEFAULT_LOAD_MONITOR_ADDRESS):
        self.base_address = load_monitor_address
        self.metric_address = parse.urljoin(self.base_address, "metric")
        self.healthy_address = parse.urljoin(self.base_address, "healthy")
        self.last_heartbeat_time = 0
        self.last_metrics_update_time = 0

        self.heartbeat()
        self.request()

        def func1():
            while True:
                time.sleep(HEARTBEAT_INTERVAL_SECONDES)
                self.heartbeat()

        def func2():
            while True:
                time.sleep(METRICS_UPDATE_INTERVAL_SECONDES)
                self.request()

        threading.Thread(target=func1).start()
        threading.Thread(target=func2).start()

    def get_raw_data(self):
        return self.metrics_data

    def get_resource_stats(self):
        data = self.metrics_data
        rs = ResourceStats(data)
        return rs

    def get_stats_size(self):
        '''
            see resourcestats.py, add_pod_numpy1, add_pod_numpy2
            default use add_pod_numpy2

        '''
        return STATE_SIZE

    def get_action_size(self):
        '''
            size = node_num + 1 (no schedule)
        '''
        return ACTION_SIZE

    def heartbeat(self):
        resp = requests.get(self.healthy_address)
        if resp.ok:
            self.last_heartbeat_time = time.time()
        else:
            logging.error("cannot get heartbeat from load monitor client")

    def valid(self) -> bool:
        if time.time() - self.last_heartbeat_time >= HEARTBEAT_TIMEOUT_SECONDES:
            return False

        return True

    def request(self, duration: str = "5m"):
        if not self.valid():
            logging.warn("load monitor invalid now")

        if duration not in ["5m", "10m", "15m"]:
            logging.warn("invalid duration, allow: 5m 10m 15, use 5m instead")
            duration = "5m"

        resp = requests.get(self.metric_address, params={"duration": duration})
        if not resp.ok:
            logging.error("cannot get metrics")

        res_dict = resp.json()
        self.last_metrics_update_time = time.time()
        self.metrics_data = res_dict
