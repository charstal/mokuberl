package rlscheduler

import (
	framework "k8s.io/kubernetes/pkg/scheduler/framework/v1alpha1"
)

const (
	requestSecond = 20
	Name          = "RLScheduler"
)

type RLScheduler struct {
	handle framework.FrameworkHandler
}

func New(obj runtime.Object, handle framework.FrameworkHandle) (framework.Plugin, error) {

}
