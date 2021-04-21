from config import TrimaranConfig

RESOURCE_THRESHOLD = TrimaranConfig.get_resource_threshold()


class Trimaran:
    def target_load_packing_calculate(occupancy_rate, kind):
        """
        https://github.com/charstal/scheduler-plugins/tree/master/kep/61-Trimaran-real-load-aware-scheduling
        Get the utilization of the current node to be scored. Call it A.
        Calculate the current pod's total CPU requests and overhead. Call it B.
        Calculate the expected utilization if the pod is scheduled under this node by adding i.e. U = A + B.
        If U <= X%, return (100 - X)U/X + X as the score
        If X% < U <= 100%, return 50(100 - U)/(100 - X)
        If U > 100%, return 0
        """
        if occupancy_rate > 100:
            return 0
        elif occupancy_rate > RESOURCE_THRESHOLD[kind]:
            return 50 * (100 - occupancy_rate) / (100 - RESOURCE_THRESHOLD[kind])
        else:
            return (100 - RESOURCE_THRESHOLD[kind]) * occupancy_rate / RESOURCE_THRESHOLD[kind] + RESOURCE_THRESHOLD[kind]
