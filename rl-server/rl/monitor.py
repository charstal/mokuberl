from k8s import K8sClient

class Monitor:
    def __init__(self):
        self.k8s_client = K8sClient()