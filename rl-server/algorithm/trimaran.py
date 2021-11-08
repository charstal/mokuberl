from config import SysConfig

RESOURCE_THRESHOLD = SysConfig.get_resource_threshold()
ITA = SysConfig.get_load_variation_risk_balancing_ita()


class Trimaran:
    def target_load_packing_calculate(occupancy_rate):
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
        elif occupancy_rate > RESOURCE_THRESHOLD:
            return 50 * (100 - occupancy_rate) / (100 - RESOURCE_THRESHOLD)
        else:
            return (100 - RESOURCE_THRESHOLD) * occupancy_rate / RESOURCE_THRESHOLD + RESOURCE_THRESHOLD

    def load_variation_risk_balancing(mean, variation):
        """
        https://github.com/kubernetes-sigs/scheduler-plugins/tree/master/kep/61-Trimaran-real-load-aware-scheduling
        mu + ita x sigma <= 100 %
        ita = 1, we have a 16% risk that the actual usage exceeds the node capacity.
        ita = 2, we have a 2.5% chance that the actual usage exceeds the node capacity.
        ita = 3, we have a 0.15% chance that the actual usage exceeds the node capacity. 
        By default, we choose ita = 1 as we would like to improve the overall utilization. 
        ita can be configured via the SafeVarianceMargin for the plugin.
        """
        if mean + ITA * variation <= 100:
            return True
        else:
            return False


if __name__ == "__main__":
    print(ITA)
