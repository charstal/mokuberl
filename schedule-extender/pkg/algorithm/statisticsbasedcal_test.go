package algorithm

import (
	"math"
	"testing"

	"github.com/charstal/load-monitor/pkg/metricstype"
	"github.com/charstal/schedule-extender/pkg/resourcestats"
	"github.com/stretchr/testify/assert"

	v1 "k8s.io/api/core/v1"
	st "k8s.io/kubernetes/pkg/scheduler/testing"
)

var (
	metrics = []metricstype.Metric{
		{
			Name:     "no_name",
			Type:     metricstype.CPU,
			Operator: "",
			Value:    40,
		},
		{
			Name:     "cpu_running_avg",
			Type:     metricstype.CPU,
			Operator: metricstype.Average,
			Value:    40,
		},
		{
			Name:     "cpu_running_std",
			Type:     metricstype.CPU,
			Operator: metricstype.Std,
			Value:    36,
		},
		{
			Name:     "mem_running_avg",
			Type:     metricstype.Memory,
			Operator: metricstype.Average,
			Value:    20,
		},
		{
			Name:     "mem_running_std",
			Type:     metricstype.Memory,
			Operator: metricstype.Std,
			Value:    10,
		},
	}

	nodeResources = map[v1.ResourceName]string{
		v1.ResourceCPU:    "1000m",
		v1.ResourceMemory: "1Gi",
	}

	node0 = st.MakeNode().Name("node0").Capacity(nodeResources).Obj()
)

func TestComputeScore(t *testing.T) {
	tests := []struct {
		name        string
		margin      float64
		sensitivity float64
		rs          *resourcestats.ResourceStats
		expected    int64
	}{
		{
			name:        "valid data",
			margin:      1,
			sensitivity: 1,
			rs: &resourcestats.ResourceStats{
				Capacity:  100,
				Req:       10,
				UsedAvg:   40,
				UsedStdev: 36,
			},
			expected: 57,
		},
		{
			name:        "zero capacity",
			margin:      1,
			sensitivity: 2,
			rs: &resourcestats.ResourceStats{
				Capacity:  0,
				Req:       10,
				UsedAvg:   40,
				UsedStdev: 36,
			},
			expected: 0,
		},
		{
			name:        "negative usedAvg",
			margin:      1,
			sensitivity: 2,
			rs: &resourcestats.ResourceStats{
				Capacity:  100,
				Req:       10,
				UsedAvg:   -40,
				UsedStdev: 36,
			},
			expected: 65,
		},
		{
			name:        "large usedAvg",
			margin:      1,
			sensitivity: 2,
			rs: &resourcestats.ResourceStats{
				Capacity:  100,
				Req:       10,
				UsedAvg:   200,
				UsedStdev: 36,
			},
			expected: 20,
		},
		{
			name:        "negative usedStdev",
			margin:      1,
			sensitivity: 2,
			rs: &resourcestats.ResourceStats{
				Capacity:  100,
				Req:       10,
				UsedAvg:   40,
				UsedStdev: -36,
			},
			expected: 75,
		},
		{
			name:        "large usedStdev",
			margin:      1,
			sensitivity: 2,
			rs: &resourcestats.ResourceStats{
				Capacity:  100,
				Req:       10,
				UsedAvg:   40,
				UsedStdev: 120,
			},
			expected: 25,
		},
		{
			name:        "large usedAvg",
			margin:      1,
			sensitivity: 2,
			rs: &resourcestats.ResourceStats{
				Capacity:  100,
				Req:       10,
				UsedAvg:   200,
				UsedStdev: 36,
			},
			expected: 20,
		},
		{
			name:        "negative margin",
			margin:      -1,
			sensitivity: 1,
			rs: &resourcestats.ResourceStats{
				Capacity:  100,
				Req:       10,
				UsedAvg:   40,
				UsedStdev: 36,
			},
			expected: 75,
		},
		{
			name:        "negative sensitivity",
			margin:      1,
			sensitivity: -1,
			rs: &resourcestats.ResourceStats{
				Capacity:  100,
				Req:       10,
				UsedAvg:   40,
				UsedStdev: 36,
			},
			expected: 57,
		},
		{
			name:        "zero sensitivity",
			margin:      1,
			sensitivity: 0,
			rs: &resourcestats.ResourceStats{
				Capacity:  100,
				Req:       10,
				UsedAvg:   40,
				UsedStdev: 36,
			},
			expected: 75,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			response := int64(math.Round(ComputeScore(tt.rs, tt.margin, tt.sensitivity)))
			assert.Equal(t, tt.expected, response)
		})
	}
}
