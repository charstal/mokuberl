from client import LoadMonitorClient
from resourcestats import ResourceStats
import json

if __name__ == "__main__":
    lmc = LoadMonitorClient()

    # print(json.dumps(r.instance.instance_map))
    print(lmc.get_resource_stats().add_pod_numpy2("a"))
