# statisticsbasedloadvariationbalancing

## 算法
算法改进自[loadVariation](https://github.com/kubernetes-sigs/scheduler-plugins/tree/master/kep/61-Trimaran-real-load-aware-scheduling#loadvariationriskbalancing-plugin)

原公式

$$
risk =  \frac{(average_{node} + request_{pod} + margin * stDev_{node}^{\frac{1}{sensitivity}})}{2}
$$


改进公式

$$
risk =  \frac{(average_{node} + average_{pod} + margin * Max(stDev_{node}, stDev_{pod})^{\frac{1}{sensitivity}})}{2}
$$

`average` 与 `stDev` 范围为(0,1)，`average` 为一段时间的平均利用率，`stDev`是一段时间的利用率标准差。`margin` 和 `sensitivity` 用来放大`stDev`的影响，推荐值为1和2。除以2为了使risk放缩到0到1。

risk 是针对节点上的各种资源独立计算的。 令 *worstRisk* 为计算出的风险中的最大值，最终节点的调度分数为。


$$score = maxScore * (1 - worstRisk)$$

## 工程实现逻辑

- metrics：node的实时数据指标
- statistics：label统计信息
- window：实时数据统计窗口时间
- r：资源

1. 若无course label，直接拒绝调度
2. 若 metrics 不存在或者window的end时间距离当前时间超过 MetricsAgentReportingIntervalSeconds 则使用DefaultMostLeastRequested 算法

$$score = Min(1 - \frac{request_{r}}{alocatable_{r}}) * 100$$

3. 若 statistics 不存在则使用 requestedBasedLoadVariation
  - 上文提到原公式过程

$$
risk =  \frac{(average_{node} + request_{pod} + margin * stDev_{node}^{\frac{1}{sensitivity}})}{2}
$$

4. 若statistics和metrics都存在
  - 使用改进公式

$$
risk =  \frac{(average_{node} + average_{pod} + margin * Max(stDev_{node}, stDev_{pod})^{\frac{1}{sensitivity}})}{2}
$$

在某一时刻，调度器接受调度请求 $s$ 。调度器得到最新的metrics，记为 $m_{t^{'}}$。


```
|-------------------timeline----------------------->|
|--------|-----------------------|------------------|
|--collector更新时间t'-------调度请求时间t--------------|
```

$t^{'}$ 为collector定时从load monitor爬取的数据时间，准确来说
是 load monitor 生成的最新时间段的窗口时间的end时间。

从 $t^{'}$ 到 $t$ 时间范围内会有其他的调度任务记为 $s_{0}, s_{1}, s_{2}...$ 

$$average_{pod} = \sum_{i=0}^n mean_{pod}^{statistics_{si}}$$

$$stDev_{pod} = \max_{i=0}^n stDev_{pod}^{statistics_{si}} $$