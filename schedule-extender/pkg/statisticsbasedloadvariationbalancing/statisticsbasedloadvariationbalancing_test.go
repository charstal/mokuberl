package statisticsbasedloadvariationbalancing

import (
	"context"
	"encoding/json"
	"log"
	"net/http"
	"net/http/httptest"
	"os"
	"strconv"
	"testing"
	"time"

	"github.com/charstal/load-monitor/pkg/metricstype"
	"github.com/stretchr/testify/assert"

	v1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/resource"
	"k8s.io/client-go/informers"
	testClientSet "k8s.io/client-go/kubernetes/fake"
	"k8s.io/kubernetes/pkg/scheduler/apis/config"
	"k8s.io/kubernetes/pkg/scheduler/framework"
	"k8s.io/kubernetes/pkg/scheduler/framework/plugins/defaultbinder"
	"k8s.io/kubernetes/pkg/scheduler/framework/plugins/queuesort"
	"k8s.io/kubernetes/pkg/scheduler/framework/runtime"
	st "k8s.io/kubernetes/pkg/scheduler/testing"

	testutil "sigs.k8s.io/scheduler-plugins/test/util"
)

var _ framework.SharedLister = &testSharedLister{}

type testSharedLister struct {
	nodes       []*v1.Node
	nodeInfos   []*framework.NodeInfo
	nodeInfoMap map[string]*framework.NodeInfo
}

func (f *testSharedLister) NodeInfos() framework.NodeInfoLister {
	return f
}

func (f *testSharedLister) List() ([]*framework.NodeInfo, error) {
	return f.nodeInfos, nil
}

func (f *testSharedLister) HavePodsWithAffinityList() ([]*framework.NodeInfo, error) {
	return nil, nil
}

func (f *testSharedLister) HavePodsWithRequiredAntiAffinityList() ([]*framework.NodeInfo, error) {
	return nil, nil
}

func (f *testSharedLister) Get(nodeName string) (*framework.NodeInfo, error) {
	return f.nodeInfoMap[nodeName], nil
}

func TestNew(t *testing.T) {
	watcherResponse := metricstype.WatcherMetrics{}
	server := httptest.NewServer(http.HandlerFunc(func(resp http.ResponseWriter, req *http.Request) {
		bytes, err := json.Marshal(watcherResponse)
		assert.Nil(t, err)
		resp.Write(bytes)
	}))
	defer server.Close()

	registeredPlugins := []st.RegisterPluginFunc{
		st.RegisterBindPlugin(defaultbinder.Name, defaultbinder.New),
		st.RegisterQueueSortPlugin(queuesort.Name, queuesort.New),
		st.RegisterScorePlugin(Name, New, 1),
	}

	cs := testClientSet.NewSimpleClientset()
	informerFactory := informers.NewSharedInformerFactory(cs, 0)
	snapshot := newTestSharedLister(nil, nil)
	fh, err := testutil.NewFramework(registeredPlugins, []config.PluginConfig{},
		"default-scheduler", runtime.WithClientSet(cs),
		runtime.WithInformerFactory(informerFactory), runtime.WithSnapshotSharedLister(snapshot))
	assert.Nil(t, err)
	os.Setenv("LOAD_MONITOR_ADDRESS", server.URL)
	p, err := New(nil, fh)
	assert.NotNil(t, p)
	assert.Nil(t, err)

}

