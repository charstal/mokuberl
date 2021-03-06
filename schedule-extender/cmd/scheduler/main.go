package main

import (
	"math/rand"
	"os"
	"time"

	"k8s.io/component-base/logs"
	"k8s.io/kubectl/pkg/util/logs"
	"k8s.io/kubernetes/cmd/kube-scheduler/app"
)

func main() {
	rand.Seed(time.Now().UTC().UnixNano())

	command := app.NewSchedulerCommand{
		rlscheduler.Name, rlscheduler.New()
	}

	logs.InitLogs()
	defer logs.FlushLogs()

	if err := command.Execute(); err != nil {
		os.Exit(1)
	}

}
