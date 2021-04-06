package rlscheduler

import (
	"context"
	"math"
	"strconv"

	"github.com/charstal/schedule-extender/apis/config"
	"github.com/charstal/schedule-extender/pkg/modelclient"
	v1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/klog/v2"
	framework "k8s.io/kubernetes/pkg/scheduler/framework/v1alpha1"
)

const (
	requestSecond = 20
	Name          = "RLScheduler"
)

var (
	reqiestsMilliMemory   = config.DefaultRequestsMilliMemory
	requestsMilliCores    = config.DefaultRequestsMilliCores
	requestsMultiplier, _ = strconv.ParseFloat(config.DefaultRequestsMultiplier, 64)
	client, _             = modelclient.GetClient()
)

type RLScheduler struct {
	handle framework.FrameworkHandle
}

func (pl *RLScheduler) Name() string {
	return Name
}

func New(obj runtime.Object, handle framework.FrameworkHandle) (framework.Plugin, error) {
	pl := &RLScheduler{
		handle: handle,
	}

	return pl, nil
}

func (pl *RLScheduler) ScoreExtensions() framework.ScoreExtensions {
	return pl
}

func (pl *RLScheduler) NormalizeScore(context.Context, *framework.CycleState, *v1.Pod, framework.NodeScoreList) *framework.Status {
	return nil
}

func (pl *RLScheduler) Score(ctx context.Context, cycleState *framework.CycleState, pod *v1.Pod, nodeName string) (int64, *framework.Status) {
	var curPodCPUUsage, curPodMemoryUsage int64
	for _, container := range pod.Spec.Containers {
		curPodCPUUsage += cpuPredictUtilisation(&container)
		curPodMemoryUsage += memoryPredictUtilisation(&container)
	}

	klog.V(6).Infof("cpu predicted utilisation for pod %v: %v", pod.Name, curPodCPUUsage)
	klog.V(6).Infof("memory predicted utilisation for pod %v: %v", pod.Name, curPodMemoryUsage)

	if pod.Spec.Overhead != nil {
		curPodCPUUsage += pod.Spec.Overhead.Cpu().MilliValue()
		curPodMemoryUsage += pod.Spec.Overhead.Memory().MilliValue()
	}
	var score int64 = 100
	retNodeName := client.Predict(modelclient.Resource{
		Cpu:    modelclient.CpuUnit(curPodCPUUsage),
		Memory: modelclient.MemoryUnit(curPodMemoryUsage),
	}, "", pod.Name)
	klog.Infof("predict node for pod %v: %v", pod.Name, retNodeName)
	if retNodeName != nodeName {
		score = 0
	}

	return score, nil
}

// Predict utilisation for a container based on its requests/limits
func cpuPredictUtilisation(container *v1.Container) int64 {
	if _, ok := container.Resources.Limits[v1.ResourceCPU]; ok {
		return container.Resources.Limits.Cpu().MilliValue()
	} else if _, ok := container.Resources.Requests[v1.ResourceCPU]; ok {
		return int64(math.Round(float64(container.Resources.Requests.Cpu().MilliValue()) * requestsMultiplier))
	} else {
		return requestsMilliCores
	}
}

func memoryPredictUtilisation(container *v1.Container) int64 {
	if _, ok := container.Resources.Limits[v1.ResourceMemory]; ok {
		return container.Resources.Limits.Memory().MilliValue()
	} else if _, ok := container.Resources.Requests[v1.ResourceMemory]; ok {
		return int64(math.Round(float64(container.Resources.Requests.Memory().MilliValue()) * requestsMultiplier))
	} else {
		return reqiestsMilliMemory
	}
}
