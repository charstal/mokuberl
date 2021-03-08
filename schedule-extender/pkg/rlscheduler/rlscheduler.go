package rlscheduler

import (
	"k8s.io/apimachinery/pkg/runtime"
	framework "k8s.io/kubernetes/pkg/scheduler/framework/v1alpha1"
)

const (
	requestSecond = 20
	Name          = "RLScheduler"
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
