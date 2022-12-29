package rlscheduler

import (
	"context"
	"encoding/json"
	"log"
	"net/http"
	"net/http/httptest"
	"os"
	"testing"

	rlapi "github.com/charstal/load-monitor/pkg/api"
	"github.com/stretchr/testify/assert"

	v1 "k8s.io/api/core/v1"
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
	server := httptest.NewServer(http.HandlerFunc(func(resp http.ResponseWriter, req *http.Request) {
		bytes, err := json.Marshal(struct{}{})
		assert.Nil(t, err)
		resp.Write(bytes)
	}))
	os.Setenv("RL_SERVER_ADDRESS", server.URL)
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

	p, err := New(nil, fh)
	assert.NotNil(t, p)
	assert.Nil(t, err)

}

func TestScore(t *testing.T) {

	nodeResources := map[v1.ResourceName]string{
		v1.ResourceCPU:    "1000m",
		v1.ResourceMemory: "1Gi",
	}

	// var mega int64 = 1024 * 1024

	tests := []struct {
		test           string
		pod            *v1.Pod
		nodes          []*v1.Node
		rlResponce     rlapi.RLClientPredictResponce
		expected       framework.NodeScoreList
		preScoreStatus bool
	}{
		{
			test: "no label use DefaultMostLeastRequested",
			pod:  st.MakePod().Name("p").Obj(),
			nodes: []*v1.Node{
				st.MakeNode().Name("node-1").Capacity(nodeResources).Obj(),
			},
			expected: []framework.NodeScore{
				{Name: "node-1", Score: 100},
			},
			preScoreStatus: false,
		},
		{
			test: "rl normal",
			pod:  st.MakePod().Name("p").Label("course_id", "a").Obj(),
			nodes: []*v1.Node{
				st.MakeNode().Name("node-1").Capacity(nodeResources).Obj(),
				st.MakeNode().Name("node-2").Capacity(nodeResources).Obj(),
			},
			rlResponce: rlapi.RLClientPredictResponce{
				State:   "success",
				Message: "",
				Result: rlapi.PredictResponceResult{
					PodName: "p",
					Node:    "node-1",
				},
			},
			expected: []framework.NodeScore{
				{Name: "node-1", Score: 100},
				{Name: "node-2", Score: 0},
			},
			preScoreStatus: true,
		},

		{
			test: "rl server respose empty",
			pod:  st.MakePod().Name("p").Label("course_id", "a").Obj(),
			nodes: []*v1.Node{
				st.MakeNode().Name("node-1").Capacity(nodeResources).Obj(),
			},
			expected: []framework.NodeScore{
				{Name: "node-1", Score: 100},
			},
			preScoreStatus: true,
		},
	}

	registeredPlugins := []st.RegisterPluginFunc{
		st.RegisterBindPlugin(defaultbinder.Name, defaultbinder.New),
		st.RegisterQueueSortPlugin(queuesort.Name, queuesort.New),
	}

	for _, tt := range tests {
		t.Run(tt.test, func(t *testing.T) {
			server := httptest.NewServer(http.HandlerFunc(func(resp http.ResponseWriter, req *http.Request) {
				bytes, err := json.Marshal(tt.rlResponce)
				assert.Nil(t, err)
				resp.Write(bytes)
			}))
			defer server.Close()

			os.Setenv("RL_SERVER_ADDRESS", server.URL)
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
			preScorePlugin := p.(framework.PreScorePlugin)
			scorePlugin := p.(framework.ScorePlugin)

			status := preScorePlugin.PreScore(context.Background(), state, tt.pod, tt.nodes)
			assert.Equal(t, status.IsSuccess(), tt.preScoreStatus)

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
