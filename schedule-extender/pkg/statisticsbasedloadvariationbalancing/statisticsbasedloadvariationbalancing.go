package statisticsbasedloadvariationbalancing

import (
	"context"
	"fmt"
	"math"
	"os"
	"strconv"

	"github.com/charstal/load-monitor/pkg/metricstype"
	"github.com/charstal/schedule-extender/apis/config"
	"github.com/charstal/schedule-extender/pkg/algorithm"
	"github.com/charstal/schedule-extender/pkg/cache"
	"github.com/charstal/schedule-extender/pkg/collector"
	"github.com/charstal/schedule-extender/pkg/resourcestats"
	v1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/klog/v2"
	"k8s.io/kubernetes/pkg/scheduler/framework"
)

const (
	Name = "StatisticsBasedLoadVariationBalancing"

	SafeVarianceMarginKey      = "SAFE_VARIANCE_MARGIN_KEY"
	SafeVarianceSensitivityKey = "SAFE_VARIANCE_SENSITIVETY_KEY"

	// Time interval in seconds for each metrics agent ingestion.
	metricsAgentReportingIntervalSeconds = 60
)

var (
	safeVarianceMargin      float64
	safeVarianceSensitivity float64
)

type StatisticsBasedLoadVariationBalancing struct {
	handle    framework.Handle
	cache     *cache.PodAssignEventHandler
	collector *collector.Collector
}

func (pl *StatisticsBasedLoadVariationBalancing) Name() string {
	return Name
}

// New : create an instance of a StatisticsBasedLoadVariationBalancing plugin
func New(obj runtime.Object, handle framework.Handle) (framework.Plugin, error) {
	klog.V(4).InfoS("Creating new instance of the StatisticsBasedLoadVariationBalancing plugin")

	collector, err := collector.NewCollector()
	if err != nil {
		return nil, err
	}

	var ok bool
	var ss string
	ss, ok = os.LookupEnv(SafeVarianceMarginKey)
	if !ok {
		safeVarianceMargin = config.DefaultSafeVarainceMargin
	} else {
		safeVarianceMargin, err = strconv.ParseFloat(ss, 64)
		if err != nil {
			panic(err)
		}
	}

	ss, ok = os.LookupEnv(SafeVarianceSensitivityKey)
	if !ok {
		safeVarianceSensitivity = config.DefaultSafeVarianceSensitivity
	} else {
		safeVarianceSensitivity, err = strconv.ParseFloat(ss, 64)
		if err != nil {
			panic(err)
		}
	}

	klog.V(4).InfoS("Using StatisticsBasedLoadVariationBalancing", "margin", safeVarianceMargin, "sensitivity", safeVarianceSensitivity)

	podAssignEventHandler := cache.New()
	podAssignEventHandler.AddToHandle(handle)

	pl := &StatisticsBasedLoadVariationBalancing{
		handle:    handle,
		cache:     podAssignEventHandler,
		collector: collector,
	}
	return pl, nil
}

func (pl *StatisticsBasedLoadVariationBalancing) Score(ctx context.Context, cycleState *framework.CycleState, pod *v1.Pod, nodeName string) (int64, *framework.Status) {
	klog.V(6).InfoS("Calculating score", "pod", klog.KObj(pod), "nodeName", nodeName)
	score := framework.MinNodeScore
	nodeInfo, err := pl.handle.SnapshotSharedLister().NodeInfos().Get(nodeName)
	node := nodeInfo.Node()
	if err != nil {
		return score, framework.NewStatus(framework.Error, fmt.Sprintf("getting node %q from Snapshot: %v", nodeName, err))
	}
	// lack of label
	_, ok := pod.Labels[config.DefaultCourseLabel]
	if !ok {
		klog.InfoS("This pod has no label of", config.DefaultCourseLabel, ", please add label; using minimum score", "nodeName", nodeName)
		return score, nil
	}
	// get node metrics
	metrics, window := pl.collector.GetNodeMetrics(nodeName)
	statistics, _ := pl.collector.GetAllStatistics()
	// if have no metrics use capacity instead
	if metrics == nil {
		klog.InfoS("Check network, Failed to get metrics for node; using DefaultMostLeastRequested", "nodeName", nodeName)
		return algorithm.DefaultMostLeastRequested(nodeInfo, pod)
	}
	// if have no statistics use request
	if statistics.StatisticsMap.IsNil() {
		klog.InfoS("lack of statistics; using RequestedBasedLoadVariation instead", "nodeName", nodeName)
		return pl.requestedBasedLoadVariation(node, pod, metrics, window)
	}

	// Todo base statisticLoadVariation

	return pl.statisticsbasedloadvariation(node, pod, metrics, statistics, window)
}

// ScoreExtensions : an interface for Score extended functionality
func (pl *StatisticsBasedLoadVariationBalancing) ScoreExtensions() framework.ScoreExtensions {
	return pl
}

