package algorithm

import (
	"math"

	"github.com/charstal/schedule-extender/pkg/resourcestats"
	v1 "k8s.io/api/core/v1"
	"k8s.io/klog/v2"
	"k8s.io/kubernetes/pkg/scheduler/framework"
)

const (
	// DefaultMilliCPURequest defines default milli cpu request number.
	DefaultMilliCPURequest int64 = 100 // 0.1 core
	// DefaultMemoryRequest defines default memory request size.
	DefaultMemoryRequest int64 = 200 * 1024 * 1024 // 200 MB

)

type resourceToValueMap map[v1.ResourceName]int64

func DefaultMostLeastRequested(nodeInfo *framework.NodeInfo, pod *v1.Pod) (int64, *framework.Status) {
	if nodeInfo == nil {
		return 0, framework.NewStatus(framework.Error, "node not found")
	}

	requested := make(resourceToValueMap)
	allocatable := make(resourceToValueMap)
	for _, resource := range resourcestats.ResourceTypeList {
		alloc, req := calculateResourceAllocatableRequest(nodeInfo, pod, resource)
		if alloc != 0 {
			// Only fill the extended resource entry when it's non-zero.
			allocatable[resource], requested[resource] = alloc, req
		}
	}

	score := framework.MaxNodeScore
	for _, resource := range resourcestats.ResourceTypeList {
		req := requested[resource]
		cap, ok := allocatable[resource]
		if !ok || cap == 0 {
			continue
		}
		partScore := (1 - float64(req)*1.0/float64(cap)) * float64(framework.MaxNodeScore)
		// fmt.Println(partScore)
		score = int64(
			math.Max(0,
				math.Min(
					float64(score),
					float64(partScore),
				)))
	}

	node := nodeInfo.Node()
	if score == 100 {
		klog.Warningf("Please add request to the pod %v, allocatableResource %v, requestedResource %v", pod.Name, allocatable, requested)
	}
	klog.V(10).InfoS("Listing internal info for allocatable resources, requested resources and score", "pod",
		klog.KObj(pod), "node", klog.KObj(node), "allocatableResource",
		allocatable, "requestedResource", requested, "resourceScore", score,
	)
	return score, nil
}

// calculateResourceAllocatableRequest returns 2 parameters:
// - 1st param: quantity of allocatable resource on the node.
// - 2nd param: aggregated quantity of requested resource on the node.
// Note: if it's an extended resource, and the pod doesn't request it, (0, 0) is returned.
func calculateResourceAllocatableRequest(nodeInfo *framework.NodeInfo, pod *v1.Pod, resource v1.ResourceName) (int64, int64) {

	requested := nodeInfo.Requested

	podRequest := calculatePodResourceRequest(pod, resource)
	// If it's an extended resource, and the pod doesn't request it. We return (0, 0)
	// as an implication to bypass scoring on this resource.
	// if podRequest == 0 && schedutil.IsScalarResourceName(resource) {
	// 	return 0, 0
	// }
	switch resource {
	case v1.ResourceCPU:
		return nodeInfo.Allocatable.MilliCPU, (requested.MilliCPU + podRequest)
	case v1.ResourceMemory:
		return nodeInfo.Allocatable.Memory, (requested.Memory + podRequest)
	case v1.ResourceEphemeralStorage:
		return nodeInfo.Allocatable.EphemeralStorage, (nodeInfo.Requested.EphemeralStorage + podRequest)
	default:
		if _, exists := nodeInfo.Allocatable.ScalarResources[resource]; exists {
			return nodeInfo.Allocatable.ScalarResources[resource], (nodeInfo.Requested.ScalarResources[resource] + podRequest)
		}
	}
	klog.V(10).InfoS("Requested resource is omitted for node score calculation", "resourceName", resource)
	return 0, 0
}

// calculatePodResourceRequest returns the total non-zero requests. If Overhead is defined for the pod and the
// PodOverhead feature is enabled, the Overhead is added to the result.
// podResourceRequest = max(sum(podSpec.Containers), podSpec.InitContainers) + overHead
func calculatePodResourceRequest(pod *v1.Pod, resource v1.ResourceName) int64 {
	var podRequest int64
	for i := range pod.Spec.Containers {
		container := &pod.Spec.Containers[i]
		value := GetRequestForResource(resource, &container.Resources.Requests, true)
		podRequest += value
	}

	for i := range pod.Spec.InitContainers {
		initContainer := &pod.Spec.InitContainers[i]
		value := GetRequestForResource(resource, &initContainer.Resources.Requests, true)
		if podRequest < value {
			podRequest = value
		}
	}

	// If Overhead is being utilized, add to the total requests for the pod
	if pod.Spec.Overhead != nil {
		if quantity, found := pod.Spec.Overhead[resource]; found {
			podRequest += quantity.Value()
		}
	}

	return podRequest
}

// GetRequestForResource returns the requested values unless nonZero is true and there is no defined request
// for CPU and memory.
// If nonZero is true and the resource has no defined request for CPU or memory, it returns a default value.
func GetRequestForResource(resource v1.ResourceName, requests *v1.ResourceList, nonZero bool) int64 {
	if requests == nil {
		return 0
	}
	switch resource {
	case v1.ResourceCPU:
		// Override if un-set, but not if explicitly set to zero
		if _, found := (*requests)[v1.ResourceCPU]; !found && nonZero {
			return DefaultMilliCPURequest
		}
		return requests.Cpu().MilliValue()
	case v1.ResourceMemory:
		// Override if un-set, but not if explicitly set to zero
		if _, found := (*requests)[v1.ResourceMemory]; !found && nonZero {
			return DefaultMemoryRequest
		}
		return requests.Memory().Value()
	case v1.ResourceEphemeralStorage:
		quantity, found := (*requests)[v1.ResourceEphemeralStorage]
		if !found {
			return 0
		}
		return quantity.Value()
	default:
		quantity, found := (*requests)[resource]
		if !found {
			return 0
		}
		return quantity.Value()
	}
}
