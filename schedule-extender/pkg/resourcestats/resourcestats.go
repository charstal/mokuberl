package resourcestats

import (
	"math"

	"github.com/charstal/load-monitor/pkg/metricstype"
	v1 "k8s.io/api/core/v1"
	"k8s.io/klog/v2"
	"k8s.io/kubernetes/pkg/scheduler/framework"
)

const (
	// MegaFactor : Mega unit multiplier
	MegaFactor = float64(1. / 1024. / 1024.)
)

// ResourceStats : statistics data for a resource
type ResourceStats struct {
	// average used (absolute)
	UsedAvg float64
	// standard deviation used (absolute)
	UsedStdev float64
	// req of pod
	Req float64
	// node capacity
	Capacity float64
}

var (
	MetricTypeList = []string{
		metricstype.CPU,
		metricstype.Memory,
	}

	ResourceTypeList = []v1.ResourceName{
		v1.ResourceCPU,
		v1.ResourceMemory,
		v1.ResourceEphemeralStorage,
		v1.ResourceStorage,
	}

	MetricType2ResourceTypeMap = map[string]v1.ResourceName{
		metricstype.CPU:    v1.ResourceCPU,
		metricstype.Memory: v1.ResourceMemory,
	}

	ResourceType2MetricTypeMap = map[v1.ResourceName]string{
		v1.ResourceCPU:    metricstype.CPU,
		v1.ResourceMemory: metricstype.Memory,
	}
)

type StatisticsResourceStats struct {
	// average used (absolute) mill
	Avg float64
	// standard deviation used (absolute) MB
	Stdev float64
}

type StatisticsResourceStatsMap map[string]StatisticsResourceStats

func CreateStatisticsResource(statistics *metricstype.StatisticsData, podLabel string) (rss *StatisticsResourceStatsMap, isValid bool) {
	if statistics == nil {
		return nil, false
	}
	if len(podLabel) == 0 {
		return nil, false
	}
	var podStatics metricstype.NodeMetrics
	var ok bool
	podStatics, ok = statistics.StatisticsMap[podLabel]
	if !ok {
		podStatics, ok = statistics.StatisticsMap[metricstype.ALL_COURSE_LABEL]
		if ok {
			klog.InfoS("Unable to find metrics for label", "label name", podLabel, "So instead of all method")
		} else {
			klog.InfoS("Unable to find metrics for label", "label name", podLabel, "and cannot find metrics of all")
			return nil, false
		}

	}

	metrics := podStatics.Metrics
	resourceList := make(StatisticsResourceStatsMap, 0)

	for _, t := range MetricTypeList {
		podUtil, podStd, metricFound := GetResourceData(metrics, t)
		if !metricFound {
			klog.V(6).InfoS("Resource usage statistics for label : no valid data")
			return nil, false
		}
		resourceList[t] = StatisticsResourceStats{Avg: podUtil, Stdev: podStd}
	}

	return &resourceList, true
}

// CreateResourceStats : get resource statistics data from measurements for a node
func CreateResourceStats(metrics []metricstype.Metric, node *v1.Node, podRequest *framework.Resource,
	resourceName v1.ResourceName, watcherType string) (rs *ResourceStats, isValid bool) {
	// get resource usage statistics
	nodeUtil, nodeStd, metricFound := GetResourceData(metrics, watcherType)
	if !metricFound {
		klog.V(6).InfoS("Resource usage statistics for node : no valid data", "node", klog.KObj(node))
		return nil, false
	}
	// get resource capacity
	rs = &ResourceStats{}
	allocatableResources := node.Status.Allocatable
	am := allocatableResources[resourceName]

	if resourceName == v1.ResourceCPU {
		rs.Capacity = float64(am.MilliValue())
		rs.Req = float64(podRequest.MilliCPU)
	} else {
		rs.Capacity = float64(am.Value())
		rs.Capacity *= MegaFactor
		rs.Req = float64(podRequest.Memory) * MegaFactor
	}

	// calculate absolute usage statistics
	rs.UsedAvg = nodeUtil * rs.Capacity / 100
	rs.UsedStdev = nodeStd * rs.Capacity / 100

	klog.V(6).InfoS("Resource usage statistics for node", "node", klog.KObj(node), "capacity",
		rs.Capacity, "required", rs.Req, "usedAvg", rs.UsedAvg, "usedStdev", rs.UsedStdev)
	return rs, true
}

