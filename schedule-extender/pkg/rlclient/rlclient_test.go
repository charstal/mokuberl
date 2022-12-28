package rlclient

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestRLClient(t *testing.T) {
	_, err := NewRLClient()
	assert.Nil(t, err)

}

func TestHeartbeat(t *testing.T) {
	client, err := NewRLClient()
	assert.Nil(t, err)

	assert.Equal(t, client.Valid(), true)
}

func TestPredict(t *testing.T) {
	client, err := NewRLClient()
	assert.Nil(t, err)

	podName := "123456"
	podLabel := "a"
	nodes := []string{"a", "b"}
	err = client.Predict(podName, podLabel, nodes)
	assert.Nil(t, err)

	nodeName, ok := client.Get(podName)
	assert.Equal(t, ok, true)
	assert.Equal(t, nodeName, "a")

	_, ok = client.Get("not found")
	assert.Equal(t, ok, false)

	// time.Sleep(120 * time.Second)
	// _, ok = client.Get(podName)
	// assert.Equal(t, ok, false)

}
