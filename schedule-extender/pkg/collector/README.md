# Collector

```go
metricsUpdateIntervalSeconds = 30                                   // 指标采集间隔
heartbeatIntervalSeconds     = 10                                   // 心跳时间间隔
heartbeatTimeoutSeconds      = 2 * metricsUpdateIntervalSeconds     // 心跳超时时间

LoadMonitorAddressKey = "LOAD_MONITOR_ADDRESS"                      // load monitor的url地址
```

`Collector` 使用异步更新Metrics的方式。
相比同步调度拉取数据的方式，异步更新的方式，网络压力更小，可用性更高。

Metrics主要分为两类，可查看[example](./example.json)：
- data （`data`字段下），node的实时监测数据指标

```json
// 
 "data": {
        "NodeMetricsMap": {
            "k8s-node02": {
                "metrics": [
                    {
                        "name": "kube_node_status_capacity",
                        "type": "cpu",
                        "operator": "Capacity",
                        "rollup": "Latest",
                        "value": 8,
                        "unit": "core"
                    },
                    ...
                ],      
                "tags": {},
                "metadata": {
                    "dataCenter": ""
                }
            },
            ...
        }
 }
```
- statistics （`statistics`字段下），pod的offline统计数据
```json
// statistics
"statistics": {
    "StatisticsMap": {
        "10.244.2.128:8443": {
            "metrics": [
                {
                    "name": "statistic",
                    "type": "cpu",
                    "operator": "Std",
                    "rollup": "15d",
                    "value": 0.4585529424024004,
                    "unit": "m"
                },
                ...
            ]
        },
        ...
    }
}
```

利用一个`mutex`保护数据并发读写。

`client` 来自[load monitor](https://github.com/charstal/load-monitor)下api的`client.go`


`NewCollector`将会构造一个`Collector`，会创建两个 goroutine

- heartbeat：每 `heartbeatIntervalSeconds` 时间调用 client 的Healthy接口，当无err则认为是成功连通，并更新 `lastHeartBeatTime`

- update：每 `metricsUpdateIntervalSeconds` 时间，先回检查心跳是否正常，不正常则跳过，减少网络带宽。然后通过调用 client 的 `GetLatestWatcherMetrics`获得所有的metrics数据。 让后更新metrics 存储原始的metrics，然后增量更新 Statistics，主要防止 Statistics 不可用。



对外提供五个接口

- GetNodeMetrics：获得某个pod的metrics
- GetStatisticsOfLabel：获得某个label的statistics
- GetNodeAllMetrics：获得所有metrics和时间窗口
- GetAllStatistics： 获得所有statistics和时间窗口
- Valid： 检查collector是否可用
  - 心跳检查
  - metircs是否有效
  - statistics是否有效
  