func CreateResourceStatsFromStatistics(metrics []metricstype.Metric, node *v1.Node, statisticsMetrics []StatisticsResourceStatsMap,
	resourceName v1.ResourceName, watcherType string) (rs *ResourceStats, isValid bool) {
	// get resource usage statistics
	nodeUtil, nodeStd, metricFound := GetResourceData(metrics, watcherType)
	if !metricFound {
		klog.V(6).InfoS("Resource usage for node : no valid data", "node", klog.KObj(node))
		return nil, false
	}
	// get resource capacity
	rs = &ResourceStats{}
	allocatableResources := node.Status.Allocatable
	am := allocatableResources[resourceName]

	podUtil, podStd, metricFound := GetStatisticsResourceData(statisticsMetrics, watcherType)
	if !metricFound {
		klog.V(6).InfoS("Resource usage statistics for node : no valid data", "node", klog.KObj(node))
		return nil, false
	}

	if resourceName == v1.ResourceCPU {
		rs.Capacity = float64(am.MilliValue())
		rs.Req = podUtil
	} else {
		rs.Capacity = float64(am.Value())
		rs.Capacity *= MegaFactor
		rs.Req = podUtil
	}

	// calculate absolute usage statistics
	rs.UsedAvg = nodeUtil + rs.Req
	rs.UsedStdev = math.Max(nodeStd, podStd)

	klog.V(6).InfoS("Resource usage statistics for node", "node", klog.KObj(node), "capacity", rs.Capacity,
		"required", rs.Req, "usedAvg", rs.UsedAvg, "usedStdev", rs.UsedStdev)
	return rs, true
}

// GetMuSigma : get average and standard deviation from statistics
func GetMuSigma(rs *ResourceStats) (float64, float64) {

	if rs.Capacity <= 0 {
		return 0, 0
	}
	mu := (rs.UsedAvg + rs.Req) / rs.Capacity
	mu = math.Max(math.Min(mu, 1), 0)
	sigma := rs.UsedStdev / rs.Capacity
	sigma = math.Max(math.Min(sigma, 1), 0)
	return mu, sigma
}

// GetResourceData : get data from measurements for a given resource type
func GetResourceData(metrics []metricstype.Metric, resourceType string) (avg float64, stDev float64, isValid bool) {
	// for backward compatibility of LoadWatcher:
	// average data metric without operator specified
	avgFound := false
	for _, metric := range metrics {
		if metric.Type == resourceType {
			if metric.Operator == metricstype.Average {
				avg = metric.Value
				avgFound = true
			} else if metric.Operator == metricstype.Std {
				stDev = metric.Value
			} else if (metric.Operator == "" || metric.Operator == metricstype.Latest) && !avgFound {
				avg = metric.Value
			}
			isValid = true
		}
	}
	return avg, stDev, isValid
}

func GetStatisticsResourceData(metrics []StatisticsResourceStatsMap, resourceType string) (avg float64, stDev float64, isValid bool) {
	avg, stDev = 0.0, 0.0
	for _, metric := range metrics {
		avg = avg + metric[resourceType].Avg
		stDev = math.Max(stDev, metric[resourceType].Stdev)
	}
	return avg, stDev, isValid
}

// GHetResourceRequested : calculate the resource demand of a pod (CPU and Memory)
func GetResourceRequested(pod *v1.Pod) *framework.Resource {
	// add up demand of all containers
	result := &framework.Resource{}
	for _, container := range pod.Spec.Containers {
		result.Add(container.Resources.Requests)
	}
	// take max_resource(sum_pod, any_init_container)
	for _, container := range pod.Spec.InitContainers {
		for rName, rQuantity := range container.Resources.Requests {
			switch rName {
			case v1.ResourceCPU:
				if cpu := rQuantity.MilliValue(); cpu > result.MilliCPU {
					result.MilliCPU = cpu
				}
			case v1.ResourceMemory:
				if mem := rQuantity.Value(); mem > result.Memory {
					result.Memory = mem
				}
			default:
			}
		}
	}
	// add any pod overhead
	if pod.Spec.Overhead != nil {
		result.Add(pod.Spec.Overhead)
	}
	return result
}
