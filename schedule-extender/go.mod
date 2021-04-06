module github.com/charstal/schedule-extender

go 1.15

require (
	github.com/patrickmn/go-cache v2.1.0+incompatible
	google.golang.org/grpc v1.27.1
	google.golang.org/protobuf v1.24.0
	k8s.io/api v0.19.0
	k8s.io/apimachinery v0.19.0
	k8s.io/component-base v0.19.0
	k8s.io/klog/v2 v2.2.0
	k8s.io/kube-scheduler v0.19.0 // indirect
	k8s.io/kubernetes v1.19.0
)

replace (
	// Below is added due to https://github.com/moby/term/pull/16
	golang.org/x/sys => golang.org/x/sys v0.0.0-20200826173525-f9321e4c35a6
	google.golang.org/grpc/naming => github.com/xiegeo/grpc-naming v1.29.1-alpha
	// google.golang.org/grpc => google.golang.org/grpc v1.27.0
	// Newer version of this breaks k8s.io/kubernetes v0.19.0
	gopkg.in/square/go-jose.v2 => gopkg.in/square/go-jose.v2 v2.2.2
	k8s.io/api => k8s.io/api v0.19.0
	k8s.io/apiextensions-apiserver => k8s.io/apiextensions-apiserver v0.19.0
	k8s.io/apimachinery => k8s.io/apimachinery v0.19.0
	k8s.io/apiserver => k8s.io/apiserver v0.19.0
	k8s.io/cli-runtime => k8s.io/cli-runtime v0.19.0
	k8s.io/client-go => k8s.io/client-go v0.19.0
	k8s.io/cloud-provider => k8s.io/cloud-provider v0.19.0
	k8s.io/cluster-bootstrap => k8s.io/cluster-bootstrap v0.19.0
	k8s.io/code-generator => k8s.io/code-generator v0.19.0
	k8s.io/component-base => k8s.io/component-base v0.19.0
	k8s.io/cri-api => k8s.io/cri-api v0.19.0
	k8s.io/csi-translation-lib => k8s.io/csi-translation-lib v0.19.0
	k8s.io/kube-aggregator => k8s.io/kube-aggregator v0.19.0
	k8s.io/kube-controller-manager => k8s.io/kube-controller-manager v0.19.0
	k8s.io/kube-proxy => k8s.io/kube-proxy v0.19.0
	k8s.io/kube-scheduler => k8s.io/kube-scheduler v0.19.0
	k8s.io/kubectl => k8s.io/kubectl v0.19.0
	k8s.io/kubelet => k8s.io/kubelet v0.19.0
	k8s.io/kubernetes => k8s.io/kubernetes v1.19.0
	k8s.io/legacy-cloud-providers => k8s.io/legacy-cloud-providers v0.19.0
	k8s.io/metrics => k8s.io/metrics v0.19.0
	k8s.io/sample-apiserver => k8s.io/sample-apiserver v0.19.0
)
