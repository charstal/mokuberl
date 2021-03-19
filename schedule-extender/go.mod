module github.com/charstal/schedule-extender

go 1.15

require (
	github.com/golang/protobuf v1.4.3
	github.com/google/go-cmp v0.5.2 // indirect
	github.com/prometheus/client_golang v1.9.0 // indirect
	github.com/stretchr/testify v1.5.1 // indirect
	google.golang.org/grpc v1.36.0
	google.golang.org/grpc/cmd/protoc-gen-go-grpc v1.1.0 // indirect
	google.golang.org/grpc/examples v0.0.0-20210309003715-fce74a94bdff // indirect
	google.golang.org/protobuf v1.25.0
	k8s.io/api v0.19.8 // indirect
	k8s.io/apimachinery v0.19.8
	k8s.io/component-base v0.19.8
	k8s.io/klog/v2 v2.2.0 // indirect
	k8s.io/kube-scheduler v0.19.8 // indirect
	k8s.io/kubernetes v1.19.8
)

replace (
	k8s.io/api => k8s.io/api v0.19.8
	k8s.io/apiextensions-apiserver => k8s.io/apiextensions-apiserver v0.19.8
	k8s.io/apimachinery => k8s.io/apimachinery v0.19.8
	k8s.io/apiserver => k8s.io/apiserver v0.19.8
	k8s.io/cli-runtime => k8s.io/cli-runtime v0.19.8
	k8s.io/client-go => k8s.io/client-go v0.19.8
	k8s.io/cloud-provider => k8s.io/cloud-provider v0.19.8
	k8s.io/cluster-bootstrap => k8s.io/cluster-bootstrap v0.19.8
	k8s.io/code-generator => k8s.io/code-generator v0.19.8
	k8s.io/component-base => k8s.io/component-base v0.19.8
	k8s.io/cri-api => k8s.io/cri-api v0.19.8
	k8s.io/csi-translation-lib => k8s.io/csi-translation-lib v0.19.8
	k8s.io/kube-aggregator => k8s.io/kube-aggregator v0.19.8
	k8s.io/kube-controller-manager => k8s.io/kube-controller-manager v0.19.8
	k8s.io/kube-proxy => k8s.io/kube-proxy v0.19.8
	k8s.io/kube-scheduler => k8s.io/kube-scheduler v0.19.8
	k8s.io/kubectl => k8s.io/kubectl v0.19.8
	k8s.io/kubelet => k8s.io/kubelet v0.19.8
	k8s.io/kubernetes => k8s.io/kubernetes v1.19.8
	k8s.io/legacy-cloud-providers => k8s.io/legacy-cloud-providers v0.19.8
	k8s.io/metrics => k8s.io/metrics v0.19.8
	k8s.io/sample-apiserver => k8s.io/sample-apiserver v0.19.8
)
