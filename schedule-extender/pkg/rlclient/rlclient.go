package rlclient

import (
	"os"
	"sync"
	"time"

	rlclientapi "github.com/charstal/load-monitor/pkg/api"
	"github.com/charstal/schedule-extender/apis/config"
	"github.com/zekroTJA/timedmap"
	"k8s.io/klog/v2"
)

const (
	metricsUpdateIntervalSeconds = 30
	heartbeatIntervalSeconds     = 10
	heartbeatTimeoutSeconds      = 2 * metricsUpdateIntervalSeconds

	cacheCleanupIntervalSeconds = 5 * 60 // 300s
	cacheExpiredIntercalSeconds = 60
	repeatRequestTimeoutSeconds = 10

	RLServerAddressKey = "RL_SERVER_ADDRESS"
)

type CacheEntry struct {
	SendRequestTime      int64
	Valid                bool
	ReceivedResponseTime int64
	Node                 string
}

type RLClient struct {
	client            rlclientapi.RLClient
	lastHeartBeatTime int64
	mu                sync.RWMutex
	cache             *timedmap.TimedMap
}

var (
	rlServerAddress string
)

func NewRLClient() (*RLClient, error) {
	var ok bool
	rlServerAddress, ok = os.LookupEnv(RLServerAddressKey)
	if !ok {
		rlServerAddress = config.DefaultRLServerAddress
	}
	klog.InfoS("rl server address", rlServerAddress)
	client, err := rlclientapi.NewRLClient(rlServerAddress)
	if err != nil {
		return nil, err
	}

	rlClient := &RLClient{
		client: client,
		cache:  timedmap.New(cacheCleanupIntervalSeconds * time.Second),
	}

	rlClient.heartbeat()
	go func() {
		ticker := time.NewTicker(time.Second * heartbeatIntervalSeconds)
		for range ticker.C {
			err = rlClient.heartbeat()
			if err != nil {
				klog.ErrorS(err, "Unable to heartbeat load monitor")
			}
		}
	}()

	return rlClient, nil
}

func (c *RLClient) Valid() bool {
	return c.heartbeatCheck()
}

func (c *RLClient) heartbeatCheck() bool {
	now := time.Now().Unix()
	return now-c.lastHeartBeatTime <= heartbeatTimeoutSeconds
}

func (c *RLClient) heartbeat() error {
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

// async send to rl server
func (c *RLClient) Predict(podName, podLabel string, nodes []string) error {
	request, err := rlclientapi.MakePredictRequest(podName, podLabel, nodes)
	if err != nil {
		return err
	}

	if !c.cache.Contains(podName) {
		value, ok := c.cache.GetValue(podName).(CacheEntry)
		now := time.Now().Unix()
		if !ok || (!value.Valid && now-value.SendRequestTime >= repeatRequestTimeoutSeconds) {
			go func() {
				cacheEntry := CacheEntry{
					SendRequestTime: now,
					Valid:           false,
				}
				c.cache.Set(podName, cacheEntry, cacheExpiredIntercalSeconds*time.Second)
				// allow repeat 3 times
				for i := 0; i < 3; i++ {
					resp, err := c.client.Predict(request)
					if err == nil {
						podName := resp.Result.PodName
						nodeName := resp.Result.Node
						c.updateCache(podName, nodeName)
						break
					}
				}
			}()
		}

	}

	// Todo need to opt the time
	// the longest time waiting server to responce
	time.Sleep(3 * time.Second)
	return nil
}

func (c *RLClient) updateCache(podName, nodeName string) {
	klog.InfoS("for pod", podName, "the rl schduler result is node", nodeName)
	now := time.Now().Unix()
	value, ok := c.cache.GetValue(podName).(CacheEntry)
	if !ok {
		panic("cannot find" + podName)
	}
	value.Node = nodeName
	value.Valid = true
	value.ReceivedResponseTime = now

	c.cache.Set(podName, value, cacheExpiredIntercalSeconds*time.Second)
}

func (c *RLClient) Get(podName string) (string, bool) {
	value, ok := c.cache.GetValue(podName).(CacheEntry)

	return value.Node, ok || value.Valid
}