func TestScore(t *testing.T) {

	nodeResources := map[v1.ResourceName]string{
		v1.ResourceCPU:    "1000m",
		v1.ResourceMemory: "1Gi",
	}

	var mega int64 = 1024 * 1024

	tests := []struct {
		test            string
		pod             *v1.Pod
		nodes           []*v1.Node
		watcherResponse metricstype.WatcherMetrics
		expected        framework.NodeScoreList
	}{
		{
			test: "no label",
			pod:  st.MakePod().Name("p").Obj(),
			nodes: []*v1.Node{
				st.MakeNode().Name("node-1").Capacity(nodeResources).Obj(),
			},
			watcherResponse: metricstype.WatcherMetrics{},
			expected: []framework.NodeScore{
				{Name: "node-1", Score: 0},
			},
		},
		{
			test: "has label use DefaultMostLeastRequested without request",
			pod:  st.MakePod().Name("p").Label("course_id", "a").Obj(),
			nodes: []*v1.Node{
				st.MakeNode().Name("node-1").Capacity(nodeResources).Obj(),
			},
			watcherResponse: metricstype.WatcherMetrics{},
			expected: []framework.NodeScore{
				{Name: "node-1", Score: 100},
			},
		},
		{
			test: "has label use DefaultMostLeastRequested with request1",
			pod:  getPodWithContainersAndOverhead(0, 0, 0, []int64{100}, []int64{512 * mega}, map[string]string{"course_id": "a"}),
			nodes: []*v1.Node{
				st.MakeNode().Name("node-1").Capacity(nodeResources).Obj(),
			},
			watcherResponse: metricstype.WatcherMetrics{},
			expected: []framework.NodeScore{
				{Name: "node-1", Score: 50},
			},
		},
		{
			test: "has label use DefaultMostLeastRequested with request2",
			pod:  getPodWithContainersAndOverhead(0, 0, 0, []int64{230}, []int64{100 * mega}, map[string]string{"course_id": "a"}),
			nodes: []*v1.Node{
				st.MakeNode().Name("node-1").Capacity(nodeResources).Obj(),
			},
			watcherResponse: metricstype.WatcherMetrics{},
			expected: []framework.NodeScore{
				{Name: "node-1", Score: 77},
			},
		},
		{
			test: "new node with 2m timeout use DefaultMostLeastRequested",
			pod:  getPodWithContainersAndOverhead(0, 0, 0, []int64{}, []int64{}, map[string]string{"course_id": "a"}),
			nodes: []*v1.Node{
				st.MakeNode().Name("node-1").Capacity(nodeResources).Obj(),
			},
			watcherResponse: metricstype.WatcherMetrics{
				Window: metricstype.Window{End: time.Now().Unix() - 60*2},
				Data: metricstype.Data{
					NodeMetricsMap: map[string]metricstype.NodeMetrics{
						"node-1": {
							Metrics: []metricstype.Metric{
								{
									Type:     metricstype.CPU,
									Operator: metricstype.Average,
									Value:    50,
								},
							},
						},
					},
				},
			},
			expected: []framework.NodeScore{
				{Name: "node-1", Score: 100},
			},
		},
		{
			test: "new node no timeout use DefaultMostLeastRequested",
			pod:  getPodWithContainersAndOverhead(0, 0, 0, []int64{}, []int64{}, map[string]string{"course_id": "a"}),
			nodes: []*v1.Node{
				st.MakeNode().Name("node-1").Capacity(nodeResources).Obj(),
			},
			watcherResponse: metricstype.WatcherMetrics{
				Window: metricstype.Window{End: time.Now().Unix()},
				Data: metricstype.Data{
					NodeMetricsMap: map[string]metricstype.NodeMetrics{
						"node-1": {
							Metrics: []metricstype.Metric{
								{
									Type:     metricstype.CPU,
									Operator: metricstype.Average,
									Value:    50,
								},
							},
						},
					},
				},
			},
			expected: []framework.NodeScore{
				{Name: "node-1", Score: 75},
			},
		},
		{
			test: "hot node",
			pod:  st.MakePod().Name("p").Label("course_id", "a").Obj(),
			nodes: []*v1.Node{

				st.MakeNode().Name("node-1").Capacity(nodeResources).Obj(),
			},
			watcherResponse: metricstype.WatcherMetrics{
				Window: metricstype.Window{End: time.Now().Unix()},
				Data: metricstype.Data{
					NodeMetricsMap: map[string]metricstype.NodeMetrics{
						"node-1": {
							Metrics: []metricstype.Metric{
								{
									Type:     metricstype.CPU,
									Operator: metricstype.Average,
									Value:    100,
								},
							},
						},
					},
				},
			},
			expected: []framework.NodeScore{
				{Name: "node-1", Score: 50},
			},
		},
		{
			test: "average and stDev metrics",
			pod:  getPodWithContainersAndOverhead(0, 0, 0, []int64{200}, []int64{256 * mega}, map[string]string{"course_id": "a"}),
			nodes: []*v1.Node{
				st.MakeNode().Name("node-1").Capacity(nodeResources).Obj(),
			},
			watcherResponse: metricstype.WatcherMetrics{
				Window: metricstype.Window{End: time.Now().Unix()},
				Data: metricstype.Data{
					NodeMetricsMap: map[string]metricstype.NodeMetrics{
						"node-1": {
							Metrics: []metricstype.Metric{
								{
									Type:     metricstype.CPU,
									Operator: metricstype.Average,
									Value:    30,
								},
								{
									Type:     metricstype.CPU,
									Operator: metricstype.Std,
									Value:    16,
								},
							},
						},
					},
				},
			},
			expected: []framework.NodeScore{
				{Name: "node-1", Score: 67},
			},
		},
		{
			test: "CPU and Memory metrics",
			pod:  getPodWithContainersAndOverhead(0, 0, 0, []int64{100}, []int64{512 * mega}, map[string]string{"course_id": "a"}),
			nodes: []*v1.Node{
				st.MakeNode().Name("node-1").Capacity(nodeResources).Obj(),
			},
			watcherResponse: metricstype.WatcherMetrics{
				Window: metricstype.Window{End: time.Now().Unix()},
				Data: metricstype.Data{
					NodeMetricsMap: map[string]metricstype.NodeMetrics{
						"node-1": {
							Metrics: []metricstype.Metric{
								{
									Type:     metricstype.CPU,
									Operator: metricstype.Average,
									Value:    40,
								},
								{
									Type:     metricstype.CPU,
									Operator: metricstype.Std,
									Value:    16,
								},
								{
									Type:     metricstype.Memory,
									Operator: metricstype.Average,
									Value:    50,
								},
								{
									Type:     metricstype.Memory,
									Operator: metricstype.Std,
									Value:    10,
								},
							},
						},
					},
				},
			},
			expected: []framework.NodeScore{
				{Name: "node-1", Score: 45},
			},
		},
		{
			test: "pick worst case: CPU or Memory",
			pod:  getPodWithContainersAndOverhead(0, 0, 0, []int64{100}, []int64{512 * mega}, map[string]string{"course_id": "a"}),
			nodes: []*v1.Node{
				st.MakeNode().Name("node-1").Capacity(nodeResources).Obj(),
			},
			watcherResponse: metricstype.WatcherMetrics{
				Window: metricstype.Window{End: time.Now().Unix()},
				Data: metricstype.Data{
					NodeMetricsMap: map[string]metricstype.NodeMetrics{
						"node-1": {
							Metrics: []metricstype.Metric{
								{
									Type:     metricstype.CPU,
									Operator: metricstype.Average,
									Value:    80,
								},
								{
									Type:     metricstype.CPU,
									Operator: metricstype.Std,
									Value:    20,
								},
								{
									Type:     metricstype.Memory,
									Operator: metricstype.Average,
									Value:    25,
								},
								{
									Type:     metricstype.Memory,
									Operator: metricstype.Std,
									Value:    15,
								},
							},
						},
					},
				},
			},
			expected: []framework.NodeScore{
				{Name: "node-1", Score: 45},
			},
		},
		{
			test: "only have statistic",
			pod:  st.MakePod().Name("p").Label("course_id", "a").Obj(),
			nodes: []*v1.Node{
				st.MakeNode().Name("node-1").Capacity(nodeResources).Obj(),
			},
			watcherResponse: metricstype.WatcherMetrics{
				Window: metricstype.Window{End: time.Now().Unix()},
				Statistics: metricstype.StatisticsData{
					StatisticsMap: map[string]metricstype.NodeMetrics{
						"all": {
							Metrics: []metricstype.Metric{
								{
									Type:     metricstype.CPU,
									Operator: metricstype.Average,
									Value:    10,
									Unit:     metricstype.M,
								},
							},
						},
					},
				},
			},
			expected: []framework.NodeScore{
				{Name: "node-1", Score: 100},
			},
		},
		{
			test: "404 resp from watcher",
			pod:  st.MakePod().Name("p").Label("course_id", "a").Obj(),
			nodes: []*v1.Node{
				st.MakeNode().Name("node-1").Capacity(nodeResources).Obj(),
			},
			watcherResponse: metricstype.WatcherMetrics{},
			expected: []framework.NodeScore{
				{Name: "node-1", Score: 100},
			},
		},
		{
			test: "statisticsbasedloadvariation pod label is in statistic with cpu",
			pod:  st.MakePod().Name("p").Label("course_id", "a").Obj(),
			nodes: []*v1.Node{
				st.MakeNode().Name("node-1").Capacity(nodeResources).Obj(),
			},
			watcherResponse: metricstype.WatcherMetrics{
				Window: metricstype.Window{End: time.Now().Unix()},
				Data: metricstype.Data{
					NodeMetricsMap: map[string]metricstype.NodeMetrics{
						"node-1": {
							Metrics: []metricstype.Metric{
								{
									Type:     metricstype.CPU,
									Operator: metricstype.Average,
									Value:    40,
								},
								{
									Type:     metricstype.CPU,
									Operator: metricstype.Std,
									Value:    16,
								},
							},
						},
					},
				},
				Statistics: metricstype.StatisticsData{
					StatisticsMap: map[string]metricstype.NodeMetrics{
						"a": {
							Metrics: []metricstype.Metric{
								{
									Type:     metricstype.CPU,
									Operator: metricstype.Average,
									Value:    100,
									Unit:     metricstype.M,
								},
								{
									Type:     metricstype.CPU,
									Operator: metricstype.Std,
									Value:    10,
									Unit:     metricstype.M,
								},
							},
						},
					},
				},
			},
			expected: []framework.NodeScore{
				{Name: "node-1", Score: 67},
			},
		},
		{
			test: "statisticsbasedloadvariation pod label is not in statistic",
			pod:  st.MakePod().Name("p").Label("course_id", "a").Obj(),
			nodes: []*v1.Node{
				st.MakeNode().Name("node-1").Capacity(nodeResources).Obj(),
			},
			watcherResponse: metricstype.WatcherMetrics{
				Window: metricstype.Window{End: time.Now().Unix()},
				Data: metricstype.Data{
					NodeMetricsMap: map[string]metricstype.NodeMetrics{
						"node-1": {
							Metrics: []metricstype.Metric{
								{
									Type:     metricstype.CPU,
									Operator: metricstype.Average,
									Value:    40,
								},
								{
									Type:     metricstype.CPU,
									Operator: metricstype.Std,
									Value:    16,
								},
							},
						},
					},
				},
				Statistics: metricstype.StatisticsData{
					StatisticsMap: map[string]metricstype.NodeMetrics{
						"all": {
							Metrics: []metricstype.Metric{
								{
									Type:     metricstype.CPU,
									Operator: metricstype.Average,
									Value:    100,
									Unit:     metricstype.M,
								},
								{
									Type:     metricstype.CPU,
									Operator: metricstype.Std,
									Value:    10,
									Unit:     metricstype.M,
								},
							},
						},
					},
				},
			},
			expected: []framework.NodeScore{
				{Name: "node-1", Score: 67},
			},
		},
		{
			test: "statisticsbasedloadvariation pod label is in statistic with cpu and the std exceed",
			pod:  st.MakePod().Name("p").Label("course_id", "a").Obj(),
			nodes: []*v1.Node{
				st.MakeNode().Name("node-1").Capacity(nodeResources).Obj(),
			},
			watcherResponse: metricstype.WatcherMetrics{
				Window: metricstype.Window{End: time.Now().Unix()},
				Data: metricstype.Data{
					NodeMetricsMap: map[string]metricstype.NodeMetrics{
						"node-1": {
							Metrics: []metricstype.Metric{
								{
									Type:     metricstype.CPU,
									Operator: metricstype.Average,
									Value:    40,
								},
								{
									Type:     metricstype.CPU,
									Operator: metricstype.Std,
									Value:    16,
								},
							},
						},
					},
				},
				Statistics: metricstype.StatisticsData{
					StatisticsMap: map[string]metricstype.NodeMetrics{
						"a": {
							Metrics: []metricstype.Metric{
								{
									Type:     metricstype.CPU,
									Operator: metricstype.Average,
									Value:    100,
									Unit:     metricstype.M,
								},
								{
									Type:     metricstype.CPU,
									Operator: metricstype.Std,
									Value:    200,
									Unit:     metricstype.M,
								},
							},
						},
					},
				},
			},
			expected: []framework.NodeScore{
				{Name: "node-1", Score: 65},
			},
		},
		{
			test: "statisticsbasedloadvariation pod label is in statistic with cpu and mem",
			pod:  st.MakePod().Name("p").Label("course_id", "a").Obj(),
			nodes: []*v1.Node{
				st.MakeNode().Name("node-1").Capacity(nodeResources).Obj(),
			},
			watcherResponse: metricstype.WatcherMetrics{
				Window: metricstype.Window{End: time.Now().Unix()},
				Data: metricstype.Data{
					NodeMetricsMap: map[string]metricstype.NodeMetrics{
						"node-1": {
							Metrics: []metricstype.Metric{
								{
									Type:     metricstype.CPU,
									Operator: metricstype.Average,
									Value:    40,
								},
								{
									Type:     metricstype.CPU,
									Operator: metricstype.Std,
									Value:    16,
								},
								{
									Type:     metricstype.Memory,
									Operator: metricstype.Average,
									Value:    50,
								},
								{
									Type:     metricstype.Memory,
									Operator: metricstype.Std,
									Value:    10,
								},
							},
						},
					},
				},
				Statistics: metricstype.StatisticsData{
					StatisticsMap: map[string]metricstype.NodeMetrics{
						"a": {
							Metrics: []metricstype.Metric{
								{
									Type:     metricstype.CPU,
									Operator: metricstype.Average,
									Value:    100,
									Unit:     metricstype.M,
								},
								{
									Type:     metricstype.CPU,
									Operator: metricstype.Std,
									Value:    10,
									Unit:     metricstype.M,
								},
								{
									Type:     metricstype.Memory,
									Operator: metricstype.Average,
									Value:    256,
									Unit:     metricstype.MiB,
								},
								{
									Type:     metricstype.Memory,
									Operator: metricstype.Std,
									Value:    10,
									Unit:     metricstype.MiB,
								},
							},
						},
					},
				},
			},
			expected: []framework.NodeScore{
				{Name: "node-1", Score: 57},
			},
		},
		{
			test: "statisticsbasedloadvariation pod label is in statistic with cpu and mem and mem std excceed",
			pod:  st.MakePod().Name("p").Label("course_id", "a").Obj(),
			nodes: []*v1.Node{
				st.MakeNode().Name("node-1").Capacity(nodeResources).Obj(),
			},
			watcherResponse: metricstype.WatcherMetrics{
				Window: metricstype.Window{End: time.Now().Unix()},
				Data: metricstype.Data{
					NodeMetricsMap: map[string]metricstype.NodeMetrics{
						"node-1": {
							Metrics: []metricstype.Metric{
								{
									Type:     metricstype.CPU,
									Operator: metricstype.Average,
									Value:    40,
								},
								{
									Type:     metricstype.CPU,
									Operator: metricstype.Std,
									Value:    16,
								},
								{
									Type:     metricstype.Memory,
									Operator: metricstype.Average,
									Value:    50,
								},
								{
									Type:     metricstype.Memory,
									Operator: metricstype.Std,
									Value:    10,
								},
							},
						},
					},
				},
				Statistics: metricstype.StatisticsData{
					StatisticsMap: map[string]metricstype.NodeMetrics{
						"a": {
							Metrics: []metricstype.Metric{
								{
									Type:     metricstype.CPU,
									Operator: metricstype.Average,
									Value:    100,
									Unit:     metricstype.M,
								},
								{
									Type:     metricstype.CPU,
									Operator: metricstype.Std,
									Value:    10,
									Unit:     metricstype.M,
								},
								{
									Type:     metricstype.Memory,
									Operator: metricstype.Average,
									Value:    256,
									Unit:     metricstype.MiB,
								},
								{
									Type:     metricstype.Memory,
									Operator: metricstype.Std,
									Value:    128,
									Unit:     metricstype.MiB,
								},
							},
						},
					},
				},
			},
			expected: []framework.NodeScore{
				{Name: "node-1", Score: 56},
			},
		},
		{
			test: "statisticsbasedloadvariation pod label is in statistic with cpu and mem with network",
			pod:  st.MakePod().Name("p").Label("course_id", "a").Obj(),
			nodes: []*v1.Node{
				st.MakeNode().Name("node-1").Capacity(nodeResources).Obj(),
			},
			watcherResponse: metricstype.WatcherMetrics{
				Window: metricstype.Window{End: time.Now().Unix()},
				Data: metricstype.Data{
					NodeMetricsMap: map[string]metricstype.NodeMetrics{
						"node-1": {
							Metrics: []metricstype.Metric{
								{
									Type:     metricstype.CPU,
									Operator: metricstype.Average,
									Value:    40,
								},
								{
									Type:     metricstype.CPU,
									Operator: metricstype.Std,
									Value:    16,
								},
								{
									Type:     metricstype.Memory,
									Operator: metricstype.Average,
									Value:    50,
								},
								{
									Type:     metricstype.Memory,
									Operator: metricstype.Std,
									Value:    10,
								},
								{
									Name:  metricstype.NODE_NETWORK_TOTAL_BYTES_PERCENTAGE_EXCLUDING_LO,
									Value: 90,
								},
							},
						},
					},
				},
				Statistics: metricstype.StatisticsData{
					StatisticsMap: map[string]metricstype.NodeMetrics{
						"a": {
							Metrics: []metricstype.Metric{
								{
									Type:     metricstype.CPU,
									Operator: metricstype.Average,
									Value:    100,
									Unit:     metricstype.M,
								},
								{
									Type:     metricstype.CPU,
									Operator: metricstype.Std,
									Value:    10,
									Unit:     metricstype.M,
								},
								{
									Type:     metricstype.Memory,
									Operator: metricstype.Average,
									Value:    256,
									Unit:     metricstype.MiB,
								},
								{
									Type:     metricstype.Memory,
									Operator: metricstype.Std,
									Value:    10,
									Unit:     metricstype.MiB,
								},
							},
						},
					},
				},
			},
			expected: []framework.NodeScore{
				{Name: "node-1", Score: 10},
			},
		},
		{
			test: "statisticsbasedloadvariation pod label is in statistic with cpu and mem with network and disk",
			pod:  st.MakePod().Name("p").Label("course_id", "a").Obj(),
			nodes: []*v1.Node{
				st.MakeNode().Name("node-1").Capacity(nodeResources).Obj(),
			},
			watcherResponse: metricstype.WatcherMetrics{
				Window: metricstype.Window{End: time.Now().Unix()},
				Data: metricstype.Data{
					NodeMetricsMap: map[string]metricstype.NodeMetrics{
						"node-1": {
							Metrics: []metricstype.Metric{
								{
									Type:     metricstype.CPU,
									Operator: metricstype.Average,
									Value:    40,
								},
								{
									Type:     metricstype.CPU,
									Operator: metricstype.Std,
									Value:    16,
								},
								{
									Type:     metricstype.Memory,
									Operator: metricstype.Average,
									Value:    50,
								},
								{
									Type:     metricstype.Memory,
									Operator: metricstype.Std,
									Value:    10,
								},
								{
									Name:  metricstype.NODE_NETWORK_TOTAL_BYTES_PERCENTAGE_EXCLUDING_LO,
									Value: 90,
								},
								{
									Name:  metricstype.NODE_DISK_SATURATION,
									Value: 95,
								},
							},
						},
					},
				},
				Statistics: metricstype.StatisticsData{
					StatisticsMap: map[string]metricstype.NodeMetrics{
						"a": {
							Metrics: []metricstype.Metric{
								{
									Type:     metricstype.CPU,
									Operator: metricstype.Average,
									Value:    100,
									Unit:     metricstype.M,
								},
								{
									Type:     metricstype.CPU,
									Operator: metricstype.Std,
									Value:    10,
									Unit:     metricstype.M,
								},
								{
									Type:     metricstype.Memory,
									Operator: metricstype.Average,
									Value:    256,
									Unit:     metricstype.MiB,
								},
								{
									Type:     metricstype.Memory,
									Operator: metricstype.Std,
									Value:    10,
									Unit:     metricstype.MiB,
								},
							},
						},
					},
				},
			},
			expected: []framework.NodeScore{
				{Name: "node-1", Score: 5},
			},
		},
	}

	registeredPlugins := []st.RegisterPluginFunc{
		st.RegisterBindPlugin(defaultbinder.Name, defaultbinder.New),
		st.RegisterQueueSortPlugin(queuesort.Name, queuesort.New),
	}

	for _, tt := range tests {
		t.Run(tt.test, func(t *testing.T) {
			server := httptest.NewServer(http.HandlerFunc(func(resp http.ResponseWriter, req *http.Request) {
				bytes, err := json.Marshal(tt.watcherResponse)
				assert.Nil(t, err)
				resp.Write(bytes)
			}))
			defer server.Close()

			os.Setenv("LOAD_MONITOR_ADDRESS", server.URL)
			nodes := append([]*v1.Node{}, tt.nodes...)
			state := framework.NewCycleState()

			cs := testClientSet.NewSimpleClientset()
			informerFactory := informers.NewSharedInformerFactory(cs, 0)
			snapshot := newTestSharedLister(nil, nodes)

			fh, err := testutil.NewFramework(registeredPlugins, []config.PluginConfig{},
				"default-scheduler", runtime.WithClientSet(cs),
				runtime.WithInformerFactory(informerFactory), runtime.WithSnapshotSharedLister(snapshot))
			assert.Nil(t, err)
			p, _ := New(nil, fh)
			scorePlugin := p.(framework.ScorePlugin)

			var actualList framework.NodeScoreList
			for _, n := range tt.nodes {
				nodeName := n.Name
				score, status := scorePlugin.Score(context.Background(), state, tt.pod, nodeName)
				assert.True(t, status.IsSuccess())
				actualList = append(actualList, framework.NodeScore{Name: nodeName, Score: score})
			}
			assert.EqualValues(t, tt.expected, actualList)
		})
	}
}

