import requests
import logging
import time
import threading
from urllib import parse

heartbeat_interval_seconds = 10
heartbeat_timeout_seconds = 60

LOAD_MONITOR_ADDRESS = "http://10.214.241.226:32020"


class LoadMonitorClient():
    def __init__(self, load_monitor_address: str):
        self.base_address = load_monitor_address
        self.metric_address = parse.urljoin(self.base_address, "metric")
        self.healthy_address = parse.urljoin(self.base_address, "healthy")
        self.last_heartbeat_time = 0

        self.heartbeat()

        def func():
            while True:
                time.sleep(heartbeat_interval_seconds)
                self.heartbeat()

        threading.Thread(target=func).start()

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

    def get(self, duration: str = "5m") -> dict:
        if not self.valid():
            logging.warn("load monitor invalid now")
            return None
        if duration not in ["5m", "10m", "15m"]:
            logging.warn("invalid duration, allow: 5m 10m 15, use 5m instead")
            duration = "5m"

        resp = requests.get(self.metric_address, params={"duration": duration})
        if not resp.ok:
            logging.error("cannot get metrics")
            return None

        res_dict = resp.json()
        return res_dict


if __name__ == "__main__":
    lmc = LoadMonitorClient(LOAD_MONITOR_ADDRESS)

    # lmc.heartbeat()
    print(lmc.get(duration="5m"))
