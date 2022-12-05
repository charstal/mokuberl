package demoscheduler

import (
	"context"

	v1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/klog/v2"
	"k8s.io/kubernetes/pkg/scheduler/framework"
)

const (
	Name = "Demoscheduler"
)

type DemoScheduler struct {
	handle framework.Handle
}

func New(obj runtime.Object, handle framework.Handle) (framework.Plugin, error) {
	pl := &DemoScheduler{
		handle: handle,
	}

	return pl, nil
}

// func (pl *DemoScheduler) Less(*framework.QueuedPodInfo, *framework.QueuedPodInfo) bool {
// 	klog.V(6).Infof("")
// 	return true
// }

func (pl *DemoScheduler) PreFilter(ctx context.Context, state *framework.CycleState, pod *v1.Pod) *framework.Status {
	klog.V(6).Infof("%s Prefilter", pod.Name)
	return nil
}

func (pl *DemoScheduler) AddPod(ctx context.Context, state *framework.CycleState, podToSchedule *v1.Pod, podInfoToAdd *framework.PodInfo, nodeInfo *framework.NodeInfo) *framework.Status {
	klog.V(6).Infof("%s AddPod", podToSchedule.Name)
	return nil
}

func (pl *DemoScheduler) RemovePod(ctx context.Context, state *framework.CycleState, podToSchedule *v1.Pod, podInfoToRemove *framework.PodInfo, nodeInfo *framework.NodeInfo) *framework.Status {
	klog.V(6).Infof("%s RemovePod", podToSchedule.Name)
	return nil
}

func (pl *DemoScheduler) Filter(ctx context.Context, state *framework.CycleState, pod *v1.Pod, nodeInfo *framework.NodeInfo) *framework.Status {
	klog.V(6).Infof("%s Filter", pod)
	return nil
}

func (pl *DemoScheduler) PostFilter(ctx context.Context, state *framework.CycleState, pod *v1.Pod, filteredNodeStatusMap framework.NodeToStatusMap) (*framework.PostFilterResult, *framework.Status) {
	klog.V(6).Infof("%s PostFilter", pod.Name)
	return nil, nil
}

func (pl *DemoScheduler) PreScore(ctx context.Context, state *framework.CycleState, pod *v1.Pod, nodes []*v1.Node) *framework.Status {
	klog.V(6).Infof("%s PreScore", pod.Name)
	return nil
}

func (pl *DemoScheduler) Score(ctx context.Context, state *framework.CycleState, pod *v1.Pod, nodeName string) (int64, *framework.Status) {
	klog.V(6).Infof("%s Score", pod.Name)
	return 100, nil
}

func (pl *DemoScheduler) Reserve(ctx context.Context, state *framework.CycleState, pod *v1.Pod, nodeName string) *framework.Status {
	klog.V(6).Infof("%s Reserve", pod.Name)
	return nil
}

func (pl *DemoScheduler) Unreserve(ctx context.Context, state *framework.CycleState, pod *v1.Pod, nodeName string) {
	klog.V(6).Infof("%s Unreserve", pod.Name)

}

// func (pl *DemoScheduler) PreBind(ctx context.Context, state *CycleState, p *v1.Pod, nodeName string) *Status {

// }

// func (pl *DemoScheduler) PostBind(ctx context.Context, state *CycleState, p *v1.Pod, nodeName string) {

// }

// func (pl *DemoScheduler) Permit(ctx context.Context, state *framework.CycleState, p *v1.Pod, nodeName string) (*framework.Status, time.Duration) {

// }

// func (pl *DemoScheduler) Bind(ctx context.Context, state *CycleState, p *v1.Pod, nodeName string) *Status {

// }

func (pl *DemoScheduler) PreFilterExtensions() framework.PreFilterExtensions {
	return pl
}

func (pl *DemoScheduler) PreFilterPlugin() framework.PreFilterPlugin {
	return pl
}

func (pl *DemoScheduler) ScoreExtensions() framework.ScoreExtensions {
	return pl
}

func (pl *DemoScheduler) NormalizeScore(ctx context.Context, state *framework.CycleState, p *v1.Pod, scores framework.NodeScoreList) *framework.Status {
	return nil
}

func (pl *DemoScheduler) Name() string {
	return Name
}