func newTestSharedLister(pods []*v1.Pod, nodes []*v1.Node) *testSharedLister {
	nodeInfoMap := make(map[string]*framework.NodeInfo)
	nodeInfos := make([]*framework.NodeInfo, 0)
	for _, pod := range pods {
		nodeName := pod.Spec.NodeName
		if _, ok := nodeInfoMap[nodeName]; !ok {
			nodeInfoMap[nodeName] = framework.NewNodeInfo()
		}
		nodeInfoMap[nodeName].AddPod(pod)
	}
	for _, node := range nodes {
		if _, ok := nodeInfoMap[node.Name]; !ok {
			nodeInfoMap[node.Name] = framework.NewNodeInfo()
		}
		err := nodeInfoMap[node.Name].SetNode(node)
		if err != nil {
			log.Fatal(err)
		}
	}

	for _, v := range nodeInfoMap {
		nodeInfos = append(nodeInfos, v)
	}

	return &testSharedLister{
		nodes:       nodes,
		nodeInfos:   nodeInfos,
		nodeInfoMap: nodeInfoMap,
	}
}

// getPodWithContainersAndOverhead : length of contCPUReq and contMemReq should be same
func getPodWithContainersAndOverhead(overhead int64, initCPUReq int64, initMemReq int64,
	contCPUReq []int64, contMemReq []int64, label map[string]string) *v1.Pod {

	newPod := st.MakePod()
	newPod.Spec.Overhead = make(map[v1.ResourceName]resource.Quantity)
	newPod.Spec.Overhead[v1.ResourceCPU] = *resource.NewMilliQuantity(overhead, resource.DecimalSI)

	newPod.Spec.InitContainers = []v1.Container{
		{Name: "test-init"},
	}
	newPod.Spec.InitContainers[0].Resources.Requests = make(map[v1.ResourceName]resource.Quantity)
	newPod.Spec.InitContainers[0].Resources.Requests[v1.ResourceCPU] = *resource.NewMilliQuantity(initCPUReq, resource.DecimalSI)
	newPod.Spec.InitContainers[0].Resources.Requests[v1.ResourceMemory] = *resource.NewQuantity(initMemReq, resource.DecimalSI)

	for i := 0; i < len(contCPUReq); i++ {
		newPod.Container("test-container-" + strconv.Itoa(i))
	}
	for i, request := range contCPUReq {
		newPod.Spec.Containers[i].Resources.Requests = make(map[v1.ResourceName]resource.Quantity)
		newPod.Spec.Containers[i].Resources.Requests[v1.ResourceCPU] = *resource.NewMilliQuantity(request, resource.DecimalSI)
		newPod.Spec.Containers[i].Resources.Requests[v1.ResourceMemory] = *resource.NewQuantity(contMemReq[i], resource.DecimalSI)

		newPod.Spec.Containers[i].Resources.Limits = make(map[v1.ResourceName]resource.Quantity)
		newPod.Spec.Containers[i].Resources.Limits[v1.ResourceCPU] = *resource.NewMilliQuantity(request, resource.DecimalSI)
		newPod.Spec.Containers[i].Resources.Limits[v1.ResourceMemory] = *resource.NewQuantity(contMemReq[i], resource.DecimalSI)
	}
	for l, v := range label {
		newPod.Label(l, v)
	}

	return newPod.Obj()
}
