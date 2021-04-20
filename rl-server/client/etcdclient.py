import etcd3
from config import SysConfig


class EtcdClient:
    def __init__(self, url, port, username, password):
        self.etcd_client = etcd3.client(host=url,
                                        port=port, user=username, password=password)

    def put_nodes(self, node_list):
        nodes = " ".join(node_list)
        self.etcd_client.put("/k8s/nodes", nodes)

    def get_nodes(self):
        res, _ = self.etcd_client.get("/k8s/nodes")
        if res == None:
            return []
        else:
            nodes = str(res.decode()).split(" ")
            return nodes


if __name__ == "__main__":
    cl = EtcdClient(url=SysConfig.get_etcd_url, port=SysConfig.get_grpc_port(), username=SysConfig.get_etcd_username(),
                    password=SysConfig.get_etcd_password())
    cl.put_nodes(["n1", "node2", "node3"])
    print(cl.get_nodes())
