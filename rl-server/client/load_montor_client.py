import requests
import logging
import time
import threading
from urllib import parse

from resourcestats import ResourceStats

heartbeat_interval_seconds = 10
heartbeat_timeout_seconds = 60
metrics_update_interval_seconds = 30

LOAD_MONITOR_ADDRESS = "http://10.214.241.226:32020"


class LoadMonitorClient():
    def __init__(self, load_monitor_address: str = LOAD_MONITOR_ADDRESS):
        self.base_address = load_monitor_address
        self.metric_address = parse.urljoin(self.base_address, "metric")
        self.healthy_address = parse.urljoin(self.base_address, "healthy")
        self.last_heartbeat_time = 0
        self.last_metrics_update_time = 0

        self.heartbeat()
        self.request()

        def func1():
            while True:
                time.sleep(heartbeat_interval_seconds)
                self.heartbeat()

        def func2():
            while True:
                time.sleep(metrics_update_interval_seconds)
                self.request()

        threading.Thread(target=func1).start()
        threading.Thread(target=func2).start()

    def get_data(self):
        return self.metrics_data

    def heartbeat(self):
        resp = requests.get(self.healthy_address)
        if resp.ok:
            self.last_heartbeat_time = time.time()
        else:
            logging.error("cannot get heartbeat from load monitor client")

    def valid(self) -> bool:
        if time.time() - self.last_heartbeat_time >= heartbeat_timeout_seconds:
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
