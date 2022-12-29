package rlscheduler

import (
	"context"
	"fmt"

	"github.com/charstal/schedule-extender/apis/config"
	"github.com/charstal/schedule-extender/pkg/algorithm"
	"github.com/charstal/schedule-extender/pkg/rlclient"
	v1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/klog/v2"
	"k8s.io/kubernetes/pkg/scheduler/framework"
)

const (
	Name = "RLScheduler"
)

type RLScheduler struct {
	handle framework.Handle
	client *rlclient.RLClient
}

func (pl *RLScheduler) Name() string {
	return Name
}

func New(obj runtime.Object, handle framework.Handle) (framework.Plugin, error) {
	klog.V(4).InfoS("Creating new instance of the RL Scheduler plugin")

	client, err := rlclient.NewRLClient()
	if err != nil {
		return nil, err
	}

	pl := &RLScheduler{
		handle: handle,
		client: client,
	}
	return pl, nil
}

func (pl *RLScheduler) PreScore(ctx context.Context, state *framework.CycleState, pod *v1.Pod, nodes []*v1.Node) *framework.Status {

	if !pl.client.Valid() {
		return framework.NewStatus(framework.Error, "rl server is unavaliable")
	}
	nodeNameList := make([]string, 0)
	podName := pod.Name
	podLabel, ok := pod.Labels[config.DefaultCourseLabel]
	if !ok {
		return framework.NewStatus(framework.Error, fmt.Sprintf("This pod has no label of %s , please check label, podname %s", config.DefaultCourseLabel, podName))
	}
	// Todo 可以进一步优化发送node的数量
	for _, node := range nodes {
		nodeNameList = append(nodeNameList, node.Name)
	}

	klog.V(6).InfoS("Prescore phase for pod", podName, "pod label", podLabel, "node list", nodeNameList)

	pl.client.Predict(podName, podLabel, nodeNameList)

	return nil
}

// if rl server is invalid, use DefaultMostLeastRequested algorithm
// if valid, the MaxScore for selected, other MinScore
func (pl *RLScheduler) Score(ctx context.Context, cycleState *framework.CycleState, pod *v1.Pod, nodeName string) (int64, *framework.Status) {

	klog.V(6).InfoS("rl for", "pod", klog.KObj(pod), "nodeName", nodeName)
	podName := pod.Name
	score := framework.MinNodeScore
	selectedNodeName, ok := pl.client.Get(podName)
	if !ok {
		nodeInfo, err := pl.handle.SnapshotSharedLister().NodeInfos().Get(nodeName)
		if err != nil {
			return score, framework.NewStatus(framework.Error, fmt.Sprintf("getting node %q from Snapshot: %v", nodeName, err))
		}
		klog.V(6).Info("rl server is invalid use DefaultMostLeastRequested instead of")
		return algorithm.DefaultMostLeastRequested(nodeInfo, pod)
	}
	if selectedNodeName == nodeName {
		return framework.MaxNodeScore, nil
	} else {
		return framework.MinNodeScore, nil
	}
}

// ScoreExtensions : an interface for Score extended functionality
func (pl *RLScheduler) ScoreExtensions() framework.ScoreExtensions {
	return pl
}

// NormalizeScore : normalize scores
func (pl *RLScheduler) NormalizeScore(context.Context, *framework.CycleState, *v1.Pod, framework.NodeScoreList) *framework.Status {
	return nil
}
