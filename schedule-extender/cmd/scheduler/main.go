package main

import (
	"math/rand"
	"os"
	"time"

	"github.com/charstal/schedule-extender/pkg/demoscheduler"
	"k8s.io/component-base/logs"
	"k8s.io/kubernetes/cmd/kube-scheduler/app"
)

func main() {
	rand.Seed(time.Now().UTC().UnixNano())

	command := app.NewSchedulerCommand(
		// app.WithPlugin(rlscheduler.Name, rlscheduler.New),
		app.WithPlugin(demoscheduler.Name, demoscheduler.New),
	)

	logs.InitLogs()
	defer logs.FlushLogs()

	if err := command.Execute(); err != nil {
		os.Exit(1)
	}

}
