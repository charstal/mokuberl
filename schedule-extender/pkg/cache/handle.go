package cache

import (
	"fmt"
	"sort"
	"sync"
	"time"

	"github.com/charstal/load-monitor/pkg/metricstype"
	v1 "k8s.io/api/core/v1"
	utilruntime "k8s.io/apimachinery/pkg/util/runtime"
	clientcache "k8s.io/client-go/tools/cache"
	"k8s.io/klog/v2"
	"k8s.io/kubernetes/pkg/scheduler/framework"
)

const (
	// pod cache cleanup interval minitues
	CacheCleanupIntervalMinutes = 5
	// load monitor fetching intervarl
	MetricsAgentReportingIntervalSeconds = 60
)

var _ clientcache.ResourceEventHandler = &PodAssignEventHandler{}

// This event handler watches assigned Pod and caches them locally
type PodAssignEventHandler struct {
	// Maintains the node-name to podInfo mapping for pods successfully bound to nodes
	ScheduledPodsCache map[string][]podInfo
	sync.RWMutex
}

// Stores Timestamp and Pod spec info object
type podInfo struct {
	// This timestamp is initialised when adding it to ScheduledPodsCache after successful binding
	Timestamp time.Time
	Pod       *v1.Pod
}

// Returns a new instance of PodAssignEventHandler, after starting a background go routine for cache cleanup
func New() *PodAssignEventHandler {
	p := PodAssignEventHandler{ScheduledPodsCache: make(map[string][]podInfo)}
	go func() {
		cacheCleanerTicker := time.NewTicker(time.Minute * CacheCleanupIntervalMinutes)
		for range cacheCleanerTicker.C {
			p.cleanupCache()
		}
	}()
	return &p
}

// AddToHandle : add event handler to framework handle
func (p *PodAssignEventHandler) AddToHandle(handle framework.Handle) {
	handle.SharedInformerFactory().Core().V1().Pods().Informer().AddEventHandler(
		clientcache.FilteringResourceEventHandler{
			FilterFunc: func(obj interface{}) bool {
				switch t := obj.(type) {
				case *v1.Pod:
					return isAssignedAndHaveLabel(t)
				case clientcache.DeletedFinalStateUnknown:
					if pod, ok := t.Obj.(*v1.Pod); ok {
						return isAssignedAndHaveLabel(pod)
					}
					utilruntime.HandleError(fmt.Errorf("unable to convert object %T to *v1.Pod", obj))
					return false
				default:
					utilruntime.HandleError(fmt.Errorf("unable to handle object: %T", obj))
					return false
				}
			},
			Handler: p,
		},
	)
}

func (p *PodAssignEventHandler) OnAdd(obj interface{}) {
	pod := obj.(*v1.Pod)
	p.updateCache(pod)
}

func (p *PodAssignEventHandler) OnUpdate(oldObj, newObj interface{}) {
	oldPod := oldObj.(*v1.Pod)
	newPod := newObj.(*v1.Pod)

	if oldPod.Spec.NodeName != newPod.Spec.NodeName {
		p.updateCache(newPod)
		p.OnDelete(oldPod)
	}
}

func (p *PodAssignEventHandler) OnDelete(obj interface{}) {
	pod := obj.(*v1.Pod)
	nodeName := pod.Spec.NodeName
	if nodeName == "" {
		return
	}
	p.Lock()
	defer p.Unlock()
	if _, ok := p.ScheduledPodsCache[nodeName]; !ok {
		return
	}
	for i, v := range p.ScheduledPodsCache[nodeName] {
		n := len(p.ScheduledPodsCache[nodeName])
		if pod.ObjectMeta.UID == v.Pod.ObjectMeta.UID {
			klog.V(10).InfoS("Deleting pod", "pod", klog.KObj(v.Pod))
			copy(p.ScheduledPodsCache[nodeName][i:], p.ScheduledPodsCache[nodeName][i+1:])
			p.ScheduledPodsCache[nodeName][n-1] = podInfo{}
			p.ScheduledPodsCache[nodeName] = p.ScheduledPodsCache[nodeName][:n-1]
			break
		}
	}

}

func (p *PodAssignEventHandler) updateCache(pod *v1.Pod) {
	if pod.Spec.NodeName == "" {
		return
	}
	p.Lock()
	p.ScheduledPodsCache[pod.Spec.NodeName] = append(p.ScheduledPodsCache[pod.Spec.NodeName],
		podInfo{Timestamp: time.Now(), Pod: pod})
	p.Unlock()
}

// Deletes podInfo entries that are older than metricsAgentReportingIntervalSeconds. Also deletes node entry if empty
func (p *PodAssignEventHandler) cleanupCache() {
	p.Lock()
	defer p.Unlock()
	for nodeName := range p.ScheduledPodsCache {
		cache := p.ScheduledPodsCache[nodeName]
		curTime := time.Now()

		idx := sort.Search(len(cache), func(i int) bool {
			return cache[i].Timestamp.Add(MetricsAgentReportingIntervalSeconds * time.Second).After(curTime)
		})
		if idx == len(cache) {
			continue
		}
		n := copy(cache, cache[idx:])
		for j := n; j < len(cache); j++ {
			cache[j] = podInfo{}
		}
		cache = cache[:n]

		if len(cache) == 0 {
			delete(p.ScheduledPodsCache, nodeName)
		} else {
			p.ScheduledPodsCache[nodeName] = cache
		}
	}
}

// Checks and returns true if the pod is assigned to a node
func isAssignedAndHaveLabel(pod *v1.Pod) bool {
	_, ok := pod.Labels[metricstype.DEFAULT_COURSE_LABEL]
	klog.InfoS("pod add into cache", klog.KObj(pod))
	return len(pod.Spec.NodeName) != 0 && ok
}
