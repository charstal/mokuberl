from client import LoadMonitorClient
from resourcestats import ResourceStats
import json

if __name__ == "__main__":
    lmc = LoadMonitorClient()

    # lmc.heartbeat()
    d = lmc.get_data()
    # print(d)
    r = ResourceStats(d)
    # print(json.dumps(r.instance.instance_map))
    print(r.add_pod_numpy1("a"))
