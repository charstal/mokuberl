package collector

import (
	"fmt"
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestCollect(t *testing.T) {
	c, err := NewCollector()
	assert.Nil(t, err)

	fmt.Printf("%v", c)
}

func TestCheckValid(t *testing.T) {
	c, err := NewCollector()
	assert.Nil(t, err)
	valid := c.Valid()

	assert.Equal(t, true, valid)
}

func TestCollectionData(t *testing.T) {
	c, err := NewCollector()
	assert.Nil(t, err)

	data, time := c.GetAllStatistics()
	fmt.Printf("%v", data)

	fmt.Printf("%v", time)
}
