# Cache

## 目的
`Cache` 库主要用来缓存已经被调度的Pod（NodeName为空）。

实质上是为了优化`Collector`拉取的数据的时间与实际调度时时间之间的差距。

cache会通过kubernetes的infomer机制，它会监听所有事件，会记录所有类型为pod且成功的调度的pod放入缓存之中，并记录发生时间，以提供算法使用。以防缓存过大，cache会定时（5min）清理所有超过时限（在当前时间-metricsAgentReportingIntervalSeconds时间之前）的pod。



## 实现方式

主要还是通过

```go
// handle framewor.Handle
type FilteringResourceEventHandler struct {
	FilterFunc func(obj interface{}) bool
	Handler    ResourceEventHandler
}

handle.SharedInformerFactory().Core().V1().Pods().Informer().AddEventHandler(clientcache.FilteringResourceEventHandler{}
```

利用该方法可以提供一个 `filter`和`handler`，当`filter`为`true`时，再采用`handler`进行处理。

同时必须实现三个接口

```go
OnAdd(obj interface{})
OnUpdate(oldObj, newObj interface{})
OnDelete(obj interface{})
```