// NormalizeScore : normalize scores
func (pl *StatisticsBasedLoadVariationBalancing) NormalizeScore(context.Context, *framework.CycleState, *v1.Pod, framework.NodeScoreList) *framework.Status {
	return nil
}

// base requested
func (pl *StatisticsBasedLoadVariationBalancing) requestedBasedLoadVariation(
	node *v1.Node,
	pod *v1.Pod,
	nodeMetrics *[]metricstype.Metric,
	metricWindow *metricstype.Window) (int64, *framework.Status) {
	// calculate CPU score
	nodeName := node.Name
	score := framework.MinNodeScore

	podRequest := resourcestats.GetResourceRequested(pod)

	scoreFunc := func(resourceType v1.ResourceName) (float64, bool) {
		resourceStats, resourceOk := resourcestats.CreateResourceStats(*nodeMetrics, node, podRequest, v1.ResourceCPU, resourcestats.ResourceType2MetricTypeMap[resourceType])
		if !resourceOk {
			return 0, false
		}
		resourceScore := algorithm.ComputeScore(resourceStats, safeVarianceMargin, safeVarianceSensitivity)
		klog.V(6).InfoS("requestedBasedLoadVariation Calculating", "pod", klog.KObj(pod), "nodeName", nodeName, resourceType, "Score", resourceScore)
		return resourceScore, true
	}
	// calculate total score
	totalScore := 100.0
	for tt, _ := range resourcestats.ResourceType2MetricTypeMap {
		s, v := scoreFunc(tt)
		if v {
			totalScore = math.Min(totalScore, s)
		}
	}

	score = int64(math.Round(totalScore))
	klog.V(6).InfoS("requestedBasedLoadVariation Calculating totalScore", "pod", klog.KObj(pod), "nodeName", nodeName, "totalScore", score)

	return score, nil
}

func (pl *StatisticsBasedLoadVariationBalancing) statisticsbasedloadvariation(
	node *v1.Node,
	pod *v1.Pod,
	nodeMetrics *[]metricstype.Metric,
	statistic *metricstype.StatisticsData,
	metricWindow *metricstype.Window,
) (int64, *framework.Status) {

	score := framework.MinNodeScore
	podLabel := pod.Labels[config.DefaultCourseLabel]
	nodeName := node.Name

	podRequest, valid := resourcestats.CreateStatisticsResource(statistic, podLabel)
	if !valid {
		return score, nil
	}

	requestList := make([]resourcestats.StatisticsResourceStatsMap, 0)
	requestList = append(requestList, *podRequest)

	for _, info := range pl.cache.ScheduledPodsCache[nodeName] {
		// If the time stamp of the scheduled pod is outside fetched metrics window, or it is within metrics reporting interval seconds, we predict util.
		// Note that the second condition doesn't guarantee metrics for that pod are not reported yet as the 0 <= t <= 2*metricsAgentReportingIntervalSeconds
		// t = metricsAgentReportingIntervalSeconds is taken as average case and it doesn't hurt us much if we are
		// counting metrics twice in case actual t is less than metricsAgentReportingIntervalSeconds
		if info.Timestamp.Unix() > metricWindow.End || info.Timestamp.Unix() <= metricWindow.End &&
			(metricWindow.End-info.Timestamp.Unix()) < metricsAgentReportingIntervalSeconds {
			re, valid := resourcestats.CreateStatisticsResource(statistic, info.Pod.Labels[config.DefaultCourseLabel])
			if valid {
				requestList = append(requestList, *re)
			}
			klog.V(6).InfoS("get statistics for pod", "podName", info.Pod.Name, "statistics", re)
		}
	}

	scoreFunc := func(resourceType v1.ResourceName) (float64, bool) {
		resourceStats, resourceOk := resourcestats.CreateResourceStatsFromStatistics(*nodeMetrics, node, requestList, v1.ResourceCPU, resourcestats.ResourceType2MetricTypeMap[resourceType])
		if !resourceOk {
			return 0, false
		}
		resourceScore := algorithm.ComputeScore(resourceStats, safeVarianceMargin, safeVarianceSensitivity)
		klog.V(6).InfoS("requestedBasedLoadVariation Calculating", "pod", klog.KObj(pod), "nodeName", nodeName, resourceType, "Score", resourceScore)
		return resourceScore, true
	}
	// calculate total score
	totalScore := 100.0
	for tt := range resourcestats.ResourceType2MetricTypeMap {
		s, v := scoreFunc(tt)
		if v {
			totalScore = math.Min(totalScore, s)
		}
	}

	score = int64(math.Round(totalScore))
	klog.V(6).InfoS("requestedBasedLoadVariation Calculating totalScore", "pod", klog.KObj(pod), "nodeName", nodeName, "totalScore", score)

	return score, nil
}
