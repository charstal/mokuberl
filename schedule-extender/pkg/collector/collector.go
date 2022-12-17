package collector

import (
	"os"
	"sync"
	"time"

	loadmonitorapi "github.com/charstal/load-monitor/pkg/api"
	"github.com/charstal/load-monitor/pkg/metricstype"
	"github.com/charstal/schedule-extender/apis/config"
	"k8s.io/klog/v2"
)

const (
	metricsUpdateIntervalSeconds = 30
	heartbeatIntervalSeconds     = 10
	heartbeatTimeoutSeconds      = 2 * metricsUpdateIntervalSeconds

	LoadMonitorAddressKey = "LOAD_MONITOR_ADDRESS"
)

type Collector struct {
	// load monitor client
	client loadmonitorapi.Client

	// metrics from load monitor
	metrics           metricstype.WatcherMetrics
	statistics        metricstype.StatisticsData
	lastHeartBeatTime int64
	mu                sync.RWMutex
}

var (
	loadMonitorAddress string
)

func NewCollector() (*Collector, error) {
	var ok bool
	loadMonitorAddress, ok = os.LookupEnv(LoadMonitorAddressKey)
	if !ok {
		loadMonitorAddress = config.DefaultLoadMonitorAddress
	}
	klog.InfoS("load monitor address", loadMonitorAddress)
	client, err := loadmonitorapi.NewServiceClient(loadMonitorAddress)
	if err != nil {
		return nil, err
	}

	collector := &Collector{
		client: client,
	}

	collector.heartbeat()
	collector.update()

	go func() {
		ticker := time.NewTicker(time.Second * heartbeatIntervalSeconds)
		for range ticker.C {
			err = collector.heartbeat()
			if err != nil {
				klog.ErrorS(err, "Unable to heartbeat load monitor")
			}
		}
	}()

	go func() {
		ticker := time.NewTicker(time.Second * metricsUpdateIntervalSeconds)
		for range ticker.C {
			err = collector.update()
			if err != nil {
				klog.ErrorS(err, "Unable to update metrics")
			}
		}
	}()

	return collector, nil
}

func (c *Collector) GetNodeMetrics(nodeName string) (*[]metricstype.Metric, *metricstype.Window) {
	allMetrics, time := c.GetNodeAllMetrics()
	// This happens if metrics were never populated since scheduler started
	if allMetrics.NodeMetricsMap == nil {
		klog.ErrorS(nil, "Metrics not available from load monitor")
		return nil, time
	}
	// Check if node is new (no metrics yet) or metrics are unavailable due to 404 or 500
	if _, ok := allMetrics.NodeMetricsMap[nodeName]; !ok {
		klog.ErrorS(nil, "Unable to find metrics for node", "nodeName", nodeName)
		return nil, time
	}

	met := allMetrics.NodeMetricsMap[nodeName].Metrics
	return &met, time
}

func (c *Collector) GetStatisticsOfLabel(label string) ([]metricstype.Metric, *metricstype.Window) {
	statis, time := c.GetAllStatistics()

	if statis.StatisticsMap == nil {
		klog.Error("Empty StatistcMap")
		return nil, time
	}

	if _, ok := statis.StatisticsMap[label]; !ok {
		all := statis.StatisticsMap[metricstype.ALL_COURSE_LABEL].Metrics
		if len(all) != 0 {
			klog.InfoS("Unable to find metrics for label", "label name", label, "So instead of all method")
		} else {
			klog.InfoS("Unable to find metrics for label", "label name", label, "and cannot find metrics of all")
			all = nil
		}
		return all, time
	}

	met := statis.StatisticsMap[label].Metrics
	return met, time
}

func (c *Collector) GetNodeAllMetrics() (*metricstype.Data, *metricstype.Window) {
	c.mu.RLock()
	node := c.metrics.Data
	time := c.metrics.Window
	c.mu.RUnlock()
	return &node, &time
}

func (c *Collector) GetAllStatistics() (*metricstype.StatisticsData, *metricstype.Window) {
	c.mu.RLock()
	time := c.metrics.Window
	statis := c.statistics
	c.mu.RUnlock()
	return &statis, &time
}

func (c *Collector) Valid() bool {
	if !c.heartbeatCheck() {
		return false
	}
	if c.metrics.IsNil() || c.metrics.Data.IsNil() {
		return false
	}
	if c.statistics.IsNil() || c.statistics.StatisticsMap.IsNil() {
		return false
	}

	return true
}

func (c *Collector) heartbeatCheck() bool {
	now := time.Now().Unix()
	return now-c.lastHeartBeatTime <= heartbeatTimeoutSeconds
}

func (c *Collector) update() error {
	if !c.heartbeatCheck() {
		klog.Error("collector heartbeat over time")
		return nil
	}
	metrics, err := c.client.GetLatestWatcherMetrics()
	if err != nil {
		klog.Error(err, "cannot fetch metrics from load monitor")
		return err
	}

	c.mu.Lock()
	if metrics != nil {
		c.metrics = *metrics
	}
	c.updateStatistics(&metrics.Statistics)
	c.mu.Unlock()
	return nil
}

func (c *Collector) updateStatistics(data *metricstype.StatisticsData) {
	if c.statistics.StatisticsMap == nil {
		c.statistics = *data
		return
	}
	for key := range data.StatisticsMap {
		c.statistics.StatisticsMap[key] = data.StatisticsMap[key]
	}
}

func (c *Collector) heartbeat() error {
	err := c.client.Healthy()
	if err != nil {
		klog.Error(err, "fail: cannot get hearbeat load monitor")
		return err
	}

	c.mu.Lock()
	c.lastHeartBeatTime = time.Now().Unix()
	c.mu.Unlock()

	return nil
}
